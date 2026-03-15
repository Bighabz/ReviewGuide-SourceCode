# Skimlinks Integration Research

**Project:** ReviewGuide.ai
**Researched:** 2026-03-15
**Overall confidence:** MEDIUM-HIGH
(Most API structure verified via Apiary docs and official sources. Some rate limits and Product Key availability details LOW confidence — confirm with account manager.)

---

## Executive Summary

Skimlinks is the right call as a catch-all affiliate aggregator for ReviewGuide.ai. One integration covers 48,500+ merchants across 50+ networks (AWIN, CJ, Rakuten, Impact, ShareASale, Partnerize, Tradedoubler, Webgains, Commission Factory, Avantlink). The cost is 25% of affiliate revenue — Skimlinks keeps that, publishers receive 75%.

The critical architectural decision: **Skimlinks has two modes**, and only one works for an AI assistant backend.

- **JavaScript snippet** — auto-affiliates links client-side. Does NOT work with server-rendered AI responses.
- **Server-Side Link Wrapper** — wraps any merchant URL in `go.redirectingat.com/?id=PUBLISHER_ID&url=ENCODED_URL` without any API call. No rate limits. Works in FastAPI.

The Product Key API (product search with images + prices) is a separate product with a dedicated sales process — not self-serve. Treat it as a future enhancement, not a Day 1 requirement.

---

## 1. API Inventory

Skimlinks publishes documentation at `developers.skimlinks.com`. There are five distinct tools:

| Tool | Purpose | Self-Serve? | Auth |
|------|---------|-------------|------|
| JavaScript snippet | Client-side auto-affiliation | Yes | Publisher ID in script tag |
| Server-Side Link Wrapper | Construct affiliate URLs server-side | Yes | No API call — URL construction only |
| Merchant API | Query merchant list, commission rates, domains | Yes (with approval) | OAuth2 client credentials |
| Product Key API | Product search with images + prices + affiliate URLs | No — contact account manager | OAuth2 + publisher domain ID |
| Reporting API | Commission reports, performance analytics, Datapipe | Yes (with approval) | OAuth2 client credentials |

### Authentication (Merchant API + Reporting API + Product Key)

All API-based tools use the same OAuth2 client credentials flow:

```
POST https://authentication.skimapis.com/access_token
Body: {
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "grant_type": "client_credentials"
}
Response: { "access_token": "...", "timestamp": ..., "expiry_timestamp": ... }
```

Credentials are found in Skimlinks Hub at: Toolbox > API > API Authentication Credentials.
The token format is `{id}:{timestamp}:{hash}` — it is timestamp-based and will expire.

---

## 2. Server-Side Link Wrapper (PRIMARY INTEGRATION PATH)

This is how ReviewGuide.ai should generate affiliate links. No API call required at link-generation time.

### How It Works

Wrap any merchant URL in the Skimlinks redirect domain:

```
https://go.redirectingat.com/?id=PUBLISHER_SITE_ID&url=ENCODED_MERCHANT_URL&xs=1&xcust=TRACKING&sref=SOURCE_PAGE
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `id` | Yes | Your Skimlinks site ID (from https://accounts.skimlinks.com/sites, format: `12345X6789`) |
| `url` | Yes | Destination merchant URL, URL-encoded |
| `xs` | Yes | Set to `1` |
| `xcust` | No | Internal tracking ID (max 50 chars, alphanumeric + underscores + pipes only). Use this to pass session_id or conversation_id |
| `sref` | No | Source referrer URL — the page/context where the link appears. If not provided, HTTP referer header is used |

**Example:**

```python
from urllib.parse import urlencode, quote

def wrap_skimlinks(
    merchant_url: str,
    publisher_id: str,
    xcust: str = None,
    sref: str = None
) -> str:
    params = {
        "id": publisher_id,
        "url": merchant_url,
        "xs": "1",
    }
    if xcust:
        params["xcust"] = xcust[:50]  # max 50 chars
    if sref:
        params["sref"] = sref
    return "https://go.redirectingat.com/?" + urlencode(params)
