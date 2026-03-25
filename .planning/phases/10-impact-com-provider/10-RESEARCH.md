# Phase 10: Impact.com Provider - Research

**Researched:** 2026-03-25
**Domain:** Impact.com Catalog API integration as an affiliate product search provider
**Confidence:** HIGH

## Summary

The Impact.com Catalog API is a REST-based product search system that uses HTTP Basic Auth (AccountSID + AuthToken) and returns JSON responses containing product data with pre-built affiliate tracking URLs. The API's `Catalogs/ItemSearch` endpoint supports keyword search across all joined advertiser catalogs, with a dedicated rate limit of 3,000 requests/hour for product search endpoints. The `Url` field in each catalog item response is already a fully tracked affiliate link -- no additional link wrapping is needed.

The existing ReviewGuide.ai codebase has a well-established affiliate provider plugin system: a `BaseAffiliateProvider` abstract class, a decorator-based `AffiliateProviderRegistry`, an auto-discovery `loader.py` that imports all `*_provider.py` files from the providers directory, and a `_PROVIDER_INIT_MAP` in the loader that maps registry names to constructor kwargs. The CJ provider is the closest architectural analog (also uses API key auth, Redis caching, and returns results from a network of multiple advertisers).

**Primary recommendation:** Create `impact_provider.py` following the CJ provider pattern, with Redis-based response caching and a Redis sorted-set rate limiter (matching the existing `rate_limiter.py` sliding-window pattern) to enforce the 3,000 req/hour ceiling.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PROV-01 | Impact.com affiliate catalog available as a product search provider with rate limiting and feature flag | Impact.com Catalog API provides `Catalogs/ItemSearch` endpoint with Keyword search, JSON responses with tracked URLs, 3,000 req/hour rate limit. Codebase has BaseAffiliateProvider + Registry + Loader pattern for plug-and-play integration. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | (already in project) | Async HTTP client for Impact.com API calls | Used by all existing providers (eBay, CJ); async-native |
| redis (aioredis) | (already in project) | Response caching + rate limiting | Existing `redis_client.py` with retry helpers; rate limiter pattern in `rate_limiter.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic (via settings) | (already in project) | Config validation for IMPACT_* env vars | Define settings fields in `config.py` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx | requests | requests is sync-only; httpx is already the project standard for async providers |
| Redis sorted-set rate limiter | In-memory counter | In-memory resets on restart, doesn't share across workers; Redis is already available and proven |
| No Python SDK for Impact.com | N/A | There is no official Impact.com Python SDK. Direct REST calls via httpx match the CJ provider approach. |

**Installation:**
```bash
# No new packages needed -- httpx and redis are already installed
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/services/affiliate/providers/
    impact_provider.py          # NEW: ImpactAffiliateProvider class
backend/app/core/
    config.py                   # ADD: IMPACT_* settings fields
backend/app/services/affiliate/
    loader.py                   # ADD: "impact" entry to _PROVIDER_INIT_MAP
backend/tests/
    test_impact_provider.py     # NEW: Unit tests following test_cj_provider.py pattern
