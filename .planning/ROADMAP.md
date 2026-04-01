# Roadmap: ReviewGuide.ai

## Milestones

- ✅ **v1.0 Core Platform** - Phases 1-11 (shipped 2026-03-26)
- ✅ **v2.0 Frontend UX Redesign** - Phases 12-16 (shipped 2026-03-17)
- 🚧 **v3.0 Visual Overhaul — Bold Editorial** - Phases 17-22 (in progress)

## Phases

<details>
<summary>✅ v1.0 Core Platform (Phases 1-11) — SHIPPED 2026-03-26</summary>

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Response Experience Overhaul** - True token streaming, progressive product cards, parallelized backend, blog narrative with buy links (completed 2026-03-17)
- [x] **Phase 2: Fix Review Source Links** - Restore clickable review citations in blog-style responses (completed 2026-03-25)
- [x] **Phase 3: Serper Shopping Provider** - Add multi-retailer product search with images as a new affiliate provider
- [x] **Phase 4: Browse Page Fixes** - Fix broken amzn.to links and truncated affiliate URL on browse pages
- [x] **Phase 5: Amazon Creators API Migration** - Migrate Amazon provider from PA-API v5 to Creators API before May 15, 2026 deadline
- [x] **Phase 6: Skimlinks Link Wrapper** - Implement server-side affiliate monetization for non-Amazon, non-eBay product URLs
- [x] **Phase 7: Skimlinks Middleware + Editor's Picks** - Wire Skimlinks as post-processing middleware and re-enable curated content on browse pages
- [x] **Phase 8: Clarifier Suggestion Chips** - Add tappable suggestion chips to clarifier agent responses
- [x] **Phase 9: Top Pick Block + Help Me Decide** - Add editorial top pick UI block and comparison intent detection
- [x] **Phase 10: Impact.com Provider** - Integrate Impact.com affiliate catalog for keyword product search
- [x] **Phase 11: Viator + CJ Expansion** - Add Viator activity provider and apply to high-value CJ advertisers

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
- [x] 01-01-PLAN.md — Wave 0 test scaffolds for all 8 RX requirements
- [x] 01-02-PLAN.md — Backend parallelism (RX-03, RX-04, RX-05)
- [x] 01-03-PLAN.md — product_compose cleanup: remove opener/conclusion, thread source URLs (RX-06, RX-07)
- [x] 01-04-PLAN.md — Early product card streaming via artifact callback (RX-01, RX-08)
- [x] 01-05-PLAN.md — Blog article token streaming via token callback (RX-02)
- [x] 01-06-PLAN.md — Human verification checkpoint

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
- [x] 02-01-PLAN.md — Thread source URLs into LLM context, update system prompt, fix citations (FIX-01)

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
- [x] 03-01-PLAN.md — SerperShoppingProvider: create provider, register in loader and product_compose (FIX-02, FIX-03, SRCH-01, SRCH-02, SRCH-03)

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
- [x] 04-01-PLAN.md — Guard amzn.to in health checker, fix menopause URL, wire CuratedProductCard into category page (FIX-04, FIX-05)

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
**Plans**: 2 plans
Plans:
- [x] 05-01-PLAN.md — Wave 0 RED test scaffolds, python-amazon-paapi dependency, config + loader updates (AMZN-01, AMZN-02, AMZN-03, AMZN-04)
- [x] 05-02-PLAN.md — Rewrite amazon_provider.py: replace PA-API v5 with Creators API library (AMZN-01, AMZN-02, AMZN-03, AMZN-04)

### Phase 6: Skimlinks Link Wrapper
**Goal**: Product URLs from Serper Shopping and other non-Amazon, non-eBay sources are monetized via Skimlinks affiliate tracking
**Depends on**: Phase 3 (Serper Shopping provides the unaffiliated URLs that Skimlinks will monetize); Skimlinks publisher approval (external dependency — apply immediately)
**Requirements**: AFFL-01, AFFL-02, AFFL-03
**Success Criteria** (what must be TRUE):
  1. A Serper Shopping result for a merchant in the Skimlinks network (e.g. Best Buy, Walmart) generates a go.redirectingat.com wrapped URL
  2. An Amazon product URL is never passed through the Skimlinks wrapper
  3. The Skimlinks merchant domain list is fetched from Redis on cache hit and from the Merchant API only on cache miss (24h TTL)
  4. The Skimlinks link wrapper can be disabled via SKIMLINKS_API_ENABLED=false without breaking product search
