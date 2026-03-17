# Roadmap: ReviewGuide.ai

## Milestones

- 🚧 **v1.0 Core Platform** - Phases 1-11 (in progress)
- 📋 **v2.0 Frontend UX Redesign** - Phases 12-16 (planned)

## Phases

<details>
<summary>🚧 v1.0 Core Platform (Phases 1-11) — In Progress</summary>

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Response Experience Overhaul** - True token streaming, progressive product cards, parallelized backend, blog narrative with buy links
- [ ] **Phase 2: Fix Review Source Links** - Restore clickable review citations in blog-style responses
- [ ] **Phase 3: Serper Shopping Provider** - Add multi-retailer product search with images as a new affiliate provider
- [ ] **Phase 4: Browse Page Fixes** - Fix broken amzn.to links and truncated affiliate URL on browse pages
- [ ] **Phase 5: Amazon Creators API Migration** - Migrate Amazon provider from PA-API v5 to Creators API before May 15, 2026 deadline
- [ ] **Phase 6: Skimlinks Link Wrapper** - Implement server-side affiliate monetization for non-Amazon, non-eBay product URLs
- [ ] **Phase 7: Skimlinks Middleware + Editor's Picks** - Wire Skimlinks as post-processing middleware and re-enable curated content on browse pages
- [ ] **Phase 8: Clarifier Suggestion Chips** - Add tappable suggestion chips to clarifier agent responses
- [ ] **Phase 9: Top Pick Block + Help Me Decide** - Add editorial top pick UI block and comparison intent detection
- [ ] **Phase 10: Impact.com Provider** - Integrate Impact.com affiliate catalog for keyword product search
- [ ] **Phase 11: Viator + CJ Expansion** - Add Viator activity provider and apply to high-value CJ advertisers

### Phase 1: Response Experience Overhaul
**Goal**: Users see product cards within 5 seconds and a streaming blog narrative with buy links — not a 90-second "Thinking..." wall. True token streaming from OpenAI, progressive UI, parallelized backend.
**Depends on**: Nothing (independent, highest priority)
**Requirements**: RX-01, RX-02, RX-03, RX-04, RX-05, RX-06, RX-07, RX-08
**Success Criteria** (what must be TRUE):
  1. Product cards appear in the chat within 5 seconds of sending a query (via stream_chunk_data SSE artifacts)
  2. Blog narrative text streams token-by-token — user sees words appearing in real-time, not a batch dump after 90s
  3. Blog text includes inline affiliate links as clickable markdown (e.g. "[Check price on Amazon →](url)")
  4. Affiliate product searches within each provider use asyncio.gather (not sequential for loop)
  5. review_search queries a maximum of 3 products (not 5) with a per-product timeout
  6. Review search and affiliate search run in parallel where data dependencies allow
  7. product_compose eliminates redundant LLM calls — no more than 4 concurrent calls
  8. No regressions in response quality — products, prices, review summaries, and affiliate links still appear
**Plans**: 6 plans
Plans:
- [ ] 01-01-PLAN.md — Wave 0 test scaffolds for all 8 RX requirements
- [ ] 01-02-PLAN.md — Backend parallelism (RX-03, RX-04, RX-05)
- [ ] 01-03-PLAN.md — product_compose cleanup: remove opener/conclusion, thread source URLs (RX-06, RX-07)
- [ ] 01-04-PLAN.md — Early product card streaming via artifact callback (RX-01, RX-08)
- [ ] 01-05-PLAN.md — Blog article token streaming via token callback (RX-02)
- [ ] 01-06-PLAN.md — Human verification checkpoint

### Phase 2: Fix Review Source Links
**Goal**: Blog-style responses attribute sources with working links to Wirecutter, Tom's Guide, Reddit, and other review sites
**Depends on**: Nothing (independent bug fix; can run in parallel with phases 3-4)
**Requirements**: FIX-01
**Success Criteria** (what must be TRUE):
  1. A product response includes named source links (e.g. "Wirecutter", "Tom's Guide") that are clickable
  2. Clicking a source link opens the original review page in a new tab
  3. Source links appear in the blog-style narrative, not just as a raw URL dump
  4. At least two sources are cited per product response when review data is available