```

### Pattern 1: Decorator-Based Provider Registration
**What:** Each provider file uses `@AffiliateProviderRegistry.register(name, required_env_vars, optional_env_vars)` as a class decorator. The loader auto-discovers by globbing `providers/*.py` and importing each module, which triggers the decorator.
**When to use:** Always -- this is how ALL affiliate providers self-register.
**Example:**
```python
# Source: backend/app/services/affiliate/providers/cj_provider.py (existing pattern)
@AffiliateProviderRegistry.register(
    "impact",
    required_env_vars=["IMPACT_ACCOUNT_SID", "IMPACT_AUTH_TOKEN"],
)
class ImpactAffiliateProvider(BaseAffiliateProvider):
    ...
```

### Pattern 2: Loader Init Map for Constructor Kwargs
**What:** `loader.py` has a `_PROVIDER_INIT_MAP` dict mapping registry names to lambda functions that return constructor kwargs from settings. This bridges the gap between settings and provider constructors.
**When to use:** Every new provider must add an entry.
**Example:**
```python
# Source: backend/app/services/affiliate/loader.py (existing pattern)
_PROVIDER_INIT_MAP = {
    # ... existing entries ...
    "impact": lambda: {
        "account_sid": settings.IMPACT_ACCOUNT_SID,
        "auth_token": settings.IMPACT_AUTH_TOKEN,
    },
}
```

### Pattern 3: Redis Caching for API Responses
**What:** CJ provider hashes search params to build a deterministic Redis key, checks cache before API call, caches response JSON with a TTL.
**When to use:** All providers that make external API calls should cache results.
**Example:**
```python
# Source: backend/app/services/affiliate/providers/cj_provider.py (existing pattern)
cache_key = self._build_cache_key(params)
cached = await redis_get_with_retry(cache_key)
if cached is not None:
    return [AffiliateProduct(**p) for p in json.loads(cached)]
# ... make API call, then cache ...
await redis_set_with_retry(cache_key, products_json, ex=self.cache_ttl)
```

### Pattern 4: Redis Sliding-Window Rate Limiter for API Calls
**What:** Use Redis sorted sets to track API call timestamps within a 1-hour window. Before each API call, check count; if at limit, skip call and return empty or cached results. This is an internal rate limiter to protect against exceeding Impact.com's 3,000/hour limit -- separate from the user-facing rate limiter.
**When to use:** For any provider with hard rate limits that would cause 429 errors.
**Example:**
```python
# Adapted from backend/app/core/rate_limiter.py sliding-window pattern
import time
from app.core.redis_client import get_redis

async def _check_api_rate_limit(self) -> bool:
    """Return True if we're under the 3,000/hour limit."""
    redis = await get_redis()
    key = "impact:api:rate_limit"
    now = int(time.time())
    window_start = now - 3600  # 1-hour window

    await redis.zremrangebyscore(key, 0, window_start)
    count = await redis.zcard(key)

    if count >= self.max_requests_per_hour:
        return False

    await redis.zadd(key, {str(now): now})
    await redis.expire(key, 3600)
    return True
```

### Anti-Patterns to Avoid
- **Hard-coding credentials in provider file:** Always read from `settings` via `config.py` Fields.
- **Creating a new httpx client per request:** Reuse a persistent `httpx.AsyncClient` instance (eBay pattern) or create one per search call within `async with` (CJ pattern). Either works; CJ pattern is simpler for a provider with no token management.
- **Skipping the loader init map:** If you only rely on the `@register` decorator without adding to `_PROVIDER_INIT_MAP`, the loader will call `provider_class()` with no args, which may crash if the constructor expects credentials.
- **Building affiliate links manually:** The Impact.com `Url` field already contains a fully-tracked affiliate link. Do NOT construct tracking URLs manually.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting | Custom in-memory counter | Redis sorted-set sliding window (existing pattern in `rate_limiter.py`) | Survives restarts, works across multiple workers, battle-tested in codebase |
| HTTP client | raw urllib/aiohttp | httpx.AsyncClient | Already used by eBay and CJ providers; async-native, timeout support |
| Response caching | File-based cache or custom dict | Redis via `redis_get_with_retry` / `redis_set_with_retry` | Already built with retry logic and connection pooling |
| Affiliate link generation | Manual URL construction with tracking params | Use the `Url` field directly from API response | Impact.com returns pre-built tracked URLs unlike eBay/Amazon |
| Provider discovery | Manual import in `__init__.py` | Auto-discovery via `loader.py` glob pattern | Adding a file named `*_provider.py` in the providers dir is all that's needed |

**Key insight:** The Impact.com API returns ready-to-use affiliate tracking URLs in the `Url` field. This is similar to CJ (which returns `buy-url`) and unlike Amazon/eBay where we construct tracking links ourselves.

## Common Pitfalls

### Pitfall 1: Rate Limit Exhaustion Under Parallel Search
**What goes wrong:** The `product_affiliate.py` MCP tool searches ALL providers for ALL products in parallel via `asyncio.gather`. With 8 products and Impact.com, that's 8 concurrent API calls. Under load, this can burn through the 3,000/hour limit quickly.
**Why it happens:** Each product search is a separate API call. The Impact.com `Keyword` parameter only searches one query at a time.
**How to avoid:** Implement the Redis rate limiter check BEFORE each API call. When the limit is reached, return empty results gracefully (log a warning, don't raise). Consider also using the `PageSize` parameter to return multiple results per call (default is 100), reducing call volume.
**Warning signs:** HTTP 429 responses from Impact.com; `X-RateLimit-Remaining-hour` header approaching zero.

### Pitfall 2: Confusing Brand API vs Publisher API Base URLs
**What goes wrong:** Using `https://api.impact.com/Advertisers/<SID>` (brand endpoint) instead of `https://api.impact.com/Mediapartners/<SID>` (publisher endpoint).
**Why it happens:** Impact.com documentation has separate sections for brands and publishers. The catalog search endpoint for publishers is under `/Mediapartners/`.
**How to avoid:** Always use the base URL `https://api.impact.com/Mediapartners/{account_sid}/Catalogs/ItemSearch` for product search.
**Warning signs:** 401 or 404 errors from the API.

### Pitfall 3: Missing Loader Init Map Entry
**What goes wrong:** Provider file is created with `@register` decorator, auto-discovered by loader, but instantiation fails because no kwargs are passed to the constructor.
**Why it happens:** The loader checks `_PROVIDER_INIT_MAP` for the provider name. If not found, it calls `provider_class()` with no arguments (line 102 of loader.py). If the constructor has required params, this crashes.
**How to avoid:** Always add the provider to `_PROVIDER_INIT_MAP` in `loader.py` alongside the provider file.
**Warning signs:** Error in startup logs: "Failed to instantiate affiliate provider 'impact'".

### Pitfall 4: Price Field Is Integer (Cents), Not Float
**What goes wrong:** The `CurrentPrice` and `OriginalPrice` fields in the Impact.com catalog item object are documented as `integer` type (likely cents or a raw integer). Treating them as dollar amounts produces wrong prices.
**Why it happens:** The API documentation lists these as `integer` type. Actual behavior may vary by advertiser catalog.
**How to avoid:** Parse price fields carefully. Test with real API responses to determine if values are in cents or dollars. Apply conversion if needed. Log raw values during development for debugging.
**Warning signs:** Prices that are 100x too high or too low compared to expected retail prices.

### Pitfall 5: Feature Flag Check Missing at Registration Time
**What goes wrong:** Provider registers with `required_env_vars=["IMPACT_ACCOUNT_SID", "IMPACT_AUTH_TOKEN"]` but there's no way to disable it when credentials ARE set (e.g., for maintenance).
**Why it happens:** The loader only checks if required env vars exist, not a feature flag.
**How to avoid:** Add `IMPACT_API_ENABLED` as a settings field (default `False`). Check it in the provider constructor or in the loader logic. The CJ provider pattern shows `CJ_API_ENABLED` in config but the CJ loader does not explicitly check it -- instead, the registration `required_env_vars` gates it. For Impact.com, add explicit feature flag checking: if `IMPACT_API_ENABLED` is False, skip registration in the loader or have the provider return empty results.
**Warning signs:** Provider active when it should be disabled; no way to turn it off without removing env vars.

## Code Examples

Verified patterns from the existing codebase:

### Provider Class Skeleton (based on CJ provider pattern)
```python
# File: backend/app/services/affiliate/providers/impact_provider.py
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
    ):
        self.account_sid = account_sid or settings.IMPACT_ACCOUNT_SID
        self.auth_token = auth_token or settings.IMPACT_AUTH_TOKEN
        self.timeout = settings.IMPACT_API_TIMEOUT
        self.cache_ttl = settings.IMPACT_CACHE_TTL
        self.max_results = settings.IMPACT_MAX_RESULTS
        self.max_requests_per_hour = settings.IMPACT_RATE_LIMIT_PER_HOUR
        self.api_enabled = settings.IMPACT_API_ENABLED

        self.search_url = (
            f"{IMPACT_API_BASE}/Mediapartners/{self.account_sid}"
            f"/Catalogs/ItemSearch"
        )

        logger.info(
            f"Impact.com provider initialized: "
            f"api_enabled={self.api_enabled}, "
            f"account_sid={self.account_sid[:8]}..."
        )

    def get_provider_name(self) -> str:
        return "Impact.com"

    async def _check_rate_limit(self) -> bool:
        """Check if we're under the hourly API rate limit."""
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

            await redis.zadd(key, {f"{now}:{id(self)}": now})
            await redis.expire(key, 3600)
            return True
        except Exception as e:
            logger.warning(f"Impact.com rate limit check failed (allowing request): {e}")
            return True  # Fail open

    def _build_cache_key(self, params: dict) -> str:
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
                logger.error(f"Impact.com API error: {response.status_code} - {response.text[:200]}")
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
                availability = stock in ("InStock", "PreOrder", "LimitedAvailability", "BackOrder")

                condition_map = {
                    "New": "new",
                    "Used": "used",
                    "Refurbished": "refurbished",
                    "OEM": "new",
                    "OpenBox": "used",
                }
                condition = condition_map.get(item.get("Condition", "New"), "new")

                shipping_rate = item.get("ShippingRate")
                shipping_cost = float(shipping_rate) if shipping_rate else None

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
        """Impact.com URLs are pre-tracked. Return the stored URL."""
        # For Impact.com, affiliate links come from the Url field in search results.
        # This method would need to look up the item by ID if called independently.
        return ""

    async def check_link_health(self, affiliate_link: str) -> bool:
        """Check if an Impact.com affiliate link is valid."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(affiliate_link, follow_redirects=False)
            is_healthy = response.status_code in (200, 301, 302)
            return is_healthy
        except Exception as e:
            logger.warning(f"Impact.com link health check failed: {e}")
            return False
```

### Config Settings to Add
```python
# Add to backend/app/core/config.py after the CJ section
# Impact.com Affiliate
IMPACT_API_ENABLED: bool = Field(default=False, description="Enable Impact.com Catalog Search API")
IMPACT_ACCOUNT_SID: str = Field(default="", description="Impact.com Account SID (starts with 'IR')")
IMPACT_AUTH_TOKEN: str = Field(default="", description="Impact.com Auth Token")
IMPACT_API_TIMEOUT: float = Field(default=10.0, description="Impact.com API request timeout in seconds")
IMPACT_CACHE_TTL: int = Field(default=28800, description="Impact.com search cache TTL in seconds (8 hours)")
IMPACT_MAX_RESULTS: int = Field(default=20, description="Max Impact.com products per search request")
IMPACT_RATE_LIMIT_PER_HOUR: int = Field(default=2500, description="Max Impact.com API requests per hour (actual limit is 3000, using 2500 as safety margin)")
```

### Loader Init Map Addition
```python
# Add to _PROVIDER_INIT_MAP in backend/app/services/affiliate/loader.py
"impact": lambda: {
    "account_sid": settings.IMPACT_ACCOUNT_SID,
    "auth_token": settings.IMPACT_AUTH_TOKEN,
},
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Impact Radius (old name) | Impact.com | ~2020 rebrand | Same API, updated branding and docs |
| XML responses only | JSON and XML supported | Unknown | Use JSON via `Accept: application/json` header |
| No scoped tokens | Scoped API tokens available | Recent (2025+) | Can create limited-permission tokens for catalog-only access |

**Deprecated/outdated:**
- The `impact` PyPI package is unrelated (it is an OTel AI SDK, not Impact.com affiliate API)
- No official Impact.com Python SDK exists; direct REST calls are the standard approach

## Open Questions

1. **Price field format (cents vs dollars)**
   - What we know: The API documentation types `CurrentPrice` as `integer`. Some affiliate APIs return cents, others return whole dollars.
   - What's unclear: Whether Impact.com returns 1299 (cents, meaning $12.99) or 12.99 (dollars as a number).
   - Recommendation: During implementation, log raw price values from a test API call. Apply `/100` conversion if values are in cents. Add a `IMPACT_PRICE_DIVISOR` setting (default 1) that can be adjusted.

2. **Response wrapper structure**
   - What we know: Items are in the response, likely under an `Items` key or a `CatalogItems` key.
   - What's unclear: The exact top-level JSON structure (is it `{"Items": [...]}` or `{"CatalogItems": [...]}` or a paginated wrapper?).
   - Recommendation: Log the full response structure on first successful API call. Adjust the `_parse_response` method to match.

3. **Feature flag implementation approach**
   - What we know: Success criteria requires `IMPACT_API_ENABLED=false` to disable the provider.
   - What's unclear: Whether to check the flag at registration time (prevent registration) or at search time (return empty).
   - Recommendation: Check at search time (in `search_products`), matching how CJ and eBay handle their `api_enabled` flags. This way the provider registers but returns empty results when disabled, which is cleaner for logging and monitoring.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `backend/pytest.ini` |
| Quick run command | `cd backend && python -m pytest tests/test_impact_provider.py -x -v` |
| Full suite command | `cd backend && python -m pytest tests/ -x -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROV-01a | Impact.com search returns AffiliateProduct results from API response | unit | `cd backend && python -m pytest tests/test_impact_provider.py::TestImpactSearch -x` | Wave 0 |
| PROV-01b | Provider auto-discovered by loader and registered in AffiliateProviderRegistry | unit | `cd backend && python -m pytest tests/test_impact_provider.py::TestImpactRegistration -x` | Wave 0 |
| PROV-01c | API calls rate-limited to 3,000/hour via Redis sliding window | unit | `cd backend && python -m pytest tests/test_impact_provider.py::TestImpactRateLimit -x` | Wave 0 |
| PROV-01d | Provider disabled via IMPACT_API_ENABLED=false returns empty results | unit | `cd backend && python -m pytest tests/test_impact_provider.py::TestImpactFeatureFlag -x` | Wave 0 |
| PROV-01e | JSON response parsing maps all fields to AffiliateProduct correctly | unit | `cd backend && python -m pytest tests/test_impact_provider.py::TestImpactParsing -x` | Wave 0 |
| PROV-01f | Redis cache hit skips API call | unit | `cd backend && python -m pytest tests/test_impact_provider.py::TestImpactCache -x` | Wave 0 |
| PROV-01g | API errors (timeout, 500, 429) return empty list without raising | unit | `cd backend && python -m pytest tests/test_impact_provider.py::TestImpactErrorHandling -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_impact_provider.py -x -v`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_impact_provider.py` -- covers PROV-01a through PROV-01g (all test classes)
- [ ] No new test fixtures needed; follow `test_cj_provider.py` pattern of mocking httpx and redis

## Sources

### Primary (HIGH confidence)
- [Impact.com Publisher Integrations Portal - Search Catalog Items](https://integrations.impact.com/impact-publisher/reference/search-catalog-items) - Endpoint URL, parameters, response fields
- [Impact.com Publisher Integrations Portal - Rate Limits](https://integrations.impact.com/impact-publisher/reference/rate-limits) - 3,000 req/hour for Product Search, 429 response code, rate limit headers
- [Impact.com Publisher Integrations Portal - Authentication](https://integrations.impact.com/impact-publisher/reference/authentication) - HTTP Basic Auth, AccountSID + AuthToken
- [Impact.com Publisher Integrations Portal - Catalog Item Object](https://integrations.impact.com/impact-publisher/reference/the-catalog-item-object) - Complete field reference including Url, CurrentPrice, ImageUrl
- [Impact.com Publisher Integrations Portal - List Catalogs](https://integrations.impact.com/impact-publisher/reference/list-catalogs) - Catalog listing for debugging/admin

### Secondary (MEDIUM confidence)
- [Impact.com Help Center - Create Tracking Links](https://help.impact.com/en/support/solutions/articles/48001237353-create-tracking-links) - Confirmed Url field contains pre-built tracking links
- Codebase analysis: `backend/app/services/affiliate/` directory - All existing provider patterns verified by direct code reading

### Tertiary (LOW confidence)
- Price field format (integer vs float) - Documented as `integer` but actual format needs validation with live API calls

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new libraries needed; all patterns verified from existing codebase
- Architecture: HIGH - Direct pattern match with CJ provider; loader, registry, and manager patterns fully understood
- Pitfalls: HIGH - Rate limits confirmed from official docs; feature flag pattern from existing providers; price format is the only uncertainty
- API details: MEDIUM - Endpoint, auth, and rate limits confirmed from official docs; response JSON wrapper structure needs validation with live calls

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable API; rate limits subject to change per Impact.com docs)