```

**Key points:**
- Works entirely server-side. No JavaScript, no browser, no API call.
- Skimlinks checks if the destination domain is a monetizable merchant at redirect time.
- If the merchant is in the Skimlinks network, it injects the appropriate affiliate tracking.
- If not, the user is passed through to the destination URL with no affiliate tracking.
- The Merchant API can be used to pre-validate whether a domain is monetizable (avoids wrapping dead links).

**Confidence:** HIGH — URL structure confirmed via Drupal module issue tracker, Datafeedr documentation, and Skimlinks SDK examples. Multiple independent sources.

---

## 3. Merchant API

Purpose: query the list of merchants Skimlinks can monetize. Use this to pre-validate URLs before wrapping.

**Base URL:** `https://api-merchants.skimlinks.com/merchants/`

**Rate Limit:** 1,000 requests/hour per API key (implemented September 2022, per official changelog).

**What a merchant record contains:**

```
advertiser_id           Integer  — internal merchant ID
name                    String   — e.g., "Walmart"
domains                 List     — monetizable domains + subdomains
partner_type            String   — "standard", "preferred", or "vip"
verticals               List     — product categories
countries               List     — countries where program is active
calculated_commission_rate  Float   — 90-day trailing avg
calculated_conversion_rate  Float   — 90-day trailing avg
calculated_ecpc         Float    — effective cost per click
estimated_payment_days  String   — avg payout timeline
estimated_attribution_window  String — cookie duration
minimum_rate / maximum_rate  Objects — commission tiers (CPA/CPC/CPL)
metadata.logo_url       String   — merchant logo
metadata.description    String   — merchant description
```

**Practical use for ReviewGuide.ai:** Cache the full merchant/domain list in Redis (refreshed daily). At link-generation time, look up whether a product URL's domain is in that list before wrapping. This avoids wrapping links to non-Skimlinks merchants.

**Confidence:** HIGH — entity schema confirmed via Apiary documentation (`jsapi.apiary.io/apis/skimlinksmerchantapi`).

---

## 4. Product Key API (Product Search)

This is NOT the same as the link wrapper. It is a separate product — a real-time product search that returns product images, prices, availability, and pre-built affiliate URLs.

**Availability:** US, UK, Germany, France, Australia publishers only. Requires contact with a Skimlinks account manager to enable — not self-serve from the Hub.

**Confidence on availability:** MEDIUM — the Apiary docs are current, but the sales requirement means terms may vary. Verify before building against it.

### Endpoints

**Single product lookup:**
```
GET /v2/publisher/{publisher_id}/product
```

**Batch product lookup:**
```
POST /v1/publisher/{publisher_id}/products
Body: { "product_urls": [...], "product_ids": [...] }
```

**Authentication:** Same OAuth2 token as Merchant/Reporting APIs, plus a `publisher_domain_id` parameter.

### Request Parameters (single product)

| Parameter | Required | Description |
|-----------|----------|-------------|
| `publisher_id` | Yes | Your publisher ID |
| `access_token` | Yes | OAuth2 token |
| `publisher_domain_id` | Yes | Your domain ID |
| `product_url` | Conditional | URL to look up (one of url/upc/product_id required) |
| `upc` | Conditional | Product UPC |
| `product_id` | Conditional | Product ID |
| `product_keywords` | No | Keyword search fallback |
| `country_code` | No | Two-letter country code |
| `domains` | No | Pipe-separated whitelist (e.g., `amazon.com|bestbuy.com`) |
| `exclude_domains` | No | Pipe-separated blacklist |
| `alternatives_size` | No | Number of alternative merchants to return (e.g., 20) |
| `per_merchant_limit` | No | Max results per merchant |
| `sort_by` | No | Field to sort (e.g., `epc`) |

### Response Fields

```
product_name            String      — product title
product_brand           String      — manufacturer
description             String      — product description
product_images          Array       — [{value: "url", xsize: W, ysize: H}]
price                   Number      — current price
original_price          Number      — pre-sale price
currency                String      — ISO 4217
is_available            Boolean     — in-stock status
latest_availability     String      — last scraped
latest_price            Number      — most recent price
latest_ts_updated       Timestamp   — when last updated
sku                     String      — merchant SKU
upc / ean / gtin        String      — product codes
merchant_name           String      — retailer name
merchant_logo           String      — logo URL
advertiser_id           Integer     — merchant ID
country                 String      — two-letter code
product_url             String      — canonical product URL
affiliated_url          String      — pre-built Skimlinks affiliate URL (use this!)
product_alternatives    Array       — same product at other merchants
commission_rate         Float       — for this merchant
conversion_rate         Float       — for this merchant
ecpc                    Float       — effective cost per click
```

### Rate Limits

