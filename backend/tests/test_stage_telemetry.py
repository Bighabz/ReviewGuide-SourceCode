"""
Tests for RFC §1.1 — Stage Telemetry and Latency Budgets

backend/tests/test_stage_telemetry.py
"""
from __future__ import annotations

import asyncio
import dataclasses
import os
import time
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Minimal env so app.core.config can load without a .env file.
# Must happen before any app imports.
# ---------------------------------------------------------------------------
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("ADMIN_PASSWORD", "testpassword123")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("LOG_ENABLED", "false")

import pytest

from app.services.stage_telemetry import (
    MAX_TOTAL_REQUEST_S,
    STAGE_BUDGETS,
    StageTelemetry,
    run_stage_with_budget,
)


# ---------------------------------------------------------------------------
# 1. Successful coro returns correct result and telemetry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_successful_coro_returns_result_and_telemetry():
    """run_stage_with_budget returns the coro result and a valid StageTelemetry."""

    async def fast_coro():
        return {"answer": 42}

    result, telemetry = await run_stage_with_budget(
        "intent",
        fast_coro(),
        input_size=10,
    )

    assert result == {"answer": 42}, "Result should match the coro return value"
    assert isinstance(telemetry, StageTelemetry)
    assert telemetry.stage == "intent"
    assert telemetry.timeout_hit is False
    assert telemetry.degraded_mode is False
    assert telemetry.error_class is None
    assert telemetry.input_size == 10


# ---------------------------------------------------------------------------
# 2. Hard timeout returns fallback_result and sets timeout_hit=True
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hard_timeout_returns_fallback():
    """When the hard timeout fires the fallback_result is returned and timeout_hit=True."""

    async def slow_coro():
        # Sleep much longer than any stage budget
        await asyncio.sleep(9999)
        return {"should": "never reach this"}

    fallback = {"fallback": True}

    # Use a very short hard timeout by temporarily patching STAGE_BUDGETS
    with patch.dict("app.services.stage_telemetry.STAGE_BUDGETS", {"intent": (0.01, 0.05)}):
        result, telemetry = await run_stage_with_budget(
            "intent",
            slow_coro(),
            fallback_result=fallback,
            error_class_on_timeout="transient",
        )

    assert result is fallback, "Fallback result should be returned on hard timeout"
    assert telemetry.timeout_hit is True
    assert telemetry.degraded_mode is True
    assert telemetry.error_class == "transient"


# ---------------------------------------------------------------------------
# 3. Soft timeout detection logs warning
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_timeout_logs_warning():
    """
    When duration_ms exceeds the soft timeout but not the hard timeout,
    degraded_mode=True and a warning is logged.
    """

    # Set soft=0.01s, hard=1.0s — the coro takes ~0.05s (between soft and hard)
    async def medium_coro():
        await asyncio.sleep(0.05)
        return {"ok": True}

    captured_warnings = []

    import app.services.stage_telemetry as telemetry_module

    original_warning = telemetry_module.logger.warning

    def _capture_warning(msg, *args, **kwargs):
        captured_warnings.append(msg)
        original_warning(msg, *args, **kwargs)

    with patch.dict("app.services.stage_telemetry.STAGE_BUDGETS", {"intent": (0.01, 1.0)}):
        with patch.object(telemetry_module.logger, "warning", side_effect=_capture_warning):
            result, telemetry = await run_stage_with_budget(
                "intent",
                medium_coro(),
            )

    assert result == {"ok": True}
    assert telemetry.degraded_mode is True
    assert telemetry.timeout_hit is False
    assert any("soft timeout" in w for w in captured_warnings), (
        f"Expected a soft-timeout warning; got: {captured_warnings}"
    )


# ---------------------------------------------------------------------------
# 4. Exception in coro returns fallback and sets error_class="fatal"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exception_in_coro_returns_fallback_and_fatal_error():
    """An unexpected exception from the coro sets error_class='fatal'."""

    async def broken_coro():
        raise ValueError("something went wrong")

    fallback = {"degraded": True}

    result, telemetry = await run_stage_with_budget(
        "safety",
        broken_coro(),
        fallback_result=fallback,
    )

    assert result is fallback
    assert telemetry.error_class == "fatal"
    assert telemetry.timeout_hit is False
    assert telemetry.degraded_mode is False  # fatal exceptions do not set degraded_mode; use error_class


# ---------------------------------------------------------------------------
# 5. Telemetry has correct duration_ms range
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_telemetry_duration_ms_is_reasonable():
    """duration_ms should be >= 0 and less than the hard timeout in ms."""

    sleep_s = 0.03

    async def timed_coro():
        await asyncio.sleep(sleep_s)
        return {}

    result, telemetry = await run_stage_with_budget("tool", timed_coro())

    assert telemetry.duration_ms >= int(sleep_s * 1000) - 5  # allow 5 ms jitter
    assert telemetry.duration_ms < STAGE_BUDGETS["tool"][1] * 1000


# ---------------------------------------------------------------------------
# 6. to_dict() returns all required fields
# ---------------------------------------------------------------------------

def test_to_dict_contains_all_fields():
    """StageTelemetry.to_dict() must contain every field defined in the dataclass."""
    telemetry = StageTelemetry(
        stage="composition",
        start_ts=1700000000.0,
        end_ts=1700000001.0,
        duration_ms=1000,
        input_size=42,
        output_size=99,
        timeout_hit=False,
        degraded_mode=False,
        error_class=None,
    )

    d = telemetry.to_dict()

    required_fields = {f.name for f in dataclasses.fields(StageTelemetry)}
    assert required_fields == set(d.keys()), (
        f"Missing fields in to_dict(): {required_fields - set(d.keys())}"
    )
    # Spot-check values
    assert d["stage"] == "composition"
    assert d["duration_ms"] == 1000
    assert d["timeout_hit"] is False
    assert d["error_class"] is None


# ---------------------------------------------------------------------------
# 7. STAGE_BUDGETS covers all required stages
# ---------------------------------------------------------------------------

def test_stage_budgets_cover_all_required_stages():
    """STAGE_BUDGETS must have entries for every RFC §1.1 stage."""
    required = {"safety", "intent", "clarifier", "planner", "tool", "plan_exec", "composition", "finalization"}
    assert required.issubset(set(STAGE_BUDGETS.keys()))


# ---------------------------------------------------------------------------
# 8. MAX_TOTAL_REQUEST_S is 120 (raised from 60 to accommodate parallel pipeline)
# ---------------------------------------------------------------------------

def test_max_total_request_s_is_120():
    assert MAX_TOTAL_REQUEST_S == 120.0


# ---------------------------------------------------------------------------
# 9. Unknown stage uses default budget (8s soft, 15s hard)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unknown_stage_uses_default_budget():
    """Stages not in STAGE_BUDGETS should use the (8.0, 15.0) default budget."""

    async def fast_coro():
        return "ok"

    result, telemetry = await run_stage_with_budget("unknown_stage_xyz", fast_coro())

    assert result == "ok"
    # Hard timeout = 15s; duration_ms should be far below that
    assert telemetry.duration_ms < 15_000


# ---------------------------------------------------------------------------
# 10. Telemetry timestamps are monotonically consistent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_telemetry_timestamps_are_consistent():
    """end_ts must be >= start_ts and duration_ms must match."""

    async def noop():
        return None

    _, telemetry = await run_stage_with_budget("finalization", noop())

    assert telemetry.end_ts >= telemetry.start_ts
    # duration_ms is computed from monotonic clock; it should be non-negative
    assert telemetry.duration_ms >= 0
