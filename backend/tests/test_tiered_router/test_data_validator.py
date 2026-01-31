# backend/tests/test_tiered_router/test_data_validator.py
import pytest
from app.services.tiered_router.data_validator import (
    DataValidator,
    ValidationResult,
    ThresholdConfig,
    INTENT_THRESHOLDS,
)


@pytest.fixture
def validator():
    return DataValidator(max_auto_tier=2)


def test_sufficient_product_results(validator):
    """3+ products should be sufficient for product intent"""
    results = {
        "amazon": {"status": "success", "data": {"products": [{"name": "p1"}, {"name": "p2"}, {"name": "p3"}]}},
    }

    result, metadata = validator.validate("product", 1, results)

    assert result == ValidationResult.SUFFICIENT
    assert metadata["item_count"] == 3


def test_insufficient_product_escalates(validator):
    """< 3 products should escalate to next tier"""
    results = {
        "amazon": {"status": "success", "data": {"products": [{"name": "p1"}, {"name": "p2"}]}},
    }

    result, metadata = validator.validate("product", 1, results)

    assert result == ValidationResult.ESCALATE
    assert metadata["next_tier"] == 2


def test_tier_3_requires_consent(validator):
    """Tier 3 escalation should require consent"""
    results = {
        "bing": {"status": "success", "data": {"products": [{"name": "p1"}]}},
    }

    result, metadata = validator.validate("product", 2, results, user_consent={"account_toggle": False})

    assert result == ValidationResult.CONSENT_REQUIRED
    assert metadata["consent_type"] == "account_toggle"


def test_tier_3_with_account_toggle_requires_per_query(validator):
    """Account toggle enabled should still require per-query consent"""
    results = {
        "bing": {"status": "success", "data": {"products": [{"name": "p1"}]}},
    }

    result, metadata = validator.validate("product", 2, results, user_consent={"account_toggle": True, "per_query": False})

    assert result == ValidationResult.CONSENT_REQUIRED
    assert metadata["consent_type"] == "per_query"


def test_tier_3_with_full_consent_escalates(validator):
    """Full consent should allow Tier 3 escalation"""
    results = {
        "bing": {"status": "success", "data": {"products": [{"name": "p1"}]}},
    }

    result, metadata = validator.validate("product", 2, results, user_consent={"account_toggle": True, "per_query": True})

    assert result == ValidationResult.ESCALATE
    assert metadata["next_tier"] == 3


def test_comparison_requires_all_products(validator):
    """Comparison intent should require all requested products"""
    results = {
        "amazon": {"status": "success", "data": {"products": [{"name": "Dyson V15"}]}},
    }

    result, metadata = validator.validate(
        "comparison", 1, results,
        requested_products=["Dyson V15", "Shark Navigator"]
    )

    assert result == ValidationResult.ESCALATE  # Missing Shark


def test_comparison_sufficient_with_all_products(validator):
    """Comparison with all products should be sufficient"""
    results = {
        "amazon": {"status": "success", "data": {"products": [
            {"name": "Dyson V15 Detect"},
            {"name": "Shark Navigator Lift-Away"},
        ]}},
    }

    result, metadata = validator.validate(
        "comparison", 1, results,
        requested_products=["Dyson V15", "Shark Navigator"]
    )

    assert result == ValidationResult.SUFFICIENT


def test_max_tier_reached(validator):
    """Tier 4 exhausted should return MAX_TIER_REACHED"""
    results = {
        "serpapi": {"status": "success", "data": {"products": [{"name": "p1"}]}},
    }

    result, metadata = validator.validate(
        "product", 4, results,
        user_consent={"account_toggle": True, "per_query": True}
    )

    assert result == ValidationResult.MAX_TIER_REACHED