| Endpoint | Per-key limit | Default |
|----------|--------------|---------|
| Single product | 80/min, 5,000/hour | Standard |
| Batch products | 20/min, 1,000/hour | Standard |

Both limits can be increased on request to the account manager.

**Confidence:** HIGH — confirmed via Apiary docs at `jsapi.apiary.io/apis/skimlinksproducts`.

---

## 5. Reporting API

Purpose: performance data — commissions, clicks, revenue. Not needed for MVP but essential for monitoring affiliate health.

**Base URL:** Uses the same auth token as above.

**Endpoints:**

| Endpoint | Purpose |
|----------|---------|
| `/publisher/{id}/commission-report` | Raw transaction data |
| `/publisher/{id}/reports` | Aggregated by date/merchant/page/device/etc |
| `/publisher/{id}/aggregation/v1/link-report` | Click-level grouped by up to 4 dimensions |
| `/publisher/{id}/aggregation/v1/page-report` | Page impression data |
| `/publisher/{id}/trending-products` | Network-wide trending products |
| `/publisher/{id}/product-report` | Products purchased after clicks |
| `/publisher/{id}/payment-status` | Invoice and payment info |
| `/publisher/{id}/deactivated-merchants` | Merchants that left network |

**Rate Limits (confirmed):**

| Endpoint type | Per-key | Per-IP |
|--------------|---------|--------|
| Commission report | 40/min, 300/hour | 80/min, 500/hour, 1,000/day |
| Aggregated reports | 40/min, 500/hour | 80/min, 500/hour, 2,000/day |
| Multi-aggregated | 5/min, 100/hour | 10/min, 100/hour, 500/day |

Multi-aggregated endpoints stream responses in NDJSON format.

**Confidence:** HIGH — confirmed via Apiary auth docs.

---

## 6. Commission Structure

### Skimlinks Cut: 25% / Publisher Gets: 75%

This is consistent across all sources and verified by Skimlinks' own FAQ. No up-front cost. Revenue share only.

**Example math:**
- Merchant pays 8% commission on $100 sale = $8 gross
- Skimlinks retains $2 (25%)
- ReviewGuide.ai receives $6 (75%)

**This is the same model regardless of which underlying network** (CJ, AWIN, Rakuten, etc.). Skimlinks handles the network relationships.

### Payment Terms

- Minimum threshold: $65 USD / £50 / €55 / ¥8,000
- Payment schedule: monthly, end of month (if threshold met)
- Clearing timeline: ~92 days from transaction date (retailers take 60 days to confirm, then Skimlinks processes)
- Payment methods: Direct deposit or PayPal (US, EU, UK, JP); PayPal only for other regions

### Commission vs Direct Relationships

| Approach | Revenue kept | Overhead | Coverage |
|----------|-------------|----------|----------|
| Skimlinks (aggregator) | 75% | Minimal — 1 integration | 48,500+ merchants |
| Direct affiliate (CJ, Rakuten, etc.) | 100% | Per-advertiser applications, per-network integration | Hundreds per network |
| Direct merchant programs (Amazon Associates, etc.) | 100% | Separate application per program | 1 retailer per program |

**Recommendation for ReviewGuide.ai:** Use Skimlinks as the catch-all fallback. Keep direct integrations (Amazon, eBay, Booking.com, Viator) for programs where the 25% premium is justified by volume or exclusivity. This matches the decision already logged in PROJECT.md.

---

## 7. Networks Covered

Skimlinks aggregates 50+ affiliate networks. Confirmed list includes:

CJ Affiliate, AWIN, Rakuten Advertising, Impact, ShareASale, Partnerize, Avantlink, Pepperjam, Tradedoubler, Webgains, Commission Factory

**Notable major US merchants accessible via Skimlinks:**
- Home Depot (confirmed — has a Skimlinks merchant page)
- Walmart (network member — largest US retailer by revenue)
- Most mid-tier and specialty retailers that participate in any of the above 50+ networks

Amazon Associates is NOT part of Skimlinks. Amazon manages its own program. This is why Amazon requires a separate direct integration.

---

## 8. Publisher Approval

Skimlinks has a rigorous approval process:
- Only ~3% of applicants are accepted
- Manual review by their Network Quality team
- Decision within 2 business days
- Criteria: original product-focused content, significant traffic from North America / Europe / APAC, adherence to FTC/ASA affiliate disclosure requirements

