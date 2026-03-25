# Phase 6: Skimlinks Link Wrapper - Research

**Researched:** 2026-03-25
**Domain:** Skimlinks Affiliate API Integration (Merchant API + Link Wrapper)
**Confidence:** HIGH

## Summary

Skimlinks provides two mechanisms relevant to Phase 6: (1) a **Merchant API** that returns a catalog of 48,500+ merchant domains with commission data, and (2) a **Link Wrapper** redirect URL format (`go.skimresources.com`) that wraps any supported merchant URL into an affiliate-tracked redirect. The server-side implementation requires fetching the merchant domain list once (cacheable to Redis with 24h TTL), then for each product URL: extracting the domain, checking membership, and constructing a `go.skimresources.com?id=...&url=...` redirect.

The existing codebase has a well-established pattern for affiliate providers (`BaseAffiliateProvider` + `AffiliateProviderRegistry` decorator + auto-discovery loader). However, Skimlinks is architecturally different from eBay/CJ/Amazon: it does not search for products. It **wraps existing URLs** from other providers (primarily Serper Shopping in Phase 3) with affiliate tracking. This means Skimlinks should NOT implement `search_products()` in the traditional sense. Instead, it should be a **link wrapping service** that the `product_affiliate` tool calls as a post-processing step on URLs from non-Amazon, non-eBay providers.

**Critical finding:** Amazon has not been a Skimlinks merchant since March 31, 2020 (Amazon removed third-party affiliate vendors including Skimlinks, Sovrn, and CJ). eBay is still supported in the Skimlinks network. However, since ReviewGuide already has direct eBay Partner Network integration (Phase 1), eBay URLs should also be excluded from Skimlinks wrapping to avoid double-affiliating. The exclusion list is therefore: Amazon domains (`amazon.*`, `amzn.to`) AND eBay domains (`ebay.*`).

**Primary recommendation:** Implement `SkimlinksLinkWrapper` as a standalone service (not a `BaseAffiliateProvider` subclass) in `backend/app/services/affiliate/skimlinks.py` with a `wrap_url(url, xcust)` method. Cache the merchant domain set in Redis. Call it from `product_affiliate.py` as post-processing on Serper Shopping results.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AFFL-01 | Serper Shopping result for Skimlinks merchant generates go.redirectingat.com/go.skimresources.com wrapped URL | Merchant API domains endpoint provides domain list; Link Wrapper URL format documented; wrap applied in product_affiliate post-processing |
| AFFL-02 | Amazon product URL never passed through Skimlinks wrapper | Amazon removed from Skimlinks since 2020; explicit domain exclusion list in wrapper; eBay also excluded (own EPN integration) |
| AFFL-03 | Merchant domain list from Redis cache (24h TTL) or Merchant API on miss | Domains endpoint (`/v4/publisher/{id}/domains`) returns full list (~26K domains); Redis caching with `redis_set_with_retry` at 86400s TTL |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | (existing) | Async HTTP client for Merchant API and auth endpoint | Already used by eBay and CJ providers |
| redis (aioredis) | (existing) | Cache merchant domain set with 24h TTL | Already used via `redis_client.py` helpers |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| urllib.parse | stdlib | URL encoding for link wrapper, domain extraction | Every link wrap operation |
| json | stdlib | Serialize/deserialize domain cache | Cache read/write |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Standalone service class | BaseAffiliateProvider subclass | BaseAffiliateProvider mandates search_products() which Skimlinks does not do; standalone is cleaner |
| Redis SET for domain cache | Redis sorted set / bloom filter | Simple JSON-serialized set is sufficient for ~26K domains; no need for probabilistic structures |

**Installation:**
No new dependencies required. All libraries already in the project.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/services/affiliate/
    skimlinks.py               # SkimlinksLinkWrapper service class
    providers/
        ... (existing providers unchanged)
backend/app/core/
    config.py                  # Add SKIMLINKS_* settings
backend/tests/
    test_skimlinks.py          # Unit tests for wrapper
