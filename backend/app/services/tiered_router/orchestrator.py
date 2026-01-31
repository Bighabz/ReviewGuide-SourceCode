# backend/app/services/tiered_router/orchestrator.py
"""Tiered API Orchestrator - Coordinates the full tier execution flow."""

import logging
from typing import Optional

from app.core.config import settings
from app.services.tiered_router.router import get_apis_for_tier, TIER_ROUTING_TABLE
from app.services.tiered_router.circuit_breaker import CircuitBreaker, get_circuit_breaker
from app.services.tiered_router.parallel_fetcher import ParallelFetcher
from app.services.tiered_router.data_validator import DataValidator, ValidationResult
from app.services.tiered_router.api_registry import API_REGISTRY
from app.services.tiered_router.api_logger import log_consent_event

logger = logging.getLogger(__name__)


class TieredAPIOrchestrator:
    """Coordinates tiered API routing flow.

    Flow:
    1. Get APIs for current tier
    2. Fetch in parallel
    3. Validate results
    4. Escalate or return
    """

    def __init__(self, circuit_breaker: Optional[CircuitBreaker] = None):
        self.circuit_breaker = circuit_breaker or get_circuit_breaker()
        self.fetcher = ParallelFetcher(self.circuit_breaker)
        self.validator = DataValidator(max_auto_tier=settings.MAX_AUTO_TIER)

    async def execute(
        self,
        intent: str,
        query: str,
        state: dict,
    ) -> dict:
        """Execute tiered API routing.

        Args:
            intent: Classified intent (product, comparison, etc.)
            query: User's search query
            state: GraphState with user context

        Returns:
            {
                "status": "success" | "consent_required" | "partial",
                "items": [...],
                "snippets": [...],
                "sources_used": [...],
                "sources_unavailable": [...],
                "consent_prompt": {...},  # If consent_required
                "tier_reached": int,
            }
        """
        current_tier = 1
        all_results = {}
        requested_items = state.get("requested_products", [])
        user_consent = {
            "account_toggle": state.get("user_extended_search_enabled", False),
            "per_query": state.get("extended_search_confirmed", False),
        }

        # Update state with current tier for logging
        state = {**state, "current_tier": current_tier}

        while current_tier <= 4:
            # Get APIs for this tier
            try:
                apis = get_apis_for_tier(intent, current_tier, self.circuit_breaker)
            except Exception as e:
                logger.error(f"Failed to get APIs for tier {current_tier}: {e}")
                apis = []

            if not apis:
                current_tier += 1
                state = {**state, "current_tier": current_tier}
                continue

            # Filter by feature flags
            apis = self._filter_by_feature_flags(apis)

            if not apis:
                current_tier += 1
                state = {**state, "current_tier": current_tier}
                continue

            # Fetch in parallel
            tier_results = await self.fetcher.fetch_tier(apis, query, state)
            all_results.update(tier_results)

            # Validate cumulative results
            validation_result, metadata = self.validator.validate(
                intent=intent,
                current_tier=current_tier,
                results=all_results,
                requested_products=requested_items,
                user_consent=user_consent,
            )

            if validation_result == ValidationResult.SUFFICIENT:
                return self._build_success_response(all_results, metadata, current_tier)

            if validation_result == ValidationResult.ESCALATE:
                next_tier = metadata["next_tier"]

                # Log consent if escalating to Tier 3-4
                if next_tier >= 3:
                    await log_consent_event(
                        user_id=state.get("user_id", "anonymous"),
                        session_id=state.get("session_id", "unknown"),
                        consent_type="per_query",
                        tier_requested=next_tier,
                    )

                current_tier = next_tier
                state = {**state, "current_tier": current_tier}
                continue

            if validation_result == ValidationResult.CONSENT_REQUIRED:
                return self._build_consent_response(all_results, metadata, current_tier)

            if validation_result == ValidationResult.MAX_TIER_REACHED:
                return self._build_partial_response(all_results, metadata, current_tier)

        # Defensive fallback
        return self._build_partial_response(all_results, {}, current_tier)

    def _filter_by_feature_flags(self, apis: list[str]) -> list[str]:
        """Filter out APIs whose feature flags are disabled."""
        filtered = []
        for api in apis:
            config = API_REGISTRY.get(api)
            if config and config.feature_flag:
                if not getattr(settings, config.feature_flag, False):
                    continue
            filtered.append(api)
        return filtered

    def _build_success_response(
        self,
        results: dict,
        metadata: dict,
        tier: int,
    ) -> dict:
        """Build response for successful tier completion."""
        items, snippets = self._extract_all_data(results)
        return {
            "status": "success",
            "items": items,
            "snippets": snippets,
            "sources_used": metadata.get("sources_used", []),
            "sources_unavailable": metadata.get("sources_unavailable", []),
            "tier_reached": tier,
        }

    def _build_consent_response(
        self,
        results: dict,
        metadata: dict,
        tier: int,
    ) -> dict:
        """Build response when consent is required."""
        items, snippets = self._extract_all_data(results)
        return {
            "status": "consent_required",
            "items": items,
            "snippets": snippets,
            "sources_used": [k for k, v in results.items() if v.get("status") == "success"],
            "consent_prompt": {
                "type": metadata.get("consent_type"),
                "message": metadata.get("message"),
                "next_tier": metadata.get("next_tier"),
            },
            "tier_reached": tier,
        }

    def _build_partial_response(
        self,
        results: dict,
        metadata: dict,
        tier: int,
    ) -> dict:
        """Build response when all tiers are exhausted."""
        items, snippets = self._extract_all_data(results)
        return {
            "status": "partial",
            "items": items,
            "snippets": snippets,
            "sources_used": metadata.get(
                "sources_used",
                [k for k, v in results.items() if v.get("status") == "success"]
            ),
            "message": metadata.get("message", "Showing results from available sources"),
            "tier_reached": tier,
        }

    def _extract_all_data(self, results: dict) -> tuple[list, list]:
        """Extract and deduplicate items and snippets from results."""
        items = []
        snippets = []
        seen_items = set()

        for api_result in results.values():
            if api_result.get("status") != "success":
                continue
            data = api_result.get("data", {})

            # Extract items with deduplication
            for item in (
                data.get("products", []) +
                data.get("hotels", []) +
                data.get("flights", [])
            ):
                item_key = self._get_item_key(item)
                if item_key not in seen_items:
                    seen_items.add(item_key)
                    items.append(item)

            # Snippets (no deduplication needed)
            snippets.extend(data.get("snippets", []))

        return items, snippets

    def _get_item_key(self, item: dict) -> tuple:
        """Generate a unique key for an item for deduplication."""
        return (
            item.get("name", "").lower().strip(),
            item.get("price"),
        )