**For ReviewGuide.ai specifically:** The editorial AI shopping assistant use case aligns well with Skimlinks' publisher profile (they cite BuzzFeed, Condé Nast, Wirecutter, Vox, New York Magazine as customers). The affiliate disclosure already present in the codebase (`/privacy`, `/terms`) satisfies disclosure requirements. The risk of rejection is low.

**AI-generated content policy:** No explicit Skimlinks policy found on AI-generated content. Their criteria is "original content that adds value to readers" — an AI assistant generating personalized shopping recommendations fits this definition. **Flag as LOW confidence** — verify before submitting application.

---

## 9. Comparison: Skimlinks vs Sovrn Commerce vs Direct Networks

### Sovrn Commerce (formerly VigLink)

Sovrn was acquired by VigLink in 2018. Now branded "Sovrn Commerce."

| Capability | Skimlinks | Sovrn Commerce |
|------------|-----------|----------------|
| Merchant count | 48,500+ | ~12,500 |
| Networks aggregated | 50+ | Fewer (exact count not published) |
| Server-side link generation | Yes — URL wrapper, no API call | Yes — POST to `https://api.viglink.com/api/link/` |
| Product search API | Yes (Product Key — needs account manager) | Yes (Price Comparison Affiliated API) |
| Product search rate limit | 80/min (single), 20/min (batch) | 100 req/sec (price comparison) |
| Revenue share (publisher keeps) | 75% | Not publicly stated |
| Merchant pre-approval needed | No — auto-joined program | Yes — must apply individually to merchants |
| JavaScript fallback | Yes | Yes |
| US merchant coverage | Excellent | Good |

**Sovrn Commerce Price Comparison API** is worth noting — it's a well-documented server-side API:
```
GET https://comparisons.sovrn.com/api/affiliate/v3.5/sites/{site-api-key}/compare/prices/{market}/by/accuracy
Authorization: secret {SECRET_KEY}
Query params: barcode / plainlink / search-keywords + optional filters
Response includes: name, deeplink (affiliate URL), image, thumbnail, salePrice, retailPrice, currency, epc, affiliatable
```
Rate limit: 100 requests/second. This is significantly more permissive than Skimlinks' Product Key API.

**Verdict:** Skimlinks has 4x the merchant coverage and no per-merchant approval requirement. Use Skimlinks as primary. If product search (images + prices) matters more than merchant breadth, Sovrn has a more accessible product API.

### Direct Network Integrations (CJ, Rakuten, AWIN, Impact)

**Pros:**
- 100% commission retention (no 25% cut to Skimlinks)
- Often better commission rates from top-tier merchants
- Direct relationship enables custom commission structures

**Cons:**
- Publisher must apply per-advertiser within each network
- Each network requires separate integration
- Advertiser approval can take weeks; some decline new publishers
- ReviewGuide.ai's CJ integration currently only has Apple Vacations + Audiobooks (per PROJECT.md context)

**Recommendation:** Continue using CJ for any specifically approved advertisers. Use Skimlinks as the fallback layer for everything else. When volume justifies it (e.g., Walmart, Best Buy, Target), negotiate direct rates through their respective networks.

---

## 10. Implementation Architecture for ReviewGuide.ai

### Recommended Approach (Two-Layer Strategy)

```
Product URL (from eBay search, SerpAPI, or CJ)
         │
         ▼
Does this URL come from a provider we have
a direct affiliate relationship with?
(Amazon, eBay, CJ approved advertiser, Booking.com, etc.)
         │
    YES  │  NO
         │   │
         │   ▼
         │  Is this domain in Skimlinks merchant cache?
         │   (Redis: merchant domain list, TTL 24h)
         │       │
         │   YES │  NO
         │       │   │
         │       │   └── Return plain URL (no affiliate)
         │       ▼
         │  Wrap with go.redirectingat.com
         │  (server-side, no API call)
         ▼
    Use existing provider link
    (already has affiliate tracking)
```

### FastAPI Provider Implementation

The existing `BaseAffiliateProvider` + `AffiliateProviderRegistry` pattern supports adding a Skimlinks provider cleanly. However, Skimlinks is architecturally different: it is a link wrapper, not a product search API.

**Two implementation options:**

**Option A: Skimlinks as a standalone provider wrapping other search results**
- SkimlinksMerchantValidator — fetches+caches merchant domain list from Merchant API
- SkimlinksLinkWrapper — pure URL transformation (no network call)
- SkimlinksProductKeyClient — optional, for product search once Product Key is enabled

