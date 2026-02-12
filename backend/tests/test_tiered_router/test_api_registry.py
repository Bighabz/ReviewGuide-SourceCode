import pytest
from app.services.tiered_router.api_registry import APIConfig, API_REGISTRY


def test_api_config_has_required_fields():
    """APIConfig should have all required fields"""
    config = APIConfig(
        name="test_api",
        mcp_tool="product_search",
        provider="test",
        cost_cents=5,
    )
    assert config.name == "test_api"
    assert config.mcp_tool == "product_search"
    assert config.provider == "test"
    assert config.cost_cents == 5
    assert config.timeout_ms == 5000  # default
    assert config.requires_consent is False  # default
    assert config.feature_flag is None  # default


def test_api_registry_contains_tier_1_affiliates():
    """Registry should contain Tier 1 affiliate APIs"""
    tier_1_apis = ["amazon_affiliate", "walmart_affiliate", "bestbuy_affiliate", "ebay_affiliate"]
    for api in tier_1_apis:
        assert api in API_REGISTRY
        assert API_REGISTRY[api].cost_cents == 0  # Affiliates are free


def test_api_registry_tier_3_4_require_consent():
    """Tier 3-4 APIs should require consent"""
    assert API_REGISTRY["reddit_api"].requires_consent is True
    assert API_REGISTRY["serpapi"].requires_consent is True


def test_api_registry_tier_3_4_have_feature_flags():
    """Tier 3-4 APIs should have feature flags"""
    assert API_REGISTRY["reddit_api"].feature_flag == "ENABLE_REDDIT_API"
    assert API_REGISTRY["serpapi"].feature_flag == "ENABLE_SERPAPI"
