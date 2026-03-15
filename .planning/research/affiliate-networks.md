# Affiliate Network API Research

**Domain:** Affiliate network APIs for AI shopping assistant
**Researched:** 2026-03-15
**Overall confidence:** HIGH (Impact, Awin, Amazon Creators), MEDIUM (Rakuten, Viator, Booking.com, TravelPayouts)

---

## Context

This research covers adding Impact.com, Rakuten Advertising, Awin, Amazon (PA-API → Creators API), Booking.com, Viator, and TravelPayouts to the existing affiliate provider system. The codebase already has a clean `BaseAffiliateProvider` ABC with `search_products`, `generate_affiliate_link`, and `check_link_health` methods. All new providers slot into this registry pattern via `@AffiliateProviderRegistry.register(...)`.

---

## 1. Impact.com

### Authentication
- **Method:** HTTP Basic Auth
- **Credentials:** Account SID (username) + Auth Token (password)
- **Endpoint base:** `https://api.impact.com/Mediapartners/<AccountSID>/`
- All requests over HTTPS required; plain HTTP fails
- Scoped tokens available for fine-grained permission control

### Product Search — YES, full keyword search
- **Endpoint:** `GET /Mediapartners/<AccountSID>/Catalogs/ItemSearch`
- **Query parameters:**
  - `Keyword` — searches all item attributes (equivalent of our `query` field)
  - `Query` — supports operators: `>`, `>=`, `<`, `<=`, `=`, `!=`, `~`, `AND`, `OR`, `IN`, `NOT IN`
  - Filter fields: `Name`, `Manufacturer`, `CurrentPrice`, `DiscountPercentage`, `Gtin`, `Color`, `Size`, `StockAvailability` (In Stock / Out of Stock / Back Order / Pre Order / Limited Availability), `Gender` (Male / Female / Unisex)
  - `SortBy`: CatalogItemId, Manufacturer, CurrentPrice, StockAvailability, Gtin, Gender
  - `PageSize`: defaults to 100
- **Response fields:** Id, CatalogId, CampaignId, CatalogItemId, Name, Description, CurrentPrice, OriginalPrice, DiscountPercentage, Currency, StockAvailability, EstimatedShipDate, Color, Size, Gender, Material, Pattern, Weight, Condition, Gtin, Asin, Mpn, Sku, Url, ImageUrl, AdditionalImageUrls, Categories, shipping info
- **NOTE:** Must be on catalog API v12 or higher — v11 and older are deprecated and will return an error

### Link Generation — YES
- **Endpoint:** `POST /Mediapartners/<AccountSID>/TrackingLinks` (create tracking link)
- Tracking links carry full attribution

### Rate Limits — HIGH confidence
| Group | Limit |
|-------|-------|
| Product Search (`/Catalogs/ItemSearch`, `/Catalogs/*/Items`) | 3,000 requests/hour |
| Actions, Clicks, performance detail | 500 requests/hour |
| Performance aggregate reports | 250 requests/hour |
| All other endpoints | 1,000 requests/hour |
| ReportExport | 100 requests/day |
| ClickExport | 10 requests/day |

- Returns `429 Too Many Requests` when exceeded
- Response headers: `X-RateLimit-Limit-hour`, `X-RateLimit-Remaining-hour`, `RateLimit-Reset`, `Retry-After`
- Rate limits "subject to change at any given time"

### Integration Assessment
- Most full-featured catalog search of all networks researched
- Rich product metadata including GTIN/ASIN cross-references
- Direct product data — not just link generation
- **Env vars needed:** `IMPACT_ACCOUNT_SID`, `IMPACT_AUTH_TOKEN`

---

## 2. Rakuten Advertising (LinkShare)

### Authentication
- **Method:** OAuth 2.0 Bearer token (password grant)
- **Token endpoint:** `POST /token` with `grant_type=password`
- Response: `access_token`, `expires_in` (3600 seconds), `refresh_token`, `token_type: bearer`
- Credentials: Client ID + Client Secret from Developer Portal application
- If token unused for 6 months, it is erased

