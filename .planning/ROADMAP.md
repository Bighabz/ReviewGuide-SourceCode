# Roadmap: ReviewGuide.ai v1.0

## Overview

ReviewGuide.ai is a working product with a broken core experience. The roadmap moves in three layers: first, fix what's visibly broken so every response is trustworthy (phases 1-3, parallelizable); second, secure Amazon's future before the hard API shutdown deadline and add the catch-all affiliate monetization layer (phases 4-6); third, upgrade the conversational UX to match the industry standard and expand the provider network (phases 7-10). Phases 1-3 can run in parallel. Phases 5-6 are gated on Skimlinks publisher approval — apply immediately.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Fix Review Source Links** - Restore clickable review citations in blog-style responses
- [ ] **Phase 2: Serper Shopping Provider** - Add multi-retailer product search with images as a new affiliate provider
- [ ] **Phase 3: Browse Page Fixes** - Fix broken amzn.to links and truncated affiliate URL on browse pages
- [ ] **Phase 4: Amazon Creators API Migration** - Migrate Amazon provider from PA-API v5 to Creators API before May 15, 2026 deadline
- [ ] **Phase 5: Skimlinks Link Wrapper** - Implement server-side affiliate monetization for non-Amazon, non-eBay product URLs
- [ ] **Phase 6: Skimlinks Middleware + Editor's Picks** - Wire Skimlinks as post-processing middleware and re-enable curated content on browse pages
- [ ] **Phase 7: Clarifier Suggestion Chips** - Add tappable suggestion chips to clarifier agent responses
- [ ] **Phase 8: Top Pick Block + Help Me Decide** - Add editorial top pick UI block and comparison intent detection
- [ ] **Phase 9: Impact.com Provider** - Integrate Impact.com affiliate catalog for keyword product search
- [ ] **Phase 10: Viator + CJ Expansion** - Add Viator activity provider and apply to high-value CJ advertisers

## Phase Details

### Phase 1: Fix Review Source Links
**Goal**: Blog-style responses attribute sources with working links to Wirecutter, Tom's Guide, Reddit, and other review sites
**Depends on**: Nothing (independent bug fix)
**Requirements**: FIX-01
**Success Criteria** (what must be TRUE):
  1. A product response includes named source links (e.g. "Wirecutter", "Tom's Guide") that are clickable
  2. Clicking a source link opens the original review page in a new tab
  3. Source links appear in the blog-style narrative, not just as a raw URL dump
  4. At least two sources are cited per product response when review data is available
**Plans**: TBD

### Phase 2: Serper Shopping Provider
**Goal**: Product search returns results from multiple retailers with product images, prices, and merchant names — not eBay alone
**Depends on**: Nothing (independent, can run in parallel with phases 1 and 3)
**Requirements**: FIX-02, FIX-03, SRCH-01, SRCH-02, SRCH-03
**Success Criteria** (what must be TRUE):
  1. A product query returns results from at least two different retailers (e.g. Best Buy and Walmart, not just eBay)
  2. Every product card displays a product image sourced from Serper shopping results
  3. Product results appear in the AffiliateProviderRegistry under the "serper_shopping" key and are auto-discovered by the provider loader
  4. Repeated identical queries within the same session do not trigger a second Serper API call (Redis cache hit)
  5. The Serper shopping provider requires no new API credentials (reuses existing SERPER_API_KEY)
**Plans**: TBD

### Phase 3: Browse Page Fixes
**Goal**: All affiliate links on browse category pages resolve correctly with no broken or truncated URLs
**Depends on**: Nothing (independent, can run in parallel with phases 1 and 2)
**Requirements**: FIX-04, FIX-05
**Success Criteria** (what must be TRUE):
  1. amzn.to links on browse pages open to the correct Amazon product page when clicked
  2. The menopause supplements category affiliate link is complete and resolves to a working product page
  3. No 404 or redirect errors appear in the browser console when clicking curated affiliate links
**Plans**: TBD

### Phase 4: Amazon Creators API Migration
**Goal**: Amazon product search continues working after May 15, 2026 using the Creators API with OAuth2 authentication
**Depends on**: Nothing (independent; schedule before May 15, 2026 deadline)
**Requirements**: AMZN-01, AMZN-02, AMZN-03, AMZN-04
**Success Criteria** (what must be TRUE):
  1. Amazon keyword search and ASIN lookup return the same product data after migration as before
  2. OAuth2 tokens refresh automatically when within 5 minutes of the 1-hour expiry, with no user-visible interruption
  3. Amazon product images are displayed via direct hotlink to Amazon CDN URLs — no caching or re-hosting
  4. The amazon_provider.py file contains no AWS Signature V4 credential logic after migration
  5. Amazon integration is live on Railway before May 15, 2026
**Plans**: TBD

### Phase 5: Skimlinks Link Wrapper
**Goal**: Product URLs from Serper Shopping and other non-Amazon, non-eBay sources are monetized via Skimlinks affiliate tracking
**Depends on**: Phase 2 (Serper Shopping provides the unaffiliated URLs that Skimlinks will monetize); Skimlinks publisher approval (external dependency — apply immediately)
**Requirements**: AFFL-01, AFFL-02, AFFL-03
**Success Criteria** (what must be TRUE):
  1. A Serper Shopping result for a merchant in the Skimlinks network (e.g. Best Buy, Walmart) generates a go.redirectingat.com wrapped URL
  2. An Amazon product URL is never passed through the Skimlinks wrapper
  3. The Skimlinks merchant domain list is fetched from Redis on cache hit and from the Merchant API only on cache miss (24h TTL)
  4. The Skimlinks link wrapper can be disabled via SKIMLINKS_API_ENABLED=false without breaking product search