**Plans**: 3 plans
Plans:
- [x] 06-01-PLAN.md — Wave 1 RED test scaffolds for all AFFL requirements (AFFL-01, AFFL-02, AFFL-03)
- [x] 06-02-PLAN.md — Config settings + SkimlinksLinkWrapper service (AFFL-01, AFFL-02, AFFL-03)
- [x] 06-03-PLAN.md — Post-processing integration in product_affiliate.py (AFFL-01, AFFL-02, AFFL-03)

### Phase 7: Skimlinks Middleware + Editor's Picks
**Goal**: Skimlinks post-processing runs automatically on all provider results, and Editor's Picks with product images are visible on browse category pages
**Depends on**: Phase 6 (Skimlinks link wrapper must be implemented and approved before middleware can run)
**Requirements**: AFFL-04, AFFL-05
**Success Criteria** (what must be TRUE):
  1. Any product URL returned by any provider is wrapped by Skimlinks if the merchant domain is in the cache — without any change to the provider itself
  2. Editor's Picks sections appear on browse category pages with product names, images, and working affiliate links
  3. Editor's Picks images load from a live provider (not placehold.co placeholders)
  4. The curatedLinks.ts data is used to populate Editor's Picks without requiring a new data source
**Plans**: 3 plans
Plans:
- [x] 07-01-PLAN.md — Wave 0 RED test scaffolds for Skimlinks middleware and Editor's Picks (AFFL-04, AFFL-05)
- [x] 07-02-PLAN.md — Backend Skimlinks post-processing middleware in product_affiliate.py (AFFL-04)
- [x] 07-03-PLAN.md — Frontend EditorsPicks component and browse category page wiring (AFFL-05)

### Phase 8: Clarifier Suggestion Chips
**Goal**: Clarifying questions arrive with tappable chip options so users can answer in one tap instead of typing
**Depends on**: Phases 2 and 3 (clarifier UX improvements are most valuable when product responses behind them are working and multi-retailer)
**Requirements**: UX-01, UX-02
**Success Criteria** (what must be TRUE):
  1. A clarifier agent response includes 2-4 suggestion chips below the prose question
  2. Tapping a chip sends its text as the user's reply without typing
  3. Chips are rendered as styled buttons consistent with the Editorial Luxury theme (DM Sans, warm ivory/charcoal palette)
  4. The clarifier_chips field is present in GraphState with a default value so LangGraph channels do not crash on existing sessions
**Plans**: 3 plans
Plans:
- [x] 08-01-PLAN.md — Wave 0 RED test scaffolds for clarifier chip rendering and click dispatch (UX-01, UX-02)
- [x] 08-02-PLAN.md — Backend: GraphState field, initial_state default, clarifier prompt chip generation (UX-01, UX-02)
- [x] 08-03-PLAN.md — Frontend: FollowupQuestion interface update, chip pill rendering in Message.tsx (UX-01, UX-02)

### Phase 9: Top Pick Block + Help Me Decide
**Goal**: Product responses lead with a single opinionated editorial recommendation, product counts are capped at 5, and comparison intent triggers a comparison table automatically
**Depends on**: Phases 2 and 3 (editorial top pick requires reliable multi-retailer results and review source attribution to be meaningful)
**Requirements**: UX-03, UX-04, UX-05
**Success Criteria** (what must be TRUE):
  1. A product response displays a "Top Pick" block above the product carousel containing: product name, headline reason (one sentence), who it's for, and who should look elsewhere
  2. No product response returns more than 5 product cards
  3. A follow-up message like "how do these compare?" or "which one should I get?" against an active product shortlist automatically returns a ComparisonTable — without the user asking for a table explicitly
  4. The top_pick ui_block type is rendered correctly in Message.tsx without modifying the existing ui_blocks dispatch logic
**Plans**: 3 plans
Plans:
- [x] 09-01-PLAN.md — Wave 0 RED test scaffolds for UX-03, UX-04, UX-05
- [x] 09-02-PLAN.md — Backend: top_pick LLM task, 5-product cap, comparison follow-up (UX-03, UX-04, UX-05)
- [x] 09-03-PLAN.md — Frontend: TopPickBlock component + BlockRegistry wiring (UX-03)

