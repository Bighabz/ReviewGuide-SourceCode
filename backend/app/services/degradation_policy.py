"""
RFC §4.3 — Controlled Degradation Policies.

Defines fail-open / fail-closed policy for each integration point.
Runtime overrides are read from environment at call time so they
take effect without a process restart.
"""
from __future__ import annotations
import os
from app.core.centralized_logger import get_logger

logger = get_logger(__name__)


class DegradationPolicy:
    FAIL_OPEN = "fail_open"
    FAIL_CLOSED = "fail_closed"

    # Default policy table (RFC §4.3)
    POLICIES: dict[str, str] = {
        "redis_rate_limit": FAIL_OPEN,
        "redis_halt_state": FAIL_CLOSED,
        "redis_cache": FAIL_OPEN,
        "perplexity": FAIL_OPEN,
        "serpapi": FAIL_OPEN,
        "ebay": FAIL_OPEN,
        "amazon": FAIL_OPEN,
        "openai": FAIL_CLOSED,
        "postgres": FAIL_CLOSED,
    }

    @classmethod
    def get_policy(cls, component: str) -> str:
        """
        Return the effective degradation policy for a component.

        Checks DEGRADE_<COMPONENT> env var first (runtime override, no restart
        required), then falls back to the POLICIES table.
        """
        env_key = f"DEGRADE_{component.upper()}"
        override = os.environ.get(env_key, "").strip().lower()
        if override in (cls.FAIL_OPEN, cls.FAIL_CLOSED):
            return override
        return cls.POLICIES.get(component, cls.FAIL_OPEN)

    @classmethod
    def is_fail_open(cls, component: str) -> bool:
        return cls.get_policy(component) == cls.FAIL_OPEN

    @classmethod
    def is_fail_closed(cls, component: str) -> bool:
        return cls.get_policy(component) == cls.FAIL_CLOSED

    @classmethod
    def get_all_policies(cls) -> dict[str, str]:
        """Return effective policy for all components (applying any env overrides)."""
        return {component: cls.get_policy(component) for component in cls.POLICIES}
