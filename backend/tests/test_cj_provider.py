"""
Tests for CJ Affiliate Provider

Covers XML parsing, API calls, error handling, and caching behavior.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.affiliate.providers.cj_provider import CJAffiliateProvider


# ============================================================
# Sample XML fixtures
# ============================================================

SAMPLE_XML_TWO_PRODUCTS = """<?xml version="1.0" encoding="UTF-8"?>
<cj-api>
  <products total-matched="2" records-returned="2" page-number="1">
    <product>
      <ad-id>12345</ad-id>
      <advertiser-id>5167350</advertiser-id>
      <advertiser-name>Apple Vacations</advertiser-name>
      <buy-url>https://www.anrdoezrs.net/click-101568669-5167350?url=https%3A%2F%2Fexample.com%2Fproduct1</buy-url>
      <description>All-inclusive Caribbean vacation package</description>
      <image-url>https://images.example.com/vacation1.jpg</image-url>
      <in-stock>true</in-stock>
      <name>Caribbean Beach Resort Package</name>
      <price>1299.99</price>
      <currency>USD</currency>
      <sale-price>999.99</sale-price>
      <sku>AV-CARIB-001</sku>
      <manufacturer-name>Apple Vacations</manufacturer-name>
    </product>
    <product>
      <ad-id>12346</ad-id>
      <advertiser-id>5167350</advertiser-id>
      <advertiser-name>Apple Vacations</advertiser-name>
      <buy-url>https://www.anrdoezrs.net/click-101568669-5167350?url=https%3A%2F%2Fexample.com%2Fproduct2</buy-url>
      <description>Mexico all-inclusive resort deal</description>
      <image-url>https://images.example.com/vacation2.jpg</image-url>
      <in-stock>true</in-stock>
      <name>Cancun Resort All-Inclusive</name>
      <price>1599.00</price>
      <currency>USD</currency>
      <sale-price></sale-price>
      <sku>AV-CANCUN-002</sku>
      <manufacturer-name>Apple Vacations</manufacturer-name>
    </product>
  </products>
</cj-api>"""

SAMPLE_XML_EMPTY = """<?xml version="1.0" encoding="UTF-8"?>
<cj-api>
  <products total-matched="0" records-returned="0" page-number="1">
  </products>
