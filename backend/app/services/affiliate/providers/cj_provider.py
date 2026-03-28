"""
CJ Affiliate (Commission Junction) Provider
Integrates with CJ GraphQL API (ads.api.cj.com) for product search and affiliate link generation.
Uses Bearer token auth, partnerStatus JOINED filter, and Redis caching.
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

logger = get_logger(__name__)

CJ_GRAPHQL_ENDPOINT = "https://ads.api.cj.com/query"

PRODUCT_SEARCH_QUERY = """
query ProductSearch($companyId: String!, $keywords: String!, $limit: Int, $pid: ID!) {
  products(
    companyId: $companyId
    keywords: $keywords
    partnerStatus: JOINED
    limit: $limit
  ) {
    totalCount
    resultList {
      catalogId
      title
      imageLink
      advertiserId
      advertiserName
      price { amount currency }
      linkCode(pid: $pid) { clickUrl }
    }
  }
}
"""


@AffiliateProviderRegistry.register(
    "cj",
    required_env_vars=["CJ_API_KEY", "CJ_WEBSITE_ID"],
)
class CJAffiliateProvider(BaseAffiliateProvider):
    """
    CJ Affiliate (Commission Junction) Provider

    Features:
    - Product search via CJ GraphQL API (ads.api.cj.com)
    - Filters to JOINED advertisers only (affiliate links generated automatically)
    - Redis caching for search results
    - clickUrl from linkCode contains fully-formed affiliate tracking link
    """

    def __init__(
        self,
        api_key: str = None,
        website_id: str = None,
        company_id: str = None,
    ):
        self.api_key = api_key or settings.CJ_API_KEY
        self.website_id = website_id or settings.CJ_WEBSITE_ID
        self.company_id = company_id or settings.CJ_PUBLISHER_ID
        self.timeout = settings.CJ_API_TIMEOUT
        self.cache_ttl = settings.CJ_CACHE_TTL
        self.max_results = settings.CJ_MAX_RESULTS

        logger.info(
            f"CJ provider initialized: "
            f"website_id={self.website_id}, "
            f"company_id={self.company_id}"
        )

    def get_provider_name(self) -> str:
        return "CJ"

    def _build_cache_key(self, query: str, limit: int) -> str:
        param_str = f"{query}:{limit}"
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return f"cj:search:{param_hash}"

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 5,
    ) -> List[AffiliateProduct]:
        effective_limit = min(limit, self.max_results)

        # Check Redis cache
        cache_key = self._build_cache_key(query, effective_limit)
        try:
            cached = await redis_get_with_retry(cache_key)
            if cached is not None:
                logger.info(f"CJ cache hit for key {cache_key}")
                products_data = json.loads(cached)
                return [AffiliateProduct(**p) for p in products_data]
        except Exception as e:
            logger.warning(f"CJ cache read failed: {e}")

        # Call CJ GraphQL API
        logger.info(f"CJ GraphQL search: query='{query}', limit={effective_limit}")
        variables = {
            "companyId": self.company_id,
            "keywords": query,
            "limit": effective_limit,
            "pid": self.website_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    CJ_GRAPHQL_ENDPOINT,
                    json={"query": PRODUCT_SEARCH_QUERY, "variables": variables},
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )

            if response.status_code != 200:
                logger.error(
                    f"CJ GraphQL error: {response.status_code} - {response.text[:200]}"
                )
                return []

            data = response.json()

            if "errors" in data:
                logger.error(f"CJ GraphQL errors: {data['errors']}")
                return []

            products = self._parse_graphql_response(data)
            logger.info(f"CJ API returned {len(products)} products for '{query}'")

        except httpx.TimeoutException:
            logger.error("CJ API request timed out")
            return []
        except Exception as e:
            logger.error(f"CJ API request failed: {e}", exc_info=True)
            return []

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
            logger.debug(f"CJ results cached: key={cache_key}, ttl={self.cache_ttl}")
        except Exception as e:
            logger.warning(f"CJ cache write failed: {e}")

        return products

    def _parse_graphql_response(self, data: dict) -> List[AffiliateProduct]:
        products = []

        try:
            result_list = data["data"]["products"]["resultList"]
        except (KeyError, TypeError):
            logger.warning("CJ GraphQL: no resultList in response")
            return []

        for item in result_list:
            try:
                # Skip products without affiliate links (not joined with advertiser)
                link_code = item.get("linkCode")
                if not link_code or not link_code.get("clickUrl"):
                    continue

                click_url = link_code["clickUrl"]
                price_obj = item.get("price", {})
                try:
                    price = float(price_obj.get("amount", 0))
                except (ValueError, TypeError):
                    price = 0.0

                catalog_id = item.get("catalogId", "")
                advertiser_id = item.get("advertiserId", "")
                product_id = f"cj-{advertiser_id}-{catalog_id}" if catalog_id else f"cj-{advertiser_id}"

                products.append(
                    AffiliateProduct(
                        product_id=product_id,
                        title=item.get("title", "Unknown Product"),
                        price=price,
                        currency=price_obj.get("currency", "USD"),
                        affiliate_link=click_url,
                        merchant=item.get("advertiserName", "CJ"),
                        image_url=item.get("imageLink"),
                        rating=None,
                        review_count=None,
                        condition="new",
                        shipping_cost=None,
                        availability=True,
                        source_url=click_url,
                    )
                )

            except Exception as e:
                logger.warning(f"Failed to parse CJ product: {e}")
                continue

        return products

    async def generate_affiliate_link(
        self,
        product_id: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> str:
        """
        CJ clickUrls from the GraphQL API are already complete affiliate links.
        This method is a fallback for constructing a deep link manually.
        """
        base = "https://www.anrdoezrs.net/links"
        url = f"{base}/{self.website_id}"
        if tracking_id:
            url += f"?sid={tracking_id}"

        logger.debug(f"Generated CJ affiliate link: {url}")
        return url

    async def check_link_health(self, affiliate_link: str) -> bool:
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


__all__ = ["CJAffiliateProvider"]
