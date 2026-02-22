"""
RFC §3.3 — Provider Capability Manifest at Startup

Builds and logs a manifest of all provider statuses at application startup.
Provides a get/set interface so the manifest can be served via the health endpoint.
"""
from __future__ import annotations

import dataclasses
import importlib as _importlib
from datetime import datetime
from typing import Literal

from app.core.centralized_logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ProviderCapabilityReport:
    provider: str
    enabled: bool
    status: Literal["ok", "missing_env", "import_error", "init_error"]
    missing_vars: list[str]
    error_message: str | None


@dataclasses.dataclass
class StartupManifest:
    timestamp: str
    providers: list[ProviderCapabilityReport]
    search_provider: str
    llm_model: str
    rate_limiting_enabled: bool
    all_critical_providers_ok: bool


# ---------------------------------------------------------------------------
# Module-level manifest store
# ---------------------------------------------------------------------------

_current_manifest: StartupManifest | None = None


def get_manifest() -> StartupManifest | None:
    """Return the current startup manifest, or None if not yet built."""
    return _current_manifest


def set_manifest(m: StartupManifest) -> None:
    """Store the startup manifest for later retrieval."""
    global _current_manifest
    _current_manifest = m


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_str(attr_name: str) -> str:
    """Safely retrieve a string setting value; returns '' on any error."""
    try:
        from app.core.config import settings
        value = getattr(settings, attr_name, "")
        return str(value) if value is not None else ""
    except Exception:
        return ""


def _get_bool(attr_name: str) -> bool:
    """Safely retrieve a bool setting value; returns False on any error."""
    try:
        from app.core.config import settings
        value = getattr(settings, attr_name, False)
        return bool(value)
    except Exception:
        return False


def _check_provider(
    name: str,
    required_vars: list[str],
    enabled: bool = True,
    module_path: str | None = None,
) -> ProviderCapabilityReport:
    """
    Check a provider by inspecting env-var presence on the settings object.

    Parameters
    ----------
    name:
        Human-readable provider name used in log output.
    required_vars:
        Attribute names on ``settings`` that must be non-empty strings for the
        provider to be considered operational.
    enabled:
        Whether this provider is switched on via its feature flag.  When
        False the report is ``status="ok"`` with ``enabled=False`` (the
        provider is simply not in use — not an error).
    module_path:
        Optional dotted module path to attempt importing.  When provided,
        an ``ImportError`` produces ``status="import_error"`` rather than
        ``"init_error"``, allowing callers to detect missing optional deps.
    """
    missing: list[str] = []

    try:
        if not enabled:
            return ProviderCapabilityReport(
                provider=name,
                enabled=False,
                status="ok",
                missing_vars=[],
                error_message=None,
            )

        # Attempt to import the provider module (catches missing optional deps).
        if module_path:
            try:
                _importlib.import_module(module_path)
            except ImportError as exc:
                return ProviderCapabilityReport(
                    provider=name,
                    enabled=True,
                    status="import_error",
                    missing_vars=[],
                    error_message=str(exc),
                )

        for var in required_vars:
            value = _get_str(var)
            if not value:
                missing.append(var)

        if missing:
            return ProviderCapabilityReport(
                provider=name,
                enabled=True,
                status="missing_env",
                missing_vars=missing,
                error_message=None,
            )

        return ProviderCapabilityReport(
            provider=name,
            enabled=True,
            status="ok",
            missing_vars=[],
            error_message=None,
        )

    except Exception as exc:
        return ProviderCapabilityReport(
            provider=name,
            enabled=enabled,
            status="init_error",
            missing_vars=missing,
            error_message=str(exc),
        )


# ---------------------------------------------------------------------------
# Manifest builder
# ---------------------------------------------------------------------------