**Plans**: TBD

### Phase 6: Skimlinks Middleware + Editor's Picks
**Goal**: Skimlinks post-processing runs automatically on all provider results, and Editor's Picks with product images are visible on browse category pages
**Depends on**: Phase 5 (Skimlinks link wrapper must be implemented and approved before middleware can run)
**Requirements**: AFFL-04, AFFL-05
**Success Criteria** (what must be TRUE):
  1. Any product URL returned by any provider is wrapped by Skimlinks if the merchant domain is in the cache — without any change to the provider itself
  2. Editor's Picks sections appear on browse category pages with product names, images, and working affiliate links
  3. Editor's Picks images load from a live provider (not placehold.co placeholders)
  4. The curatedLinks.ts data is used to populate Editor's Picks without requiring a new data source
**Plans**: TBD

### Phase 7: Clarifier Suggestion Chips
**Goal**: Clarifying questions arrive with tappable chip options so users can answer in one tap instead of typing
**Depends on**: Phases 1 and 2 (clarifier UX improvements are most valuable when product responses behind them are working and multi-retailer)
**Requirements**: UX-01, UX-02
**Success Criteria** (what must be TRUE):
  1. A clarifier agent response includes 2-4 suggestion chips below the prose question
  2. Tapping a chip sends its text as the user's reply without typing
  3. Chips are rendered as styled buttons consistent with the Editorial Luxury theme (DM Sans, warm ivory/charcoal palette)
  4. The clarifier_chips field is present in GraphState with a default value so LangGraph channels do not crash on existing sessions
**Plans**: TBD

### Phase 8: Top Pick Block + Help Me Decide
**Goal**: Product responses lead with a single opinionated editorial recommendation, product counts are capped at 5, and comparison intent triggers a comparison table automatically
**Depends on**: Phases 1 and 2 (editorial top pick requires reliable multi-retailer results and review source attribution to be meaningful)
**Requirements**: UX-03, UX-04, UX-05
**Success Criteria** (what must be TRUE):
  1. A product response displays a "Top Pick" block above the product carousel containing: product name, headline reason (one sentence), who it's for, and who should look elsewhere
  2. No product response returns more than 5 product cards
  3. A follow-up message like "how do these compare?" or "which one should I get?" against an active product shortlist automatically returns a ComparisonTable — without the user asking for a table explicitly
  4. The top_pick ui_block type is rendered correctly in Message.tsx without modifying the existing ui_blocks dispatch logic
**Plans**: TBD

### Phase 9: Impact.com Provider
**Goal**: Impact.com affiliate catalog is available as a product search provider, adding higher-commission direct brand relationships
**Depends on**: Nothing (independent; can run alongside phases 7-8)
**Requirements**: PROV-01
**Success Criteria** (what must be TRUE):
  1. A product query returns Impact.com catalog results alongside eBay and Serper Shopping results
  2. Impact.com results are auto-discovered by the provider loader and registered in AffiliateProviderRegistry
  3. Impact.com API calls are rate-limited to stay within 3,000 requests/hour
  4. The provider can be disabled via IMPACT_API_ENABLED=false without affecting other providers
**Plans**: TBD

### Phase 10: Viator + CJ Expansion
**Goal**: Viator activity search is available for travel queries, and CJ advertiser coverage is expanded to include major retail brands
**Depends on**: Nothing (independent; Viator is code work, CJ expansion is a business action with no code change)
**Requirements**: PROV-02, PROV-03
**Success Criteria** (what must be TRUE):
  1. A travel query asking for activities or experiences returns Viator results with activity names, images, prices, and booking links
  2. Viator results are auto-discovered by the provider loader and registered in AffiliateProviderRegistry
  3. CJ advertiser applications for at least 3 of the target programs (Best Buy, Dell, Target, Wayfair, Nike) are submitted and confirmation emails received
  4. Once a CJ advertiser approves the application, their products appear in CJ search results without any code change
**Plans**: TBD

## Progress

**Execution Order:**
Phases 1, 2, 3 can execute in parallel. Phase 4 executes independently but must complete before May 15, 2026. Phases 5-6 are sequential and depend on Skimlinks publisher approval. Phases 7-8 follow phases 1-2. Phases 9-10 are independent.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Fix Review Source Links | 0/TBD | Not started | - |
| 2. Serper Shopping Provider | 0/TBD | Not started | - |
| 3. Browse Page Fixes | 0/TBD | Not started | - |
| 4. Amazon Creators API Migration | 0/TBD | Not started | - |
| 5. Skimlinks Link Wrapper | 0/TBD | Not started | - |
| 6. Skimlinks Middleware + Editor's Picks | 0/TBD | Not started | - |
| 7. Clarifier Suggestion Chips | 0/TBD | Not started | - |
| 8. Top Pick Block + Help Me Decide | 0/TBD | Not started | - |
| 9. Impact.com Provider | 0/TBD | Not started | - |
| 10. Viator + CJ Expansion | 0/TBD | Not started | - |