### Phase 10: Impact.com Provider
**Goal**: Impact.com affiliate catalog is available as a product search provider, adding higher-commission direct brand relationships
**Depends on**: Nothing (independent; can run alongside phases 8-9)
**Requirements**: PROV-01
**Success Criteria** (what must be TRUE):
  1. A product query returns Impact.com catalog results alongside eBay and Serper Shopping results
  2. Impact.com results are auto-discovered by the provider loader and registered in AffiliateProviderRegistry
  3. Impact.com API calls are rate-limited to stay within 3,000 requests/hour
  4. The provider can be disabled via IMPACT_API_ENABLED=false without affecting other providers
**Plans**: 2 plans
Plans:
- [x] 10-01-PLAN.md — Wave 0 RED test scaffolds for all PROV-01 behaviors
- [x] 10-02-PLAN.md — Config settings, ImpactAffiliateProvider class, loader wiring (PROV-01)

### Phase 11: Viator + CJ Expansion
**Goal**: Viator activity search is available for travel queries, and CJ advertiser coverage is expanded to include major retail brands
**Depends on**: Nothing (independent; Viator is code work, CJ expansion is a business action with no code change)
**Requirements**: PROV-02, PROV-03
**Success Criteria** (what must be TRUE):
  1. A travel query asking for activities or experiences returns Viator results with activity names, images, prices, and booking links
  2. Viator results are auto-discovered by the provider loader and registered in AffiliateProviderRegistry
  3. CJ advertiser applications for at least 3 of the target programs (Best Buy, Dell, Target, Wayfair, Nike) are submitted and confirmation emails received
  4. Once a CJ advertiser approves the application, their products appear in CJ search results without any code change
**Plans**: 4 plans
Plans:
- [x] 11-01-PLAN.md — Wave 0 RED test scaffolds for all PROV-02 behaviors
- [x] 11-02-PLAN.md — ViatorActivityProvider class, config settings, loader registration (PROV-02)
- [x] 11-03-PLAN.md — MCP tool, GraphState wiring, travel_compose integration (PROV-02)
- [x] 11-04-PLAN.md — CJ advertiser applications + Viator API credentials (PROV-03)

</details>

<details>
<summary>✅ v2.0 Frontend UX Redesign (Phases 12-16) — SHIPPED 2026-03-17</summary>

- [x] **Phase 12: Navigation Shell** - Mobile bottom tab bar, desktop top nav, central FAB, iOS safe area, layout baseline (completed 2026-03-17)
- [x] **Phase 13: Discover Screen** - Unified entry point replacing Browse/Chat split — hero search, category chips, trending cards (completed 2026-03-17)
- [x] **Phase 14: Chat Screen** - Restructured AI responses, compact inline product cards, suggestion chips, source citations (completed 2026-03-17)
- [x] **Phase 15: Results Screen** - Dedicated `/results/:id` route with desktop split panel and mobile full-width layouts (completed 2026-03-17)
- [x] **Phase 16: Placeholder Routes and Build QA** - `/saved`, `/compare` stubs, Suspense wrappers, `next build` clean pass (completed 2026-03-17)

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
- [x] 13-01-PLAN.md — Wave 0 test scaffolds for all DISC requirements (DISC-01 through DISC-05)
- [x] 13-02-PLAN.md — Discover screen components: trendingTopics data, DiscoverSearchBar, CategoryChipRow, TrendingCards, page.tsx orchestrator (DISC-01 through DISC-05)
- [x] 13-03-PLAN.md — Route migration: update MobileTabBar/UnifiedTopbar hrefs, /browse redirect, visual verification (DISC-01, DISC-02, DISC-05)

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
- [x] 14-01-PLAN.md — Wave 0 test scaffolds for all CHAT requirements (CHAT-01 through CHAT-06)
- [x] 14-02-PLAN.md — Backend review_sources fix, InlineProductCard, SourceCitations, ChatStatusContext (CHAT-02, CHAT-03, CHAT-04)
- [x] 14-03-PLAN.md — Integration: Message.tsx bubbles, BlockRegistry wiring, MobileHeader status, chip restyle (CHAT-01, CHAT-03, CHAT-05, CHAT-06)
- [x] 14-04-PLAN.md — Full test suite, build check, and human visual verification (all CHAT requirements)

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
**Plans**: 3 plans
Plans:
- [x] 15-01-PLAN.md — Wave 0 RED tests, extractResultsData utility, CSS card accent variables (RES-01 through RES-06, RESP-01, RESP-02)
- [x] 15-02-PLAN.md — ResultsProductCard, ResultsQuickActions, ResultsHeader components (RES-02, RES-03, RES-04, RES-05, RESP-01, RESP-02)
- [x] 15-03-PLAN.md — Results page.tsx, MobileHeader wiring, MobileTabBar active state, human verification (RES-01, RES-02, RES-06, RESP-01, RESP-02)

