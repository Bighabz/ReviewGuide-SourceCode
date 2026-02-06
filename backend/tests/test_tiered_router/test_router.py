import pytest
from unittest.mock import MagicMock
from app.services.tiered_router.router import (
    TIER_ROUTING_TABLE,
    get_apis_for_tier,
    UnknownIntentError,
)


def test_tier_routing_table_has_product_intent():
    """Routing table should have product intent with 4 tiers"""
    assert "product" in TIER_ROUTING_TABLE
    assert 1 in TIER_ROUTING_TABLE["product"]
    assert 4 in TIER_ROUTING_TABLE["product"]


def test_tier_1_product_has_affiliates():
    """Product Tier 1 should have affiliate APIs"""
    tier_1 = TIER_ROUTING_TABLE["product"][1]
    assert "amazon_affiliate" in tier_1
    assert "walmart_affiliate" in tier_1


def test_tier_3_product_has_reddit():
    """Product Tier 3 should have reddit_api"""
    tier_3 = TIER_ROUTING_TABLE["product"][3]
    assert "reddit_api" in tier_3


def test_get_apis_for_tier_returns_apis():
    """get_apis_for_tier should return list of APIs"""
    mock_cb = MagicMock()
    mock_cb.is_open.return_value = False

    apis = get_apis_for_tier("product", 1, mock_cb)

    assert isinstance(apis, list)
    assert len(apis) > 0
    assert "amazon_affiliate" in apis


def test_get_apis_for_tier_filters_circuit_broken():
    """get_apis_for_tier should filter out circuit-broken APIs"""
    mock_cb = MagicMock()
    mock_cb.is_open.side_effect = lambda api: api == "amazon_affiliate"

    apis = get_apis_for_tier("product", 1, mock_cb)

    assert "amazon_affiliate" not in apis


def test_get_apis_for_tier_unknown_intent_raises():
    """get_apis_for_tier should raise for unknown intent"""
    mock_cb = MagicMock()
    mock_cb.is_open.return_value = False

    with pytest.raises(UnknownIntentError):
        get_apis_for_tier("invalid_intent", 1, mock_cb)


def test_price_check_has_no_tier_3_4():
    """price_check should have empty Tier 3-4"""
    assert TIER_ROUTING_TABLE["price_check"][3] == []
    assert TIER_ROUTING_TABLE["price_check"][4] == []
