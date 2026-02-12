# backend/app/services/tiered_router/data_validator.py
"""Data Validator - Check thresholds and decide on tier escalation."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ValidationResult(Enum):
    """Possible outcomes of data validation."""
    SUFFICIENT = "sufficient"
    ESCALATE = "escalate"
    CONSENT_REQUIRED = "consent_required"
    MAX_TIER_REACHED = "max_tier_reached"


@dataclass
class ThresholdConfig:
    """Threshold configuration for an intent type.

    Attributes:
        min_items: Minimum products/hotels/flights required
        min_snippets: Minimum review snippets required
        min_sources: Minimum unique sources required
        require_all_items: For comparison - must have all requested items
    """
    min_items: int = 0
    min_snippets: int = 0
    min_sources: int = 0
    require_all_items: bool = False


INTENT_THRESHOLDS: dict[str, ThresholdConfig] = {
    "product": ThresholdConfig(min_items=3),
    "comparison": ThresholdConfig(require_all_items=True),
    "price_check": ThresholdConfig(min_items=1),
    "review_deep_dive": ThresholdConfig(min_snippets=5, min_sources=2),
    "travel": ThresholdConfig(min_items=1, min_snippets=3),
}


class DataValidator:
    """Validate tier results and decide on escalation.

    Args:
        max_auto_tier: Highest tier that can auto-escalate without consent (1-2)
    """

    def __init__(self, max_auto_tier: int = 2):
        self.max_auto_tier = max_auto_tier

    def validate(
        self,
        intent: str,
        current_tier: int,
        results: dict[str, dict],
        requested_products: Optional[list[str]] = None,
        user_consent: Optional[dict] = None,
    ) -> tuple[ValidationResult, dict]:
        """Validate results and determine next action.

        Args:
            intent: The classified intent type
            current_tier: Current tier level (1-4)
            results: Dict of API results keyed by API name
            requested_products: For comparison - specific products to find
            user_consent: {"account_toggle": bool, "per_query": bool}

        Returns:
            Tuple of (ValidationResult, metadata dict)
        """
        threshold = INTENT_THRESHOLDS.get(intent, ThresholdConfig())

        successful = {k: v for k, v in results.items() if v.get("status") == "success"}
        failed = {k: v for k, v in results.items() if v.get("status") != "success"}

        items = self._extract_items(successful)
        snippets = self._extract_snippets(successful)
        sources_used = list(successful.keys())

        is_sufficient = self._check_threshold(
            threshold, items, snippets, requested_products, sources_used
        )

        if is_sufficient:
            return ValidationResult.SUFFICIENT, {
                "sources_used": sources_used,
                "sources_unavailable": list(failed.keys()),
                "item_count": len(items),
                "snippet_count": len(snippets),
            }

        next_tier = current_tier + 1

        # Auto-escalate within allowed tiers
        if next_tier <= self.max_auto_tier:
            return ValidationResult.ESCALATE, {"next_tier": next_tier}

        # Tier 3-4 requires consent
        if next_tier <= 4:
            user_consent = user_consent or {}

            if not user_consent.get("account_toggle"):
                return ValidationResult.CONSENT_REQUIRED, {
                    "consent_type": "account_toggle",
                    "message": "Enable Extended Search in Settings to search more sources",
                }

            if not user_consent.get("per_query"):
                return ValidationResult.CONSENT_REQUIRED, {
                    "consent_type": "per_query",
                    "message": "Search deeper?",
                    "next_tier": next_tier,
                }

            return ValidationResult.ESCALATE, {"next_tier": next_tier}

        # All tiers exhausted
        return ValidationResult.MAX_TIER_REACHED, {
            "partial_results": True,
            "sources_used": sources_used,
            "message": "Showing results from available sources",
        }

    def _check_threshold(
        self,
        threshold: ThresholdConfig,
        items: list,
        snippets: list,
        requested_products: Optional[list[str]] = None,
        sources_used: Optional[list[str]] = None,
    ) -> bool:
        """Check if results meet threshold requirements."""
        if threshold.require_all_items:
            if not requested_products:
                return len(items) >= 2  # Default: need at least 2 for comparison
            found_names = {item.get("name", "").lower() for item in items}
            return all(
                any(req.lower() in name for name in found_names)
                for req in requested_products
            )

        if threshold.min_items and len(items) < threshold.min_items:
            return False
        if threshold.min_snippets and len(snippets) < threshold.min_snippets:
            return False
        if threshold.min_sources and len(sources_used or []) < threshold.min_sources:
            return False

        return True

    def _extract_items(self, results: dict) -> list:
        """Extract all items (products, hotels, flights) from results."""
        items = []
        for api_result in results.values():
            data = api_result.get("data", {})
            items.extend(data.get("products", []))
            items.extend(data.get("hotels", []))
            items.extend(data.get("flights", []))
        return items

    def _extract_snippets(self, results: dict) -> list:
        """Extract all review snippets from results."""
        snippets = []
        for api_result in results.values():
            data = api_result.get("data", {})
            snippets.extend(data.get("snippets", []))
        return snippets
