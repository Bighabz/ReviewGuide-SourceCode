"""
Tests for RFC §4.3 — Controlled Degradation Policies.
"""
from __future__ import annotations
import os
import pytest


# ---------------------------------------------------------------------------
# Helper: import without triggering the full app initialisation chain
# ---------------------------------------------------------------------------

def _get_policy_class():
    from app.services.degradation_policy import DegradationPolicy
    return DegradationPolicy


# ---------------------------------------------------------------------------
# Default policy table
# ---------------------------------------------------------------------------

def test_default_policy_fail_open():
    """redis_cache, perplexity, serpapi, ebay, amazon should default to fail_open."""
    DP = _get_policy_class()
    fail_open_components = ["redis_cache", "perplexity", "serpapi", "ebay", "amazon", "redis_rate_limit"]
    for component in fail_open_components:
        # Ensure no env override is active
        env_key = f"DEGRADE_{component.upper()}"
        os.environ.pop(env_key, None)
        assert DP.get_policy(component) == DP.FAIL_OPEN, (
            f"{component} should default to fail_open"
        )


def test_default_policy_fail_closed():
    """redis_halt_state, openai, postgres should default to fail_closed."""
    DP = _get_policy_class()
    fail_closed_components = ["redis_halt_state", "openai", "postgres"]
    for component in fail_closed_components:
        env_key = f"DEGRADE_{component.upper()}"
        os.environ.pop(env_key, None)
        assert DP.get_policy(component) == DP.FAIL_CLOSED, (
            f"{component} should default to fail_closed"
        )


# ---------------------------------------------------------------------------
# Runtime env-var overrides
# ---------------------------------------------------------------------------

def test_env_override_changes_policy():
    """DEGRADE_PERPLEXITY=fail_closed should override the default fail_open."""
    DP = _get_policy_class()
    os.environ["DEGRADE_PERPLEXITY"] = "fail_closed"
    try:
        assert DP.get_policy("perplexity") == DP.FAIL_CLOSED
    finally:
        os.environ.pop("DEGRADE_PERPLEXITY", None)


def test_env_override_is_case_insensitive():
    """DEGRADE_SERPAPI=FAIL_OPEN (upper-case value) should still resolve correctly."""
    DP = _get_policy_class()
    os.environ["DEGRADE_SERPAPI"] = "FAIL_OPEN"
    try:
        assert DP.get_policy("serpapi") == DP.FAIL_OPEN
    finally:
        os.environ.pop("DEGRADE_SERPAPI", None)


def test_invalid_override_falls_back_to_default():
    """An unrecognised env-var value should be ignored; default policy returned."""
    DP = _get_policy_class()
    os.environ["DEGRADE_PERPLEXITY"] = "invalid_value"
    try:
        # perplexity default is fail_open
        assert DP.get_policy("perplexity") == DP.FAIL_OPEN
    finally:
        os.environ.pop("DEGRADE_PERPLEXITY", None)


# ---------------------------------------------------------------------------
# get_all_policies
# ---------------------------------------------------------------------------

def test_get_all_policies_returns_all_components():
    """get_all_policies() must contain exactly the 9 RFC §4.3 components."""
    DP = _get_policy_class()
    expected_components = {
        "redis_rate_limit",
        "redis_halt_state",
        "redis_cache",
        "perplexity",
        "serpapi",
        "ebay",
        "amazon",
        "openai",
        "postgres",
    }
    policies = DP.get_all_policies()
    assert set(policies.keys()) == expected_components
    # Every value must be one of the two valid strings
    for component, policy in policies.items():
        assert policy in (DP.FAIL_OPEN, DP.FAIL_CLOSED), (
            f"{component} has unexpected policy value: {policy}"
        )


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def test_is_fail_open_convenience():
    """is_fail_open('perplexity') should return True when no override is set."""
    DP = _get_policy_class()
    os.environ.pop("DEGRADE_PERPLEXITY", None)
    assert DP.is_fail_open("perplexity") is True


def test_is_fail_closed_convenience():
    """is_fail_closed('openai') should return True when no override is set."""
    DP = _get_policy_class()
    os.environ.pop("DEGRADE_OPENAI", None)
    assert DP.is_fail_closed("openai") is True
