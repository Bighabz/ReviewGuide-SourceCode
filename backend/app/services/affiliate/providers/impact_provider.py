"""
Impact.com Affiliate Catalog Provider
Integrates with Impact.com Catalog ItemSearch API for product search.
Uses HTTP Basic Auth, Redis caching, and Redis-based rate limiting.
"""
import hashlib
import json
import time
from typing import List, Optional

import httpx

from app.core.centralized_logger import get_logger
from app.core.config import settings
from app.core.redis_client import get_redis, redis_get_with_retry, redis_set_with_retry
from app.services.affiliate.base import BaseAffiliateProvider, AffiliateProduct
from app.services.affiliate.registry import AffiliateProviderRegistry

logger = get_logger(__name__)

IMPACT_API_BASE = "https://api.impact.com"


@AffiliateProviderRegistry.register(
    "impact",
    required_env_vars=["IMPACT_ACCOUNT_SID", "IMPACT_AUTH_TOKEN"],
)
class ImpactAffiliateProvider(BaseAffiliateProvider):
    """
    Impact.com Catalog Search Provider

    Features:
    - Product search via Catalogs/ItemSearch API
    - HTTP Basic Auth (AccountSID + AuthToken)
    - Redis caching for search results
    - Redis sliding-window rate limiting (3,000 req/hour)
    - Affiliate links provided directly by Impact.com (Url field)
    """

    def __init__(
        self,
        account_sid: str = None,
        auth_token: str = None,
        api_enabled: bool = None,
    ):
        self.account_sid = account_sid or settings.IMPACT_ACCOUNT_SID
        self.auth_token = auth_token or settings.IMPACT_AUTH_TOKEN
        self.timeout = settings.IMPACT_API_TIMEOUT
        self.cache_ttl = settings.IMPACT_CACHE_TTL
        self.max_results = settings.IMPACT_MAX_RESULTS
        self.max_requests_per_hour = settings.IMPACT_RATE_LIMIT_PER_HOUR
        self.api_enabled = api_enabled if api_enabled is not None else settings.IMPACT_API_ENABLED

        self.search_url = (
            f"{IMPACT_API_BASE}/Mediapartners/{self.account_sid}"
            f"/Catalogs/ItemSearch"
        )

        logger.info(
            f"Impact.com provider initialized: "
            f"api_enabled={self.api_enabled}, "
            f"account_sid={self.account_sid[:8] if len(self.account_sid) >= 8 else self.account_sid}..."
        )

    def get_provider_name(self) -> str:
        return "Impact.com"

    async def _check_rate_limit(self) -> bool:
        """Check if we're under the hourly API rate limit using Redis sorted set."""
        try:
            redis = await get_redis()
            key = "impact:api:rate_limit"
            now = int(time.time())
            window_start = now - 3600

            await redis.zremrangebyscore(key, 0, window_start)
            count = await redis.zcard(key)

            if count >= self.max_requests_per_hour:
                logger.warning(
                    f"Impact.com rate limit reached: {count}/{self.max_requests_per_hour} per hour"
                )
                return False

            await redis.zadd(key, {f"{now}:{id(self)}:{time.time_ns()}": now})
            await redis.expire(key, 3600)
            return True
        except Exception as e:
            logger.warning(f"Impact.com rate limit check failed (allowing request): {e}")
            return True  # Fail open

    def _build_cache_key(self, params: dict) -> str:
        """Build a deterministic Redis cache key from search params."""
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return f"impact:search:{param_hash}"

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
    ) -> List[AffiliateProduct]:
        """Search Impact.com catalog for products matching query."""
        if not self.api_enabled:
            logger.debug("Impact.com API disabled, returning empty results")
            return []

        # Build params
        params = {"Keyword": query, "PageSize": min(limit, self.max_results)}
        if brand:
            params["Manufacturer"] = brand

        # Check cache
        cache_key = self._build_cache_key(params)
        try:
            cached = await redis_get_with_retry(cache_key)
            if cached is not None:
                logger.info(f"Impact.com cache hit: {cache_key}")
                return [AffiliateProduct(**p) for p in json.loads(cached)]
        except Exception as e:
            logger.warning(f"Impact.com cache read failed: {e}")

        # Check rate limit
        if not await self._check_rate_limit():
            logger.warning("Impact.com rate limit reached, returning empty results")
            return []

        # Call API
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.search_url,
                    params=params,
                    auth=(self.account_sid, self.auth_token),
                    headers={"Accept": "application/json"},
                )

            if response.status_code == 429:
                logger.warning("Impact.com API returned 429 (rate limited)")
                return []

            if response.status_code != 200:
                logger.error(
                    f"Impact.com API error: {response.status_code} - "
                    f"{response.text[:200]}"
                )
                return []

            products = self._parse_response(response.json())

            # Cache results
            try:
                products_json = json.dumps([
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
                ])
                await redis_set_with_retry(cache_key, products_json, ex=self.cache_ttl)
            except Exception as e:
                logger.warning(f"Impact.com cache write failed: {e}")

            return products

        except httpx.TimeoutException:
            logger.error("Impact.com API request timed out")
            return []
        except Exception as e:
            logger.error(f"Impact.com search error: {e}", exc_info=True)
            return []

    def _parse_response(self, data: dict) -> List[AffiliateProduct]:
        """Parse Impact.com ItemSearch JSON response."""
        products = []
        items = data.get("Items", [])

        for item in items:
            try:
                # Url field contains the pre-built affiliate tracking link
                affiliate_url = item.get("Url", "")
                current_price = item.get("CurrentPrice", 0)
                # Price may be integer (cents) or float -- handle both
                price = float(current_price) if current_price else 0.0

                stock = item.get("StockAvailability", "")
                availability = stock in (
                    "InStock", "PreOrder", "LimitedAvailability", "BackOrder"
                )

                condition_map = {
                    "New": "new",
                    "Used": "used",
                    "Refurbished": "refurbished",
                    "OEM": "new",
                    "OpenBox": "used",
                }
                condition = condition_map.get(item.get("Condition", "New"), "new")

                shipping_rate = item.get("ShippingRate")
                shipping_cost = float(shipping_rate) if shipping_rate is not None else None

                products.append(AffiliateProduct(
                    product_id=str(item.get("CatalogItemId", "")),
                    title=item.get("Name", ""),
                    price=price,
                    currency=item.get("Currency", "USD"),
                    affiliate_link=affiliate_url,
                    merchant=item.get("CampaignName", "Impact.com"),
                    image_url=item.get("ImageUrl"),
                    rating=None,  # Impact.com does not provide ratings
                    review_count=None,
                    condition=condition,
                    shipping_cost=shipping_cost,
                    availability=availability,
                    source_url=affiliate_url,
                ))
            except Exception as e:
                logger.warning(f"Failed to parse Impact.com item: {e}")
                continue

        return products

    async def generate_affiliate_link(
        self,
        product_id: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> str:
        """Impact.com URLs are pre-tracked in the Url field. Return empty string."""
        return ""

    async def check_link_health(self, affiliate_link: str) -> bool:
        """Check if an Impact.com affiliate link is valid."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(affiliate_link, follow_redirects=False)
            return response.status_code in (200, 301, 302)
        except Exception as e:
            logger.warning(f"Impact.com link health check failed: {e}")
            return False


__all__ = ["ImpactAffiliateProvider"]
