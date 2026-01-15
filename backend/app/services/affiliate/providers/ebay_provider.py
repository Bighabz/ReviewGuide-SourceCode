"""
eBay Affiliate Network Provider
Integrates with eBay Partner Network API for product search and affiliate link generation
"""
from app.core.centralized_logger import get_logger
import httpx
import base64
import hashlib
from typing import List, Dict, Any, Optional
from urllib.parse import quote, urlencode
from app.services.affiliate.base import BaseAffiliateProvider, AffiliateProduct
from app.core.config import settings

logger = get_logger(__name__)


# eBay marketplace IDs by country code
EBAY_MARKETPLACES: Dict[str, str] = {
    "US": "EBAY_US",
    "GB": "EBAY_GB",
    "UK": "EBAY_GB",
    "DE": "EBAY_DE",
    "FR": "EBAY_FR",
    "IT": "EBAY_IT",
    "ES": "EBAY_ES",
    "AU": "EBAY_AU",
    "CA": "EBAY_CA",
    "IE": "EBAY_IE",
    "NL": "EBAY_NL",
    "BE": "EBAY_BE",
    "AT": "EBAY_AT",
    "CH": "EBAY_CH",
    "PL": "EBAY_PL",
    "IN": "EBAY_IN",
    "SG": "EBAY_SG",
    "HK": "EBAY_HK",
    "MY": "EBAY_MY",
    "PH": "EBAY_PH",
}

# eBay domain URLs by country code (for affiliate links)
EBAY_DOMAINS: Dict[str, str] = {
    "US": "ebay.com",
    "GB": "ebay.co.uk",
    "UK": "ebay.co.uk",
    "DE": "ebay.de",
    "FR": "ebay.fr",
    "IT": "ebay.it",
    "ES": "ebay.es",
    "AU": "ebay.com.au",
    "CA": "ebay.ca",
    "IE": "ebay.ie",
    "NL": "ebay.nl",
    "BE": "ebay.be",
    "AT": "ebay.at",
    "CH": "ebay.ch",
    "PL": "ebay.pl",
    "IN": "ebay.in",
    "SG": "ebay.com.sg",
    "HK": "ebay.com.hk",
    "MY": "ebay.com.my",
    "PH": "ebay.ph",
}