### Phase 16: Placeholder Routes and Build QA
**Goal**: All bottom tab destinations have working routes that don't throw errors, every new page uses correct Suspense wrappers, and `next build` passes cleanly — confirming the entire milestone is production-deployable.
**Depends on**: Phases 12-15 (all nav shell and screen work must be complete before build validation)
**Requirements**: PLCH-01, PLCH-02
**Success Criteria** (what must be TRUE):
  1. Navigating to `/saved` shows a polished placeholder page with a "Coming soon" message — no errors, no blank screen, no thrown exceptions
  2. Navigating to `/compare` shows a polished placeholder page with a "Coming soon" message — no errors, no blank screen, no thrown exceptions
  3. Running `next build` completes without errors and all new routes appear as "(Static)" in the build output (not "ƒ" dynamic)
  4. On a real iOS device, the bottom tab bar does not overlap the keyboard when the chat input is focused, dark mode renders all new components correctly, and carousel swipe works on `/results/:id`
**Plans**: 1 plan
Plans:
- [x] 16-01-PLAN.md — Placeholder pages (/saved, /compare), nav href updates, build QA (PLCH-01, PLCH-02)

</details>

---

### v3.0 Visual Overhaul — Bold Editorial (Phases 17-22)

**Milestone Goal:** Full site visual refresh with Shopify-level polish — bold colors, AI-generated product imagery, premium product cards — while keeping the warm editorial foundation. Pure frontend: no backend changes required.

- [x] **Phase 17: Token Foundation + Dark Mode Fixes** - Add bold CSS tokens, fix hardcoded dark mode colors across product card leaf components (completed 2026-04-01)
- [ ] **Phase 18: AI Image Generation** - Generate and commit all hero, mosaic, and category images as a unified visual batch
- [ ] **Phase 19: Mosaic Hero** - Build MosaicHero component and wire into discover landing page
- [ ] **Phase 20: Discover + Browse Page Upgrades** - Bold category heroes, upgraded carousel and trending cards, per-category accent color injection
- [ ] **Phase 21: Chat + Results Card Polish** - Premium product card treatment across all chat and results card variants
- [ ] **Phase 22: Visual QA + Consistency Pass** - Full site screenshot walk-through, token test coverage, hardcoded color audit

## Phase Details

### Phase 17: Token Foundation + Dark Mode Fixes
**Goal**: The CSS token system is extended with bold editorial values, every new token has a dark mode counterpart, and all hardcoded color regressions in product card leaf components are converted to semantic tokens — so subsequent phases build on a correct, tested foundation.
**Depends on**: Nothing (first phase of v3.0; establishes rules all subsequent phases follow)
**Requirements**: TOK-01, TOK-02, TOK-03
**Success Criteria** (what must be TRUE):
  1. New bold accent color tokens are visible in browser DevTools on `<html>` — vibrant blues, terracotta, and energetic greens appear on `:root` and are overridden in `[data-theme="dark"]`
  2. Toggling dark mode in the browser does not produce any white/light color flashes on ProductReview, TopPickBlock, or ProductCards components (hardcoded `text-green-700` / `text-red-700` / `text-emerald-600` eliminated)
  3. Running `npm run test:run` passes with zero failures after all globals.css edits — the designTokens.test.ts contract is intact
  4. Larger, bolder heading sizes are visible in the browser: category hero h1 renders at `clamp(2.5rem, 5vw, 4.5rem)` measured in DevTools
