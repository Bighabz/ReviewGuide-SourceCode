"""
Tests for Impact.com Affiliate Catalog Provider

Covers search, registration, rate limiting, feature flag, parsing, caching,
and error handling behavior.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.affiliate.providers.impact_provider import ImpactAffiliateProvider


# ============================================================
# Sample JSON fixtures
# ============================================================

SAMPLE_JSON_TWO_PRODUCTS = {
    "Items": [
        {
            "CatalogItemId": "98765",
            "Name": "Sony WH-1000XM5 Wireless Headphones",
            "CurrentPrice": 348.00,
            "Currency": "USD",
            "Url": "https://track.impact.com/click/12345/sony-wh1000xm5",
            "ImageUrl": "https://images.example.com/sony-xm5.jpg",
            "CampaignName": "Best Buy Electronics",
            "StockAvailability": "InStock",
            "Condition": "New",
            "ShippingRate": 0,
            "Manufacturer": "Sony",
        },
        {
            "CatalogItemId": "98766",
            "Name": "Bose QuietComfort Ultra Earbuds",
            "CurrentPrice": 299.00,
            "Currency": "USD",
            "Url": "https://track.impact.com/click/12345/bose-qc-ultra",
            "ImageUrl": "https://images.example.com/bose-qc.jpg",
            "CampaignName": "Bose Direct",
            "StockAvailability": "InStock",
            "Condition": "New",
            "ShippingRate": 5.99,
            "Manufacturer": "Bose",
        },
    ]
}

SAMPLE_JSON_EMPTY = {"Items": []}


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def provider():
    """Create an Impact.com provider instance with test credentials."""
    return ImpactAffiliateProvider(
        account_sid="test-sid",
        auth_token="test-token",
        api_enabled=True,
    )


# ============================================================
# TestImpactSearch (PROV-01a)
# ============================================================

class TestImpactSearch:
    @pytest.mark.asyncio
    async def test_search_calls_api(self, provider):
        """Should call Impact.com API and return parsed products."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_JSON_TWO_PRODUCTS

        with patch("app.services.affiliate.providers.impact_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.impact_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch.object(provider, "_check_rate_limit", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("wireless headphones", limit=10)

        assert len(products) == 2
        assert products[0].title == "Sony WH-1000XM5 Wireless Headphones"
        assert products[1].title == "Bose QuietComfort Ultra Earbuds"


# ============================================================
# TestImpactRegistration (PROV-01b)
# ============================================================

class TestImpactRegistration:
    def test_provider_registered_in_registry(self):
        """Importing impact_provider module should register 'impact' in the registry."""
        from app.services.affiliate.registry import AffiliateProviderRegistry
        # Module is already imported at the top of this file, triggering the decorator
        providers = AffiliateProviderRegistry.list_providers()
        assert "impact" in providers

    def test_loader_init_map_has_impact(self):
        """Loader _PROVIDER_INIT_MAP should contain an 'impact' entry."""
        from app.services.affiliate.loader import _PROVIDER_INIT_MAP
        assert "impact" in _PROVIDER_INIT_MAP


# ============================================================
# TestImpactRateLimit (PROV-01c)
# ============================================================

class TestImpactRateLimit:
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_when_exceeded(self, provider):
        """When rate limit is exceeded, search should return empty without calling API."""
        with patch("app.services.affiliate.providers.impact_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch.object(provider, "_check_rate_limit", new_callable=AsyncMock, return_value=False), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_http:

            products = await provider.search_products("headphones")

        assert products == []
        mock_http.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_allows_when_under(self, provider):
        """When under rate limit, search should proceed and return products."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_JSON_TWO_PRODUCTS

        with patch("app.services.affiliate.providers.impact_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.impact_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch.object(provider, "_check_rate_limit", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("headphones")

        assert len(products) == 2


# ============================================================
# TestImpactFeatureFlag (PROV-01d)
# ============================================================

class TestImpactFeatureFlag:
    @pytest.mark.asyncio
    async def test_disabled_returns_empty(self):
        """When api_enabled=False, search should return empty without calling API."""
        disabled_provider = ImpactAffiliateProvider(
            account_sid="test-sid",
            auth_token="test-token",
            api_enabled=False,
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_http:
            products = await disabled_provider.search_products("headphones")

        assert products == []
        mock_http.assert_not_called()


# ============================================================
# TestImpactParsing (PROV-01e)
# ============================================================

class TestImpactParsing:
    def test_parse_response_maps_fields(self, provider):
        """Should correctly map all Impact.com JSON fields to AffiliateProduct."""
        products = provider._parse_response(SAMPLE_JSON_TWO_PRODUCTS)

        assert len(products) == 2

        p1 = products[0]
        assert p1.product_id == "98765"
        assert p1.title == "Sony WH-1000XM5 Wireless Headphones"
        assert p1.price == 348.00
        assert p1.currency == "USD"
        assert p1.affiliate_link.startswith("https://track.impact.com")
        assert p1.merchant == "Best Buy Electronics"
        assert p1.image_url == "https://images.example.com/sony-xm5.jpg"
        assert p1.rating is None
        assert p1.condition == "new"
        assert p1.availability is True
        assert p1.shipping_cost == 0

    def test_parse_empty_items(self, provider):
        """Empty Items list should return empty product list."""
        products = provider._parse_response(SAMPLE_JSON_EMPTY)
        assert products == []

    def test_parse_missing_fields(self, provider):
        """Items with only Name and CatalogItemId should not raise."""
        sparse_data = {
            "Items": [
                {
                    "CatalogItemId": "99999",
                    "Name": "Minimal Product",
                }
            ]
        }
        products = provider._parse_response(sparse_data)
        assert len(products) == 1
        assert products[0].product_id == "99999"
        assert products[0].title == "Minimal Product"
        assert products[0].price == 0.0
        assert products[0].currency == "USD"
        assert products[0].condition == "new"


# ============================================================
# TestImpactCache (PROV-01f)
# ============================================================

class TestImpactCache:
    @pytest.mark.asyncio
    async def test_cache_hit_skips_api(self, provider):
        """On cache hit, should return products without calling the API."""
        cached_data = json.dumps([
            {
                "product_id": "impact-cached",
                "title": "Cached Impact Product",
                "price": 99.99,
                "currency": "USD",
                "affiliate_link": "https://track.impact.com/cached",
                "merchant": "CachedMerchant",
                "image_url": None,
                "rating": None,
                "review_count": None,
                "condition": "new",
                "shipping_cost": None,
                "availability": True,
                "source_url": "https://track.impact.com/cached",
            }
        ])

        with patch("app.services.affiliate.providers.impact_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=cached_data), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_http:

            products = await provider.search_products("cached query")

        assert len(products) == 1
        assert products[0].title == "Cached Impact Product"
        mock_http.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_writes_results(self, provider):
        """On cache miss, should call API and write results to Redis cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_JSON_TWO_PRODUCTS

        with patch("app.services.affiliate.providers.impact_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.impact_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True) as mock_redis_set, \
             patch.object(provider, "_check_rate_limit", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("headphones")

        assert len(products) == 2
        mock_redis_set.assert_called_once()


# ============================================================
# TestImpactErrorHandling (PROV-01g)
# ============================================================

class TestImpactErrorHandling:
    @pytest.mark.asyncio
    async def test_timeout_returns_empty(self, provider):
        """httpx.TimeoutException should return empty list, not raise."""
        with patch("app.services.affiliate.providers.impact_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch.object(provider, "_check_rate_limit", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.TimeoutException("Connection timed out")):

            products = await provider.search_products("headphones")

        assert products == []

    @pytest.mark.asyncio
    async def test_500_returns_empty(self, provider):
        """HTTP 500 response should return empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("app.services.affiliate.providers.impact_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch.object(provider, "_check_rate_limit", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("headphones")

        assert products == []

    @pytest.mark.asyncio
    async def test_429_returns_empty(self, provider):
        """HTTP 429 response should return empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"

        with patch("app.services.affiliate.providers.impact_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch.object(provider, "_check_rate_limit", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("headphones")

        assert products == []