### Product Search — YES, but XML-only
- **Endpoint:** The Product Search API (accessible at `developers.rakutenadvertising.com`)
- **Format:** XML only (no JSON support for product search responses)
- **Max results:** 5,000 per call, no limit on maximum page
- Search by keywords, filter by advertiser, price range
- Products include: name, description, price, sale price, category, image URL, affiliate tracking URL (buy URL embedded in response)

### Link Generation — YES, dedicated API
- **Deep Links API** — generates valid trackable affiliate deep links
- Endpoint documented at `developers.rakutenadvertising.com/guides/deep_link`
- Custom `u1` tracking value (sub-ID) supported
- Provides confidence that generated links are "valid and eligible for commission tracking"

### Rate Limits — MEDIUM confidence
- Product Search API: **100 calls/minute** (confirmed from help center)
- Other reports: 100 calls/minute per report type
- Token expires in 1 hour; refresh token flow required

### Integration Assessment
- XML parsing required (same pattern as existing CJ provider — already have `_parse_xml_response`)
- Buy URL likely embedded directly in product search response (same as CJ)
- Deep Links API is separate from product search
- **Env vars needed:** `RAKUTEN_CLIENT_ID`, `RAKUTEN_CLIENT_SECRET`, `RAKUTEN_SITE_ID`

---

## 3. Awin

### Authentication
- **Method:** Bearer token (OAuth2)
- Token generated at `https://ui.awin.com/awin-api`
- Token is personal user-level (not publisher-specific)
- API base: `https://api.awin.com`

### Product Search — FEED-BASED, not real-time search
- **Critical distinction:** Awin does NOT have a keyword product search API endpoint
- Product access is via **data feed download** (bulk CSV/JSONL per advertiser)
- **Feed download endpoint:** `GET https://api.awin.com/publishers/{PUBLISHER_ID}/awinfeeds/download/{ADVERTISER_ID}-{VERTICAL}-{LOCALE}`
- Feed formats: Legacy CSV (Awin format) or Enhanced (Google Shopping JSONL format)
- Feed fields: pid, name, description, price, brand, upc, ean, mpn, isbn, purl (deep_link), imgurl, currency, delcost, instock, stockquant, condition, colour, dimensions, category, and more
- Feeds are per-advertiser — you must know which advertisers you want to pull from
- Publisher can check which programmes they have active relationships with via API

### Link Generation — YES, batch deep link creation
- **Endpoint:** `POST` to generate tracking link at `https://api.awin.com`
- Generates Awin tracking links based on advertiser ID + destination URL
- **Batch support:** Up to 100 links per request
- **Important limitation:** "Not compatible with real-time link creation in the browser" — designed for bulk/pre-generation, not on-the-fly per-user requests
- Deep links: must pass the destination URL + advertiser ID; Awin applies the correct prefix/suffix per advertiser settings

### Rate Limits — HIGH confidence
- **Feed downloads:** 5 requests/minute, no concurrent requests to same advertiser
- **Publisher API (general):** 20 requests/minute per user
- Different key for feed API vs Publisher API

### Integration Assessment
- **Most complex to integrate** for product search — no real-time search
- Workflow: periodically ingest feeds → store locally → search local DB → generate link on demand
- Link generation is NOT suitable for real-time per-query use (batch only)
- For this AI assistant, Awin is best suited for: pre-seeded product database from specific advertiser relationships, not live query-time search
- **Env vars needed:** `AWIN_OAUTH_TOKEN`, `AWIN_PUBLISHER_ID`

---

## 4. Amazon (PA-API 5.0 → Creators API)

### CRITICAL: PA-API is being deprecated

**PA-API 5.0 deprecation timeline:**
- **January 31, 2026:** Offers V1 retired (already retired)
- **April 30, 2026:** PA-API deprecated — stop new integrations NOW
- **May 15, 2026:** PA-API v5 endpoint retired entirely
- **Current state (March 2026):** PA-API is in its final weeks; the existing `amazon_provider.py` is on borrowed time

**Migrate to Amazon Creators API.** The existing implementation in `amazon_provider.py` uses AWS Signature V4 with `AMAZON_ACCESS_KEY`/`AMAZON_SECRET_KEY` — this will stop working by May 2026.

