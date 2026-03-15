# Requirements: ReviewGuide.ai v1.0

**Defined:** 2026-03-15
**Core Value:** Conversational product discovery that searches live reviews and returns blog-style editorial responses with cross-retailer affiliate links.

## v1 Requirements

### Response Experience

- [ ] **RX-01**: First visible content (product cards) appears within 5 seconds of sending a query
- [ ] **RX-02**: Blog narrative streams token-by-token from OpenAI via SSE (not batch-then-chunk)
- [ ] **RX-03**: Affiliate product searches parallelized within each provider (asyncio.gather instead of sequential for loop)
- [ ] **RX-04**: Review search limited to top 3 products (down from 5) with per-product timeout
- [ ] **RX-05**: Review search and affiliate search run in parallel where data dependencies allow
- [ ] **RX-06**: product_compose eliminates redundant LLM calls (combine where possible, remove unnecessary ones)
- [ ] **RX-07**: Blog-style response includes inline affiliate buy links as markdown (e.g. "Check price on Amazon →")
- [ ] **RX-08**: Product cards render above blog narrative, arriving progressively via stream_chunk_data

### Bug Fixes

- [ ] **FIX-01**: Blog-style responses include clickable review source links (Wirecutter, Tom's Guide, Reddit, etc.)
- [ ] **FIX-02**: Product search returns results from multiple retailers, not just eBay
- [ ] **FIX-03**: Product cards display images from search results
- [ ] **FIX-04**: Static Amazon amzn.to affiliate links resolve correctly on browse pages
- [ ] **FIX-05**: Truncated affiliate link in menopause supplements category is corrected

### Product Search

- [ ] **SRCH-01**: Serper.dev shopping endpoint integrated as an affiliate provider returning products with images, prices, and merchant info
- [ ] **SRCH-02**: Serper shopping provider registered in AffiliateProviderRegistry and auto-discovered by loader
- [ ] **SRCH-03**: Serper shopping results cached in Redis to avoid duplicate API calls

### Amazon Migration

- [ ] **AMZN-01**: Amazon provider migrated from PA-API v5 (AWS Sig V4) to Creators API (OAuth2 client credentials) before May 15, 2026
- [ ] **AMZN-02**: OAuth2 token refresh with 1-hour expiry and 5-minute buffer implemented
- [ ] **AMZN-03**: Amazon product images served via direct CDN hotlink (no caching/re-hosting)
- [ ] **AMZN-04**: Existing Amazon search operations (keyword search, ASIN lookup) work identically after migration

### Affiliate Coverage

- [ ] **AFFL-01**: Skimlinks server-side link wrapper monetizes non-Amazon, non-eBay, non-CJ product URLs
- [ ] **AFFL-02**: Skimlinks merchant domain list cached in Redis (24h TTL) to avoid per-request API calls
- [ ] **AFFL-03**: Amazon URLs never passed through Skimlinks wrapper (Amazon not in network)
- [ ] **AFFL-04**: AffiliateManager applies Skimlinks as post-processing middleware after all providers return
- [ ] **AFFL-05**: Editor's Picks re-enabled on browse category pages with product images from available providers

### Conversational UX

- [ ] **UX-01**: Clarifier agent returns 2-4 tappable suggestion chips alongside prose questions
- [ ] **UX-02**: Suggestion chips rendered as buttons in chat UI, dispatch sendSuggestion event on click
- [ ] **UX-03**: "Top Pick" editorial block displayed above product carousel with: product name, headline reason, who it's for, who should look elsewhere
- [ ] **UX-04**: Comparison intent detected on follow-up messages, auto-triggers ComparisonTable for active shortlist
- [ ] **UX-05**: Product responses capped at 3-5 products (no 10+ product walls)

### Provider Expansion

- [ ] **PROV-01**: Impact.com affiliate provider integrated with keyword product search (3,000 req/hour)
- [ ] **PROV-02**: Viator Basic tier provider integrated for activity/experience search
- [ ] **PROV-03**: CJ advertiser applications submitted for high-value programs (Best Buy, Dell, Target, Wayfair, Nike)

## v2 Requirements

### Personalization

- **PERS-01**: Optional user accounts with saved search history and preferences
- **PERS-02**: "More like this / Not interested" feedback buttons on product cards
- **PERS-03**: Cross-session preference memory ("last time you preferred Sony")

### Price Intelligence

- **PRICE-01**: Price alerts — user sets target, notified when product drops below
- **PRICE-02**: 30/90-day price history per product
- **PRICE-03**: Auto-buy agent for price targets (requires accounts + payment)

### Additional Providers

- **PROV-04**: Awin feed ingestion pipeline for batch product data
- **PROV-05**: Rakuten Advertising provider with XML product search
- **PROV-06**: TravelPayouts flights integration
- **PROV-07**: Skimlinks Product Key API for product images/prices (requires account manager approval)

### Advanced UX

- **UX-06**: Visual threading of shortlist across conversation turns
- **UX-07**: Guided entry for "I don't know what I need" queries (problem-first framing)
- **UX-08**: Per-product review sentiment bars with source breakdown

## Out of Scope

| Feature | Reason |
|---------|--------|
| User accounts / login | Anonymous-first for v1, reduces friction |
| Mobile native app | Web-first, responsive design covers mobile |
| Stored product database | Live search is the differentiator |
| Post-purchase support | We're an affiliate, not a retailer |
| Real-time price monitoring | Requires persistent infrastructure, defer to v2 |
| Awin real-time search | Awin has no real-time keyword search API; feed-only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| RX-01 | Phase 1 | Pending |
| RX-02 | Phase 1 | Pending |
| RX-03 | Phase 1 | Pending |
| RX-04 | Phase 1 | Pending |
| RX-05 | Phase 1 | Pending |
| RX-06 | Phase 1 | Pending |
| RX-07 | Phase 1 | Pending |
| RX-08 | Phase 1 | Pending |
| FIX-01 | Phase 2 | Pending |
| FIX-02 | Phase 3 | Pending |
| FIX-03 | Phase 3 | Pending |
| FIX-04 | Phase 4 | Pending |
| FIX-05 | Phase 4 | Pending |
| SRCH-01 | Phase 3 | Pending |
| SRCH-02 | Phase 3 | Pending |
| SRCH-03 | Phase 3 | Pending |
| AMZN-01 | Phase 5 | Pending |
| AMZN-02 | Phase 5 | Pending |
| AMZN-03 | Phase 5 | Pending |
| AMZN-04 | Phase 5 | Pending |
| AFFL-01 | Phase 6 | Pending |
| AFFL-02 | Phase 6 | Pending |
| AFFL-03 | Phase 6 | Pending |
| AFFL-04 | Phase 7 | Pending |
| AFFL-05 | Phase 7 | Pending |
| UX-01 | Phase 8 | Pending |
| UX-02 | Phase 8 | Pending |
| UX-03 | Phase 9 | Pending |
| UX-04 | Phase 9 | Pending |
| UX-05 | Phase 9 | Pending |
| PROV-01 | Phase 10 | Pending |
| PROV-02 | Phase 11 | Pending |
| PROV-03 | Phase 11 | Pending |

**Coverage:**
- v1 requirements: 33 total
- Mapped to phases: 33
- Unmapped: 0

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-15 after adding PERF requirements*