**Plans**: 2 plans
Plans:
- [ ] 17-01-PLAN.md — Bold accent palette, typography scale tokens, missing dark mode gap fixes in globals.css (TOK-01, TOK-02, TOK-03)
- [ ] 17-02-PLAN.md — Convert 9 hardcoded color classes in ProductReview, TopPickBlock, ProductCards to semantic tokens (TOK-03)

### Phase 18: AI Image Generation
**Goal**: A complete, visually consistent batch of AI-generated product and category images is committed to the repository — all sharing a single canonical style, pre-optimized as WebP under 200KB — so every subsequent component that references images can finalize its implementation without waiting.
**Depends on**: Phase 17 (the target aesthetic established by Phase 17 tokens informs the canonical image style prompt)
**Requirements**: IMG-01, IMG-02, IMG-03
**Success Criteria** (what must be TRUE):
  1. At least 15 bold product category hero images (headphones, laptops, kitchen, travel, fitness, etc.) exist in `/public/images/` as WebP files, each under 200KB
  2. At least 8 mosaic tile images exist in `/public/images/` as WebP files — diverse products at varied angles — all sharing consistent lighting, color temperature, and stylization
  3. Viewing all generated images side-by-side in a browser reveals a coherent visual language: no mismatched lighting or wildly different color palettes between images
  4. Every generated image file is under 200KB — verified by checking file sizes in the filesystem
**Plans**: TBD

### Phase 19: Mosaic Hero
**Goal**: Users landing on the discover page see a Shopify-style mosaic collage of bold product images as the hero background — creating an immediate first impression of visual richness — with the search bar and headline floating over it with readable contrast, and no LCP or CLS regressions.
**Depends on**: Phase 17 (bold tokens for overlay gradient colors), Phase 18 (mosaic tile images must exist before component can be finalized)
**Requirements**: HERO-01, HERO-02, HERO-03, HERO-04
**Success Criteria** (what must be TRUE):
  1. On the landing page (`/`), user sees a grid of overlapping, slightly-rotated product image tiles filling the hero area — replacing the previous plain background
  2. The search bar and headline text remain legible over the mosaic — no product image bleeds through at full opacity behind text
  3. The mosaic layout is built with CSS Grid and `transform: rotate()` — no additional JavaScript library is imported to implement it
  4. Lighthouse mobile audit shows LCP under 2.5s and CLS under 0.1 after the mosaic hero is live (the first visible mosaic image uses `loading="eager"`)
**Plans**: TBD

### Phase 20: Discover + Browse Page Upgrades
**Goal**: The discover page carousel and trending cards have bold visual presence with real product images, and browse category hero sections use AI-generated background images with gradient overlays — transforming category pages into a magazine-cover experience.
**Depends on**: Phase 17 (typography tokens for bold category hero h1), Phase 18 (category hero background images must exist)
**Requirements**: DISC-06, DISC-07, BRW-01, BRW-02
**Success Criteria** (what must be TRUE):
  1. Browse category hero sections display full-bleed AI-generated background images with a gradient overlay — text on the hero passes WCAG AA contrast when measured with a contrast checker
  2. Editor's Picks cards on browse pages are visually prominent with bolder typography and colors consistent with the v3.0 bold editorial language
  3. The discover page product carousel renders real product images with `loading="eager"` on the first slide — no icon placeholders remain
  4. Category chips and trending cards on the discover page have stronger visual presence — larger images, bolder color treatment — compared to the pre-v3.0 state
**Plans**: TBD

### Phase 21: Chat + Results Card Polish
**Goal**: Every product card variant across the chat and results screens has premium spacing, bolder typography, spring-physics hover animations, a clean 3-column "Where to Buy" section with merchant labels, and no Framer Motion regressions during active streaming.
**Depends on**: Phase 17 (semantic color tokens required before hardcoded colors can be safely removed from cards)
**Requirements**: CHT-01, CHT-02, CARD-01, CARD-02, CARD-03, CARD-04, RES-07, RES-08
**Success Criteria** (what must be TRUE):
  1. AI response text in chat uses bolder heading sizes and better paragraph spacing — a side-by-side screenshot comparison with the pre-v3.0 state shows clear typographic improvement
  2. Inline product cards in chat have a visible hover animation (smooth lift with shadow) when hovered — price displays in a larger, bolder weight
  3. ProductReview cards display a maximum of 3 "Where to Buy" offers with clean merchant names derived from the offer URL (e.g. "Best Buy" not "bestbuy.com/product/123...")
  4. TopPickBlock renders with a stronger gradient CTA and a larger product image than the pre-v3.0 version
  5. Card hover effects use Framer Motion spring physics (`stiffness: 400, damping: 28`) — verified by watching the card lift smoothly rather than linearly
  6. During active AI response streaming, the Chrome DevTools Performance panel shows no frame drops below 55fps caused by card animations
  7. Product grid cards on the results page match the bold v3.0 visual language; the sources section uses bolder, larger colored dots
