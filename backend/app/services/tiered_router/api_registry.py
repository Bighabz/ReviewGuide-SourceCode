"""API Registry - Maps logical API names to implementation details."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class APIConfig:
    """Configuration for a single API endpoint.

    Attributes:
        name: Logical name used in routing table
        mcp_tool: MCP tool name to execute
        provider: Provider key passed to MCP tool
        cost_cents: Cost per call in cents (0 for affiliates)
        timeout_ms: Request timeout in milliseconds
        requires_consent: Whether Tier 3-4 consent is needed
        feature_flag: Config flag that must be enabled (e.g., ENABLE_SERPAPI)
    """
    name: str
    mcp_tool: str
    provider: str
    cost_cents: int
    timeout_ms: int = 5000
    requires_consent: bool = False
    feature_flag: Optional[str] = None


API_REGISTRY: dict[str, APIConfig] = {
    # ============================================
    # TIER 1 - Affiliates (free, revenue share)
    # ============================================
    "amazon_affiliate": APIConfig(
        name="amazon_affiliate",
        mcp_tool="product_affiliate",
        provider="amazon",
        cost_cents=0,
    ),
    "ebay_affiliate": APIConfig(
        name="ebay_affiliate",
        mcp_tool="product_affiliate",
        provider="ebay",
        cost_cents=0,
    ),
    "walmart_affiliate": APIConfig(
        name="walmart_affiliate",
        mcp_tool="product_affiliate",
        provider="walmart",
        cost_cents=0,
    ),
    "bestbuy_affiliate": APIConfig(
        name="bestbuy_affiliate",
        mcp_tool="product_affiliate",
        provider="bestbuy",
        cost_cents=0,
    ),

    # ============================================
    # TIER 1 - Search (low cost)
    # ============================================
    "google_cse_product": APIConfig(
        name="google_cse_product",
        mcp_tool="product_search",
        provider="google_cse",
        cost_cents=1,
    ),
    "google_cse_travel": APIConfig(
        name="google_cse_travel",
        mcp_tool="travel_search",
        provider="google_cse",
        cost_cents=1,
    ),

    # ============================================
    # TIER 2 - Extended search
    # ============================================
    "bing_search": APIConfig(
        name="bing_search",
        mcp_tool="product_search",
        provider="bing",
        cost_cents=1,
    ),
    "youtube_transcripts": APIConfig(
        name="youtube_transcripts",
        mcp_tool="product_evidence",
        provider="youtube",
        cost_cents=0,
        feature_flag="ENABLE_YOUTUBE_TRANSCRIPTS",
    ),
    "google_shopping": APIConfig(
        name="google_shopping",
        mcp_tool="product_search",
        provider="google_shopping",
        cost_cents=1,
    ),

    # ============================================
    # TIER 3 - Consent required
    # ============================================
    "reddit_api": APIConfig(
        name="reddit_api",
        mcp_tool="product_evidence",
        provider="reddit",
        cost_cents=1,
        requires_consent=True,
        feature_flag="ENABLE_REDDIT_API",
    ),

    # ============================================
    # TIER 2 - Review search (core feature)
    # ============================================
    "serpapi": APIConfig(
        name="serpapi",
        mcp_tool="review_search",
        provider="serpapi",
        cost_cents=1,
        requires_consent=False,
        feature_flag="ENABLE_SERPAPI",
    ),

    # ============================================
    # TRAVEL APIs
    # ============================================
    "amadeus": APIConfig(
        name="amadeus",
        mcp_tool="travel_search_flights",
        provider="amadeus",
        cost_cents=0,
    ),
    "booking": APIConfig(
        name="booking",
        mcp_tool="travel_search_hotels",
        provider="booking",
        cost_cents=0,
    ),
    "expedia": APIConfig(
        name="expedia",
        mcp_tool="travel_search_hotels",
        provider="expedia",
        cost_cents=0,
    ),
    "skyscanner": APIConfig(
        name="skyscanner",
        mcp_tool="travel_search_flights",
        provider="skyscanner",
        cost_cents=0,
    ),
    "tripadvisor": APIConfig(
        name="tripadvisor",
        mcp_tool="travel_destination_facts",
        provider="tripadvisor",
        cost_cents=0,
    ),
}


def get_api_config(api_name: str) -> Optional[APIConfig]:
    """Get API configuration by name."""
    return API_REGISTRY.get(api_name)