class EbayAffiliateProvider(BaseAffiliateProvider):
    """
    eBay Partner Network (EPN) Integration

    Features:
    - OAuth token generation from App ID + Cert ID
    - Product search via eBay Browse API
    - Affiliate link generation with campaign tracking
    - Link health monitoring
    - Category-based filtering
    - Price range filtering
    """

    def __init__(
        self,
        app_id: str = None,
        cert_id: str = None,
        campaign_id: str = None,
        custom_id: str = None,
        timeout: int = 10,
    ):
        """
        Initialize eBay affiliate provider

        Args:
            app_id: eBay Application ID
            cert_id: eBay Cert ID (Client Secret)
            campaign_id: eBay Partner Network Campaign ID
            custom_id: Custom tracking ID for additional tracking
            timeout: Request timeout in seconds
        """
        self.app_id = app_id or settings.EBAY_APP_ID
        self.cert_id = cert_id or settings.EBAY_CERT_ID
        self.campaign_id = campaign_id or settings.EBAY_CAMPAIGN_ID
        self.custom_id = custom_id or settings.EBAY_AFFILIATE_CUSTOM_ID
        self.timeout = timeout
        self.oauth_token = None  # Will be generated on demand

        # eBay API endpoints
        self.base_url = "https://api.ebay.com"
        self.oauth_url = f"{self.base_url}/identity/v1/oauth2/token"
        self.browse_api = f"{self.base_url}/buy/browse/v1"

        # Client for HTTP requests
        self.client = httpx.AsyncClient(timeout=self.timeout)

        if not all([self.app_id, self.cert_id]):
            logger.warning(
                "eBay credentials not fully configured. "
                "Set EBAY_APP_ID and EBAY_CERT_ID in environment."
            )

        if not self.campaign_id:
            logger.warning(
                "eBay Campaign ID not configured. "
                "Affiliate tracking will not be active. "
                "Set EBAY_CAMPAIGN_ID in environment."
            )

    def get_provider_name(self) -> str:
        """Return provider name"""
        return "eBay"

    async def _get_oauth_token(self) -> str:
        """
        Generate OAuth token from App ID and Cert ID

        Uses client_credentials flow with Basic Auth
        Token is valid for ~2 hours (7200 seconds)

        Returns:
            OAuth access token
        """
        if self.oauth_token:
            # TODO: Add token expiry check in production
            return self.oauth_token

        try:
            # Create Basic Auth header: base64(app_id:cert_id)
            credentials = f"{self.app_id}:{self.cert_id}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded_credentials}"
            }

            data = {
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            }

            logger.debug("Requesting eBay OAuth token")
            response = await self.client.post(
                self.oauth_url,
                headers=headers,
                data=data
            )

            if response.status_code != 200:
                logger.error(f"eBay OAuth error: {response.status_code} - {response.text}")
                raise Exception(f"Failed to get eBay OAuth token: {response.status_code}")

            token_data = response.json()
            self.oauth_token = token_data["access_token"]
            logger.info("Successfully obtained eBay OAuth token")
            return self.oauth_token

        except Exception as e:
            logger.error(f"Failed to get eBay OAuth token: {str(e)}", exc_info=True)
            raise

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
        country_code: Optional[str] = None,
    ) -> List[AffiliateProduct]:
        """
        Search for products on eBay

        Uses eBay Browse API to search for products with filters

        Args:
            query: Search query
            category: Optional category filter
            brand: Optional brand filter
            min_price: Minimum price
            max_price: Maximum price
            limit: Maximum results
            country_code: ISO country code for regional eBay marketplace (e.g., "US", "GB", "DE")
        """
        # Determine marketplace based on country code
        effective_country = (country_code or settings.AMAZON_DEFAULT_COUNTRY).upper()
        marketplace_id = EBAY_MARKETPLACES.get(effective_country, "EBAY_US")

        logger.info("=" * 80)
        logger.info("EBAY SEARCH - INPUT PARAMETERS:")
        logger.info(f"  Query: '{query}'")
        logger.info(f"  Category: {category}")
        logger.info(f"  Brand: {brand}")
        logger.info(f"  Min Price: ${min_price}")
        logger.info(f"  Max Price: ${max_price}")
        logger.info(f"  Limit: {limit}")
        logger.info(f"  Country: {effective_country}")
        logger.info(f"  Marketplace ID: {marketplace_id}")

        try:
            # Get OAuth token
            token = await self._get_oauth_token()

            # Build search query with filters
            search_query = self._build_search_query(
                query, category, brand, min_price, max_price
            )

            # Build filters
            filters = self._build_filters(category, min_price, max_price)

            logger.info(f"  Final Search Query: '{search_query}'")
            logger.info(f"  Final Filters: '{filters}'")

            # Make API request
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": marketplace_id,  # Dynamic marketplace based on country
            }

            params = {
                "q": search_query,
                "limit": min(limit, settings.EBAY_MAX_RESULTS),  # Use configured max results
                "filter": filters,
            }

            url = f"{self.browse_api}/item_summary/search"
            logger.info(f"  eBay API URL: {url}")
            logger.info(f"  Request params: {params}")
            response = await self.client.get(url, headers=headers, params=params)

            if response.status_code != 200:
                logger.error(
                    f"eBay API error: {response.status_code} - {response.text}"
                )
                return []

            data = response.json()
            items = data.get("itemSummaries", [])

            logger.info(f"EBAY SEARCH - API RESPONSE:")
            logger.info(f"  Status Code: {response.status_code}")
            logger.info(f"  Total Results: {len(items)}")

            # Log first 3 items for debugging
            for idx, item in enumerate(items[:3], 1):
                logger.info(f"  Result #{idx}:")
                logger.info(f"    Title: {item.get('title', 'N/A')}")
                logger.info(f"    Item ID: {item.get('itemId', 'N/A')}")
                logger.info(f"    Price: {item.get('price', {}).get('value', 'N/A')} {item.get('price', {}).get('currency', '')}")
                logger.info(f"    Image: {item.get('image')}")
                logger.info(f"    ThumbnailImages: {item.get('thumbnailImages')}")

            if len(items) > 3:
                logger.info(f"  ... and {len(items) - 3} more results")
            logger.info("=" * 80)

            # Convert to AffiliateProduct objects
            products = []
            for item in items:
                try:
                    product = self._parse_ebay_item(item, country_code=effective_country)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to parse eBay item: {e}")
                    continue

            logger.info(f"eBay: Successfully parsed {len(products)} products")
            return products

        except httpx.TimeoutException:
            logger.error("eBay API request timeout")
            return []
        except Exception as e:
            logger.error(f"eBay search error: {e}", exc_info=True)
            return []

    def _build_search_query(
        self,
        query: str,
        category: Optional[str],
        brand: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
    ) -> str:
        """Build eBay search query with filters"""
        # Use the full query as-is (should be the full product title from Perplexity)
        # Don't manipulate or add category/negative keywords - let the full title do the work
        if query:
            return query

        # Fallback: if no query, use category
        if category:
            return category

        return ""

    def _build_filters(
        self,
        category: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
    ) -> str:
        """Build eBay filter string"""
        filters = []

        # Price filters
        if min_price is not None:
            filters.append(f"price:[{min_price}..],priceCurrency:USD")
        if max_price is not None:
            filters.append(f"price:[..{max_price}],priceCurrency:USD")

        # Only new items
        filters.append("conditions:{NEW}")

        # Only buy-it-now (not auctions)
        filters.append("buyingOptions:{FIXED_PRICE}")

        # Removed hardcoded category ID filter - let the full product title handle specificity

        return "|".join(filters) if filters else ""

    def _parse_ebay_item(self, item: Dict[str, Any], country_code: str = "US") -> Optional[AffiliateProduct]:
        """Parse eBay item into AffiliateProduct"""
        try:
            item_id = item.get("itemId")
            title = item.get("title", "")

            # Price
            price_obj = item.get("price", {})
            price = float(price_obj.get("value", 0))
            currency = price_obj.get("currency", "USD")

            # Image - try multiple fields
            image_url = None
            if item.get("image") and item["image"].get("imageUrl"):
                image_url = item["image"]["imageUrl"]
            elif item.get("thumbnailImages") and len(item["thumbnailImages"]) > 0:
                image_url = item["thumbnailImages"][0].get("imageUrl")
            elif item.get("additionalImages") and len(item["additionalImages"]) > 0:
                image_url = item["additionalImages"][0].get("imageUrl")

            # Log if no image found for debugging
            if not image_url:
                logger.warning(f"No image URL found for item {item_id} - '{title[:50]}...'")

            # Generate affiliate link with EPN tracking (country-specific)
            affiliate_link = self._generate_affiliate_url(item_id, country_code=country_code)

            # Fallback to itemWebUrl if item_id parsing failed
            if not affiliate_link:
                affiliate_link = item.get("itemWebUrl", "")

            # Additional details
            condition = item.get("condition", "New")
            seller = item.get("seller", {}).get("username", "eBay")

            # Shipping
            shipping_cost = None
            shipping_options = item.get("shippingOptions", [])
            if shipping_options and shipping_options[0].get("shippingCost"):
                shipping_obj = shipping_options[0]["shippingCost"]
                shipping_cost = float(shipping_obj.get("value", 0))

            # Source URL (same as affiliate_link in this case)
            source_url = affiliate_link

            return AffiliateProduct(
                product_id=item_id,
                title=title,
                price=price,
                currency=currency,
                affiliate_link=affiliate_link,
                merchant=f"eBay ({seller})",
                image_url=image_url,
                rating=None,  # eBay doesn't provide ratings in Browse API
                review_count=None,
                condition=condition,
                shipping_cost=shipping_cost,
                availability=True,
                source_url=source_url,
            )

        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to parse eBay item: {e}")
            return None

    def _generate_affiliate_url(self, product_id: str, custom_id: str = None, country_code: str = "US") -> str:
        """
        Generate eBay affiliate link with EPN tracking parameters

        Args:
            product_id: eBay item ID (may be in format "v1|legacyId|...")
            custom_id: Optional custom tracking ID (overrides instance custom_id)
            country_code: ISO country code for regional eBay domain

        Returns:
            eBay product URL with affiliate tracking parameters
        """
        # Extract legacy item ID from Browse API format
        legacy_item_id = product_id
        if "|" in product_id:
            parts = product_id.split("|")
            if len(parts) >= 2:
                legacy_item_id = parts[1]

        # Get country-specific domain
        domain = EBAY_DOMAINS.get(country_code.upper(), "ebay.com")

        # Build base URL
        base_url = f"https://www.{domain}/itm/{legacy_item_id}"

        # Add EPN tracking parameters if campaign ID is configured
        logger.debug(f"Generating affiliate URL - campaign_id: {self.campaign_id}")
        if self.campaign_id:
            # EPN tracking parameters per https://developer.ebay.com/api-docs/buy/static/ref-epn-link.html
            params = {
                "mkcid": settings.EBAY_MKCID,       # Channel ID (1=EPN)
                "mkrid": settings.EBAY_MKRID,       # Rotation ID (marketplace)
                "campid": self.campaign_id,         # Campaign ID
                "toolid": settings.EBAY_TOOLID,     # Tool ID (10001=default)
                "mkevt": settings.EBAY_MKEVT        # Event type (1=Click)
            }

            # Add custom tracking ID if provided
            tracking_custom_id = custom_id or self.custom_id
            if tracking_custom_id:
                params["customid"] = tracking_custom_id

            # Build query string
            query_string = urlencode(params)
            affiliate_url = f"{base_url}?{query_string}"
            logger.info(f"Generated eBay affiliate link: {affiliate_url}")
            return affiliate_url

        # Return direct link if no campaign ID configured
        logger.warning(f"No campaign ID configured, returning direct link: {base_url}")
        return base_url

    async def generate_affiliate_link(
        self,
        product_id: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> str:
        """
        Generate eBay product link with affiliate tracking

        Args:
            product_id: eBay item ID (may be in format "v1|legacyId|...")
            campaign_id: Optional override for campaign ID (not used, set via env)
            tracking_id: Optional custom tracking ID for this specific link

        Returns:
            eBay affiliate link with tracking parameters
        """
        return self._generate_affiliate_url(product_id, custom_id=tracking_id)

    async def check_link_health(self, affiliate_link: str) -> bool:
        """
        Check if an eBay affiliate link is still valid

        Makes a HEAD request to check if the link returns 200
        """
        try:
            response = await self.client.head(
                affiliate_link,
                follow_redirects=True,
                timeout=5,
            )
            is_healthy = response.status_code == 200
            logger.debug(
                f"eBay link health check: {affiliate_link[:50]}... = {is_healthy}"
            )
            return is_healthy

        except Exception as e:
            logger.warning(f"eBay link health check failed: {e}")
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Export
__all__ = ["EbayAffiliateProvider"]