```

### Pattern 1: SkimlinksLinkWrapper as a Service (not a Provider)

**What:** A standalone service class with `wrap_url()`, `is_supported_domain()`, and `refresh_merchant_domains()` methods. NOT a `BaseAffiliateProvider` subclass.

**When to use:** Skimlinks does not search for products -- it monetizes existing URLs. The BaseAffiliateProvider interface requires `search_products()` and `generate_affiliate_link()` which do not map to Skimlinks' link-wrapping model.

**Example:**
```python
# backend/app/services/affiliate/skimlinks.py

import json
from typing import Optional, Set
from urllib.parse import quote, urlparse

import httpx

from app.core.centralized_logger import get_logger
from app.core.config import settings
from app.core.redis_client import redis_get_with_retry, redis_set_with_retry

logger = get_logger(__name__)

# Domains to NEVER wrap (already have direct affiliate programs)
EXCLUDED_DOMAINS = {
    "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr",
    "amazon.it", "amazon.es", "amazon.ca", "amazon.com.au",
    "amazon.in", "amazon.co.jp", "amazon.com.br", "amazon.sg",
    "amzn.to",
    "ebay.com", "ebay.co.uk", "ebay.de", "ebay.fr",
    "ebay.it", "ebay.es", "ebay.com.au", "ebay.ca",
}

REDIS_DOMAIN_CACHE_KEY = "skimlinks:merchant_domains"
DOMAIN_CACHE_TTL = 86400  # 24 hours

AUTH_URL = "https://authentication.skimapis.com/access_token"
DOMAINS_URL = "https://merchants.skimapis.com/v4/publisher/{publisher_id}/domains"
LINK_WRAPPER_BASE = "https://go.skimresources.com"


