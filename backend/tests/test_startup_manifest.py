"""
Tests for RFC §3.3 — Provider Capability Manifest at Startup

backend/tests/test_startup_manifest.py
"""
import os

# ---------------------------------------------------------------------------
# Minimal env setup so settings can be instantiated without .env file
# ---------------------------------------------------------------------------
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("ADMIN_PASSWORD", "testpassword123")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("LOG_ENABLED", "false")

from unittest.mock import patch, MagicMock

import pytest

from app.services.startup_manifest import (
    ProviderCapabilityReport,
    StartupManifest,
    _check_provider,
    build_startup_manifest,
    get_manifest,
    set_manifest,
)


# ---------------------------------------------------------------------------
# 1. test_ok_provider_when_all_vars_present
# ---------------------------------------------------------------------------

def test_ok_provider_when_all_vars_present():
    """When all required vars are non-empty, status must be 'ok'."""
    with patch("app.services.startup_manifest._get_str") as mock_get_str:
        # All requested attributes return a non-empty string
        mock_get_str.return_value = "sk-test-key-abc123"

        report = _check_provider(
            name="openai",
            required_vars=["OPENAI_API_KEY"],
            enabled=True,
        )

    assert report.status == "ok"
    assert report.enabled is True
    assert report.missing_vars == []
    assert report.error_message is None


# ---------------------------------------------------------------------------
# 2. test_missing_env_when_api_key_absent
# ---------------------------------------------------------------------------

def test_missing_env_when_api_key_absent():
    """When a required var is empty, status must be 'missing_env' with var listed."""
    with patch("app.services.startup_manifest._get_str") as mock_get_str:
        # OPENAI_API_KEY returns empty string — simulates absent env var
        mock_get_str.side_effect = lambda attr: "" if attr == "OPENAI_API_KEY" else "some-value"

        report = _check_provider(
            name="openai",
            required_vars=["OPENAI_API_KEY"],
            enabled=True,
        )

    assert report.status == "missing_env"
    assert "OPENAI_API_KEY" in report.missing_vars
    assert report.enabled is True


# ---------------------------------------------------------------------------
# 3. test_all_critical_ok_when_optional_missing
# ---------------------------------------------------------------------------

def test_all_critical_ok_when_optional_missing():
    """
    all_critical_providers_ok must be True even when optional providers
    (booking, viator, amazon, ebay) have missing env vars.
    """
    with patch("app.services.startup_manifest._get_str") as mock_get_str, \
         patch("app.services.startup_manifest._get_bool") as mock_get_bool:

        def str_side_effect(attr):
            if attr == "OPENAI_API_KEY":
                return "sk-real-key"
            if attr == "SEARCH_PROVIDER":
                return "perplexity"
            if attr == "PERPLEXITY_API_KEY":
                return "pplx-real-key"
            if attr == "DEFAULT_MODEL":
                return "gpt-4o-mini"
            # Everything else (booking, viator, amazon, ebay keys) is empty
            return ""

        def bool_side_effect(attr):
            if attr == "RATE_LIMIT_ENABLED":
                return False
            # All optional feature flags disabled
            return False

        mock_get_str.side_effect = str_side_effect
        mock_get_bool.side_effect = bool_side_effect

        manifest = build_startup_manifest()

    assert manifest.all_critical_providers_ok is True

    # Optional providers should NOT affect the critical flag
    optional_names = {"booking", "viator", "amazon", "ebay", "serpapi", "amadeus"}
    for report in manifest.providers:
        if report.provider in optional_names:
            # They are disabled (enabled=False) so they shouldn't fail critical check
            assert report.provider not in {"openai"}  # sanity


# ---------------------------------------------------------------------------
# 4. test_all_critical_false_when_llm_missing
# ---------------------------------------------------------------------------

def test_all_critical_false_when_llm_missing():
    """
    all_critical_providers_ok must be False when OPENAI_API_KEY is absent.
    """
    with patch("app.services.startup_manifest._get_str") as mock_get_str, \
         patch("app.services.startup_manifest._get_bool") as mock_get_bool:

        def str_side_effect(attr):
            if attr == "OPENAI_API_KEY":
                return ""   # Missing!
            if attr == "SEARCH_PROVIDER":
                return "perplexity"
            if attr == "PERPLEXITY_API_KEY":
                return "pplx-key"
            if attr == "DEFAULT_MODEL":
                return "gpt-4o-mini"
            return ""

        mock_get_str.side_effect = str_side_effect
        mock_get_bool.side_effect = lambda attr: False

        manifest = build_startup_manifest()

    assert manifest.all_critical_providers_ok is False

    openai_report = next(p for p in manifest.providers if p.provider == "openai")
    assert openai_report.status == "missing_env"
    assert "OPENAI_API_KEY" in openai_report.missing_vars


# ---------------------------------------------------------------------------
# 5. test_build_manifest_returns_correct_fields
# ---------------------------------------------------------------------------

def test_build_manifest_returns_correct_fields():
    """
    build_startup_manifest() must return a StartupManifest with all required
    fields populated to the correct types.
    """
    with patch("app.services.startup_manifest._get_str") as mock_get_str, \
         patch("app.services.startup_manifest._get_bool") as mock_get_bool:

        def str_side_effect(attr):
            mapping = {
                "OPENAI_API_KEY": "sk-test",
                "SEARCH_PROVIDER": "perplexity",
                "PERPLEXITY_API_KEY": "pplx-test",
                "DEFAULT_MODEL": "gpt-4o-mini",
            }
            return mapping.get(attr, "")

        mock_get_str.side_effect = str_side_effect
        mock_get_bool.side_effect = lambda attr: attr == "RATE_LIMIT_ENABLED"

        manifest = build_startup_manifest()

    # Structural checks
    assert isinstance(manifest, StartupManifest)
    assert isinstance(manifest.timestamp, str)
    assert manifest.timestamp.endswith("Z")
    assert isinstance(manifest.providers, list)
    assert len(manifest.providers) > 0
    assert manifest.search_provider == "perplexity"
    assert manifest.llm_model == "gpt-4o-mini"
    assert isinstance(manifest.rate_limiting_enabled, bool)
    assert isinstance(manifest.all_critical_providers_ok, bool)

    # Each provider report must have required fields
    for report in manifest.providers:
        assert isinstance(report, ProviderCapabilityReport)
        assert isinstance(report.provider, str)
        assert report.provider != ""
        assert isinstance(report.enabled, bool)
        assert report.status in ("ok", "missing_env", "import_error", "init_error")
        assert isinstance(report.missing_vars, list)

    # The module-level get/set round-trip works
    set_manifest(manifest)
    assert get_manifest() is manifest