</cj-api>"""


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def provider():
    """Create a CJ provider instance with test credentials."""
    return CJAffiliateProvider(
        api_key="test-api-key",
        website_id="test-website-id",
    )


# ============================================================
# Tests
# ============================================================

class TestCJProviderName:
    def test_provider_name(self, provider):
        """Provider name should return 'CJ'."""
        assert provider.get_provider_name() == "CJ"


class TestCJXMLParsing:
    def test_parse_products_from_xml(self, provider):
        """Should parse sample XML with 2 products and map all fields correctly."""
        products = provider._parse_xml_response(SAMPLE_XML_TWO_PRODUCTS)

        assert len(products) == 2

        # First product: has sale-price, should use it
        p1 = products[0]
        assert p1.product_id == "cj-12345"
        assert p1.title == "Caribbean Beach Resort Package"
        assert p1.price == 999.99  # sale-price preferred
        assert p1.currency == "USD"
        assert p1.affiliate_link == "https://www.anrdoezrs.net/click-101568669-5167350?url=https%3A%2F%2Fexample.com%2Fproduct1"
        assert p1.merchant == "Apple Vacations"
        assert p1.image_url == "https://images.example.com/vacation1.jpg"
        assert p1.rating is None
        assert p1.review_count is None
        assert p1.condition == "new"
        assert p1.availability is True
        assert p1.source_url == p1.affiliate_link

        # Second product: sale-price is empty, should use regular price
        p2 = products[1]
        assert p2.product_id == "cj-12346"
        assert p2.title == "Cancun Resort All-Inclusive"
        assert p2.price == 1599.00  # falls back to regular price
        assert p2.currency == "USD"
        assert p2.merchant == "Apple Vacations"
        assert p2.image_url == "https://images.example.com/vacation2.jpg"
        assert p2.availability is True

    def test_parse_empty_response(self, provider):
        """Empty XML response should return an empty list."""
        products = provider._parse_xml_response(SAMPLE_XML_EMPTY)
        assert products == []

    def test_fallback_to_regular_price(self, provider):
        """When sale-price is empty, should use the regular price."""
        products = provider._parse_xml_response(SAMPLE_XML_TWO_PRODUCTS)

        # Second product has empty sale-price
        p2 = products[1]
        assert p2.price == 1599.00

    def test_parse_invalid_xml(self, provider):
        """Malformed XML should return an empty list, not raise."""
        products = provider._parse_xml_response("<not valid xml>>>>>")
        assert products == []


class TestCJSearch:
    @pytest.mark.asyncio
    async def test_search_calls_api(self, provider):
        """Should call CJ API and return parsed products."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_XML_TWO_PRODUCTS

        with patch("app.services.affiliate.providers.cj_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.cj_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("vacation packages", limit=10)

        assert len(products) == 2
        assert products[0].title == "Caribbean Beach Resort Package"
        assert products[1].title == "Cancun Resort All-Inclusive"

    @pytest.mark.asyncio
    async def test_search_handles_api_error(self, provider):
        """500 response from CJ API should return an empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("app.services.affiliate.providers.cj_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.cj_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):

            products = await provider.search_products("vacation packages")

        assert products == []

    @pytest.mark.asyncio
    async def test_search_handles_timeout(self, provider):
        """httpx.TimeoutException should be caught and return an empty list."""
        with patch("app.services.affiliate.providers.cj_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch("app.services.affiliate.providers.cj_provider.redis_set_with_retry", new_callable=AsyncMock, return_value=True), \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.TimeoutException("Connection timed out")):

            products = await provider.search_products("vacation packages")

        assert products == []

    @pytest.mark.asyncio
    async def test_search_uses_cache(self, provider):
        """Should return cached results on cache hit without calling the API."""
        import json
        cached_data = json.dumps([
            {
                "product_id": "cj-cached",
                "title": "Cached Product",
                "price": 49.99,
                "currency": "USD",
                "affiliate_link": "https://example.com/cached",
                "merchant": "CachedMerchant",
                "image_url": None,
                "rating": None,
                "review_count": None,
                "condition": "new",
                "shipping_cost": None,
                "availability": True,
                "source_url": "https://example.com/cached",
            }
        ])

        with patch("app.services.affiliate.providers.cj_provider.redis_get_with_retry", new_callable=AsyncMock, return_value=cached_data) as mock_redis_get, \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_http:

            products = await provider.search_products("cached query")

        assert len(products) == 1
        assert products[0].title == "Cached Product"
        # HTTP should not have been called
        mock_http.assert_not_called()


class TestCJLinkHealth:
    @pytest.mark.asyncio
    async def test_check_link_healthy(self, provider):
        """200/301/302 responses should be considered healthy."""
        for status in (200, 301, 302):
            mock_response = MagicMock()
            mock_response.status_code = status

            with patch("httpx.AsyncClient.head", new_callable=AsyncMock, return_value=mock_response):
                result = await provider.check_link_health("https://www.anrdoezrs.net/click-test")

            assert result is True, f"Status {status} should be healthy"

    @pytest.mark.asyncio
    async def test_check_link_unhealthy(self, provider):
        """404 response should be considered unhealthy."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient.head", new_callable=AsyncMock, return_value=mock_response):
            result = await provider.check_link_health("https://www.anrdoezrs.net/click-bad")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_link_exception(self, provider):
        """Network errors should return False, not raise."""
        with patch("httpx.AsyncClient.head", new_callable=AsyncMock, side_effect=httpx.ConnectError("Connection refused")):
            result = await provider.check_link_health("https://www.anrdoezrs.net/click-err")

        assert result is False
