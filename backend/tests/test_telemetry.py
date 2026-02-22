"""
Tests for RFC §4.1 — Unified Trace Model (telemetry endpoints)

backend/tests/test_telemetry.py
"""
import os

# ---------------------------------------------------------------------------
# Minimal env setup so settings can be instantiated without a .env file.
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

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from app.api.v1.telemetry import router as telemetry_router
from app.core.config import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_admin_token() -> str:
    """Mint a JWT that satisfies require_admin (type='admin')."""
    payload = {"sub": "testadmin", "type": "admin"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _make_test_app() -> FastAPI:
    """Minimal FastAPI app that only mounts the telemetry router."""
    app = FastAPI()
    app.include_router(telemetry_router, prefix="/v1")
    return app


# ---------------------------------------------------------------------------
# 1. test_render_milestones_endpoint_accepts_valid_payload
# ---------------------------------------------------------------------------

def test_render_milestones_endpoint_accepts_valid_payload():
    """POST /v1/telemetry/render with a fully-populated payload returns 200 {"status": "ok"}."""
    client = TestClient(_make_test_app(), raise_server_exceptions=False)

    payload = {
        "interaction_id": "abc-123",
        "request_sent_ts": 1_700_000_000_000,
        "first_status_ts": 1_700_000_000_500,
        "first_content_ts": 1_700_000_001_000,
        "first_artifact_ts": 1_700_000_001_200,
        "done_ts": 1_700_000_003_000,
    }

    response = client.post("/v1/telemetry/render", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# 2. test_render_milestones_with_all_nulls_accepted
# ---------------------------------------------------------------------------

def test_render_milestones_with_all_nulls_accepted():
    """POST /v1/telemetry/render with all optional timestamps as null returns 200."""
    client = TestClient(_make_test_app(), raise_server_exceptions=False)

    payload = {
        "interaction_id": "xyz-456",
        "request_sent_ts": 1_700_000_000_000,
        "first_status_ts": None,
        "first_content_ts": None,
        "first_artifact_ts": None,
        "done_ts": None,
    }

    response = client.post("/v1/telemetry/render", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# 3. test_render_milestones_logs_ttfc_when_first_content_present
# ---------------------------------------------------------------------------

def test_render_milestones_logs_ttfc_when_first_content_present():
    """
    When first_content_ts is set, the endpoint must log a ttfc_ms value equal to
    first_content_ts - request_sent_ts.
    """
    client = TestClient(_make_test_app(), raise_server_exceptions=False)

    request_sent = 1_700_000_000_000
    first_content = 1_700_000_001_500  # 1500 ms later

    payload = {
        "interaction_id": "ttfc-test-id",
        "request_sent_ts": request_sent,
        "first_status_ts": request_sent + 200,
        "first_content_ts": first_content,
        "first_artifact_ts": None,
        "done_ts": request_sent + 3_000,
    }

    captured_extra: dict = {}

    # Patch logger.info inside the telemetry module to capture the extra dict
    import app.api.v1.telemetry as telemetry_module

    original_info = telemetry_module.logger.info

    def _capture_info(msg, *args, **kwargs):
        extra = kwargs.get("extra", {})
        if "ttfc_ms" in extra:
            captured_extra.update(extra)
        original_info(msg, *args, **kwargs)

    with patch.object(telemetry_module.logger, "info", side_effect=_capture_info):
        response = client.post("/v1/telemetry/render", json=payload)

    assert response.status_code == 200
    assert "ttfc_ms" in captured_extra, "logger.info must be called with ttfc_ms in extra"
    assert captured_extra["ttfc_ms"] == first_content - request_sent


# ---------------------------------------------------------------------------
# 4. test_admin_trace_endpoint_requires_auth
# ---------------------------------------------------------------------------

def test_admin_trace_endpoint_requires_auth_no_token():
    """GET /v1/admin/trace/:id without a token must return 401."""
    client = TestClient(_make_test_app(), raise_server_exceptions=False)

    response = client.get("/v1/admin/trace/some-interaction-id")

    assert response.status_code == 401, (
        f"Expected 401 without admin credentials, got {response.status_code}"
    )


def test_admin_trace_endpoint_requires_auth_non_admin_token():
    """GET /v1/admin/trace/:id with a non-admin JWT must return 403."""
    client = TestClient(_make_test_app(), raise_server_exceptions=False)

    # Mint a regular-user token (type != 'admin')
    user_token = jwt.encode(
        {"sub": "regularuser", "type": "user"},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.get(
        "/v1/admin/trace/some-interaction-id",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403, (
        f"Expected 403 for non-admin token, got {response.status_code}"
    )


def test_admin_trace_endpoint_accessible_with_admin_token():
    """GET /v1/admin/trace/:id with a valid admin JWT must return 200 with interaction_id."""
    client = TestClient(_make_test_app(), raise_server_exceptions=False)
    token = _make_admin_token()

    interaction_id = "test-trace-correlation-id"

    response = client.get(
        f"/v1/admin/trace/{interaction_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["interaction_id"] == interaction_id
    # Must reference the Langfuse tag lookup in the message
    assert "request_id:" + interaction_id in body["message"]
