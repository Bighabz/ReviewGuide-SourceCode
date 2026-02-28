"""
CJ Affiliate (Commission Junction) Provider
Integrates with CJ Product Search API for product search and affiliate link generation.
Uses XML-based API with Bearer token auth and Redis caching.
"""
import hashlib
import json
import xml.etree.ElementTree as ET
from typing import List, Optional
from urllib.parse import urlencode

import httpx

from app.core.centralized_logger import get_logger
from app.core.config import settings
from app.core.redis_client import redis_get_with_retry, redis_set_with_retry
from app.services.affiliate.base import BaseAffiliateProvider, AffiliateProduct
from app.services.affiliate.registry import AffiliateProviderRegistry

logger = get_logger(__name__)

CJ_API_ENDPOINT = "https://product-search.api.cj.com/v2/product-search"


@AffiliateProviderRegistry.register(
    "cj",
    required_env_vars=["CJ_API_KEY", "CJ_WEBSITE_ID"],
)
class CJAffiliateProvider(BaseAffiliateProvider):
    """
    CJ Affiliate (Commission Junction) Provider

    Features:
    - Product search via CJ Product Search API (XML)
    - Redis caching for search results
    - Affiliate links provided directly by CJ (buy-url)
    - Link health monitoring via HEAD requests
    """

    def __init__(
        self,
        api_key: str = None,
        website_id: str = None,
    ):
        """
        Initialize CJ affiliate provider.

        Args:
            api_key: CJ personal access token (Bearer token). Falls back to settings.
            website_id: CJ publisher website ID (PID). Falls back to settings.
        """
        self.api_key = api_key or settings.CJ_API_KEY
        self.website_id = website_id or settings.CJ_WEBSITE_ID
        self.advertiser_ids = settings.CJ_ADVERTISER_IDS or "joined"
        self.timeout = settings.CJ_API_TIMEOUT
        self.cache_ttl = settings.CJ_CACHE_TTL
        self.max_results = settings.CJ_MAX_RESULTS

        logger.info(
            f"CJ provider initialized: "
            f"website_id={self.website_id}, "
            f"advertiser_ids={self.advertiser_ids}"
        )

    def get_provider_name(self) -> str:
        """Return provider name"""
        return "CJ"

    def _build_cache_key(self, params: dict) -> str:
        """Build a deterministic Redis cache key from search parameters."""
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return f"cj:search:{param_hash}"

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
    ) -> List[AffiliateProduct]:
        """
        Search for products via CJ Product Search API.

        Checks Redis cache first. On cache miss, calls the CJ API,
        parses the XML response, and caches the result.

        Args:
            query: Search query string
            category: Optional category filter (unused by CJ API)
            brand: Optional brand filter (unused by CJ API)
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Maximum number of results

        Returns:
            List of AffiliateProduct objects
        """
        # Build API params
        params = {
            "website-id": self.website_id,
            "keywords": query,
            "advertiser-ids": self.advertiser_ids,
            "records-per-page": min(limit, self.max_results),
        }
        if min_price is not None:
            params["low-price"] = str(min_price)
        if max_price is not None:
            params["high-price"] = str(max_price)

        # Check Redis cache
        cache_key = self._build_cache_key(params)
        try:
            cached = await redis_get_with_retry(cache_key)
            if cached is not None:
                logger.info(f"CJ cache hit for key {cache_key}")
                products_data = json.loads(cached)
                return [AffiliateProduct(**p) for p in products_data]
        except Exception as e:
            logger.warning(f"CJ cache read failed: {e}")

        # Call CJ API
        logger.info(f"CJ API search: query='{query}', limit={limit}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    CJ_API_ENDPOINT,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                    },
                )

            if response.status_code != 200:
                logger.error(
                    f"CJ API error: {response.status_code} - {response.text[:200]}"
                )
                return []

            products = self._parse_xml_response(response.text)
            logger.info(f"CJ API returned {len(products)} products for '{query}'")

        except httpx.TimeoutException:
            logger.error("CJ API request timed out")
            return []
        except Exception as e:
            logger.error(f"CJ API request failed: {e}", exc_info=True)
            return []

        # Cache results (including empty lists to avoid repeated failed lookups)
        try:
            products_json = json.dumps(
                [
                    {
                        "product_id": p.product_id,
                        "title": p.title,
                        "price": p.price,
                        "currency": p.currency,
                        "affiliate_link": p.affiliate_link,
                        "merchant": p.merchant,
                        "image_url": p.image_url,
                        "rating": p.rating,
                        "review_count": p.review_count,
                        "condition": p.condition,
                        "shipping_cost": p.shipping_cost,
                        "availability": p.availability,
                        "source_url": p.source_url,
                    }
                    for p in products
                ]
            )
            await redis_set_with_retry(cache_key, products_json, ex=self.cache_ttl)
            logger.debug(f"CJ results cached: key={cache_key}, ttl={self.cache_ttl}")
        except Exception as e:
            logger.warning(f"CJ cache write failed: {e}")

        return products

    def _parse_xml_response(self, xml_text: str) -> List[AffiliateProduct]:
        """
        Parse CJ Product Search API XML response into AffiliateProduct list.

        Prefers sale-price over regular price when sale-price is non-empty.

        Args:
            xml_text: Raw XML response body

        Returns:
            List of AffiliateProduct objects
        """
        products = []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"CJ XML parse error: {e}")
            return []

        # Find all <product> elements under <products>
        products_elem = root.find("products")
        if products_elem is None:
            logger.warning("CJ XML: no <products> element found")
            return []

        for product_elem in products_elem.findall("product"):
            try:
                # Extract fields with safe defaults
                ad_id = self._xml_text(product_elem, "ad-id", "")
                name = self._xml_text(product_elem, "name", "Unknown Product")
                regular_price = self._xml_text(product_elem, "price", "0")
                sale_price = self._xml_text(product_elem, "sale-price", "")
                currency = self._xml_text(product_elem, "currency", "USD")
                buy_url = self._xml_text(product_elem, "buy-url", "")
                image_url = self._xml_text(product_elem, "image-url", "")
                advertiser_name = self._xml_text(product_elem, "advertiser-name", "CJ")
                sku = self._xml_text(product_elem, "sku", "")
                in_stock = self._xml_text(product_elem, "in-stock", "true")
                manufacturer = self._xml_text(product_elem, "manufacturer-name", "")

                # Prefer sale-price when non-empty
                price_str = sale_price if sale_price.strip() else regular_price
                try:
                    price = float(price_str)
                except (ValueError, TypeError):
                    price = 0.0

                # Build product ID from ad-id and sku
                product_id = f"cj-{ad_id}" if ad_id else f"cj-{sku}"

                products.append(
                    AffiliateProduct(
                        product_id=product_id,
                        title=name,
                        price=price,
                        currency=currency,
                        affiliate_link=buy_url,
                        merchant=advertiser_name,
                        image_url=image_url if image_url else None,
                        rating=None,  # CJ API does not provide ratings
                        review_count=None,
                        condition="new",
                        shipping_cost=None,
                        availability=in_stock.lower() == "true",
                        source_url=buy_url,
                    )
                )

            except Exception as e:
                logger.warning(f"Failed to parse CJ product element: {e}")
                continue

        return products

    @staticmethod
    def _xml_text(parent: ET.Element, tag: str, default: str = "") -> str:
        """Safely extract text from an XML element."""
        elem = parent.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
        return default

    async def generate_affiliate_link(
        self,
        product_id: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> str:
        """
        Generate CJ affiliate link for a product.

        CJ buy-urls from the Product Search API are already complete affiliate links.
        This method constructs a deep-link URL using CJ's format.

        Args:
            product_id: CJ product/ad ID
            campaign_id: Optional campaign identifier
            tracking_id: Optional custom tracking identifier (e.g., session_id)

        Returns:
            CJ affiliate tracking URL
        """
        # Construct a CJ deep link
        params = {
            "pid": self.website_id,
            "advid": product_id,
        }
        if tracking_id:
            params["sid"] = tracking_id

        base = "https://www.anrdoezrs.net/links"
        url = f"{base}/{self.website_id}?{urlencode(params)}"

        logger.debug(f"Generated CJ affiliate link: {url}")
        return url

    async def check_link_health(self, affiliate_link: str) -> bool:
        """
        Check if a CJ affiliate link is still valid.

        Makes a HEAD request with a 5-second timeout.
        Accepts 200, 301, and 302 as healthy status codes (CJ links redirect).

        Args:
            affiliate_link: The CJ affiliate URL to check

        Returns:
            True if link is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(
                    affiliate_link,
                    follow_redirects=False,
                )
            is_healthy = response.status_code in (200, 301, 302)
            logger.debug(
                f"CJ link health check: {affiliate_link[:60]}... "
                f"status={response.status_code} healthy={is_healthy}"
            )
            return is_healthy

        except Exception as e:
            logger.warning(f"CJ link health check failed: {e}")
            return False


# Export
__all__ = ["CJAffiliateProvider"]
