# Phase 5: Amazon Creators API Migration - Research

**Researched:** 2026-03-25
**Domain:** Amazon Affiliate API Migration (PA-API v5 to Creators API)
**Confidence:** MEDIUM

## Summary

Amazon is retiring the Product Advertising API (PA-API) v5 on May 15, 2026. The replacement is the **Amazon Creators API**, which uses OAuth 2.0 authentication via Login with Amazon (LwA) instead of AWS Signature Version 4. The migration is primarily a "plumbing + casing" change: same operations (SearchItems, GetItems, GetVariations, GetBrowseNodes), but with OAuth2 bearer tokens instead of HMAC signatures, lowerCamelCase parameter names instead of PascalCase, and new credential types (Credential ID + Credential Secret instead of AWS Access Key + Secret Key).

The current `amazon_provider.py` (850 lines) contains a full AWS Signature V4 implementation that must be replaced with OAuth2 token acquisition and bearer token headers. The existing mock/curated data path will remain unchanged. The `python-amazon-paapi` library (v6.2.0, MIT license) provides a mature Python wrapper with async support via `AsyncAmazonCreatorsApi` that handles token management internally, eliminating the need to hand-roll OAuth2 token refresh logic.

**Primary recommendation:** Use the `python-amazon-paapi[async]` library (v6.2.0) as the Creators API client. Replace the entire `_send_paapi_request` method and AWS Signature V4 logic with the library's `AsyncAmazonCreatorsApi`. Keep the existing mock/curated data fallback paths, `AffiliateProduct` dataclass mapping, and provider registry integration intact.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AMZN-01 | Amazon keyword search and ASIN lookup return the same product data after migration as before | Creators API exposes identical SearchItems and GetItems operations; the `python-amazon-paapi` library wraps both with `search_items()` and `get_items()` methods returning equivalent data (title, price, images, reviews, ASIN) |
| AMZN-02 | OAuth2 tokens refresh automatically when within 5 minutes of the 1-hour expiry, with no user-visible interruption | The `python-amazon-paapi` library handles token lifecycle internally; for custom implementation, tokens last 3600s and should be refreshed at the 55-minute mark via Redis-cached token with TTL |
| AMZN-03 | Amazon product images are displayed via direct hotlink to Amazon CDN URLs -- no caching or re-hosting | Creators API returns image URLs from `images-na.ssl-images-amazon.com` and `m.media-amazon.com` domains identical to PA-API v5; the existing `_parse_paapi_response` already extracts `Images.Primary.Large.URL` |
| AMZN-04 | The amazon_provider.py file contains no AWS Signature V4 credential logic after migration | Migration removes the entire `_send_paapi_request` method (lines 547-641), all `hmac`/`hashlib` signature code, `PAAPI_HOSTS`, `PAAPI_REGIONS` dicts, and `AMAZON_ACCESS_KEY`/`AMAZON_SECRET_KEY` config references |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-amazon-paapi[async] | 6.2.0 | Amazon Creators API client with OAuth2 and async support | Official community wrapper; MIT license; handles OAuth2 token lifecycle, request throttling, response parsing; supports 20+ countries; 6.x is Creators API exclusive |
| httpx | 0.28.1 | HTTP client (already in project) | Already used by amazon_provider.py for PA-API requests; the library uses it internally for async |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| redis | 7.0.1 | Token caching (already in project) | Cache OAuth2 tokens in Redis if implementing custom token management instead of relying on library internals |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-amazon-paapi | Hand-rolled OAuth2 + httpx | Full control but must implement token refresh, request formatting, response parsing, throttling manually; 200+ lines of custom code vs zero |
| python-amazon-paapi | creatorsapi_python_sdk (Amazon's bundled SDK) | Lower-level, less documented, no community support; python-amazon-paapi wraps it with a better API |

**Installation:**
```bash
pip install python-amazon-paapi[async]==6.2.0
```

Add to `requirements.txt`:
```
# =============================
# Amazon Creators API
# =============================
python-amazon-paapi[async]==6.2.0
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/services/affiliate/providers/
  amazon_provider.py          # Rewritten: Creators API via python-amazon-paapi
  curated_amazon_links.py     # Unchanged: static curated data stays as-is
backend/app/core/
  config.py                   # Updated: replace PA-API config vars with Creators API vars
```

### Pattern 1: Library-Based API Client (Recommended)
**What:** Use `AsyncAmazonCreatorsApi` as an async context manager for all API calls.
**When to use:** Production mode when `AMAZON_API_ENABLED=true`.
**Example:**
```python
# Source: python-amazon-paapi docs (PyPI, v6.2.0)
from amazon_creatorsapi import AsyncAmazonCreatorsApi, Country

class AmazonAffiliateProvider(BaseAffiliateProvider):
    def __init__(self, credential_id, credential_secret, associate_tag, country_code="US"):
        self.credential_id = credential_id
        self.credential_secret = credential_secret
        self.associate_tag = associate_tag
        self.country = self._map_country(country_code)

    async def _search_real_api(self, query, category, limit, ...):
        async with AsyncAmazonCreatorsApi(
            credential_id=self.credential_id,
            credential_secret=self.credential_secret,
            tag=self.associate_tag,
            country=self.country,
            throttling=1.0,  # 1 second between requests
        ) as api:
            results = await api.search_items(
                keywords=query,
                search_index=self._map_category_to_search_index(category),
                item_count=min(limit, 10),
            )
            return self._convert_to_affiliate_products(results)
```

### Pattern 2: Config Settings Migration
**What:** Replace AWS credential settings with Creators API credential settings.
**When to use:** In `config.py` and `.env` files.
**Example:**
```python
# OLD (remove these)
AMAZON_ACCESS_KEY: str = Field(default="", description="Amazon PA-API Access Key")
AMAZON_SECRET_KEY: str = Field(default="", description="Amazon PA-API Secret Key")

# NEW (add these)
AMAZON_CREDENTIAL_ID: str = Field(default="", description="Amazon Creators API Credential ID")
AMAZON_CREDENTIAL_SECRET: str = Field(default="", description="Amazon Creators API Credential Secret")
```

### Pattern 3: Graceful Degradation (Existing Pattern -- Keep)
**What:** When API is disabled or credentials missing, fall back to curated links then search URLs.
**When to use:** Always -- the existing mock/curated data path is the primary production path today.
**Example:**
```python
# This pattern already exists and should NOT change:
if self.api_enabled:
    return await self._search_real_api(...)
else:
    return await self._search_mock_data(...)  # curated links -> search URLs
```

### Anti-Patterns to Avoid
- **Hand-rolling OAuth2 token refresh:** The library handles this internally. Do not add Redis-based token caching alongside the library -- it will double-cache and create stale token issues.
- **Keeping AWS Signature V4 as fallback:** The PA-API endpoint dies on May 15. There is no reason to keep dual-path API code. Remove it completely.
- **Creating a new provider class:** Do NOT create a separate `amazon_creators_provider.py`. Modify the existing `amazon_provider.py` in place. The provider registry name stays `"amazon"`, the loader init map stays the same pattern.
- **Caching or proxying Amazon images:** Amazon CDN URLs are intended for direct hotlinking. Do not download, cache, or re-host product images -- this violates Amazon's TOS and is unnecessary.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OAuth2 token acquisition + refresh | Custom token manager with Redis caching | `python-amazon-paapi` library (handles internally) | Token lifecycle includes edge cases: expiry drift, concurrent refresh, retry on 401; library handles all of this |
| AWS Signature V4 signing | Keep existing HMAC code | Remove entirely | PA-API endpoint dies May 15, 2026; signature code becomes dead code |
| Request parameter casing conversion | Manual PascalCase-to-camelCase mapping | `python-amazon-paapi` library (handles internally) | Library accepts Python-style kwargs and translates to API-expected casing |
| Response parsing for Creators API | Custom JSON traversal | Library's typed response objects | Library returns objects with `.item_info.title.display_value`, `.offers.listings[0].price.amount` etc. |
| Request throttling | Custom rate limiter | Library's `throttling` parameter | Built-in with configurable delay (default 1s between requests) |

**Key insight:** The `python-amazon-paapi` library abstracts away every difference between PA-API v5 and Creators API. From the caller's perspective, the API surface is identical -- `search_items()`, `get_items()` -- just with different constructor parameters (credential_id/credential_secret instead of access_key/secret_key).

## Common Pitfalls

### Pitfall 1: 10 Qualifying Sales Requirement
**What goes wrong:** Creators API returns empty results or 403 errors despite valid credentials.
**Why it happens:** Amazon requires at least 10 qualifying sales within the past 30 days for API access eligibility. New or low-traffic associates may not meet this threshold.
**How to avoid:** Verify the associate account has sufficient qualifying sales before migration. If not, the curated data fallback path must remain the primary production path.
**Warning signs:** API returns empty `items_result` or authentication errors despite correct credentials.

### Pitfall 2: Credential Version Confusion (v2 vs v3)
**What goes wrong:** OAuth2 token request fails with authentication errors.
**Why it happens:** Amazon issues two credential versions: v2.x (Cognito-based, form-encoded + Basic auth header) and v3.x (LwA-based, JSON body). The `python-amazon-paapi` library supports both but the initialization differs. New credentials created after February 2026 are v3.x.
**How to avoid:** When creating credentials in Associates Central > Tools > Creators API, note the version. Pass `version="2.2"` or `version="3.0"` to the constructor accordingly. For new setups, use v3.
**Warning signs:** Token endpoint returns 400 or "invalid_client" errors.

### Pitfall 3: Regional Credential Scoping
**What goes wrong:** API works for US marketplace but fails for UK, DE, JP.
**Why it happens:** Creators API credentials are scoped by region, not marketplace:
- **NA region:** US, CA, MX, BR (one credential set)
- **EU region:** UK, DE, FR, IT, ES, NL, BE, EG, IN, IE, PL, SA, SE, TR, AE
- **FE region:** JP, SG, AU

Each region requires its own Credential ID + Secret pair.
**How to avoid:** For the current ReviewGuide.ai deployment (US-only based on `AMAZON_DEFAULT_COUNTRY=US`), a single NA credential set suffices. If expanding to other regions later, store region-specific credentials.
**Warning signs:** Works for US ASINs but returns "InvalidPartnerTag" for non-US marketplaces.

### Pitfall 4: Library Connection Lifecycle
**What goes wrong:** Connection pool exhaustion or "session closed" errors under load.
**Why it happens:** Creating a new `AsyncAmazonCreatorsApi` instance per request opens a new HTTP connection each time.
**How to avoid:** Use the async context manager pattern for request batching, or create a single long-lived instance stored on the provider. The library's connection pooling works best with `async with` blocks.
**Warning signs:** Increasing latency over time, connection timeout errors, `httpx` pool exhaustion warnings.

### Pitfall 5: Keeping Dead PA-API Code
**What goes wrong:** Config references `AMAZON_ACCESS_KEY`/`AMAZON_SECRET_KEY` that no one sets, code paths that can never execute, confusion for future developers.
**Why it happens:** Fear of breaking things during migration leads to "just add the new path alongside the old one."
**How to avoid:** Clean removal of all PA-API-specific code: `PAAPI_HOSTS`, `PAAPI_REGIONS`, `_send_paapi_request`, AWS Signature V4 signing, and the old config settings. The `AMAZON_API_ENABLED` flag stays (controls mock vs real mode) but the "real" path changes to Creators API.
**Warning signs:** `AMAZON_ACCESS_KEY` still in config.py after migration.

### Pitfall 6: Railway Environment Variable Update
**What goes wrong:** Migration works locally but fails on Railway deployment.
**Why it happens:** New env vars (`AMAZON_CREDENTIAL_ID`, `AMAZON_CREDENTIAL_SECRET`) not added to Railway. Old env vars (`AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`) still set but unused.
**How to avoid:** Update Railway env vars as part of the deployment step. Remove old vars, add new ones.
**Warning signs:** Backend logs show "Creators API credentials not configured" on Railway but works locally.

## Code Examples

Verified patterns from library documentation and project codebase:

### Initialization with AsyncAmazonCreatorsApi
```python
# Source: python-amazon-paapi PyPI docs (v6.2.0)
from amazon_creatorsapi import AsyncAmazonCreatorsApi, Country

async with AsyncAmazonCreatorsApi(
    credential_id="your_credential_id",
    credential_secret="your_credential_secret",
    tag="yoursite-20",
    country=Country.US,
    throttling=1.0,
) as api:
    # Search by keyword
    results = await api.search_items(keywords="wireless headphones")

    # Get specific items by ASIN
    items = await api.get_items(["B0CH9K2ZLF", "B08X4YMTPM"])
```

### Converting Library Response to AffiliateProduct
```python
# Maps library response objects to the existing AffiliateProduct dataclass
def _convert_to_affiliate_products(
    self, items: list, country_code: str
) -> List[AffiliateProduct]:
    results = []
    for item in items:
        asin = item.asin

        # Title
        title = "Unknown Product"
        if item.item_info and item.item_info.title:
            title = item.item_info.title.display_value

        # Image URL (direct Amazon CDN hotlink)
        image_url = ""
        if item.images and item.images.primary and item.images.primary.large:
            image_url = item.images.primary.large.url

        # Price
        price = 0.0
        currency = "USD"
        if item.offers and item.offers.listings:
            listing = item.offers.listings[0]
            if listing.price:
                price = listing.price.amount
                currency = listing.price.currency

        # Reviews
        rating = None
        review_count = None
        if item.customer_reviews:
            if item.customer_reviews.star_rating:
                rating = float(item.customer_reviews.star_rating.value)
            if item.customer_reviews.count:
                review_count = int(item.customer_reviews.count)

        # Affiliate link
        affiliate_link = generate_amazon_affiliate_link(
            asin=asin,
            country_code=country_code,
            associate_tag=self.associate_tag,
        )

        results.append(AffiliateProduct(
            product_id=asin,
            title=title,
            price=price,
            currency=currency,
            affiliate_link=affiliate_link,
            merchant="Amazon",
            image_url=image_url,
            rating=rating,
            review_count=review_count,
            condition="new",
            availability=True,
            source_url=affiliate_link,
        ))
    return results
```

### Config Settings Update
```python
# In backend/app/core/config.py -- replace PA-API settings
# Amazon Associates / Creators API
AMAZON_API_ENABLED: bool = Field(
    default=False,
    description="Enable real Amazon Creators API (requires API credentials)"
)
AMAZON_CREDENTIAL_ID: str = Field(
    default="",
    description="Amazon Creators API Credential ID (from Associates Central > Tools > Creators API)"
)
AMAZON_CREDENTIAL_SECRET: str = Field(
    default="",
    description="Amazon Creators API Credential Secret"
)
AMAZON_ASSOCIATE_TAG: str = Field(
    default="",
    description="Amazon Associate Tag (e.g., yoursite-20)"
)
AMAZON_ASSOCIATE_TAGS: str = Field(
    default="US:,UK:,DE:,FR:,JP:,CA:,AU:",
    description="Comma-separated country:tag pairs for regional affiliate tags"
)
AMAZON_DEFAULT_COUNTRY: str = Field(
    default="US",
    description="Default country code for Amazon links"
)
```

### Loader Update
```python
# In backend/app/services/affiliate/loader.py -- update _PROVIDER_INIT_MAP
"amazon": lambda: {
    "credential_id": settings.AMAZON_CREDENTIAL_ID,
    "credential_secret": settings.AMAZON_CREDENTIAL_SECRET,
    "country_code": settings.AMAZON_DEFAULT_COUNTRY,
    "associate_tag": settings.AMAZON_ASSOCIATE_TAG,
},
```

### Registry Decorator Update
```python
# In amazon_provider.py -- update required/optional env vars
@AffiliateProviderRegistry.register(
    "amazon",
    required_env_vars=[],
    optional_env_vars=["AMAZON_CREDENTIAL_ID", "AMAZON_CREDENTIAL_SECRET", "AMAZON_ASSOCIATE_TAG"],
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PA-API v5 with AWS Signature V4 | Creators API with OAuth2 Bearer tokens | April 2025 (announced), May 15 2026 (PA-API endpoint death) | Must migrate before deadline or lose all Amazon API access |
| AWS Access Key + Secret Key | Credential ID + Credential Secret (from Associates Central) | February 2026 (v3 credentials issued) | New credential type; old credentials stop working May 15 |
| PascalCase parameters (`PartnerTag`, `ItemIds`) | lowerCamelCase parameters (`partnerTag`, `itemIds`) | Creators API launch | Breaking change in request format; library handles translation |
| Offers V1 endpoint | Offers V2 endpoint | January 31, 2026 (V1 retired) | Already retired; Creators API uses V2 exclusively |

**Deprecated/outdated:**
- **PA-API v5 endpoint** (`webservices.amazon.com/paapi5/*`): Dies May 15, 2026. No extensions.
- **AWS Signature V4 for product data**: Replaced by OAuth2 bearer tokens.
- **Offers V1**: Already dead since January 31, 2026. Offers V2 (Creators API only) is the replacement.

## Migration Timeline

| Date | Event | Action Required |
|------|-------|----------------|
| January 31, 2026 | Offers V1 retired | Already past -- Creators API Offers V2 required for pricing data |
| April 30, 2026 | PA-API formally deprecated | Migration should be complete by this date |
| **May 15, 2026** | **PA-API endpoint retired** | **Hard deadline -- API calls to PA-API v5 will fail** |

**Current date:** March 25, 2026. **51 days remain** before the hard deadline.

## Open Questions

1. **Associate Account Qualifying Sales**
   - What we know: Amazon requires 10 qualifying sales in the past 30 days for Creators API access
   - What's unclear: Whether the ReviewGuide.ai Amazon Associates account meets this threshold
   - Recommendation: Check Associates Central dashboard before starting implementation. If threshold not met, the migration is still necessary (code-level), but testing against the live API will require meeting the threshold first. The curated data fallback ensures the app works regardless.

2. **Credential Version (v2 vs v3)**
   - What we know: v2.x uses Cognito auth, v3.x uses LwA auth. New credentials since Feb 2026 are v3.x.
   - What's unclear: Which version the project's credentials will be (depends on when they're created)
   - Recommendation: Create fresh credentials (will be v3.x). Pass `version="3.0"` or omit version (library auto-detects for recent versions). The `python-amazon-paapi` v6.2.0 supports both.

3. **Library Response Object Attribute Names**
   - What we know: Library returns typed objects with dot-access (e.g., `item.item_info.title.display_value`)
   - What's unclear: Exact attribute names may differ from the examples in the README for edge cases (missing data, null fields)
   - Recommendation: The conversion function must handle None checks at every level (item_info may be None, title may be None, etc.) -- same defensive pattern as the existing `_parse_paapi_response`.

4. **Creators API Endpoint Host**
   - What we know: The official docs are behind a JavaScript-rendered SPA that cannot be fetched. Third-party sources confirm OAuth2 via `https://api.amazon.com/auth/o2/token` for NA region.
   - What's unclear: The exact product data endpoint host (likely still `webservices.amazon.com` or a new host). The library abstracts this away.
   - Recommendation: Use the library; it handles endpoint routing internally. Do not try to construct raw API URLs.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 + pytest-asyncio 1.2.0 |
| Config file | `backend/tests/conftest.py` (exists -- mocks Redis + DB) |
| Quick run command | `cd backend && python -m pytest tests/test_amazon_provider.py -x -v` |
| Full suite command | `cd backend && python -m pytest tests/ -x -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AMZN-01 | Keyword search returns same data fields (title, price, image, ASIN, affiliate link) | unit | `python -m pytest tests/test_amazon_provider.py::test_search_items_returns_expected_fields -x` | Wave 0 |
| AMZN-01 | ASIN lookup returns product data | unit | `python -m pytest tests/test_amazon_provider.py::test_get_items_by_asin -x` | Wave 0 |
| AMZN-02 | Token refresh called before expiry (mock clock) | unit | `python -m pytest tests/test_amazon_provider.py::test_token_auto_refresh -x` | Wave 0 |
| AMZN-03 | Image URLs are Amazon CDN hotlinks (not cached/proxied) | unit | `python -m pytest tests/test_amazon_provider.py::test_image_urls_are_amazon_cdn -x` | Wave 0 |
| AMZN-04 | No AWS Signature V4 code in amazon_provider.py | unit (code inspection) | `python -m pytest tests/test_amazon_provider.py::test_no_aws_sigv4_code -x` | Wave 0 |
| AMZN-04 | No AMAZON_ACCESS_KEY / AMAZON_SECRET_KEY in config | unit (code inspection) | `python -m pytest tests/test_amazon_provider.py::test_no_legacy_config_vars -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_amazon_provider.py -x -v`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_amazon_provider.py` -- covers AMZN-01, AMZN-02, AMZN-03, AMZN-04 (does not exist yet)
- [ ] `python-amazon-paapi[async]==6.2.0` in requirements.txt -- needed for import in tests

## Sources

### Primary (HIGH confidence)
- [python-amazon-paapi PyPI](https://pypi.org/project/python-amazon-paapi/) - v6.2.0 release (March 12, 2026), API methods, async support, Creators API migration status
- [python-amazon-paapi GitHub](https://github.com/sergioteula/python-amazon-paapi) - Source code structure, initialization, search_items/get_items usage
- [Amazon PA-API v5 Docs](https://webservices.amazon.com/paapi5/documentation/) - Current (dying) API format, SearchItems/GetItems reference for comparison
- [Amazon Creators API Portal](https://affiliate-program.amazon.com/creatorsapi) - Official credential creation portal

### Secondary (MEDIUM confidence)
- [KeywordRush Migration Guide](https://www.keywordrush.com/blog/amazon-creator-api-what-changed-and-how-to-switch/) - lowerCamelCase parameter changes, regional credential scoping (NA/EU/FE), v2 vs v3 credential differences, verified against library behavior
- [WordPress.org Migration Thread](https://wordpress.org/support/topic/breaking-change-amazon-creators-api-migration-v6-0-0/) - Credential setup steps (Associates Central > Tools > Creators API), breaking change confirmation
- [Amazon Login with Amazon Docs](https://developer.amazon.com/docs/login-with-amazon/retrieve-token-other-platforms-cbl-docs.html) - OAuth2 token endpoint (`https://api.amazon.com/auth/o2/token`), token format (`Atc|...`), 3600s TTL
- [Amazon App Submission API Auth](https://developer.amazon.com/docs/app-submission-api/auth.html) - OAuth2 client_credentials grant flow, regional token endpoints (NA/EU/FE)

### Tertiary (LOW confidence)
- [Logie.ai Creators API Guide](https://logie.ai/news/amazons-2026-creator-api-guide/) - 10 qualifying sales requirement (not verified against official docs, but widely reported)
- [Oreate.ai Blog](https://www.oreateai.com/blog/navigating-amazons-product-advertising-api-a-shift-towards-creators-api/) - April 30, 2026 deprecation date (official retirement is May 15 per Amazon notice)

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - Library exists and is actively maintained (v6.2.0, March 2026), but internal token management is abstracted and could not be verified via official Amazon docs (SPA blocks scraping)
- Architecture: HIGH - Migration path is well-understood: same operations, different auth. Provider pattern in codebase is clean and modular.
- Pitfalls: MEDIUM - 10 qualifying sales requirement is widely reported but could not be verified against official Amazon documentation. Regional credential scoping confirmed by multiple sources.

**Research date:** 2026-03-25
**Valid until:** 2026-05-15 (hard deadline -- after this date, research is moot as PA-API is dead)
