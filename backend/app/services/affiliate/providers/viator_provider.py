"""
Viator Activity Provider
Integrates with Viator Partner API v2 for activity/tour search and affiliate link generation.
Uses JSON-based API with exp-api-key header auth and Redis caching.
Falls back to PLP search URLs when API is unavailable.
"""
import hashlib
import json
from typing import List, Optional

import httpx

from app.core.centralized_logger import get_logger
from app.core.config import settings
from app.core.redis_client import redis_get_with_retry, redis_set_with_retry
from app.services.affiliate.base import BaseAffiliateProvider, AffiliateProduct
from app.services.affiliate.registry import AffiliateProviderRegistry
from app.services.travel.providers.viator_plp_provider import ViatorPLPLinkGenerator

logger = get_logger(__name__)

VIATOR_API_BASE = "https://api.viator.com/partner"


@AffiliateProviderRegistry.register(
    "viator",
    required_env_vars=["VIATOR_API_KEY"],
    optional_env_vars=["VIATOR_AFFILIATE_ID"],
)
class ViatorActivityProvider(BaseAffiliateProvider):
    """
    Viator Partner API v2 Activity Provider

    Features:
    - Activity search via /search/freetext (POST, JSON)
    - Redis caching for search results (8-hour TTL)
    - Affiliate links with PID tracking
    - PLP fallback when API is unavailable
    - Link health monitoring via HEAD requests
    """

    def __init__(
        self,
        api_key: str = None,
        affiliate_id: str = None,
    ):
        """
        Initialize Viator activity provider.

        Args:
            api_key: Viator Partner API key (exp-api-key header). Falls back to settings.
            affiliate_id: Viator affiliate ID (PID). Falls back to settings.
        """
        self.api_key = api_key or settings.VIATOR_API_KEY
        self.affiliate_id = affiliate_id or settings.VIATOR_AFFILIATE_ID
        self.timeout = settings.VIATOR_API_TIMEOUT
        self.cache_ttl = settings.VIATOR_CACHE_TTL
        self.max_results = settings.VIATOR_MAX_RESULTS

        logger.info(
            f"Viator provider initialized: "
            f"affiliate_id={self.affiliate_id}"
        )

    def get_provider_name(self) -> str:
        """Return provider name"""
        return "Viator"

    def _build_cache_key(self, params: dict) -> str:
        """Build a deterministic Redis cache key from search parameters."""
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return f"viator:search:{param_hash}"

    def _build_affiliate_link(self, product_url: str) -> str:
        """Append affiliate tracking params to a Viator product URL."""
        if not product_url:
            return ""
        separator = "&" if "?" in product_url else "?"
        return f"{product_url}{separator}pid={self.affiliate_id}&mcid=42383&medium=api"

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
        Search for activities via Viator Partner API /search/freetext.

        Checks Redis cache first. On cache miss, calls the Viator API,
        parses the JSON response, and caches the result.
        On any exception, falls back to PLP search URL.

        Args:
            query: Search query string (e.g., "Paris tours")
            category: Optional category filter (unused by Viator API)
            brand: Optional brand filter (unused by Viator API)
            min_price: Minimum price filter (unused by Viator API)
            max_price: Maximum price filter (unused by Viator API)
            limit: Maximum number of results

        Returns:
            List of AffiliateProduct objects
        """
        # Build search params for cache key
        search_params = {
            "query": query,
            "limit": min(limit, self.max_results),
        }

        # Check Redis cache
        cache_key = self._build_cache_key(search_params)
        try:
            cached = await redis_get_with_retry(cache_key)
            if cached is not None:
                logger.info(f"Viator cache hit for key {cache_key}")
                products_data = json.loads(cached)
                return [AffiliateProduct(**p) for p in products_data]
        except Exception as e:
            logger.warning(f"Viator cache read failed: {e}")

        # Call Viator API
        logger.info(f"Viator API search: query='{query}', limit={limit}")
        try:
            headers = {
                "exp-api-key": self.api_key,
                "Accept-Language": "en-US",
                "Accept": "application/json;version=2.0",
                "Content-Type": "application/json",
            }
            body = {
                "searchTerm": query,
                "searchTypes": [
                    {
                        "searchType": "PRODUCTS",
                        "pagination": {
                            "start": 1,
                            "count": min(limit, self.max_results),
                        },
                    }
                ],
                "currency": "USD",
                "productSorting": {
                    "sort": "DEFAULT",
                    "order": "DESCENDING",
                },
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{VIATOR_API_BASE}/search/freetext",
                    headers=headers,
                    json=body,
                )

            if response.status_code != 200:
                logger.error(
                    f"Viator API error: {response.status_code} - {response.text[:200]}"
                )
                return []

            data = response.json()
            products = self._parse_api_response(data)
            logger.info(f"Viator API returned {len(products)} activities for '{query}'")

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.error(f"Viator API connection error: {e}")
            # Fall back to PLP search URL
            fallback_url = ViatorPLPLinkGenerator.generate_activity_search_url(query)
            return [
                AffiliateProduct(
                    product_id="viator-plp-fallback",
                    title=f"Activities in {query}",
                    price=0.0,
                    currency="USD",
                    affiliate_link=fallback_url,
                    merchant="Viator",
                    image_url=None,
                    source_url=fallback_url,
                )
            ]
        except Exception as e:
            logger.error(f"Viator API request failed: {e}", exc_info=True)
            # Fall back to PLP search URL
            fallback_url = ViatorPLPLinkGenerator.generate_activity_search_url(query)
            return [
                AffiliateProduct(
                    product_id="viator-plp-fallback",
                    title=f"Activities in {query}",
                    price=0.0,
                    currency="USD",
                    affiliate_link=fallback_url,
                    merchant="Viator",
                    image_url=None,
                    source_url=fallback_url,
                )
            ]

        # Cache results
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
            logger.debug(f"Viator results cached: key={cache_key}, ttl={self.cache_ttl}")
        except Exception as e:
            logger.warning(f"Viator cache write failed: {e}")

        return products

    def _parse_api_response(self, data: dict) -> List[AffiliateProduct]:
        """
        Parse Viator /search/freetext JSON response into AffiliateProduct list.

        Args:
            data: Raw JSON response dict

        Returns:
            List of AffiliateProduct objects
        """
        products = []

        try:
            results = data.get("products", {}).get("results", [])
        except (AttributeError, TypeError):
            logger.warning("Viator response: no products.results found")
            return []

        for product in results:
            try:
                product_code = product.get("productCode", "")
                title = product.get("title", "Unknown Activity")
                price = product.get("pricing", {}).get("summary", {}).get("fromPrice", 0.0)
                currency = product.get("currency", "USD")
                product_url = product.get("productUrl", "")
                thumbnail_url = product.get("thumbnailUrl", "")
                rating = product.get("rating", None)
                review_count = product.get("reviewCount", None)

                # Build affiliate link from product URL
                affiliate_link = self._build_affiliate_link(product_url)

                products.append(
                    AffiliateProduct(
                        product_id=f"viator-{product_code}",
                        title=title,
                        price=float(price) if price else 0.0,
                        currency=currency,
                        affiliate_link=affiliate_link,
                        merchant="Viator",
                        image_url=thumbnail_url if thumbnail_url else None,
                        rating=float(rating) if rating is not None else None,
                        review_count=int(review_count) if review_count is not None else None,
                        condition="new",
                        shipping_cost=None,
                        availability=True,
                        source_url=product_url,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse Viator product: {e}")
                continue

        return products

    async def generate_affiliate_link(
        self,
        product_id: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> str:
        """
        Generate Viator affiliate deep link for a product.

        Args:
            product_id: Viator product code
            campaign_id: Optional campaign identifier
            tracking_id: Optional custom tracking identifier

        Returns:
            Viator affiliate tracking URL
        """
        url = f"https://www.viator.com/tours/{product_id}?pid={self.affiliate_id}&mcid=42383&medium=api"
        if tracking_id:
            url += f"&sid={tracking_id}"
        logger.debug(f"Generated Viator affiliate link: {url}")
        return url

    async def check_link_health(self, affiliate_link: str) -> bool:
        """
        Check if a Viator affiliate link is still valid.

        Makes a HEAD request with a 5-second timeout.
        Accepts 200, 301, and 302 as healthy status codes.

        Args:
            affiliate_link: The Viator affiliate URL to check

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
                f"Viator link health check: {affiliate_link[:60]}... "
                f"status={response.status_code} healthy={is_healthy}"
            )
            return is_healthy
        except Exception as e:
            logger.warning(f"Viator link health check failed: {e}")
            return False


# Export
__all__ = ["ViatorActivityProvider"]
