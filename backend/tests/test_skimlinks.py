"""
Unit tests for Skimlinks Link Wrapper service.

Covers:
  AFFL-01: Supported merchant URLs are wrapped with go.skimresources.com redirect
  AFFL-02: Amazon and eBay URLs are never wrapped (excluded domains)
  AFFL-03: Merchant domain list cached in Redis with 24h TTL, fetched from API on miss
  Feature flag: SKIMLINKS_API_ENABLED=false returns original URL unchanged
  Auth: OAuth2 token fetch and graceful failure handling
"""
import os

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
os.environ.setdefault("ADMIN_PASSWORD", "testpassword123")

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.affiliate.skimlinks import (  # noqa: E402
    SkimlinksLinkWrapper,
    EXCLUDED_DOMAINS,
    DOMAIN_CACHE_TTL,
    REDIS_DOMAIN_CACHE_KEY,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def wrapper():
    """Create a SkimlinksLinkWrapper with test credentials (enabled)."""
    with patch("app.services.affiliate.skimlinks.settings") as mock_settings:
        mock_settings.SKIMLINKS_PUBLISHER_ID = "12345"
        mock_settings.SKIMLINKS_DOMAIN_ID = "67890"
        mock_settings.SKIMLINKS_CLIENT_ID = "test-client"
        mock_settings.SKIMLINKS_CLIENT_SECRET = "test-secret"
        mock_settings.SKIMLINKS_API_ENABLED = True
        mock_settings.SKIMLINKS_DOMAIN_CACHE_TTL = 86400
        w = SkimlinksLinkWrapper()
    return w


@pytest.fixture
def disabled_wrapper():
    """Create a SkimlinksLinkWrapper with feature flag disabled."""
    with patch("app.services.affiliate.skimlinks.settings") as mock_settings:
        mock_settings.SKIMLINKS_PUBLISHER_ID = "12345"
        mock_settings.SKIMLINKS_DOMAIN_ID = "67890"
        mock_settings.SKIMLINKS_CLIENT_ID = "test-client"
        mock_settings.SKIMLINKS_CLIENT_SECRET = "test-secret"
        mock_settings.SKIMLINKS_API_ENABLED = False
        mock_settings.SKIMLINKS_DOMAIN_CACHE_TTL = 86400
        w = SkimlinksLinkWrapper()
    return w


@pytest.fixture
def mock_merchant_domains():
    """Standard set of merchant domains for testing."""
    return {"bestbuy.com", "walmart.com", "target.com", "newegg.com"}


# ---------------------------------------------------------------------------
# TestWrapUrl -- AFFL-01, AFFL-02
# ---------------------------------------------------------------------------

class TestWrapUrl:
    """Tests for URL wrapping logic: supported domains, exclusions, www prefix."""

    @pytest.mark.asyncio
    async def test_supported_domain_wrapped(self, wrapper, mock_merchant_domains):
        """AFFL-01: A URL from a supported merchant domain is wrapped with go.skimresources.com."""
        with patch.object(wrapper, "_get_merchant_domains", new_callable=AsyncMock, return_value=mock_merchant_domains):
            result = await wrapper.wrap_url("https://www.bestbuy.com/site/sony-wh1000xm5/12345.p")

        assert result.startswith("https://go.skimresources.com")
        assert "id=12345X67890" in result
        assert "xs=1" in result
        assert "bestbuy.com" in result  # URL-encoded original URL contains the domain

    @pytest.mark.asyncio
    async def test_unsupported_domain_passthrough(self, wrapper, mock_merchant_domains):
        """AFFL-01: A URL from an unsupported domain passes through unchanged."""
        original_url = "https://www.unknownshop.com/product"
        with patch.object(wrapper, "_get_merchant_domains", new_callable=AsyncMock, return_value=mock_merchant_domains):
            result = await wrapper.wrap_url(original_url)

        assert result == original_url

    @pytest.mark.asyncio
    async def test_www_prefix_stripped(self, wrapper):
        """AFFL-01: www. prefix is stripped before domain lookup so www.bestbuy.com matches bestbuy.com."""
        domains = {"bestbuy.com"}
        with patch.object(wrapper, "_get_merchant_domains", new_callable=AsyncMock, return_value=domains):
            result = await wrapper.wrap_url("https://www.bestbuy.com/product")

        assert result.startswith("https://go.skimresources.com")

    @pytest.mark.asyncio
    async def test_amazon_excluded(self, wrapper):
        """AFFL-02: Amazon URLs are never wrapped, even if amazon.com is in the domain set."""
        domains = {"amazon.com", "bestbuy.com"}
        with patch.object(wrapper, "_get_merchant_domains", new_callable=AsyncMock, return_value=domains):
            # amazon.com
            result = await wrapper.wrap_url("https://www.amazon.com/dp/B09XS7JWHH")
            assert result == "https://www.amazon.com/dp/B09XS7JWHH"

            # amzn.to
            result = await wrapper.wrap_url("https://amzn.to/3abc123")
            assert result == "https://amzn.to/3abc123"

            # amazon.co.uk
            result = await wrapper.wrap_url("https://www.amazon.co.uk/dp/B09XS7JWHH")
            assert result == "https://www.amazon.co.uk/dp/B09XS7JWHH"

    @pytest.mark.asyncio
    async def test_ebay_excluded(self, wrapper):
        """AFFL-02: eBay URLs are never wrapped, even if ebay.com is in the domain set."""
        domains = {"ebay.com", "bestbuy.com"}
        with patch.object(wrapper, "_get_merchant_domains", new_callable=AsyncMock, return_value=domains):
            # ebay.com
            result = await wrapper.wrap_url("https://www.ebay.com/itm/12345")
            assert result == "https://www.ebay.com/itm/12345"

            # ebay.co.uk
            result = await wrapper.wrap_url("https://www.ebay.co.uk/itm/67890")
            assert result == "https://www.ebay.co.uk/itm/67890"


# ---------------------------------------------------------------------------
# TestDomainCache -- AFFL-03
# ---------------------------------------------------------------------------

class TestDomainCache:
    """Tests for Redis domain caching: hit, miss, TTL."""

    @pytest.mark.asyncio
    async def test_cache_hit(self, wrapper):
        """AFFL-03: When Redis returns cached domain JSON, _get_merchant_domains returns cached set without API call."""
        wrapper._merchant_domains = None  # Clear in-memory cache
        cached_json = json.dumps(["bestbuy.com", "walmart.com"])

        with patch("app.services.affiliate.skimlinks.redis_get_with_retry", new_callable=AsyncMock, return_value=cached_json) as mock_get, \
             patch.object(wrapper, "_fetch_domains_from_api", new_callable=AsyncMock) as mock_api:
            domains = await wrapper._get_merchant_domains()

        assert domains == {"bestbuy.com", "walmart.com"}
        mock_get.assert_called_once_with(REDIS_DOMAIN_CACHE_KEY)
        mock_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_fetches_api(self, wrapper):
        """AFFL-03: When Redis returns None, _get_merchant_domains calls the API and writes to Redis."""
        wrapper._merchant_domains = None  # Clear in-memory cache
        api_domains = {"bestbuy.com", "walmart.com"}

        with patch("app.services.affiliate.skimlinks.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch.object(wrapper, "_fetch_domains_from_api", new_callable=AsyncMock, return_value=api_domains) as mock_api, \
             patch("app.services.affiliate.skimlinks.redis_set_with_retry", new_callable=AsyncMock) as mock_set:
            domains = await wrapper._get_merchant_domains()

        assert domains == api_domains
        mock_api.assert_called_once()
        mock_set.assert_called_once()
        # Verify the key and TTL
        call_kwargs = mock_set.call_args
        assert call_kwargs[0][0] == REDIS_DOMAIN_CACHE_KEY  # key
        assert call_kwargs[1]["ex"] == DOMAIN_CACHE_TTL  # TTL = 86400

    @pytest.mark.asyncio
    async def test_cache_ttl(self, wrapper):
        """AFFL-03: The Redis SET call uses ex=86400 (24 hours)."""
        wrapper._merchant_domains = None
        api_domains = {"bestbuy.com"}

        with patch("app.services.affiliate.skimlinks.redis_get_with_retry", new_callable=AsyncMock, return_value=None), \
             patch.object(wrapper, "_fetch_domains_from_api", new_callable=AsyncMock, return_value=api_domains), \
             patch("app.services.affiliate.skimlinks.redis_set_with_retry", new_callable=AsyncMock) as mock_set:
            await wrapper._get_merchant_domains()

        assert mock_set.call_args[1]["ex"] == 86400


# ---------------------------------------------------------------------------
# TestFeatureFlag
# ---------------------------------------------------------------------------

class TestFeatureFlag:
    """Tests for the SKIMLINKS_API_ENABLED feature flag."""

    @pytest.mark.asyncio
    async def test_disabled_passthrough(self, disabled_wrapper):
        """When enabled=False, wrap_url returns original URL without checking domains."""
        original_url = "https://www.bestbuy.com/product"
        with patch.object(disabled_wrapper, "_get_merchant_domains", new_callable=AsyncMock) as mock_domains:
            result = await disabled_wrapper.wrap_url(original_url)

        assert result == original_url
        mock_domains.assert_not_called()


# ---------------------------------------------------------------------------
# TestAuth
# ---------------------------------------------------------------------------

class TestAuth:
    """Tests for OAuth2 token fetch and graceful failure."""

    @pytest.mark.asyncio
    async def test_token_fetch(self, wrapper):
        """_get_access_token POSTs to auth URL and returns the token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-token-123",
            "expiry_timestamp": 9999999999,
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.affiliate.skimlinks.httpx.AsyncClient", return_value=mock_client_instance):
            token = await wrapper._get_access_token()

        assert token == "test-token-123"

    @pytest.mark.asyncio
    async def test_token_failure_graceful(self, wrapper):
        """When auth returns non-200, _fetch_domains_from_api returns empty set."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.affiliate.skimlinks.httpx.AsyncClient", return_value=mock_client_instance):
            domains = await wrapper._fetch_domains_from_api()

        assert domains == set()


# ---------------------------------------------------------------------------
# TestProductAffiliateIntegration -- end-to-end wiring
# ---------------------------------------------------------------------------

from mcp_server.tools.product_affiliate import product_affiliate  # noqa: E402


class TestProductAffiliateIntegration:
    """Integration tests for Skimlinks post-processing in product_affiliate."""

    def _make_mock_result(self, url="https://www.bestbuy.com/site/product/12345", merchant="Best Buy", source="serper_shopping"):
        """Create a mock search result object."""
        mock_result = MagicMock()
        mock_result.merchant = merchant
        mock_result.price = 299.99
        mock_result.currency = "USD"
        mock_result.affiliate_link = url
        mock_result.condition = "new"
        mock_result.title = "Sony WH-1000XM5"
        mock_result.image_url = "https://example.com/image.jpg"
        mock_result.rating = 4.7
        mock_result.review_count = 500
        mock_result.product_id = "SKU12345"
        return mock_result

    @pytest.mark.asyncio
    async def test_serper_offers_wrapped(self):
        """When Skimlinks is enabled and serper_shopping returns bestbuy.com URLs, URLs are wrapped."""
        mock_result = self._make_mock_result(
            url="https://www.bestbuy.com/site/product/12345",
            source="serper_shopping"
        )
        mock_provider = MagicMock()
        mock_provider.search_products = AsyncMock(return_value=[mock_result])

        state = {
            "normalized_products": [{"title": "Sony WH-1000XM5"}],
            "session_id": "test-session-123",
            "user_message": "best headphones",
            "slots": {},
            "last_search_context": {},
        }

        with patch("app.services.affiliate.manager.affiliate_manager") as mock_manager, \
             patch("app.core.config.settings") as mock_settings, \
             patch("app.services.affiliate.skimlinks.skimlinks_wrapper") as mock_skimlinks:

            mock_settings.MAX_AFFILIATE_OFFERS_PER_PRODUCT = 3
            mock_settings.AMAZON_DEFAULT_COUNTRY = "US"
            mock_settings.USE_CURATED_LINKS = False
            mock_manager.get_available_providers.return_value = ["serper_shopping"]
            mock_manager.get_provider.return_value = mock_provider

            # Configure Skimlinks mock
            mock_skimlinks.enabled = True
            mock_skimlinks.wrap_url = AsyncMock(
                return_value="https://go.skimresources.com?id=12345X67890&xs=1&url=https%3A%2F%2Fwww.bestbuy.com%2Fsite%2Fproduct%2F12345"
            )

            result = await product_affiliate(state)

        assert result["success"] is True
        assert "serper_shopping" in result["affiliate_products"]
        offers = result["affiliate_products"]["serper_shopping"][0]["offers"]
        assert offers[0]["url"].startswith("https://go.skimresources.com")

    @pytest.mark.asyncio
    async def test_amazon_offers_not_wrapped(self):
        """When Skimlinks is enabled and amazon provider returns amazon.com URLs, those URLs remain unchanged."""
        state = {
            "normalized_products": [{"title": "Sony WH-1000XM5"}],
            "session_id": "test-session-123",
            "user_message": "best headphones",
            "slots": {},
            "last_search_context": {},
        }

        # Use curated links path for Amazon
        mock_curated = [{"url": "https://www.amazon.com/dp/B09XS7JWHH", "title": "Sony WH-1000XM5", "price": 298, "image_url": "https://example.com/img.jpg", "asin": "B09XS7JWHH"}]

        with patch("app.services.affiliate.manager.affiliate_manager") as mock_manager, \
             patch("app.core.config.settings") as mock_settings, \
             patch("app.services.affiliate.skimlinks.skimlinks_wrapper") as mock_skimlinks, \
             patch("app.services.affiliate.providers.curated_amazon_links.find_curated_links", return_value=mock_curated):

            mock_settings.MAX_AFFILIATE_OFFERS_PER_PRODUCT = 3
            mock_settings.AMAZON_DEFAULT_COUNTRY = "US"
            mock_settings.USE_CURATED_LINKS = False
            mock_manager.get_available_providers.return_value = ["amazon"]
            mock_manager.get_provider.return_value = None  # Force curated path

            mock_skimlinks.enabled = True
            mock_skimlinks.wrap_url = AsyncMock(side_effect=AssertionError("wrap_url should not be called for Amazon"))

            result = await product_affiliate(state)

        assert result["success"] is True
        # Amazon provider results should have original URL
        if "amazon" in result["affiliate_products"]:
            for group in result["affiliate_products"]["amazon"]:
                for offer in group.get("offers", []):
                    assert "go.skimresources.com" not in offer["url"]

    @pytest.mark.asyncio
    async def test_skimlinks_disabled_no_wrapping(self):
        """When SKIMLINKS_API_ENABLED=false, all URLs remain unchanged."""
        mock_result = self._make_mock_result(
            url="https://www.bestbuy.com/site/product/12345",
            source="serper_shopping"
        )
        mock_provider = MagicMock()
        mock_provider.search_products = AsyncMock(return_value=[mock_result])

        state = {
            "normalized_products": [{"title": "Sony WH-1000XM5"}],
            "session_id": "test-session-123",
            "user_message": "best headphones",
            "slots": {},
            "last_search_context": {},
        }

        with patch("app.services.affiliate.manager.affiliate_manager") as mock_manager, \
             patch("app.core.config.settings") as mock_settings, \
             patch("app.services.affiliate.skimlinks.skimlinks_wrapper") as mock_skimlinks:

            mock_settings.MAX_AFFILIATE_OFFERS_PER_PRODUCT = 3
            mock_settings.AMAZON_DEFAULT_COUNTRY = "US"
            mock_settings.USE_CURATED_LINKS = False
            mock_manager.get_available_providers.return_value = ["serper_shopping"]
            mock_manager.get_provider.return_value = mock_provider

            # Skimlinks DISABLED
            mock_skimlinks.enabled = False
            mock_skimlinks.wrap_url = AsyncMock(side_effect=AssertionError("wrap_url should not be called when disabled"))

            result = await product_affiliate(state)

        assert result["success"] is True
        # URL should be unchanged (the original bestbuy URL)
        offers = result["affiliate_products"]["serper_shopping"][0]["offers"]
        assert offers[0]["url"] == "https://www.bestbuy.com/site/product/12345"

    @pytest.mark.asyncio
    async def test_skimlinks_error_graceful(self):
        """When skimlinks_wrapper.wrap_url raises an exception, product_affiliate still returns successfully."""
        mock_result = self._make_mock_result(
            url="https://www.bestbuy.com/site/product/12345",
            source="serper_shopping"
        )
        mock_provider = MagicMock()
        mock_provider.search_products = AsyncMock(return_value=[mock_result])

        state = {
            "normalized_products": [{"title": "Sony WH-1000XM5"}],
            "session_id": "test-session-123",
            "user_message": "best headphones",
            "slots": {},
            "last_search_context": {},
        }

        with patch("app.services.affiliate.manager.affiliate_manager") as mock_manager, \
             patch("app.core.config.settings") as mock_settings, \
             patch("app.services.affiliate.skimlinks.skimlinks_wrapper") as mock_skimlinks:

            mock_settings.MAX_AFFILIATE_OFFERS_PER_PRODUCT = 3
            mock_settings.AMAZON_DEFAULT_COUNTRY = "US"
            mock_settings.USE_CURATED_LINKS = False
            mock_manager.get_available_providers.return_value = ["serper_shopping"]
            mock_manager.get_provider.return_value = mock_provider

            mock_skimlinks.enabled = True
            mock_skimlinks.wrap_url = AsyncMock(side_effect=Exception("Skimlinks API error"))

            result = await product_affiliate(state)

        # Function should still return successfully despite Skimlinks error
        assert result["success"] is True
        assert "serper_shopping" in result["affiliate_products"]