**Plans**: TBD

### Phase 22: Visual QA + Consistency Pass
**Goal**: A human has walked through every page of the site on both mobile and desktop, confirmed visual consistency, verified no hardcoded colors remain in refreshed components, and the design token test suite covers all new tokens added in this milestone — making the v3.0 release a confident, documented sign-off.
**Depends on**: Phases 17-21 (all visual work must be complete before QA gate)
**Requirements**: QA-01, QA-02, QA-03
**Success Criteria** (what must be TRUE):
  1. A complete screenshot walk-through (homepage, a browse category page, a chat session with product results, the results page) on both mobile (375px) and desktop (1440px) shows consistent bold editorial visual language across all four surfaces
  2. `npm run test:run` passes with new assertions in designTokens.test.ts that cover every CSS variable added in Phase 17 — no new token is untested
  3. A grep for hardcoded color values (`text-green-700`, `text-red-700`, `text-emerald-600`, `bg-blue-`, `text-blue-`, and similar Tailwind palette utilities) in all components modified during v3.0 returns zero results
**Plans**: TBD

---

## Progress

**Execution Order:**
v3.0 phases execute in order: 17 -> 18 -> 19 -> 20 -> 21 -> 22. Phases 17 and 18 are the foundation; Phase 17 must complete before any component work (tokens), Phase 18 must complete before Phase 19 (images). Phases 20 and 21 depend on Phase 17 but are independent of each other and can proceed in parallel if resources allow. Phase 22 is the hard gate — no release without it.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Response Experience Overhaul | v1.0 | 6/6 | Complete | 2026-03-17 |
| 2. Fix Review Source Links | v1.0 | 1/1 | Complete | 2026-03-25 |
| 3. Serper Shopping Provider | v1.0 | 1/1 | Complete | - |
| 4. Browse Page Fixes | v1.0 | 1/1 | Complete | - |
| 5. Amazon Creators API Migration | v1.0 | 2/2 | Complete | - |
| 6. Skimlinks Link Wrapper | v1.0 | 3/3 | Complete | 2026-03-25 |
| 7. Skimlinks Middleware + Editor's Picks | v1.0 | 3/3 | Complete | 2026-03-26 |
| 8. Clarifier Suggestion Chips | v1.0 | 3/3 | Complete | - |
| 9. Top Pick Block + Help Me Decide | v1.0 | 3/3 | Complete | 2026-03-25 |
| 10. Impact.com Provider | v1.0 | 2/2 | Complete | 2026-03-25 |
| 11. Viator + CJ Expansion | v1.0 | 4/4 | Complete | 2026-03-26 |
| 12. Navigation Shell | v2.0 | 3/3 | Complete | 2026-03-17 |
| 13. Discover Screen | v2.0 | 3/3 | Complete | 2026-03-17 |
| 14. Chat Screen | v2.0 | 4/4 | Complete | 2026-03-17 |
| 15. Results Screen | v2.0 | 3/3 | Complete | 2026-03-17 |
| 16. Placeholder Routes and Build QA | v2.0 | 1/1 | Complete | 2026-03-17 |
| 17. Token Foundation + Dark Mode Fixes | 2/2 | Complete    | 2026-04-01 | - |
| 18. AI Image Generation | v3.0 | 0/TBD | Not started | - |
| 19. Mosaic Hero | v3.0 | 0/TBD | Not started | - |
| 20. Discover + Browse Page Upgrades | v3.0 | 0/TBD | Not started | - |
| 21. Chat + Results Card Polish | v3.0 | 0/TBD | Not started | - |
| 22. Visual QA + Consistency Pass | v3.0 | 0/TBD | Not started | - |