**Plans**: 1 plan
Plans:
- [ ] 02-01-PLAN.md — Thread source URLs into LLM context, update system prompt, fix citations (FIX-01)

### Phase 3: Serper Shopping Provider
**Goal**: Product search returns results from multiple retailers with product images, prices, and merchant names — not eBay alone
**Depends on**: Nothing (independent, can run in parallel with phases 2 and 4)
**Requirements**: FIX-02, FIX-03, SRCH-01, SRCH-02, SRCH-03
**Success Criteria** (what must be TRUE):
  1. A product query returns results from at least two different retailers (e.g. Best Buy and Walmart, not just eBay)
  2. Every product card displays a product image sourced from Serper shopping results
  3. Product results appear in the AffiliateProviderRegistry under the "serper_shopping" key and are auto-discovered by the provider loader
  4. Repeated identical queries within the same session do not trigger a second Serper API call (Redis cache hit)
  5. The Serper shopping provider requires no new API credentials (reuses existing SERPER_API_KEY)
**Plans**: 1 plan
Plans:
- [ ] 03-01-PLAN.md — SerperShoppingProvider: create provider, register in loader and product_compose (FIX-02, FIX-03, SRCH-01, SRCH-02, SRCH-03)

### Phase 4: Browse Page Fixes
**Goal**: All affiliate links on browse category pages resolve correctly with no broken or truncated URLs
**Depends on**: Nothing (independent, can run in parallel with phases 2 and 3)
**Requirements**: FIX-04, FIX-05
**Success Criteria** (what must be TRUE):
  1. amzn.to links on browse pages open to the correct Amazon product page when clicked
  2. The menopause supplements category affiliate link is complete and resolves to a working product page
  3. No 404 or redirect errors appear in the browser console when clicking curated affiliate links
**Plans**: 1 plan
Plans:
- [ ] 04-01-PLAN.md — Guard amzn.to in health checker, fix menopause URL, wire CuratedProductCard into category page (FIX-04, FIX-05)

### Phase 5: Amazon Creators API Migration
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

### Phase 6: Skimlinks Link Wrapper
**Goal**: Product URLs from Serper Shopping and other non-Amazon, non-eBay sources are monetized via Skimlinks affiliate tracking
**Depends on**: Phase 3 (Serper Shopping provides the unaffiliated URLs that Skimlinks will monetize); Skimlinks publisher approval (external dependency — apply immediately)
**Requirements**: AFFL-01, AFFL-02, AFFL-03
**Success Criteria** (what must be TRUE):
  1. A Serper Shopping result for a merchant in the Skimlinks network (e.g. Best Buy, Walmart) generates a go.redirectingat.com wrapped URL
  2. An Amazon product URL is never passed through the Skimlinks wrapper
  3. The Skimlinks merchant domain list is fetched from Redis on cache hit and from the Merchant API only on cache miss (24h TTL)
  4. The Skimlinks link wrapper can be disabled via SKIMLINKS_API_ENABLED=false without breaking product search
**Plans**: TBD

### Phase 7: Skimlinks Middleware + Editor's Picks
**Goal**: Skimlinks post-processing runs automatically on all provider results, and Editor's Picks with product images are visible on browse category pages
**Depends on**: Phase 6 (Skimlinks link wrapper must be implemented and approved before middleware can run)
**Requirements**: AFFL-04, AFFL-05
**Success Criteria** (what must be TRUE):
  1. Any product URL returned by any provider is wrapped by Skimlinks if the merchant domain is in the cache — without any change to the provider itself
  2. Editor's Picks sections appear on browse category pages with product names, images, and working affiliate links
  3. Editor's Picks images load from a live provider (not placehold.co placeholders)
  4. The curatedLinks.ts data is used to populate Editor's Picks without requiring a new data source
**Plans**: TBD

### Phase 8: Clarifier Suggestion Chips
**Goal**: Clarifying questions arrive with tappable chip options so users can answer in one tap instead of typing
**Depends on**: Phases 2 and 3 (clarifier UX improvements are most valuable when product responses behind them are working and multi-retailer)
**Requirements**: UX-01, UX-02
**Success Criteria** (what must be TRUE):
  1. A clarifier agent response includes 2-4 suggestion chips below the prose question
  2. Tapping a chip sends its text as the user's reply without typing
  3. Chips are rendered as styled buttons consistent with the Editorial Luxury theme (DM Sans, warm ivory/charcoal palette)
  4. The clarifier_chips field is present in GraphState with a default value so LangGraph channels do not crash on existing sessions
