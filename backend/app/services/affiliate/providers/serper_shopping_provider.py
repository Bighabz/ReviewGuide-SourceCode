"""
Serper Shopping Provider
Google Shopping results via Serper.dev — multi-retailer products with images.
Reuses SERPAPI_API_KEY. No new credentials required.
"""
import dataclasses
import hashlib
import json
from typing import List, Optional

import httpx

from app.core.centralized_logger import get_logger
from app.core.config import settings
from app.core.redis_client import redis_get_with_retry, redis_set_with_retry
from app.services.affiliate.base import BaseAffiliateProvider, AffiliateProduct
from app.services.affiliate.registry import AffiliateProviderRegistry

logger = get_logger(__name__)

SERPER_SHOPPING_URL = "https://google.serper.dev/shopping"
CACHE_TTL = 3600  # 1 hour


def _parse_price(price_str: str) -> float:
    """Parse formatted price string like '$1,299.99' to float."""
    try:
        return float(price_str.replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0


@AffiliateProviderRegistry.register(
    "serper_shopping",
    required_env_vars=["SERPAPI_API_KEY"],
)
class SerperShoppingProvider(BaseAffiliateProvider):
    """
    Google Shopping results via Serper.dev.

    Returns multi-retailer products with product images, prices, and merchant names.
    Uses SERPAPI_API_KEY (same key as review_search). Results cached in Redis for 1 hour.
    """

    def get_provider_name(self) -> str:
        return "Serper Shopping"

    def _build_cache_key(self, params: dict) -> str:
        param_str = json.dumps(params, sort_keys=True)
        return f"serper_shopping:{hashlib.md5(param_str.encode()).hexdigest()[:12]}"

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
    ) -> List[AffiliateProduct]:
        if not settings.SERPAPI_API_KEY:
            logger.warning("SerperShoppingProvider: SERPAPI_API_KEY not set, returning empty")
            return []

        params = {"q": query, "num": min(limit, 10)}
        cache_key = self._build_cache_key(params)

        # Check Redis cache
        try:
            cached = await redis_get_with_retry(cache_key)
            if cached is not None:
                logger.info(f"Serper shopping cache hit: {cache_key}")
                return [AffiliateProduct(**p) for p in json.loads(cached)]
        except Exception as e:
            logger.warning(f"Serper shopping cache read failed: {e}")

        # Call Serper API
        logger.info(f"Serper shopping API call: query='{query}'")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    SERPER_SHOPPING_URL,
                    json=params,
                    headers={"X-API-KEY": settings.SERPAPI_API_KEY},
                )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Serper shopping API error: {e}")
            return []

        products = []
        for item in data.get("shopping", []):
            price = _parse_price(item.get("price", ""))

            if min_price is not None and price > 0 and price < min_price:
                continue
            if max_price is not None and price > 0 and price > max_price:
                continue

            rating_raw = item.get("rating")
            rating = float(rating_raw) if rating_raw is not None else None
            count_raw = item.get("ratingCount")
            review_count = int(count_raw) if count_raw is not None else None

            link = item.get("link", "")
            products.append(AffiliateProduct(
                product_id=item.get("productId") or f"serper_{item.get('position', 0)}",
                title=item.get("title", ""),
                price=price,
                currency="USD",
                affiliate_link=link,
                merchant=item.get("source", ""),
                image_url=item.get("imageUrl"),
                rating=rating,
                review_count=review_count,
                condition="new",
                availability=True,
                source_url=link,
            ))

        result = products[:limit]

        # Cache result
        try:
            serialized = json.dumps([dataclasses.asdict(p) for p in result])
            await redis_set_with_retry(cache_key, serialized, ex=CACHE_TTL)
        except Exception as e:
            logger.warning(f"Serper shopping cache write failed: {e}")

        return result

    async def generate_affiliate_link(
        self,
        product_id: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> str:
        # Direct retailer URLs — no affiliate wrapping at MVP stage (Skimlinks in Phase 6)
        return product_id

    async def check_link_health(self, affiliate_link: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
                resp = await client.head(affiliate_link)
                return resp.status_code < 400
        except Exception:
            return False