**Option B: Skimlinks as a post-processing middleware in AffiliateManager**
- After aggregating results from all providers (eBay, CJ, etc.), pass any non-affiliated URLs through Skimlinks wrapper
- Cleaner separation of concerns for ReviewGuide.ai's use case

Option B is recommended because Skimlinks is fundamentally a link monetization layer, not a product catalog. The existing providers handle product discovery; Skimlinks monetizes links that other providers can't cover.

### Required Environment Variables

```env
SKIMLINKS_PUBLISHER_ID=12345X6789      # From accounts.skimlinks.com/sites
SKIMLINKS_CLIENT_ID=abc123             # From Toolbox > API > Auth Credentials
SKIMLINKS_CLIENT_SECRET=xyz789         # From Toolbox > API > Auth Credentials
SKIMLINKS_API_ENABLED=true             # Feature flag (default false)

# Optional — only if Product Key API is enabled
SKIMLINKS_DOMAIN_ID=67890              # publisher_domain_id for Product Key
```

### Merchant Domain Cache

Fetch the Skimlinks merchant domain list and store in Redis:

```python
# Pseudocode
async def refresh_merchant_cache():
    """Refresh Skimlinks merchant domain list. Run daily via cron or startup."""
    access_token = await get_skimlinks_token()
    merchants = await fetch_all_merchants(access_token)  # paginate as needed

    domain_set = set()
    for merchant in merchants:
        for domain in merchant["domains"]:
            domain_set.add(domain.lower())

    await redis.set(
        "skimlinks:merchant_domains",
        json.dumps(list(domain_set)),
        ex=86400  # 24h TTL
    )
```

### Link Construction

```python
from urllib.parse import urlencode

SKIMLINKS_REDIRECT_BASE = "https://go.redirectingat.com/"

def build_skimlinks_url(
    merchant_url: str,
    publisher_id: str,
    xcust: str = None,  # use conversation_id or session_id
    sref: str = "https://reviewguide.ai"
) -> str:
    params = {
        "id": publisher_id,
        "url": merchant_url,
        "xs": "1",
        "sref": sref,
    }
    if xcust:
        # Max 50 chars, alphanumeric + underscore + pipe only
        safe_xcust = "".join(c for c in xcust if c.isalnum() or c in "_|")[:50]
        params["xcust"] = safe_xcust
    return SKIMLINKS_REDIRECT_BASE + "?" + urlencode(params)
```

---

## 11. Pitfalls

### Critical

**P1: JavaScript-only assumption**
The most widely documented Skimlinks integration is the JS snippet. Multiple blog posts and tutorials only describe JS. The server-side link wrapper is documented but less prominent. If you follow the quickstart guide, you will build the wrong integration for an AI backend.
Prevention: Use `go.redirectingat.com` URL wrapping (described in section 2 above). Never use the JS snippet in the FastAPI backend.

**P2: Merchant domain validation gap**
Without pre-validating domains against the Skimlinks merchant list, you will wrap links to non-Skimlinks merchants. Those links will still redirect fine (Skimlinks passes through non-monetizable URLs), but you lose the ability to detect coverage gaps.
Prevention: Maintain the Redis merchant domain cache and validate before wrapping.

**P3: Amazon is not in Skimlinks**
Amazon Associates operates separately and never joined Skimlinks or any aggregator. Any Amazon URL wrapped in `go.redirectingat.com` will pass through without affiliate tracking.
Prevention: Route Amazon product URLs through the direct Amazon provider, never through Skimlinks wrapper.

**P4: Commission clearing delay**
90-day clearing window means you will not see affiliate revenue in your first 3 months post-launch.
Prevention: Plan cash flow accordingly. Do not rely on affiliate revenue for operational expenses in the first quarter.

### Moderate

**P5: Product Key requires account manager**
The product search API (images, prices, affiliated_url) is not self-serve. You need to contact Skimlinks and be approved separately for this capability.
Prevention: Don't build your product carousel or Editor's Picks feature assuming Product Key will be available at launch. Use existing eBay/CJ product data for those features until Product Key is approved.

**P6: Publisher approval is selective**
3% acceptance rate. If you are rejected, the entire Skimlinks strategy fails.
Prevention: Apply as early as possible. Ensure the site has substantial editorial content before applying. The existing browse pages and chat functionality should qualify.