**Plans**: TBD

### Phase 9: Top Pick Block + Help Me Decide
**Goal**: Product responses lead with a single opinionated editorial recommendation, product counts are capped at 5, and comparison intent triggers a comparison table automatically
**Depends on**: Phases 2 and 3 (editorial top pick requires reliable multi-retailer results and review source attribution to be meaningful)
**Requirements**: UX-03, UX-04, UX-05
**Success Criteria** (what must be TRUE):
  1. A product response displays a "Top Pick" block above the product carousel containing: product name, headline reason (one sentence), who it's for, and who should look elsewhere
  2. No product response returns more than 5 product cards
  3. A follow-up message like "how do these compare?" or "which one should I get?" against an active product shortlist automatically returns a ComparisonTable — without the user asking for a table explicitly
  4. The top_pick ui_block type is rendered correctly in Message.tsx without modifying the existing ui_blocks dispatch logic
**Plans**: TBD

### Phase 10: Impact.com Provider
**Goal**: Impact.com affiliate catalog is available as a product search provider, adding higher-commission direct brand relationships
**Depends on**: Nothing (independent; can run alongside phases 8-9)
**Requirements**: PROV-01
**Success Criteria** (what must be TRUE):
  1. A product query returns Impact.com catalog results alongside eBay and Serper Shopping results
  2. Impact.com results are auto-discovered by the provider loader and registered in AffiliateProviderRegistry
  3. Impact.com API calls are rate-limited to stay within 3,000 requests/hour
  4. The provider can be disabled via IMPACT_API_ENABLED=false without affecting other providers
**Plans**: TBD

### Phase 11: Viator + CJ Expansion
**Goal**: Viator activity search is available for travel queries, and CJ advertiser coverage is expanded to include major retail brands
**Depends on**: Nothing (independent; Viator is code work, CJ expansion is a business action with no code change)
**Requirements**: PROV-02, PROV-03
**Success Criteria** (what must be TRUE):
  1. A travel query asking for activities or experiences returns Viator results with activity names, images, prices, and booking links
  2. Viator results are auto-discovered by the provider loader and registered in AffiliateProviderRegistry
  3. CJ advertiser applications for at least 3 of the target programs (Best Buy, Dell, Target, Wayfair, Nike) are submitted and confirmation emails received
  4. Once a CJ advertiser approves the application, their products appear in CJ search results without any code change
**Plans**: TBD

</details>

---

### v2.0 Frontend UX Redesign (Phases 12-16)

**Milestone Goal:** Complete frontend redesign — unified Discover -> Chat -> Results flow with mobile-first, app-like navigation and structured AI responses, evolving the editorial luxury aesthetic. No backend changes required.

- [x] **Phase 12: Navigation Shell** - Mobile bottom tab bar, desktop top nav, central FAB, iOS safe area, layout baseline (completed 2026-03-17)
- [x] **Phase 13: Discover Screen** - Unified entry point replacing Browse/Chat split — hero search, category chips, trending cards (completed 2026-03-17)
- [ ] **Phase 14: Chat Screen** - Restructured AI responses, compact inline product cards, suggestion chips, source citations
- [ ] **Phase 15: Results Screen** - Dedicated `/results/:id` route with desktop split panel and mobile full-width layouts
- [ ] **Phase 16: Placeholder Routes and Build QA** - `/saved`, `/compare` stubs, Suspense wrappers, `next build` clean pass

## Phase Details

### Phase 12: Navigation Shell
**Goal**: App-like navigation is in place on all screens — mobile gets a fixed bottom tab bar with central FAB, desktop keeps the existing top nav, and every new component is built on the correct `h-dvh` / CSS variable / dark mode baseline from day one.
**Depends on**: Nothing (first phase — establishes layout context for all subsequent phases)
**Requirements**: NAV-01, NAV-02, NAV-03, NAV-04, NAV-05
**Success Criteria** (what must be TRUE):
  1. On mobile (<768px), user sees a fixed bottom tab bar with 5 tabs (Discover, Saved, Ask, Compare, Profile) and a raised central FAB for Ask
  2. On desktop (>=1024px), user sees the existing top navigation bar; the bottom tab bar is not visible
  3. Tapping the central FAB from any screen navigates to `/chat?new=1` and starts a new research session
  4. Animated page transitions play between routes — tabs animate in/out without full white-flash reloads
  5. On an iPhone with a home indicator, the bottom tab bar does not overlap the home swipe gesture area (safe area inset respected)