def build_startup_manifest() -> StartupManifest:
    """
    Inspect all configured providers and return a StartupManifest.

    Critical providers: OpenAI LLM.
    Optional providers: search (perplexity), serpapi, amazon, ebay,
                        booking, amadeus, viator.
    """
    try:
        from app.core.config import settings

        search_provider = _get_str("SEARCH_PROVIDER") or "perplexity"
        llm_model = _get_str("DEFAULT_MODEL") or "gpt-4o-mini"
        rate_limiting_enabled = _get_bool("RATE_LIMIT_ENABLED")

        providers: list[ProviderCapabilityReport] = []

        # ------------------------------------------------------------------
        # 1. OpenAI LLM — CRITICAL
        # ------------------------------------------------------------------
        providers.append(
            _check_provider(
                name="openai",
                required_vars=["OPENAI_API_KEY"],
                enabled=True,
            )
        )

        # ------------------------------------------------------------------
        # 2. Search provider (Perplexity or OpenAI-search)
        # ------------------------------------------------------------------
        if search_provider == "perplexity":
            providers.append(
                _check_provider(
                    name="perplexity",
                    required_vars=["PERPLEXITY_API_KEY"],
                    enabled=True,
                )
            )
        else:
            # OpenAI search reuses OPENAI_API_KEY — no extra vars needed
            providers.append(
                _check_provider(
                    name="openai_search",
                    required_vars=["OPENAI_API_KEY"],
                    enabled=True,
                )
            )

        # ------------------------------------------------------------------
        # 3. SerpAPI (reviews) — optional
        # ------------------------------------------------------------------
        serpapi_enabled = _get_bool("ENABLE_SERPAPI")
        providers.append(
            _check_provider(
                name="serpapi",
                required_vars=["SERPAPI_API_KEY"],
                enabled=serpapi_enabled,
            )
        )

        # ------------------------------------------------------------------
        # 4. Amazon affiliate — optional
        # ------------------------------------------------------------------
        amazon_enabled = _get_bool("AMAZON_API_ENABLED")
        providers.append(
            _check_provider(
                name="amazon",
                required_vars=[
                    "AMAZON_ACCESS_KEY",
                    "AMAZON_SECRET_KEY",
                    "AMAZON_ASSOCIATE_TAG",
                ],
                enabled=amazon_enabled,
            )
        )

        # ------------------------------------------------------------------
        # 5. eBay affiliate — optional (treated as enabled when any key set)
        # ------------------------------------------------------------------
        ebay_app_id = _get_str("EBAY_APP_ID")
        ebay_enabled = bool(ebay_app_id)
        providers.append(
            _check_provider(
                name="ebay",
                required_vars=["EBAY_APP_ID", "EBAY_CERT_ID", "EBAY_CAMPAIGN_ID"],
                enabled=ebay_enabled,
            )
        )

        # ------------------------------------------------------------------
        # 6. Booking.com travel — optional
        # ------------------------------------------------------------------
        booking_api_key = _get_str("BOOKING_API_KEY")
        booking_affiliate_id = _get_str("BOOKING_AFFILIATE_ID")
        booking_enabled = bool(booking_api_key or booking_affiliate_id)
        providers.append(
            _check_provider(
                name="booking",
                required_vars=["BOOKING_API_KEY", "BOOKING_AFFILIATE_ID"],
                enabled=booking_enabled,
            )
        )

        # ------------------------------------------------------------------
        # 7. Amadeus flights — optional
        # ------------------------------------------------------------------
        amadeus_key = _get_str("AMADEUS_API_KEY")
        amadeus_enabled = bool(amadeus_key)
        providers.append(
            _check_provider(
                name="amadeus",
                required_vars=["AMADEUS_API_KEY", "AMADEUS_API_SECRET"],
                enabled=amadeus_enabled,
            )
        )

        # ------------------------------------------------------------------
        # 8. Viator activities — optional
        # ------------------------------------------------------------------
        viator_id = _get_str("VIATOR_AFFILIATE_ID")
        viator_enabled = bool(viator_id)
        providers.append(
            _check_provider(
                name="viator",
                required_vars=["VIATOR_AFFILIATE_ID"],
                enabled=viator_enabled,
            )
        )

        # ------------------------------------------------------------------
        # Determine all_critical_providers_ok
        # Only OpenAI LLM is critical.
        # ------------------------------------------------------------------
        openai_report = next(p for p in providers if p.provider == "openai")
        all_critical_ok = openai_report.status == "ok"

        return StartupManifest(
            timestamp=datetime.utcnow().isoformat() + "Z",
            providers=providers,
            search_provider=search_provider,
            llm_model=llm_model,
            rate_limiting_enabled=rate_limiting_enabled,
            all_critical_providers_ok=all_critical_ok,
        )

    except Exception as exc:
        # Last-resort fallback: return a manifest that marks everything failed
        logger.error(f"[startup] Failed to build startup manifest: {exc}", exc_info=True)
        return StartupManifest(
            timestamp=datetime.utcnow().isoformat() + "Z",
            providers=[
                ProviderCapabilityReport(
                    provider="unknown",
                    enabled=False,
                    status="init_error",
                    missing_vars=[],
                    error_message=str(exc),
                )
            ],
            search_provider="unknown",
            llm_model="unknown",
            rate_limiting_enabled=False,
            all_critical_providers_ok=False,
        )


# ---------------------------------------------------------------------------
# Manifest logger
# ---------------------------------------------------------------------------

_STATUS_ICON = {
    "ok": "\u2705",           # ✅
    "missing_env": "\u26a0\ufe0f",  # ⚠️
    "import_error": "\u274c",  # ❌
    "init_error": "\u274c",    # ❌
}


def log_startup_manifest(manifest: StartupManifest) -> None:
    """Log the startup manifest in the format described in RFC §3.3."""
    lines = ["[startup] Provider manifest:"]

    for report in manifest.providers:
        icon = _STATUS_ICON.get(report.status, "?")

        if report.status == "ok":
            if report.enabled:
                detail = "ok"
            else:
                detail = "disabled"
        elif report.status == "missing_env":
            vars_str = ", ".join(report.missing_vars)
            detail = f"missing_env: {vars_str}"
        else:
            detail = report.status
            if report.error_message:
                detail += f": {report.error_message}"

        lines.append(f"  {icon} {report.provider:<20} — {detail}")

    lines.append(
        f"  search_provider={manifest.search_provider}  "
        f"llm_model={manifest.llm_model}  "
        f"rate_limiting={manifest.rate_limiting_enabled}  "
        f"all_critical_ok={manifest.all_critical_providers_ok}"
    )

    logger.info("\n".join(lines))