class SkimlinksLinkWrapper:
    """Server-side Skimlinks link wrapper for monetizing product URLs."""

    def __init__(self):
        self.publisher_id = settings.SKIMLINKS_PUBLISHER_ID
        self.domain_id = settings.SKIMLINKS_DOMAIN_ID
        self.site_id = f"{self.publisher_id}X{self.domain_id}"
        self.client_id = settings.SKIMLINKS_CLIENT_ID
        self.client_secret = settings.SKIMLINKS_CLIENT_SECRET
        self.enabled = settings.SKIMLINKS_API_ENABLED
        self._access_token: Optional[str] = None
        self._merchant_domains: Optional[Set[str]] = None

    async def wrap_url(
        self, url: str, xcust: Optional[str] = None
    ) -> str:
        """Wrap a URL with Skimlinks tracking if domain is supported.
        Returns original URL unchanged if not supported or disabled."""
        if not self.enabled:
            return url

        domain = self._extract_domain(url)
        if not domain:
            return url

        if domain in EXCLUDED_DOMAINS:
            return url

        domains = await self._get_merchant_domains()
        if domain not in domains:
            return url

        # Construct wrapped URL
        encoded_url = quote(url, safe="")
        wrapped = f"{LINK_WRAPPER_BASE}?id={self.site_id}&xs=1&url={encoded_url}"
        if xcust:
            wrapped += f"&xcust={xcust}"

        return wrapped

    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        """Extract bare domain from URL (strips www. prefix)."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain or None
        except Exception:
            return None

    async def _get_merchant_domains(self) -> Set[str]:
        """Get merchant domains from Redis cache or Merchant API."""
        if self._merchant_domains is not None:
            return self._merchant_domains

        # Try Redis cache first
        try:
            cached = await redis_get_with_retry(REDIS_DOMAIN_CACHE_KEY)
            if cached:
                self._merchant_domains = set(json.loads(cached))
                return self._merchant_domains
        except Exception as e:
            logger.warning(f"Skimlinks domain cache read failed: {e}")

        # Cache miss -- fetch from API
        self._merchant_domains = await self._fetch_domains_from_api()

        # Write to Redis
        try:
            await redis_set_with_retry(
                REDIS_DOMAIN_CACHE_KEY,
                json.dumps(list(self._merchant_domains)),
                ex=DOMAIN_CACHE_TTL,
            )
        except Exception as e:
            logger.warning(f"Skimlinks domain cache write failed: {e}")

        return self._merchant_domains

    async def _fetch_domains_from_api(self) -> Set[str]:
        """Fetch all merchant domains from Skimlinks Merchant API."""
        token = await self._get_access_token()
        if not token:
            return set()

        url = DOMAINS_URL.format(publisher_id=self.publisher_id)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url, params={"access_token": token}
                )
            if resp.status_code != 200:
                logger.error(f"Skimlinks domains API: {resp.status_code}")
                return set()
            data = resp.json()
            domains = {d["domain"] for d in data.get("domains", [])}
            logger.info(f"Skimlinks: fetched {len(domains)} merchant domains")
            return domains
        except Exception as e:
            logger.error(f"Skimlinks domains fetch failed: {e}")
            return set()

    async def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token for Merchant API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(AUTH_URL, json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                })
            if resp.status_code != 200:
                logger.error(f"Skimlinks auth failed: {resp.status_code}")
                return None
            self._access_token = resp.json().get("access_token")
            return self._access_token
        except Exception as e:
            logger.error(f"Skimlinks auth error: {e}")
            return None
```

### Pattern 2: Post-Processing in product_affiliate.py

**What:** After all provider searches complete, iterate over non-Amazon/non-eBay offers and apply Skimlinks wrapping.

**When to use:** In the `product_affiliate` tool, after the `search_provider()` gather completes.

**Example:**
```python
# In product_affiliate.py, after building affiliate_products dict:

from app.services.affiliate.skimlinks import skimlinks_wrapper

# Post-process: wrap non-Amazon, non-eBay URLs with Skimlinks
if skimlinks_wrapper.enabled:
    for provider_name, product_groups in affiliate_products.items():
        if provider_name in ("amazon", "ebay"):
            continue  # Skip direct affiliate providers
        for group in product_groups:
            for offer in group.get("offers", []):
                original_url = offer.get("url", "")
                if original_url:
                    offer["url"] = await skimlinks_wrapper.wrap_url(
                        original_url, xcust=session_id
                    )
```

### Pattern 3: Feature Flag (SKIMLINKS_API_ENABLED)

**What:** Boolean env var that gates all Skimlinks functionality. When `false`, `wrap_url()` returns the original URL unchanged.

**When to use:** Always. Matches the existing pattern (`CJ_API_ENABLED`, `USE_MOCK_AFFILIATE`).

**Example:**
```python
# In backend/app/core/config.py
SKIMLINKS_API_ENABLED: bool = Field(
    default=False,
    description="Enable Skimlinks affiliate link wrapping"
)
SKIMLINKS_PUBLISHER_ID: str = Field(
    default="",
    description="Skimlinks publisher ID (numeric, before the X)"
)
SKIMLINKS_DOMAIN_ID: str = Field(
    default="",
    description="Skimlinks domain ID (numeric, after the X)"
)
SKIMLINKS_CLIENT_ID: str = Field(
    default="",
    description="Skimlinks API client ID for OAuth2"
)
SKIMLINKS_CLIENT_SECRET: str = Field(
    default="",
    description="Skimlinks API client secret for OAuth2"
)
```

### Anti-Patterns to Avoid
- **Making Skimlinks a BaseAffiliateProvider subclass:** It does not search for products. Forcing it into the provider interface would require dummy implementations of `search_products()` and `generate_affiliate_link()`.
- **Wrapping Amazon/eBay URLs:** Amazon left Skimlinks in March 2020. eBay has its own EPN integration. Double-wrapping would break tracking or lose commissions.
- **Fetching the domain list on every request:** The Merchant API has rate limits (40/min, 1000/hr). Cache in Redis with 24h TTL and also keep an in-memory set per process.
- **Using go.redirectingat.com instead of go.skimresources.com:** Both work, but the official API documentation for server-side link wrapping specifies `go.skimresources.com` as the canonical endpoint.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Domain extraction from URLs | Custom regex parser | `urllib.parse.urlparse` | Handles edge cases (ports, auth, IPv6) |
| URL encoding for link wrapper | Manual string replacement | `urllib.parse.quote(url, safe="")` | Correct RFC 3986 encoding |
| Redis caching with retry | Custom retry loop | `redis_get_with_retry` / `redis_set_with_retry` | Already exists in `app.core.redis_client` with exponential backoff |
| HTTP client | `requests` (sync) | `httpx.AsyncClient` | Matches existing async patterns, already a dependency |

**Key insight:** The hardest part of this integration is NOT the API calls (they are straightforward REST). It is the **domain matching logic**: the Merchant API returns ~26K domains including subdomains (e.g., `m.bestbuy.com` alongside `bestbuy.com`). The wrapper must normalize both the cached domain AND the product URL domain to handle `www.` prefixes and mobile subdomains.

## Common Pitfalls

### Pitfall 1: Subdomain Mismatch
**What goes wrong:** A product URL is `https://www.bestbuy.com/...` but the Merchant API returns `bestbuy.com` (without `www.`). The domain check fails and the URL is not wrapped.
**Why it happens:** The Skimlinks domains endpoint returns domains both with and without subdomains (e.g., `bestbuy.com` AND `m.bestbuy.com`).
**How to avoid:** Strip `www.` prefix from the product URL domain before checking. For the cache set, store domains as-is from the API (they include necessary subdomains). When checking a URL, try both the raw domain and the `www.`-stripped version.
**Warning signs:** Wrapped URL count is much lower than expected for known merchants.

### Pitfall 2: Rate Limiting on Merchant API
**What goes wrong:** The domains endpoint returns HTTP 429 because the app fetched the domain list too frequently.
**Why it happens:** Rate limit is 40 requests/min and 1000/hour. Without caching, every product search triggers a domain fetch.
**How to avoid:** Redis cache with 24h TTL + in-memory process cache. The domain list changes infrequently (merchants join/leave on a weekly/monthly basis).
**Warning signs:** `429 Too Many Requests` in logs after deploy.

### Pitfall 3: Feature Flag Not Wired to Config
**What goes wrong:** Setting `SKIMLINKS_API_ENABLED=false` in Railway does not actually disable wrapping because the code checks a hardcoded boolean instead of `settings.SKIMLINKS_API_ENABLED`.
**Why it happens:** From MEMORY.md: "Railway env vars: ALWAYS verify new feature flags exist on Railway after adding them."
**How to avoid:** Read the flag from `settings` on every call (not at import time). Test the disabled path explicitly.
**Warning signs:** Skimlinks wrapping active in prod when it should be off.

### Pitfall 4: Double-Affiliating eBay URLs
**What goes wrong:** A Serper Shopping result returns an eBay URL. Skimlinks wraps it (eBay is in their network). But the product also has a direct eBay EPN link from the eBay provider. User clicks the Skimlinks-wrapped eBay link and commission goes to Skimlinks instead of the direct EPN account.
**Why it happens:** eBay is a valid Skimlinks merchant, so the domain check passes.
**How to avoid:** Exclude all `ebay.*` domains in the `EXCLUDED_DOMAINS` set, same as Amazon.
**Warning signs:** eBay commission appears in Skimlinks dashboard instead of EPN dashboard.

### Pitfall 5: OAuth Token Expiry
**What goes wrong:** The access token obtained during startup expires after ~7 days (`expiry_timestamp`), and subsequent domain refresh calls fail silently.
**Why it happens:** Token is cached in memory but never refreshed.
**How to avoid:** Check `expiry_timestamp` before each API call. Re-authenticate if within 5 minutes of expiry. The domain cache itself (24h) is refreshed more often than the token expires, so each cache refresh re-authenticates.
**Warning signs:** Domain cache stops refreshing; logs show auth failures.

## Code Examples

### Constructing the Skimlinks Redirect URL
```python
# Source: Skimlinks Link Wrapper API documentation (developers.skimlinks.com/link.html)
# Verified via Apiary docs (jsapi.apiary.io/apis/skimlinkslinkapi)
from urllib.parse import quote

LINK_WRAPPER_BASE = "https://go.skimresources.com"
site_id = "12345X67890"  # {publisher_id}X{domain_id}

def wrap_url(url: str, xcust: str = None) -> str:
    encoded = quote(url, safe="")
    wrapped = f"{LINK_WRAPPER_BASE}?id={site_id}&xs=1&url={encoded}"
    if xcust:
        # xcust max 50 chars, alphanumeric + underscore + pipe only
        wrapped += f"&xcust={xcust[:50]}"
    return wrapped

# Example:
# wrap_url("https://www.bestbuy.com/site/sony-wh1000xm5/12345.p")
# => "https://go.skimresources.com?id=12345X67890&xs=1&url=https%3A%2F%2Fwww.bestbuy.com%2Fsite%2Fsony-wh1000xm5%2F12345.p"
```

### Fetching Merchant Domains from API
```python
# Source: Skimlinks Merchant API (jsapi.apiary.io/apis/skimlinksmerchantapi)
# Endpoint: GET /v4/publisher/{publisher_id}/domains
# Auth: OAuth2 client_credentials via https://authentication.skimapis.com/access_token

async def fetch_domains(publisher_id: str, access_token: str) -> set:
    url = f"https://merchants.skimapis.com/v4/publisher/{publisher_id}/domains"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params={"access_token": access_token})
    data = resp.json()
    # Response: {"domains": [{"id": 49333, "domain": "newegg.com", ...}, ...], "num_returned": 26324}
    return {d["domain"] for d in data.get("domains", [])}
```

### OAuth2 Authentication
```python
# Source: Skimlinks Merchant API Auth docs
# POST https://authentication.skimapis.com/access_token
# Body: {"client_id": "...", "client_secret": "...", "grant_type": "client_credentials"}
# Response: {"access_token": "12345:1553009669:8dd2c1721db55554ff1f9b4444431125",
#            "timestamp": 1553009669, "expiry_timestamp": 1553614469}

async def get_access_token(client_id: str, client_secret: str) -> tuple:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://authentication.skimapis.com/access_token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
        )
    data = resp.json()
    return data["access_token"], data["expiry_timestamp"]
```

### Config Settings Pattern (matching existing style)
```python
# Source: Existing config.py patterns for CJ_API_ENABLED, EBAY_APP_ID, etc.
# Add to backend/app/core/config.py Settings class:

# Skimlinks
SKIMLINKS_API_ENABLED: bool = Field(default=False, description="Enable Skimlinks affiliate link wrapping")
SKIMLINKS_PUBLISHER_ID: str = Field(default="", description="Skimlinks publisher ID (numeric)")
SKIMLINKS_DOMAIN_ID: str = Field(default="", description="Skimlinks domain ID (numeric)")
SKIMLINKS_CLIENT_ID: str = Field(default="", description="Skimlinks Merchant API client ID")
SKIMLINKS_CLIENT_SECRET: str = Field(default="", description="Skimlinks Merchant API client secret")
SKIMLINKS_DOMAIN_CACHE_TTL: int = Field(default=86400, description="Skimlinks merchant domain cache TTL in seconds (24h)")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| JavaScript-only (skimlinks.js) | Server-side Link Wrapper API | Available since ~2017 | Works on mobile, RSS, email; not blocked by ad blockers |
| Amazon in Skimlinks network | Amazon removed from Skimlinks | March 31, 2020 | Must exclude Amazon domains; use direct PA-API/Creators API |
| Product API key auth | OAuth2 client_credentials for Merchant API | September 2022 | Requires client_id + client_secret from Publisher Hub |
| go.redirectingat.com | go.skimresources.com (canonical) | ~2020 | Both work; official docs prefer go.skimresources.com |

**Deprecated/outdated:**
- **Product API key (legacy):** Replaced by OAuth2 client_credentials flow as of September 2022
- **Amazon integration:** Removed March 2020; Amazon URLs must be excluded from Skimlinks wrapping

## Open Questions

1. **Skimlinks Publisher Approval Status**
   - What we know: The roadmap says "apply immediately" as an external dependency
   - What's unclear: Whether the application has been submitted and approved
   - Recommendation: The code can be built and tested with mock data. Feature flag (`SKIMLINKS_API_ENABLED=false`) keeps it dormant until approval confirmed. Credentials (publisher_id, domain_id, client_id, client_secret) are obtained from Publisher Hub after approval.

2. **Domain List Size and Memory**
   - What we know: The domains endpoint returns ~26,324 domains (from API example response). Serialized as JSON, this is roughly 500KB-1MB.
   - What's unclear: Exact current count and growth rate
   - Recommendation: A Python `set` of 30K short strings uses ~2MB of memory. This is trivial. Cache in Redis AND in-memory per process.

3. **Serper Shopping URL Format**
   - What we know: Phase 3 (Serper Shopping) is a dependency. Serper Shopping returns product URLs from merchant websites.
   - What's unclear: The exact URL format Serper Shopping returns (direct merchant URL or Serper redirect)
   - Recommendation: The wrapper should handle both cases. If Serper returns a redirect URL, the domain check should be against the final destination. However, for initial implementation, check the domain of the URL as-is. Phase 7 (Skimlinks Middleware) can add redirect-following if needed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (auto mode) |
| Config file | `backend/pytest.ini` |
| Quick run command | `cd backend && python -m pytest tests/test_skimlinks.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AFFL-01 | Supported merchant URL is wrapped with go.skimresources.com | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestWrapUrl::test_supported_domain_wrapped -x` | Wave 0 |
| AFFL-01 | Unsupported domain URL passes through unchanged | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestWrapUrl::test_unsupported_domain_passthrough -x` | Wave 0 |
| AFFL-02 | Amazon URL never wrapped | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestWrapUrl::test_amazon_excluded -x` | Wave 0 |
| AFFL-02 | eBay URL never wrapped | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestWrapUrl::test_ebay_excluded -x` | Wave 0 |
| AFFL-03 | Redis cache hit returns domains without API call | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestDomainCache::test_cache_hit -x` | Wave 0 |
| AFFL-03 | Redis cache miss triggers API fetch and caches result | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestDomainCache::test_cache_miss_fetches_api -x` | Wave 0 |
| AFFL-03 | Cache TTL is 24 hours (86400 seconds) | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestDomainCache::test_cache_ttl -x` | Wave 0 |
| N/A | Feature flag disabled returns original URL | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestFeatureFlag::test_disabled_passthrough -x` | Wave 0 |
| N/A | OAuth2 token fetch success | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestAuth::test_token_fetch -x` | Wave 0 |
| N/A | OAuth2 token fetch failure returns empty domain set | unit | `cd backend && python -m pytest tests/test_skimlinks.py::TestAuth::test_token_failure_graceful -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_skimlinks.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_skimlinks.py` -- covers AFFL-01, AFFL-02, AFFL-03
- [ ] No framework install needed (pytest + pytest-asyncio already configured)

## Sources

### Primary (HIGH confidence)
- Skimlinks Merchant API -- full endpoint documentation via [Apiary](https://jsapi.apiary.io/apis/skimlinksmerchantapi/introduction/entities/merchant.html): endpoints, auth, domain entity, rate limits, response format
- Skimlinks Link Wrapper API -- via [Apiary](https://jsapi.apiary.io/apis/skimlinkslinkapi/introduction/parameters.html): URL format, parameters (id, url, xcust, sref, xs)
- [Datafeedr Skimlinks link replacement](https://datafeedrapi.helpscoutdocs.com/article/33-replace-affiliate-link-with-a-skimlinks-link): Confirmed URL construction pattern with xs=1 parameter
- Existing codebase: `backend/app/services/affiliate/` -- base.py, registry.py, loader.py, manager.py, providers/ebay_provider.py, providers/cj_provider.py

### Secondary (MEDIUM confidence)
- [Skimlinks publisher ID format](https://support.skimlinks.com/hc/en-us/articles/223835748-Where-can-I-locate-my-Publisher-ID-): "{publisher_id}X{domain_id}" format confirmed
- [Amazon removal from Skimlinks](https://support.skimlinks.com/hc/en-us/articles/360026739133-Does-Skimlinks-work-with-Amazon): Confirmed March 31, 2020 removal
- [Skimlinks September 2022 API changes](https://support.skimlinks.com/hc/en-us/articles/6993058288541-September-12-2022-Changes-to-Merchant-and-Commissions-APIs): OAuth2 migration for Merchant API
- [Ruby Skimlinks gem README](https://github.com/manuelmeurer/skimlinks/blob/master/README.md): Cross-verified Merchant API structure and authentication pattern

### Tertiary (LOW confidence)
- go.redirectingat.com vs go.skimresources.com equivalence -- community sources agree both work; official docs prefer go.skimresources.com

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all patterns match existing codebase
- Architecture: HIGH -- wrapper-not-provider pattern is clearly correct based on Skimlinks' link-wrapping model vs existing search-based providers
- Pitfalls: HIGH -- Amazon removal verified officially; rate limits documented; domain matching concerns identified from API response analysis
- API details: HIGH -- full endpoint docs, auth flow, response format, and rate limits obtained from Apiary documentation

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (Skimlinks API is stable; last breaking change was September 2022)