**P7: 25% revenue share compounds with network fees**
Some affiliate networks (AWIN in particular) charge their own publisher-side transaction fee. When Skimlinks routes through AWIN, the effective publisher cut may be less than 75% of the headline commission rate.
Prevention: For high-volume merchants where you can negotiate direct, prefer direct relationships over Skimlinks routing.

**P8: Rate limit on Merchant API**
1,000 calls/hour is adequate for cache refresh but not for per-request domain validation.
Prevention: Cache the merchant domain list in Redis and do set lookup, never call the Merchant API per product link.

### Minor

**P9: Token expiry**
The OAuth2 access token is timestamp-based. It will expire.
Prevention: Cache the token and refresh proactively before expiry using `expiry_timestamp` from the token response. Use a background task or token manager class.

**P10: xcust tracking limit**
50 characters maximum, alphanumeric + underscore + pipe only. UUIDs (36 chars with hyphens) need character sanitization.
Prevention: Strip hyphens from UUID or use a shorter identifier format.

---

## 12. Data Availability Summary

| Data type | Skimlinks Link Wrapper | Skimlinks Product Key API | Sovrn Comparison API |
|-----------|----------------------|--------------------------|---------------------|
| Affiliate URL | Yes — via URL wrapping | Yes — `affiliated_url` field | Yes — `deeplink` field |
| Product image | No | Yes — `product_images` array | Yes — `image` + `thumbnail` |
| Current price | No | Yes — `price`, `latest_price` | Yes — `salePrice`, `retailPrice` |
| Product title | No | Yes — `product_name` | Yes — `name` |
| In-stock status | No | Yes — `is_available` | Partial |
| Alternative merchants | No | Yes — `product_alternatives` | Yes — multiple results per query |
| Commission rate | No | Yes — `commission_rate` | Yes — `epc` |
| Merchant coverage | 48,500+ merchants | Same, filtered for Product Key partners | ~12,500 merchants |
| Self-serve | Yes | No — account manager | Yes |

**Bottom line:** The link wrapper alone (self-serve, Day 1) solves the monetization coverage problem. Product Key (requires approval) solves the product data problem. For Editor's Picks on browse pages, Product Key or Sovrn's API is needed.

---

## Sources

- Skimlinks Developer Portal: https://developers.skimlinks.com/
- Reporting API Apiary docs: https://jsapi.apiary.io/apis/skimlinksreporting/introduction/authentication/example:-getting-the-access-token-in-rest-api-client-applications.html
- Merchant API entity schema: https://jsapi.apiary.io/apis/skimlinksmerchantapi/introduction/entities/merchant.html
- Product Key API Apiary docs: https://jsapi.apiary.io/apis/skimlinksproducts/introduction/product-key-api/overview.html
- Merchant API rate limit changelog (2022): https://support.skimlinks.com/hc/en-us/articles/6993058288541-September-12-2022-Changes-to-Merchant-and-Commissions-APIs
- Link Wrapper URL format (Drupal module): https://www.drupal.org/project/skimlinks/issues/2934095
- Link format (Datafeedr): https://datafeedrapi.helpscoutdocs.com/article/33-replace-affiliate-link-with-a-skimlinks-link
- Commission structure: https://support.skimlinks.com/hc/en-us/articles/223835508-How-much-does-Skimlinks-charge
- Payment terms: https://www.skimlinks.com/blog/money-money-money-we-answer-common-publisher-questions-about-skimlinks-payments-and-commissions/
- Networks covered: https://advertisers.skimlinks.com/hc/en-us/articles/4408489869841-Which-affiliate-networks-does-Skimlinks-work-with
- Skimlinks Python SDK (official, Python 2.7): https://github.com/skimhub/skimlinks-sdk
- Ruby gem wrapper with response fields: https://www.rubydoc.info/gems/skimlinks/1.0.1
- Publisher approval criteria: https://www.skimlinks.com/blog/the-skimlinks-approvals-process/
- Sovrn Commerce link check API: https://developer.sovrn.com/reference/link
- Sovrn Commerce price comparison API: https://developer.sovrn.com/reference/product-affiliate-api
- Skimlinks vs Sovrn comparison: https://mrwebcapitalist.com/skimlinks-vs-viglink-which-one-is-better/
- AI affiliate network comparison: https://www.getchatads.com/blog/five-best-affiliate-networks-for-ai-shopping-assistants/
- W3Techs market share: https://w3techs.com/technologies/comparison/ad-commissionjunction,ad-linkshare,ad-skimlinks