### Amazon Creators API Authentication (replacement)
- **Method:** OAuth 2.0 client-credentials flow
- Tokens valid ~1 hour
- New credential type: `Credential ID` + `Credential Secret` (NOT AWS keys)
- Create credentials in Associates Central → Creators API section → "Create App" → "Add New Credential"
- **Region-based credentials** (not marketplace-specific): one credential set covers all locales in a region:
  - NA region: US, Canada, Mexico, Brazil
  - EU region: UK, Germany, France, Italy, Spain, others
  - FE region: Japan, Singapore, Australia
- camelCase field names (`itemIds` not `ItemIds`, `partnerTag` not `PartnerTag`)
- Official docs: `https://affiliate-program.amazon.com/creatorsapi/docs/`

### Approval Requirements — HIGH confidence (strict)
- Must be an approved Amazon Associate
- **10 qualified shipped sales in trailing 30 days** to gain and maintain API access
- Requirement is per region (NA, EU, FE) — need 10 sales in each region for that region's access
- Access suspended after 30 consecutive days without qualified sales; returns within 2 days after sales resume
- "Qualifying sales" = shipped items (1 order with 5 items = 5 qualifying sales)
- Not accepting new PA-API customers — new projects must onboard to Creators API directly

### Product Search Capabilities
- Keyword-based product search (same operations as PA-API: Search, Get, Variations)
- Returns: title, price, availability, images, affiliate links, review count and rating
- Max 10 results per call (same as PA-API)
- SearchIndex categories supported
- Brand, price range filters supported

### Image Policy — HIGH confidence, strict rules
- Images ONLY obtainable via API (PA-API or Creators API) — no downloading or re-hosting
- Every image **must link directly to the relevant Amazon product page**
- Images cannot be displayed alone without links
- Images used strictly for product promotion only
- Cannot cache or host images on own infrastructure
- Must display via hotlink (direct URL from API response)

### Rate Limits — HIGH confidence
- **Starting:** 1 TPS (transactions per second), 8,640 TPD (per day) — for first 30 days
- **Scales with revenue:** 1 TPS per $4,320 shipped item revenue in previous 30 days
- **Maximum:** 10 TPS
- TPD cap: even if TPS allows, once daily limit exhausted, requests throttle
- This means a new/low-volume account gets ~1 request/second

### Integration Assessment
- **Immediate action required:** Update `amazon_provider.py` to Creators API before May 2026
- The core product search interface stays the same (search/get/variations)
- Authentication is the biggest change — swap AWS Sig V4 for OAuth 2.0 client credentials
- Region-based credentials simplifies multi-country logic
- Image policy is the hardest constraint for this application: all Amazon images must be hotlinked, not cached
- **Env vars to add:** `AMAZON_CREATORS_CREDENTIAL_ID`, `AMAZON_CREATORS_CREDENTIAL_SECRET`
- **Env vars to retire:** `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`

---

## 5. Booking.com Affiliate (Demand API)

### Authentication
- **Method:** API Key + Affiliate ID header on every request
- `API-key` header + `X-Affiliate-Id` header
- Maximum 2 active API keys per account at once
- Obtain credentials via Partner Centre after approval

### Approval Process — MEDIUM confidence
- Must apply as a Managed Affiliate Partner via online form
- Multi-stage approval: application → present integration project → account activation
- **Current status (March 2026):** Applications for connectivity solutions paused due to T&C update; regular affiliate partnership still open
- Once approved, API keys and Affiliate ID issued through Partner Centre

### Product Search — YES, hotel availability search
- **Endpoint type:** RESTful, HTTPS POST, JSON responses
- **Search endpoint:** `/v3/accommodation/search` (Demand API v3+)
- Search parameters: destination, check-in/check-out dates, number of rooms, adults/children
- Returns: cheapest available product per property by default
- Location filter triggers popularity-sorted results instead of price-sorted
- Optional "extras" parameter for additional data: `description`, `facilities`, `payment`, `photos`, `policies`, `rooms`
- Also: availability check, reviews endpoint, property details

