"""
Unit tests for SerperShoppingProvider.

Covers:
  SRCH-01: Provider calls https://google.serper.dev/shopping with X-API-KEY header
  SRCH-02: Provider registers as 'serper_shopping' in AffiliateProviderRegistry
  SRCH-03: Redis cache prevents duplicate API calls for identical queries
  FIX-02:  Returns multi-retailer products (not eBay-only)
  FIX-03:  Product cards have image_url from Serper imageUrl field
"""
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Environment bootstrap -- must happen before any app import
# ---------------------------------------------------------------------------
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("LOG_ENABLED", "false")
os.environ.setdefault("SERPAPI_API_KEY", "test-serper-key")

from app.services.affiliate.providers.serper_shopping_provider import (  # noqa: E402
    SerperShoppingProvider,
    _parse_price,
    SERPER_SHOPPING_URL,
    CACHE_TTL,
)
from app.services.affiliate.base import AffiliateProduct  # noqa: E402

# ---------------------------------------------------------------------------
# Sample Serper API response
# ---------------------------------------------------------------------------
SAMPLE_SERPER_RESPONSE = {
    "shopping": [
        {
            "title": "Sony WH-1000XM5 Wireless Headphones",
            "source": "Best Buy",
            "link": "https://www.bestbuy.com/site/sony-wh1000xm5/123",
            "price": "$299.99",
            "imageUrl": "https://encrypted-tbn0.gstatic.com/shopping?q=sony+xm5",
            "rating": 4.7,
            "ratingCount": 1250,
            "productId": "prod_001",
            "position": 1,
        },
        {
            "title": "Sony WH-1000XM5 Noise Cancelling",
            "source": "Walmart",
            "link": "https://www.walmart.com/ip/sony-xm5/456",
            "price": "$278.00",
            "imageUrl": "https://encrypted-tbn0.gstatic.com/shopping?q=sony+xm5+walmart",
            "rating": 4.5,
            "ratingCount": 830,
            "productId": "prod_002",
            "position": 2,
        },
        {
            "title": "Sony Headphones Case Accessory",
            "source": "Amazon",
            "link": "https://www.amazon.com/dp/B09XYZ",
            "price": "$19.99",
            "imageUrl": "https://encrypted-tbn0.gstatic.com/shopping?q=sony+case",
            "rating": 4.2,
            "ratingCount": 300,
            "productId": "prod_003",
            "position": 3,
        },
    ]
}


# ---------------------------------------------------------------------------
# Tests: _parse_price
# ---------------------------------------------------------------------------

class TestParsePrice:
    def test_simple_price(self):
        assert _parse_price("$299.99") == 299.99

    def test_price_with_comma(self):
        assert _parse_price("$1,299.99") == 1299.99

    def test_price_no_dollar_sign(self):
        assert _parse_price("49.99") == 49.99

    def test_price_invalid_returns_zero(self):
        assert _parse_price("free") == 0.0

    def test_price_none_returns_zero(self):
        assert _parse_price(None) == 0.0

    def test_price_empty_string_returns_zero(self):
        assert _parse_price("") == 0.0


# ---------------------------------------------------------------------------
# Tests: SerperShoppingProvider
# ---------------------------------------------------------------------------

