"""
Tests for RFC §3.3 — Provider Capability Manifest at Startup

backend/tests/test_startup_manifest.py
"""
import dataclasses
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
from fastapi.testclient import TestClient

from app.services.startup_manifest import (
    ProviderCapabilityReport,
    StartupManifest,
    _check_provider,
    build_startup_manifest,
    get_manifest,
    set_manifest,
)


# ---------------------------------------------------------------------------
# Minimal FastAPI app for HTTP-level endpoint tests
# ---------------------------------------------------------------------------

def _make_test_manifest(all_critical_ok: bool, providers_ok: bool = True) -> StartupManifest:
    """Build a minimal StartupManifest for use in HTTP endpoint tests."""
    status = "ok" if providers_ok else "missing_env"
    return StartupManifest(
        timestamp="2026-01-01T00:00:00+00:00",
        providers=[
            ProviderCapabilityReport(
                provider="openai",
                enabled=True,
                status="ok" if all_critical_ok else "missing_env",
                missing_vars=[] if all_critical_ok else ["OPENAI_API_KEY"],
                error_message=None,
            ),
            ProviderCapabilityReport(
                provider="perplexity",
                enabled=True,
                status=status,
                missing_vars=[] if providers_ok else ["PERPLEXITY_API_KEY"],
                error_message=None,
            ),
        ],
        search_provider="perplexity",
        llm_model="gpt-4o-mini",
        rate_limiting_enabled=False,
        all_critical_providers_ok=all_critical_ok,
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

    # Optional providers' status must not influence the critical flag regardless of their state
    optional_names = {"booking", "viator", "amazon", "ebay", "serpapi", "amadeus"}
    for report in manifest.providers:
        if report.provider in optional_names:
            assert report.status in ("ok", "missing_env", "import_error", "init_error")


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
    # datetime.now(timezone.utc).isoformat() produces "+00:00" suffix
    assert "+00:00" in manifest.timestamp or manifest.timestamp.endswith("Z")
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


# ---------------------------------------------------------------------------
# 6. test_import_error_when_module_cannot_be_loaded
# ---------------------------------------------------------------------------

def test_import_error_when_module_cannot_be_loaded():
    """When a provider module raises ImportError, status must be 'import_error'."""
    # Patch the module-level _importlib alias so we don't disturb mock's own resolver
    with patch("app.services.startup_manifest._importlib") as mock_importlib:
        mock_importlib.import_module.side_effect = ImportError("No module named 'fake_provider'")
        with patch("app.services.startup_manifest._get_str", return_value="some-key"):
            report = _check_provider(
                name="fake",
                required_vars=["SOME_API_KEY"],
                enabled=True,
                module_path="fake_provider.module",
            )

    assert report.status == "import_error"
    assert report.provider == "fake"
    assert report.enabled is True
    assert "fake_provider" in (report.error_message or "")


# ---------------------------------------------------------------------------
# 7. test_readiness_endpoint_returns_200_when_all_ok
# ---------------------------------------------------------------------------

def test_readiness_endpoint_returns_200_when_all_ok():
    """GET /health/ready returns 200 with status='ok' when all enabled providers are ok."""
    from app.api.v1.health import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)

    manifest = _make_test_manifest(all_critical_ok=True, providers_ok=True)

    with patch("app.api.v1.health.get_manifest", return_value=manifest):
        response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "manifest" in body
    assert "timestamp" in body


# ---------------------------------------------------------------------------
# 8. test_readiness_endpoint_returns_200_degraded_when_optional_missing
# ---------------------------------------------------------------------------

def test_readiness_endpoint_returns_200_degraded_when_optional_missing():
    """GET /health/ready returns 200 with status='degraded' when optional providers are missing."""
    from app.api.v1.health import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)

    # Critical OK but optional perplexity is missing_env
    manifest = _make_test_manifest(all_critical_ok=True, providers_ok=False)

    with patch("app.api.v1.health.get_manifest", return_value=manifest):
        response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"


# ---------------------------------------------------------------------------
# 9. test_readiness_endpoint_returns_503_when_critical_missing
# ---------------------------------------------------------------------------

def test_readiness_endpoint_returns_503_when_critical_missing():
    """GET /health/ready returns 503 with status='unavailable' when LLM key is absent."""
    from app.api.v1.health import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)

    manifest = _make_test_manifest(all_critical_ok=False)

    with patch("app.api.v1.health.get_manifest", return_value=manifest):
        response = client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["detail"]["status"] == "unavailable"


# ---------------------------------------------------------------------------
# 10. test_build_startup_manifest_fallback_on_exception
# ---------------------------------------------------------------------------

def test_build_startup_manifest_fallback_on_exception():
    """When an unexpected error occurs in build_startup_manifest, a safe fallback manifest is returned."""
    # Force _get_str to raise an exception to trigger the outer except block
    with patch("app.services.startup_manifest._get_str", side_effect=RuntimeError("unexpected")):
        manifest = build_startup_manifest()

    # Must return a valid StartupManifest, never raise
    assert isinstance(manifest, StartupManifest)
    assert manifest.all_critical_providers_ok is False
    assert len(manifest.providers) == 1
    assert manifest.providers[0].provider == "unknown"
    assert manifest.providers[0].status == "init_error"