### Link Generation — YES, URL parameter-based
- Affiliate link format: `https://www.booking.com/hotel/{country}/{property-slug}.html?aid={AFFILIATE_ID}`
- Deep link builder constructs links to specific property pages
- URL parameters for pre-filled search: `checkin`, `checkout`, `no_rooms`, `group_adults`
- Label parameter for link-level tracking: `label={custom_label}`
- App deep link format: `booking://hotel/{hotel_id}?affiliate_id={AFFILIATE_ID}`
- No server-side link generation API — links are constructed by concatenating parameters

### Rate Limits — MEDIUM confidence
- Sandbox: **50 requests/minute**
- Production: contact Account Manager for specific limits (not publicly documented)
- `429 Too Many Requests` response; access restricted for ~1 minute before reset

### Integration Assessment
- Best for travel/hotel use case specifically (aligns with existing travel workflow)
- The Demand API is separate from the affiliate program links — the API returns property data, and links are self-constructed with `?aid=` parameter
- Simpler than other networks: no complex link generation API needed
- Existing `booking_provider.py` in travel providers may already handle parts of this
- **Env vars needed:** `BOOKING_API_KEY`, `BOOKING_AFFILIATE_ID`

---

## 6. Viator Partner Affiliate API

### Authentication
- **New-style (recommended):** API key in header (required for booking cancellation endpoints)
- **Legacy:** API key as query parameter (still supported but deprecated path)
- Immediate Basic Access upon affiliate account creation — no approval wait

### Access Tiers — HIGH confidence
| Tier | Access Level | Requirements |
|------|-------------|--------------|
| Basic | Product summaries, search, images, pricing, ratings | Immediate on signup |
| Full Access | All Basic + real-time availability check (`/availability/check`) + reviews | Authorization by Viator required |
| Full + Booking | All Full + in-site booking (customers transact on your site) | Authorization by Viator required |

### Product Search — YES, real-time
- **Endpoint:** `/products/search`
- Returns product summaries: title, short description, cover images, review ratings/counts, pricing
- Search filters: destination IDs, price range, date range, category tag IDs, flags (free cancellation, skip-the-line)
- **Pagination:** max 50 products per call (`"count": 50`), first page `"start": 1`, paginate with subsequent start values
- Separate freetext search endpoint: `/search/freetext`
- Additional endpoint: `/products/{product-code}` for full product details

### Link Generation — URL parameter-based (cookie attribution)
- Generate URL: any active viator.com URL + tracking parameters appended
- Cookie window: **30 days** — earn commission on any booking within 30 days of click
- Commission: 8% per booking (earned after experience is completed)
- Campaign tracking parameters: optional but recommended for analytics
- Cookie-based only — if user clears browser cache, attribution is lost

### Rate Limits — MEDIUM confidence
- Rolling 10-second window calculation
- `429 Too Many Requests` when exceeded
- Exact per-second limits not publicly documented

### Integration Assessment
- Best for activities/experiences/tours in travel domain
- Basic search is immediately available — no approval barrier
- Full availability check requires Viator approval
- Cookie-based tracking is simpler than network-based (no server-side link API needed)
- For this AI assistant: use Basic tier initially, request Full Access for real-time availability
- **Env vars needed:** `VIATOR_API_KEY`

---

## 7. TravelPayouts

### Authentication
- **Method:** API token in header (`X-Access-Token`) or query parameter (`token=`)
- Registration in TravelPayouts affiliate network required
- Separate token for flights API vs hotels API

### What It Covers
TravelPayouts is an umbrella platform for multiple travel affiliate programs. Key APIs:

**Flights (Aviasales API):**
- Real-time multi-city search: roundtrip, one-way, open-jaw
- Passenger types: adults (up to 9), children, infants
- Trip classes: Economy, Business
- Results include: prices from multiple booking agencies ("gates"), flight details, baggage, ratings
- Affiliate tracking: booking URLs in results from each "gate"
- Restriction: **automatic collection of all links is prohibited** — links only generated when user clicks "Buy"

**Hotels (Hotellook API):**
- Hotel search by destination, dates, guests
- Real-time availability and pricing

**Reference Data:**
- Countries, cities, airports, airlines, routes

### Rate Limits — MEDIUM confidence
- Flights API: **200 queries/hour per IP** (may be negotiated)
- Hotels (Hotellook): **60 requests/minute** default (increase by request to support)
- New API version released November 1, 2025 — recommended for new integrations
- As of June 2024, new rate limits introduced (exact tiers not publicly documented)