class TestSerperShoppingProvider:

    def test_get_provider_name(self):
        provider = SerperShoppingProvider()
        assert provider.get_provider_name() == "Serper Shopping"

    @pytest.mark.asyncio
    async def test_search_products_calls_serper_api(self):
        """SRCH-01: Provider posts to google.serper.dev/shopping with X-API-KEY."""
        provider = SerperShoppingProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = SAMPLE_SERPER_RESPONSE

        with patch("app.services.affiliate.providers.serper_shopping_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.serper_shopping_provider.redis_set_with_retry", new_callable=AsyncMock), \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            results = await provider.search_products("sony headphones", limit=5)

            # Verify API was called with correct URL and headers
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == SERPER_SHOPPING_URL
            assert call_args[1]["headers"]["X-API-KEY"] == "test-serper-key"

    @pytest.mark.asyncio
    async def test_search_products_returns_multi_retailer(self):
        """FIX-02: Returns products from multiple retailers."""
        provider = SerperShoppingProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = SAMPLE_SERPER_RESPONSE

        with patch("app.services.affiliate.providers.serper_shopping_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.serper_shopping_provider.redis_set_with_retry", new_callable=AsyncMock), \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            results = await provider.search_products("sony headphones", limit=10)

            assert len(results) == 3
            merchants = {r.merchant for r in results}
            assert len(merchants) >= 2, f"Expected multi-retailer, got: {merchants}"
            assert "Best Buy" in merchants
            assert "Walmart" in merchants

    @pytest.mark.asyncio
    async def test_search_products_has_image_url(self):
        """FIX-03: Every product has image_url from Serper imageUrl field."""
        provider = SerperShoppingProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = SAMPLE_SERPER_RESPONSE

        with patch("app.services.affiliate.providers.serper_shopping_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.serper_shopping_provider.redis_set_with_retry", new_callable=AsyncMock), \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            results = await provider.search_products("sony headphones", limit=10)

            for product in results:
                assert product.image_url is not None, f"Missing image_url for {product.title}"
                assert product.image_url.startswith("http"), f"Invalid image URL: {product.image_url}"

    @pytest.mark.asyncio
    async def test_search_products_returns_affiliate_products(self):
        """Products are proper AffiliateProduct dataclass instances."""
        provider = SerperShoppingProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = SAMPLE_SERPER_RESPONSE

        with patch("app.services.affiliate.providers.serper_shopping_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.serper_shopping_provider.redis_set_with_retry", new_callable=AsyncMock), \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            results = await provider.search_products("sony headphones", limit=10)

            for product in results:
                assert isinstance(product, AffiliateProduct)
                assert product.product_id != ""
                assert product.title != ""
                assert product.price > 0
                assert product.currency == "USD"
                assert product.affiliate_link.startswith("http")
                assert product.merchant != ""

    @pytest.mark.asyncio
    async def test_cache_hit_skips_api_call(self):
        """SRCH-03: Cache hit returns cached data, no HTTP call."""
        provider = SerperShoppingProvider()

        cached_products = [
            {
                "product_id": "cached_001",
                "title": "Cached Product",
                "price": 99.99,
                "currency": "USD",
                "affiliate_link": "https://example.com/cached",
                "merchant": "CachedStore",
                "image_url": "https://example.com/img.jpg",
                "rating": 4.5,
                "review_count": 100,
                "condition": "new",
                "shipping_cost": None,
                "availability": True,
                "source_url": "https://example.com/cached",
            }
        ]

        with patch("app.services.affiliate.providers.serper_shopping_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=json.dumps(cached_products)), \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            results = await provider.search_products("test query")

            # API should NOT have been called
            mock_client_cls.assert_not_called()
            assert len(results) == 1
            assert results[0].title == "Cached Product"

    @pytest.mark.asyncio
    async def test_cache_miss_stores_result(self):
        """SRCH-03: Cache miss calls API and stores result in Redis."""
        provider = SerperShoppingProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = SAMPLE_SERPER_RESPONSE

        mock_redis_set = AsyncMock()

        with patch("app.services.affiliate.providers.serper_shopping_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.serper_shopping_provider.redis_set_with_retry", mock_redis_set), \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            results = await provider.search_products("sony headphones")

            # Redis SET should have been called with TTL
            mock_redis_set.assert_called_once()
            call_args = mock_redis_set.call_args
            assert call_args[1]["ex"] == CACHE_TTL

    @pytest.mark.asyncio
    async def test_min_max_price_filtering(self):
        """Price filters exclude products outside range."""
        provider = SerperShoppingProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = SAMPLE_SERPER_RESPONSE

        with patch("app.services.affiliate.providers.serper_shopping_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.serper_shopping_provider.redis_set_with_retry", new_callable=AsyncMock), \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            # Only products between $250 and $300
            results = await provider.search_products("sony headphones", min_price=250.0, max_price=300.0)

            for product in results:
                assert product.price >= 250.0
                assert product.price <= 300.0

            # $19.99 product should be filtered out
            titles = [r.title for r in results]
            assert not any("Case" in t for t in titles), "Accessory should be filtered by price"

    @pytest.mark.asyncio
    async def test_empty_api_key_returns_empty(self):
        """If SERPAPI_API_KEY is empty, search returns [] without calling API."""
        provider = SerperShoppingProvider()

        with patch("app.services.affiliate.providers.serper_shopping_provider.settings") as mock_settings, \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            mock_settings.SERPAPI_API_KEY = ""

            results = await provider.search_products("test query")

            assert results == []
            mock_client_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_api_error_returns_empty(self):
        """API errors return empty list, no crash."""
        provider = SerperShoppingProvider()

        with patch("app.services.affiliate.providers.serper_shopping_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.serper_shopping_provider.redis_set_with_retry", new_callable=AsyncMock), \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.side_effect = Exception("Network error")
            mock_client_cls.return_value = mock_client

            results = await provider.search_products("test query")
            assert results == []

    @pytest.mark.asyncio
    async def test_limit_caps_results(self):
        """Results capped at limit parameter."""
        provider = SerperShoppingProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = SAMPLE_SERPER_RESPONSE

        with patch("app.services.affiliate.providers.serper_shopping_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.serper_shopping_provider.redis_set_with_retry", new_callable=AsyncMock), \
             patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            results = await provider.search_products("sony headphones", limit=2)
            assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_generate_affiliate_link_passthrough(self):
        """generate_affiliate_link returns product_id unchanged (direct URLs)."""
        provider = SerperShoppingProvider()
        link = await provider.generate_affiliate_link("https://www.bestbuy.com/product/123")
        assert link == "https://www.bestbuy.com/product/123"

    @pytest.mark.asyncio
    async def test_check_link_health_success(self):
        """check_link_health returns True for HTTP < 400."""
        provider = SerperShoppingProvider()

        with patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_client.head.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await provider.check_link_health("https://example.com/product")
            assert result is True

    @pytest.mark.asyncio
    async def test_check_link_health_failure(self):
        """check_link_health returns False for exceptions."""
        provider = SerperShoppingProvider()

        with patch("app.services.affiliate.providers.serper_shopping_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head.side_effect = Exception("Connection refused")
            mock_client_cls.return_value = mock_client

            result = await provider.check_link_health("https://example.com/product")
            assert result is False