**Plans**: 3 plans
Plans:
- [x] 12-01-PLAN.md — Wave 0 test scaffolds for all NAV requirements (NAV-01 through NAV-05)
- [x] 12-02-PLAN.md — Core navigation components: NavLayout, MobileTabBar, MobileHeader (NAV-01, NAV-03, NAV-05)
- [x] 12-03-PLAN.md — Integration: layout.tsx wiring, template.tsx transitions, UnifiedTopbar labels, cleanup (NAV-02, NAV-04, NAV-05)

### Phase 13: Discover Screen
**Goal**: The app's entry point is a single editorial screen where users can start research, explore categories, or tap a trending topic — replacing the current split Browse/Chat landing pages.
**Depends on**: Phase 12 (NavLayout must be in place for the Discover screen to render inside the correct navigation context)
**Requirements**: DISC-01, DISC-02, DISC-03, DISC-04, DISC-05
**Success Criteria** (what must be TRUE):
  1. User lands on `/` and sees an editorial hero headline (serif italic accent) with a centered search bar — no separate Browse or Chat entry pages required
  2. User can scroll a horizontal row of category chips (Popular, Tech, Travel, Kitchen, Fitness, and others) and tap one to start a focused research session
  3. User sees at least 3 trending research cards (icon, title, subtitle); tapping any card navigates to chat with that query pre-loaded
  4. User who has made a prior search sees a "For You" chip as the first chip in the category row
  5. Tapping the search bar (not typing, just tapping) navigates to the chat screen with the input immediately focused and ready to type
**Plans**: 3 plans
Plans:
- [ ] 13-01-PLAN.md — Wave 0 test scaffolds for all DISC requirements (DISC-01 through DISC-05)
- [ ] 13-02-PLAN.md — Discover screen components: trendingTopics data, DiscoverSearchBar, CategoryChipRow, TrendingCards, page.tsx orchestrator (DISC-01 through DISC-05)
- [ ] 13-03-PLAN.md — Route migration: update MobileTabBar/UnifiedTopbar hrefs, /browse redirect, visual verification (DISC-01, DISC-02, DISC-05)

### Phase 14: Chat Screen
**Goal**: AI responses follow a predictable structure users can scan — summary, ranked product cards, source links, follow-up chips — and the chat UI is visually polished with correct bubble alignment and a live status indicator during streaming.
**Depends on**: Phase 12 (NavLayout for ChatHeader on mobile), Phase 13 (Discover provides the entry path into Chat)
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06
**Success Criteria** (what must be TRUE):
  1. An AI product response always renders in this order: editorial summary text, then compact inline product cards, then source citation links, then follow-up suggestion chips
  2. Inline product cards are compact (no taller than 64px) and show image, rank number, product name, price, and a tappable affiliate link — all within one horizontal row
  3. While the AI is generating a response, the chat header displays a live status string such as "Researching • 4 sources analyzed" that updates as results arrive
  4. Source citation links are clickable and open the original review article URL in a new tab
  5. User's own messages appear right-aligned in a blue bubble; AI messages appear left-aligned in a white bubble with a "✦ ReviewGuide" label
  6. Follow-up suggestion chips appear below each AI response and submitting one (by tap) sends it as the next user message without any typing
**Plans**: 4 plans
Plans:
- [ ] 14-01-PLAN.md — Wave 0 test scaffolds for all CHAT requirements (CHAT-01 through CHAT-06)
- [ ] 14-02-PLAN.md — Backend review_sources fix, InlineProductCard, SourceCitations, ChatStatusContext (CHAT-02, CHAT-03, CHAT-04)
- [ ] 14-03-PLAN.md — Integration: Message.tsx bubbles, BlockRegistry wiring, MobileHeader status, chip restyle (CHAT-01, CHAT-03, CHAT-05, CHAT-06)
- [ ] 14-04-PLAN.md — Full test suite, build check, and human visual verification (all CHAT requirements)