### Access Requirements
- Flight API: requires account + volume threshold (confirmed via email for higher limits)
- Hotels API: separate registration/approval from flights

### Link Generation — Results-embedded
- Booking URLs are included in API results from each "gate" (airline/OTA)
- The URL includes affiliate tracking by virtue of the token used to make the request
- No separate link creation step needed — the result URLs are already tracked

### Integration Assessment
- Strong for flights (complements Booking.com's hotel focus)
- Multiple search sources in single response (comparison-ready)
- Strict rule against bulk link harvesting (only generate links at click time)
- Works well with existing travel infrastructure
- **Env vars needed:** `TRAVELPAYOUTS_TOKEN`, optionally separate hotel token

---

## 8. Cross-Network Analysis

### Which Networks Offer True Product Search vs Just Link Generation

| Network | Real-time Product Search | Link Generation | Notes |
|---------|--------------------------|-----------------|-------|
| Impact.com | YES — keyword + filter | YES — tracking link API | Best catalog search coverage |
| Rakuten Advertising | YES — keyword, XML response | YES — Deep Links API | XML only |
| Awin | NO — feed-based only | YES — batch (100/req) | No real-time search |
| Amazon Creators API | YES — keyword + category | Self-constructed (`/dp/{ASIN}?tag=`) | Strict image policy |
| Booking.com Demand | YES — availability/hotel search | Self-constructed (`?aid=`) | Travel only |
| Viator | YES — product/experience search | URL parameter + cookie | Travel/activities only |
| TravelPayouts | YES — flights + hotels | URLs in results | Travel only |

### Common Patterns Across All APIs

**Authentication patterns:**
1. HTTP Basic Auth with static credentials (Impact.com) — simplest, no expiry
2. Bearer token, short-lived with refresh (Rakuten, Awin, Amazon) — must handle token refresh
3. API key in header (Viator, TravelPayouts, Booking.com) — simplest to implement

**Link construction approaches:**
1. **Links in search results** (CJ, Rakuten Product Search, TravelPayouts) — affiliate URL returned by API directly
2. **Self-constructed** (Amazon, Booking.com, Viator) — publisher builds URL with own identifier appended
3. **API-generated tracking links** (Impact.com, Awin, Rakuten Deep Links) — call a link API to wrap any destination URL

**Product data richness (rank order):**
1. Impact.com — most fields, GTIN/ASIN cross-refs, availability granularity
2. Amazon Creators API — rich (title, price, images, ratings, features)
3. Rakuten — solid (XML, price, image, buy URL)
4. CJ — solid (existing, XML, price, image, buy URL)
5. Awin — rich but batch/offline only
6. Travel APIs — domain-specific, not general products

### Can We Build a Unified Provider Interface?

**YES** — the existing `BaseAffiliateProvider` already defines the right abstraction:
- `search_products(query, category, brand, min_price, max_price, limit)` — all product-search networks support this
- `generate_affiliate_link(product_id, campaign_id, tracking_id)` — every network has some form
- `check_link_health(affiliate_link)` — HEAD request works universally

**Adaptations needed per provider:**

```
Impact.com:   search_products → /Catalogs/ItemSearch (v12)
              generate_affiliate_link → /TrackingLinks

Rakuten:      search_products → Product Search API (parse XML)
              generate_affiliate_link → Deep Links API
              _token_refresh() required (1h expiry)

Awin:         search_products → NOT FEASIBLE real-time
                               → alternatives:
                                 (a) pre-index feeds into local DB,
                                 (b) skip Awin for product search, use for link generation only
              generate_affiliate_link → batch link builder (workaround: single-item batch)

Amazon:       search_products → Creators API SearchItems
              generate_affiliate_link → self-construct /dp/{ASIN}?tag=
              CRITICAL: update before May 2026

Booking.com:  search_products → accommodation search (travel context only)
              generate_affiliate_link → construct URL with ?aid=

Viator:       search_products → /products/search
              generate_affiliate_link → append tracking params to viator.com URL

TravelPayouts: search_products → flights/hotels search
               generate_affiliate_link → URLs embedded in results
```

**Awin edge case:** Awin does not fit the `search_products` model without an intermediate feed ingestion step. Options:
1. Implement `AwinFeedIngester` that downloads and indexes feeds to Redis/Postgres, then `AwinAffiliateProvider.search_products` queries the local index
2. Use Awin only for its link generation (turn URLs from other sources into Awin tracking links)
3. Skip Awin product search entirely; use it only for link wrapping

---

## 9. Pitfalls and Critical Warnings

### CRITICAL: Amazon API Must Be Updated Before May 2026
The existing `amazon_provider.py` uses AWS Signature V4 with `AMAZON_ACCESS_KEY`/`AMAZON_SECRET_KEY`. These credentials are **incompatible with Creators API**. New credentials (Credential ID + Credential Secret) must be created in Associates Central. PA-API is retired May 15, 2026 — this is the highest-urgency item.

### Amazon Image Hotlinking Is Non-Negotiable
Amazon product images CANNOT be cached, stored, or re-hosted. They must be displayed via direct hotlink to Amazon's CDN URL. Any violation risks account termination. Current mock mode uses `placehold.co` placeholder images — this is fine for dev, but production must use direct API image URLs.

### Amazon 10-Sales Threshold Is Enforced Per Region
Meeting the threshold in the US does not grant UK access. Each region (NA, EU, FE) needs its own 10 qualified shipped sales. The `AMAZON_API_ENABLED` flag in config needs to account for this — consider per-region enable flags.

### Awin Link Builder Is NOT Real-Time
Awin explicitly states their link builder API "isn't compatible with real-time link creation in the browser." Building an Awin provider that calls their link API at query time will fail in production. Approach: either pre-generate tracking links during feed ingestion, or use affiliate link wrapping patterns.

### Rakuten Product Search Returns XML Only
Rakuten's Product Search API only returns XML (same as CJ). The existing `_parse_xml_response` pattern from `cj_provider.py` can be reused. The Rakuten XML schema differs from CJ's but the parsing approach is identical.

### Impact.com Catalog API Version Deprecation
Must use v12 or higher for catalog endpoints. v11 and older will return error responses. Ensure all API calls use the `/Mediapartners/<SID>/Catalogs/ItemSearch` v12 path.

### Booking.com Partnership Status (March 2026)
Connectivity solutions applications are paused as of the time of this research. Standard affiliate partnership is still available. The Demand API (v3+) requires Managed Affiliate Partner status. Factor in 1-4 week approval delay for new integrations.

### TravelPayouts Prohibits Bulk Link Collection
Links must only be generated when a user clicks a "Buy" button — not batch-harvested. Building a caching layer that pre-fetches and stores all flight booking URLs would violate their ToS.

### Amazon Rate Limits Scale With Revenue (Not Time)
New accounts start at 1 TPS. For a new deployment with low referral volume, this is effectively 1 request/second maximum. The AI assistant's product search flow must implement queuing/debouncing to avoid hitting this immediately. The existing Redis cache on CJ/Awin patterns must be extended to Amazon.

---

## 10. Implementation Recommendations

### Priority Order
1. **Update Amazon provider to Creators API** — deadline May 2026, highest urgency
2. **Impact.com** — best real-time product search, high rate limits (3,000/hour), rich data
3. **Rakuten Advertising** — solid product search, reuses CJ XML pattern
4. **Viator** — zero approval barrier for Basic tier, perfect for travel domain
5. **TravelPayouts** — complements Booking.com with flight search
6. **Booking.com** — approval process, but aligns with existing `booking_provider.py`
7. **Awin** — defer or implement with feed-ingestion architecture only

### Suggested Env Vars to Add

```env
# Impact.com
IMPACT_ACCOUNT_SID=
IMPACT_AUTH_TOKEN=

# Rakuten Advertising
RAKUTEN_CLIENT_ID=
RAKUTEN_CLIENT_SECRET=
RAKUTEN_PUBLISHER_SITE_ID=

# Awin
AWIN_OAUTH_TOKEN=
AWIN_PUBLISHER_ID=

# Amazon Creators API (replacing PA-API)
AMAZON_CREATORS_CREDENTIAL_ID=
AMAZON_CREATORS_CREDENTIAL_SECRET=
# Retiring: AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY

# Viator
VIATOR_API_KEY=

# Booking.com (may already exist partially)
BOOKING_API_KEY=
BOOKING_AFFILIATE_ID=

# TravelPayouts
TRAVELPAYOUTS_TOKEN=
```

### Token Refresh Pattern (for Rakuten, Amazon Creators)

Rakuten tokens expire in 1 hour; Amazon Creators tokens expire in ~1 hour. Both need the same pattern already used by eBay (`_get_oauth_token` with `token_expires_at` check and 5-minute buffer). This can be extracted into a shared `OAuthTokenMixin` base class to avoid duplication across Rakuten, Amazon Creators, and future networks.

### Feed Ingestion for Awin (if pursued)

A separate `AwinFeedIngester` service (run as a periodic background task via the existing `scheduler.py`) would:
1. Pull feed list for active advertiser relationships
2. Download JSONL/CSV feeds per advertiser
3. Parse and upsert products into a dedicated Postgres table
4. `AwinAffiliateProvider.search_products` then queries this local table

This is architecturally separate from the live-API providers and should be treated as a data pipeline, not an affiliate provider in the real-time sense.

---

## Sources

- [Impact.com Publisher API — Rate Limits](https://integrations.impact.com/impact-publisher/reference/rate-limits)
- [Impact.com — Search Catalog Items Endpoint](https://integrations.impact.com/impact-publisher/reference/search-catalog-items)
- [Impact.com — Authentication](https://integrations.impact.com/impact-publisher/reference/authentication)
- [Rakuten Advertising — Product Search API (Publisher Help)](https://pubhelp.rakutenadvertising.com/hc/en-us/articles/5949953174029-Product-Search-API)
- [Rakuten Advertising — Product Search API (Developer Portal)](https://developers.rakutenadvertising.com/guides/product_search)
- [Rakuten Advertising — Deep Links API](https://developers.rakutenadvertising.com/guides/deep_link)
- [Rakuten Advertising — Access Tokens](https://developers.rakutenadvertising.com/guides/access_tokens)
- [Awin — Link Builder API](https://www.awin.com/us/how-to-use-awin/link-builder-api)
- [Awin — Publisher API Introduction](https://help.awin.com/apidocs/introduction-1)
- [Awin — Product Feed Publisher Guide](https://help.awin.com/docs/product-feed-publisher-guide-intro)
- [Awin — Enhanced Feeds (Google Format API)](https://developer.awin.com/apidocs/retail-publisher-productapidocumentation-1)
- [Amazon PA-API 5.0 — Rate Limits](https://webservices.amazon.com/paapi5/documentation/troubleshooting/api-rates.html)
- [Amazon PA-API 5.0 — Register](https://webservices.amazon.com/paapi5/documentation/register-for-pa-api.html)
- [Amazon Creators API — Documentation Home](https://affiliate-program.amazon.com/creatorsapi/docs/)
- [Amazon Creators API — What Changed (keywordrush.com)](https://www.keywordrush.com/blog/amazon-creator-api-what-changed-and-how-to-switch/)
- [Amazon Associates Eligibility — 10-Sales Rule](https://www.keywordrush.com/blog/amazon-pa-api-associatenoteligible-error-is-there-a-new-10-sales-rule/)
- [Booking.com — Demand API](https://developers.booking.com/demand/docs/open-api/demand-api)
- [Booking.com — API V3 Partnership Hub](https://partnerships.booking.com/api-v3)
- [Booking.com — Rate Limiting](https://developers.booking.com/demand/docs/development-guide/rate-limiting)
- [Viator — Affiliate API Levels of Access](https://partnerresources.viator.com/travel-commerce/levels-of-access/)
- [Viator — New Product Search Capabilities](https://partnerresources.viator.com/travel-commerce/affiliate/search-api/)
- [Viator — Affiliate Attribution](https://partnerresources.viator.com/travel-commerce/affiliate/attribution/)
- [TravelPayouts — API Reference](https://travelpayouts.github.io/slate/)
- [TravelPayouts — API Rate Limits](https://support.travelpayouts.com/hc/en-us/articles/4402565416594-API-rate-limits)
