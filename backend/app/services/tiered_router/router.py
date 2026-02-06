"""Tiered API Router - Deterministic routing table lookup."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .circuit_breaker import CircuitBreaker


class UnknownIntentError(Exception):
    """Raised when intent has no routing rules defined."""
    pass


# Routing table: intent -> tier -> list of API names
TIER_ROUTING_TABLE: dict[str, dict[int, list[str]]] = {
    "product": {
        1: [
            "amazon_affiliate",
            "walmart_affiliate",
            "bestbuy_affiliate",
            "ebay_affiliate",
            "google_cse_product",
        ],
        2: ["bing_search", "youtube_transcripts"],
        3: ["reddit_api"],
        4: ["serpapi"],
    },
    "comparison": {
        1: [
            "amazon_affiliate",
            "walmart_affiliate",
            "bestbuy_affiliate",
            "ebay_affiliate",
            "google_cse_product",
        ],
        2: ["bing_search", "youtube_transcripts"],
        3: ["reddit_api"],
        4: ["serpapi"],
    },
    "price_check": {
        1: [
            "amazon_affiliate",
            "walmart_affiliate",
            "bestbuy_affiliate",
            "ebay_affiliate",
        ],
        2: ["google_shopping"],
        3: [],  # No Tier 3-4 for price checks
        4: [],
    },
    "review_deep_dive": {
        1: ["google_cse_product"],
        2: ["bing_search", "youtube_transcripts"],
        3: ["reddit_api"],
        4: ["serpapi"],
    },
    "travel": {
        1: ["amadeus", "booking", "expedia", "google_cse_travel"],
        2: ["skyscanner", "tripadvisor"],
        3: [],
        4: [],
    },
}


def get_apis_for_tier(
    intent: str,
    tier: int,
    circuit_breaker: "CircuitBreaker",
) -> list[str]:
    """Get available APIs for a given intent and tier.

    Args:
        intent: The classified intent (product, comparison, etc.)
        tier: The tier level (1-4)
        circuit_breaker: CircuitBreaker instance to filter unavailable APIs

    Returns:
        List of API names available for this tier

    Raises:
        UnknownIntentError: If intent has no routing rules
    """
    if intent not in TIER_ROUTING_TABLE:
        raise UnknownIntentError(f"No routing rules for intent: {intent}")

    apis = TIER_ROUTING_TABLE.get(intent, {}).get(tier, [])

    # Filter out circuit-broken APIs
    return [api for api in apis if not circuit_breaker.is_open(api)]
