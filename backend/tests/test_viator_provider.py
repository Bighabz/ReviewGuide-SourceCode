"""
Tests for Viator Activity Provider

Covers API search, response parsing, caching, fallback behavior,
registration, and MCP tool integration.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import json


# ============================================================
# Sample JSON fixtures (Viator /search/freetext response format)
# ============================================================

SAMPLE_VIATOR_RESPONSE = {
    "products": {
        "results": [
            {
                "productCode": "12345P1",
                "title": "Skip-the-Line Eiffel Tower Tour",
                "description": "Expert-guided tour of the Eiffel Tower...",
                "thumbnailUrl": "https://media.tacdn.com/media/attractions/eiffel.jpg",
                "rating": 4.8,
                "reviewCount": 2341,
                "pricing": {"summary": {"fromPrice": 65.00}},
                "currency": "USD",
                "duration": {"fixedDurationInMinutes": 120},
                "flags": ["FREE_CANCELLATION"],
                "productUrl": "https://www.viator.com/tours/Paris/Skip-Line-Eiffel/d479-12345P1",
            },
            {
                "productCode": "67890P2",
                "title": "Seine River Dinner Cruise",
                "description": "Enjoy a gourmet dinner while cruising the Seine...",
                "thumbnailUrl": "https://media.tacdn.com/media/attractions/seine-cruise.jpg",
                "rating": 4.5,
                "reviewCount": 1823,
                "pricing": {"summary": {"fromPrice": 95.50}},
                "currency": "USD",
                "duration": {"fixedDurationInMinutes": 180},
                "flags": [],
                "productUrl": "https://www.viator.com/tours/Paris/Seine-Dinner-Cruise/d479-67890P2",
            },
        ],
        "totalCount": 2,
    }
}

SAMPLE_VIATOR_EMPTY = {"products": {"results": [], "totalCount": 0}}


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def provider():
    """Create a Viator provider instance with test credentials."""
    from app.services.affiliate.providers.viator_provider import ViatorActivityProvider
    return ViatorActivityProvider(
        api_key="test-key",
        affiliate_id="test-pid",
    )


# ============================================================
# Tests
# ============================================================

class TestViatorRegistration:
    """Importing viator_provider registers 'viator' in AffiliateProviderRegistry."""

    def test_viator_in_registry(self):
        """Provider name 'viator' should appear in registry after import."""
        from app.services.affiliate.registry import AffiliateProviderRegistry
        from app.services.affiliate.providers import viator_provider  # noqa: F401

        assert "viator" in AffiliateProviderRegistry.list_providers()


class TestViatorSearch:
    """search_products calls Viator API and returns List[AffiliateProduct]."""

    @pytest.mark.asyncio
    async def test_search_calls_api(self, provider):
        """Should call Viator API POST /search/freetext and return AffiliateProduct list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_VIATOR_RESPONSE

        with patch("app.services.affiliate.providers.viator_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.viator_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("Paris tours", limit=10)

        assert len(products) == 2
        assert products[0].title == "Skip-the-Line Eiffel Tower Tour"
        assert products[1].title == "Seine River Dinner Cruise"

    @pytest.mark.asyncio
    async def test_search_handles_api_error(self, provider):
        """500 response from Viator API should return an empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("app.services.affiliate.providers.viator_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.viator_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("Paris tours")

        assert products == []

    @pytest.mark.asyncio
    async def test_search_handles_timeout(self, provider):
        """httpx.TimeoutException should be caught and fall back to PLP link."""
        with patch("app.services.affiliate.providers.viator_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.viator_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.TimeoutException("Connection timed out")):

            products = await provider.search_products("Paris tours")

        # Timeout falls back to PLP link (1 fallback result)
        assert len(products) == 1
        assert "viator.com/searchResults" in products[0].affiliate_link


class TestViatorResponseParsing:
    """Parsed results have correct fields: name, price, affiliate_link, image_url, currency."""

    @pytest.mark.asyncio
    async def test_parsed_fields(self, provider):
        """Parsed products should have all required fields with correct values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_VIATOR_RESPONSE

        with patch("app.services.affiliate.providers.viator_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.viator_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("Paris tours")

        p1 = products[0]
        assert p1.title != ""
        assert p1.price > 0
        assert "pid=" in p1.affiliate_link
        assert p1.image_url != ""
        assert p1.currency == "USD"
        assert isinstance(p1.rating, float)
        assert isinstance(p1.review_count, int)

        p2 = products[1]
        assert p2.title == "Seine River Dinner Cruise"
        assert p2.price == 95.50
        assert p2.image_url == "https://media.tacdn.com/media/attractions/seine-cruise.jpg"


class TestViatorCaching:
    """Cache hit returns cached results; cache miss calls API and caches."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_without_api_call(self, provider):
        """Should return cached results on cache hit without calling the API."""
        cached_data = json.dumps([
            {
                "product_id": "viator-cached",
                "title": "Cached Activity",
                "price": 49.99,
                "currency": "USD",
                "affiliate_link": "https://www.viator.com/cached?pid=test-pid",
                "merchant": "Viator",
                "image_url": "https://media.tacdn.com/cached.jpg",
                "rating": 4.5,
                "review_count": 100,
                "condition": "new",
                "shipping_cost": None,
                "availability": True,
                "source_url": "https://www.viator.com/cached",
            }
        ])

        with patch("app.services.affiliate.providers.viator_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=cached_data) as mock_redis_get, \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_http:

            products = await provider.search_products("cached query")

        assert len(products) == 1
        assert products[0].title == "Cached Activity"
        # HTTP should not have been called
        mock_http.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_calls_api_and_caches(self, provider):
        """Should call API on cache miss and cache the result."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_VIATOR_RESPONSE

        with patch("app.services.affiliate.providers.viator_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.viator_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True) as mock_redis_set, \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_http:

            products = await provider.search_products("Paris tours")

        assert len(products) == 2
        mock_http.assert_called_once()
        mock_redis_set.assert_called_once()


class TestViatorFallback:
    """When API call raises exception, returns PLP fallback search URL."""

    @pytest.mark.asyncio
    async def test_connect_error_falls_back_to_plp(self, provider):
        """ConnectError should fall back to a single AffiliateProduct with PLP search URL."""
        with patch("app.services.affiliate.providers.viator_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.viator_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.ConnectError("Connection refused")):

            products = await provider.search_products("Paris tours")

        assert len(products) == 1
        assert "viator.com/searchResults" in products[0].affiliate_link
        assert products[0].merchant == "Viator"
        assert products[0].product_id == "viator-plp-fallback"


class TestViatorMCPTool:
    """travel_search_activities MCP tool returns dict with 'activities' key."""

    @pytest.mark.asyncio
    async def test_mcp_tool_returns_activities(self):
        """Tool should return dict with 'activities' key when destination is provided."""
        from mcp_server.tools.travel_search_activities import travel_search_activities

        # Mock the ViatorActivityProvider
        mock_products = [
            MagicMock(
                title="Test Activity",
                price=50.0,
                currency="USD",
                affiliate_link="https://www.viator.com/test?pid=test",
                image_url="https://media.tacdn.com/test.jpg",
                rating=4.5,
                review_count=100,
                merchant="Viator",
            )
        ]

        with patch("mcp_server.tools.travel_search_activities.ViatorActivityProvider") as MockProvider:
            mock_instance = AsyncMock()
            mock_instance.search_products.return_value = mock_products
            MockProvider.return_value = mock_instance

            state = {"slots": {"destination": "Paris"}}
            result = await travel_search_activities(state)

        assert "activities" in result
        assert len(result["activities"]) > 0
        assert result["activities"][0]["name"] == "Test Activity"