### Phase 15: Results Screen
**Goal**: Users can navigate to a dedicated, shareable Results page for any completed research session — with a full product grid, source panel, and quick actions — laid out in a desktop split panel and a mobile full-width view.
**Depends on**: Phase 14 (ChatHeader expand icon from Phase 14 navigates to Results; source citation fix from Phase 14 must be in place for SourcesPanel to display data)
**Requirements**: RES-01, RES-02, RES-03, RES-04, RES-05, RES-06, RESP-01, RESP-02
**Success Criteria** (what must be TRUE):
  1. User can navigate to `/results/:id` and see a full results view for a completed research session — the URL is shareable and loads correctly on a fresh page visit
  2. On mobile (<768px), all screens including Results render in a single-column full-width layout; product cards appear in a horizontal scroll row
  3. On desktop (>=1024px), the Results page shows a 3-column product card grid, a persistent left sidebar, and a max-width 1200px content area — all in a single viewport with no scrolling required to reach any primary content panel
  4. Product cards on the Results page show real Amazon product images, prices, and working affiliate links sourced from the curated static data (120+ products)
  5. Each product card displays a rank badge (e.g. "#1 Top Pick", "#2 Best Value") and a score bar
  6. The Results page includes a quick actions panel with Compare side by side, Export to list, and Share results — and a Sources section listing colored dots, source names, and clickable article links
**Plans**: TBD

### Phase 16: Placeholder Routes and Build QA
**Goal**: All bottom tab destinations have working routes that don't throw errors, every new page uses correct Suspense wrappers, and `next build` passes cleanly — confirming the entire milestone is production-deployable.
**Depends on**: Phases 12-15 (all nav shell and screen work must be complete before build validation)
**Requirements**: PLCH-01, PLCH-02
**Success Criteria** (what must be TRUE):
  1. Navigating to `/saved` shows a polished placeholder page with a "Coming soon" message — no errors, no blank screen, no thrown exceptions
  2. Navigating to `/compare` shows a polished placeholder page with a "Coming soon" message — no errors, no blank screen, no thrown exceptions
  3. Running `next build` completes without errors and all new routes appear as "(Static)" in the build output (not "ƒ" dynamic)
  4. On a real iOS device, the bottom tab bar does not overlap the keyboard when the chat input is focused, dark mode renders all new components correctly, and carousel swipe works on `/results/:id`
**Plans**: TBD

## Progress

**Execution Order:**
v2.0 phases execute sequentially: 12 -> 13 -> 14 -> 15 -> 16. Phase 12 is a hard prerequisite for all others. Phases 13, 14, 15 chain in order due to component dependencies (NavLayout -> Discover -> ChatHeader -> ResultsPage). Phase 16 runs last as build QA gate.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Response Experience Overhaul | v1.0 | 5/6 | In Progress | - |
| 2. Fix Review Source Links | v1.0 | 0/1 | Not started | - |
| 3. Serper Shopping Provider | v1.0 | 0/1 | Not started | - |
| 4. Browse Page Fixes | v1.0 | 0/1 | Not started | - |
| 5. Amazon Creators API Migration | v1.0 | 0/TBD | Not started | - |
| 6. Skimlinks Link Wrapper | v1.0 | 0/TBD | Not started | - |
| 7. Skimlinks Middleware + Editor's Picks | v1.0 | 0/TBD | Not started | - |
| 8. Clarifier Suggestion Chips | v1.0 | 0/TBD | Not started | - |
| 9. Top Pick Block + Help Me Decide | v1.0 | 0/TBD | Not started | - |
| 10. Impact.com Provider | v1.0 | 0/TBD | Not started | - |
| 11. Viator + CJ Expansion | v1.0 | 0/TBD | Not started | - |
| 12. Navigation Shell | v2.0 | 3/3 | Complete | 2026-03-17 |
| 13. Discover Screen | v2.0 | 3/3 | Complete | 2026-03-17 |
| 14. Chat Screen | 2/4 | In Progress|  | - |
| 15. Results Screen | v2.0 | 0/TBD | Not started | - |
| 16. Placeholder Routes and Build QA | v2.0 | 0/TBD | Not started | - |
