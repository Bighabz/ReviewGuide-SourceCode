# Project Research Summary

**Project:** ReviewGuide.ai — AI Shopping Assistant
**Domain:** Conversational commerce, affiliate monetization, cross-retailer product search
**Researched:** 2026-03-15
**Confidence:** HIGH (bugs + fixes), HIGH (affiliate network APIs), MEDIUM-HIGH (UX patterns + Skimlinks)

---

## Executive Summary

ReviewGuide.ai is an editorial AI shopping assistant — Amazon Rufus without the retailer lock-in, Wirecutter with a conversational interface. The product category is well-established and converging fast: Amazon Rufus, Google Shopping AI Mode, ChatGPT Shopping, and Perplexity Shopping all launched or significantly expanded within a 90-day window in late 2025. The core pattern that emerged across all successful implementations is: natural language in, curated shortlist of 3-5 out, progressive narrowing through suggestion chips, culminating in a single opinionated recommendation with explicit "because" reasoning. ReviewGuide.ai already has the LangGraph multi-agent pipeline, state management, and frontend components to execute this pattern — the gaps are primarily in product data coverage (eBay-only results), affiliate link coverage (no catch-all for non-CJ merchants), and conversational UX surface (clarifier agent asks questions in prose, no chips).

There is one hard deadline that overrides all other sequencing decisions: Amazon PA-API v5 is retired on May 15, 2026 — roughly 8 weeks from today. The existing `amazon_provider.py` uses AWS Signature V4 credentials that stop working on that date. The replacement is the Amazon Creators API (OAuth2 client credentials, different credential type). This migration is the single highest-urgency technical item in the entire roadmap. Everything else is additive; this is existential for the Amazon integration.

Beyond the deadline, the strategic opportunity is clear and achievable in a focused development sprint: (1) add Serper.dev shopping as a provider — it uses the existing API key and simultaneously fixes eBay-only results, missing product images, and broader retailer coverage in one new file; (2) implement Skimlinks server-side link wrapper as a catch-all affiliate monetization layer — it requires no API call at link-generation time and covers 48,500+ merchants; (3) add suggestion chips to the clarifier agent's question responses — the highest-impact UX improvement, converting prose questions into tappable 1-click answers that match the universal SOTA pattern. The "top pick with reasoning" editorial block is the differentiator that no competitor offers, and it builds on the LangGraph output format that already exists.

---

## Key Findings

### Recommended Stack

The existing stack (FastAPI + LangGraph, Next.js 14, PostgreSQL + Redis) is the correct foundation and does not need changes. All four research domains confirm that the architecture supports the required capabilities. The gaps are at the provider layer (affiliate integrations), not the infrastructure layer.

**Core technologies for new integrations:**
- Serper.dev shopping endpoint (`https://google.serper.dev/shopping`): product search + images — reuses existing `SERPAPI_API_KEY`, no new credential
- Skimlinks server-side link wrapper (`go.redirectingat.com`): affiliate monetization catch-all — no API call at runtime, URL construction only
- Amazon Creators API (OAuth2): replaces PA-API v5 — new credential type (`AMAZON_CREATORS_CREDENTIAL_ID` + `AMAZON_CREATORS_CREDENTIAL_SECRET`), otherwise same search operations
- Impact.com Catalog API v12: best real-time product search of any standalone affiliate network — keyword + filter, 3,000 req/hour, returns GTIN/ASIN cross-refs

**Providers to defer:**
- Awin: no real-time product search API; feed-ingestion pipeline required; defer until feed infrastructure is built
- Rakuten: XML-only responses; lower priority given Serper covers the same breadth with richer data
- TravelPayouts: strong for flights, but only needed after travel domain UX is addressed

See `affiliate-networks.md` and `skimlinks-integration.md` for full API details.

### Expected Features

**Must have (table stakes — already expected by users in this category):**
- Multi-retailer product search results (not eBay-only)
- Product images in every result card
- Review source attribution with clickable links to Wirecutter, Tom's Guide, Reddit
- Affiliate links on all product recommendations (monetization viability)
- Working Amazon integration (pre-May 2026 deadline)

**Should have (competitive differentiators):**
- Suggestion chips on clarifier questions (converts prose into 1-tap options)
- "Top pick with reasoning" editorial block above product carousel (Wirecutter pattern applied to chat)
- Skimlinks catch-all wrapper on non-Amazon, non-eBay product URLs (monetizes Serper results)
- "Help Me Decide" trigger when user has a shortlist and expresses comparison intent
- Cross-retailer price comparison visibility (unique vs retailer-owned assistants)

**Defer to v2+:**
- Persistent preference memory across sessions (requires consent UX, Pro tier consideration)
- "More like this / Not interested" feedback buttons on product cards (high effort, medium-term)
- Awin feed ingestion pipeline
- Viator Full Access tier (availability check requires separate Viator approval)
- Skimlinks Product Key API for product search (requires account manager approval, not self-serve)
- Per-session conversational memory surfaced as "last time you preferred Sony" prompts

See `shopping-assistant-ux.md` and `product-search-fixes.md` for full feature analysis.

### Architecture Approach

The existing plugin architecture (`BaseAffiliateProvider` + `AffiliateProviderRegistry` + `loader.py`) is the right pattern and handles all new providers without changes to `manager.py`, `registry.py`, or `base.py`. New providers register via decorator; `product_compose.py` iterates `affiliate_products.keys()` dynamically. The main architectural decision for Skimlinks is: implement it as a post-processing middleware in `AffiliateManager` (wrapping non-affiliated URLs after all providers return results) rather than as a search provider, because Skimlinks is a monetization layer, not a product catalog.

**Major components involved in this roadmap:**
1. `SerperShoppingProvider` — new file in `providers/`, 3-step registration, uses existing key
2. `SkimlinksLinkWrapper` + `SkimlinksMerchantValidator` — middleware post-processing, Redis cache for merchant domain list (24h TTL, 1,000 req/hour limit means must cache, never call per-product)
3. `amazon_provider.py` — auth layer swap from AWS Sig V4 to OAuth2; search operations unchanged; image hotlinking constraint enforced
4. `product_compose.py` — 3 targeted edits to thread review source URLs into LLM context, update system prompt, fix `citations` collection
5. `GraphState` + clarifier agent — add `clarifier_chips` field for suggestion chip payloads; new `top_pick` UI block type in frontend

See `product-search-fixes.md` for exact line numbers and code snippets for the `product_compose.py` fixes.

### Critical Pitfalls

1. **Amazon PA-API hard deadline (May 15, 2026)** — AWS Signature V4 credentials stop working. `amazon_provider.py` must be migrated to Creators API (OAuth2 client credentials) before this date. 10 qualified shipped sales required to maintain Creators API access — plan for this activation period. See `affiliate-networks.md` for full migration details.

2. **Skimlinks JS snippet trap** — The most-documented Skimlinks integration is the JavaScript snippet for client-side auto-affiliation. This does NOT work in a FastAPI backend. Use the server-side link wrapper (`go.redirectingat.com`) only. Amazon URLs must never be passed to Skimlinks (Amazon Associates is not in the Skimlinks network). See `skimlinks-integration.md` §11 for full pitfall list.

3. **Skimlinks Merchant API rate limit (1,000 req/hour)** — The merchant domain list must be cached in Redis (24h TTL). Never call the Merchant API per product URL. Without this cache, link validation will be rate-limited immediately at any meaningful query volume.

4. **Awin link builder is not real-time** — Awin's API documentation explicitly states their link builder is "not compatible with real-time link creation in the browser." Do not build an Awin provider that calls their link API at query time; it will fail in production.

5. **Prose-only clarifier questions are a UX anti-pattern** — Every major AI shopping assistant (Rufus, ChatGPT Shopping, Perplexity) uses tappable suggestion chips alongside clarifying questions. Returning prose questions without chips is documented in UX research as the highest-friction clarification pattern, with clarification abandonment rates above 30% when chips are absent.

6. **Amazon image hotlinking policy** — Amazon product images cannot be cached, stored, or re-hosted. They must be displayed via direct hotlink to Amazon's CDN URL as returned by the API. Any violation risks account termination. The current mock mode uses `placehold.co` — acceptable for dev, but production must use direct API image URLs.

7. **Showing 15+ products** — The "paradox of choice" effect is well-documented in shopping UX research. CP AXTRA reported 108% increase in basket additions when showing "Top 5" vs larger grids. Hard limit all product responses to 3-5 products. Comparison tables should cap at 3-4 items.

---

## Risk Matrix

| Risk | Severity | Likelihood | Deadline | Mitigation |
|------|----------|------------|----------|------------|
| Amazon PA-API shutdown | Critical — Amazon integration dies entirely | Certain | May 15, 2026 | Migrate `amazon_provider.py` to Creators API now |
| Skimlinks publisher rejection (3% acceptance) | High — catch-all monetization strategy fails | Low (strong content fit) | Pre-launch | Apply early; ensure editorial content is prominent before applying |
| Serper.dev shopping image policy at scale | Medium — potential ToS violation | Low for MVP traffic | None | Verify Serper ToS for shopping image display; standard industry practice |
| Skimlinks Product Key approval delay | Medium — affects Editor's Picks feature | Possible | None | Design Editor's Picks to work with existing provider data; treat Product Key as enhancement |
| Amazon 10-sales threshold not met | Medium — Creators API access suspended | Possible for new launch | Ongoing | Build Serper Shopping as primary search fallback so Amazon downtime doesn't break product search |
| amzn.to CORS resolution failure | Low-Medium — browse page links broken | Possible | None | Use as `href` only; never `fetch()`; skip in link health checker |

---

## Implications for Roadmap

### Phase 1: Fix What's Broken (immediate, ~1-2 days)

**Rationale:** Three bugs (eBay-only results, missing review links, broken amzn.to links) are preventing the core product from working correctly. Two of them are diagnosed to specific lines in `product_compose.py`. Fixing these before adding new capabilities ensures a stable baseline.

**Delivers:** Functional multi-retailer product search with images; review source attribution in blog-style responses; working amzn.to links on browse pages.

**Addresses:**
- Bug 1 (eBay-only): Add `SerperShoppingProvider` — new file + 3-line registration, uses existing Serper key. Simultaneously resolves Bug 4 (missing images).
- Bug 2 (review links): 3 edits in `product_compose.py` — thread `source.url` into `blog_data_parts`, update system prompt, fix `citations` collection.
- Bug 3 (amzn.to): Diagnostic log check + guard in `link_health_checker.py`; ensure links rendered as `href` only.

**Avoids:** Shipping new features on a broken foundation.

**Research flag:** No deeper research needed — root causes confirmed in `product-search-fixes.md` with exact line numbers.

---

### Phase 2: Amazon Migration (urgent, ~2-3 days, deadline May 15 2026)

**Rationale:** This is a hard deadline. PA-API v5 retires May 15, 2026. The authentication swap is well-understood; the risk is timeline, not technical complexity.

**Delivers:** Amazon product search that continues working after May 15. OAuth2 client credentials replacing AWS Signature V4. Region-based credentials covering NA, EU, FE.

**Addresses:**
- `amazon_provider.py` auth layer: swap to Creators API OAuth2 (`AMAZON_CREATORS_CREDENTIAL_ID`, `AMAZON_CREATORS_CREDENTIAL_SECRET`)
- Token refresh pattern: extract `OAuthTokenMixin` from eBay provider pattern (same 1-hour token + 5-minute buffer approach)
- Image hotlinking enforcement: ensure no Amazon image URLs are cached or re-hosted
- Per-region enable flags: `AMAZON_API_ENABLED_NA`, `AMAZON_API_ENABLED_EU` (10-sales threshold enforced per region)

**Avoids:** Amazon integration silently going dark on May 15.

**Research flag:** No deeper research needed — full Creators API spec in `affiliate-networks.md`. One open question: confirm 10-sales activation timeline with Associates Central before migration.

---

### Phase 3: Affiliate Coverage (Skimlinks, ~2-3 days)

**Rationale:** After Phase 1 adds Serper Shopping, its results will have direct retailer URLs with no affiliate tracking. Skimlinks server-side wrapper monetizes those URLs instantly with zero additional API calls at query time. This is the highest-ROI affiliate addition relative to implementation effort.

**Delivers:** Affiliate link monetization on Serper Shopping results and any other non-Amazon, non-eBay product URLs. Coverage across 48,500+ merchants via a single integration.

**Addresses:**
- `SkimlinksLinkWrapper`: URL construction helper (`go.redirectingat.com/?id=...&url=...&xs=1`)
- `SkimlinksMerchantValidator`: Redis-cached merchant domain list (24h TTL, populated by daily background refresh from Merchant API)
- `AffiliateManager` post-processing middleware: after all providers return results, wrap non-affiliated URLs through Skimlinks if domain is in merchant cache
- Environment variables: `SKIMLINKS_PUBLISHER_ID`, `SKIMLINKS_CLIENT_ID`, `SKIMLINKS_CLIENT_SECRET`, `SKIMLINKS_API_ENABLED`

**Pre-condition:** Skimlinks publisher application must be submitted and approved (~2 business days). Apply immediately — do not wait until Phase 3 begins.

**Avoids:** Building against Skimlinks JS snippet (server-side wrapper only); wrapping Amazon URLs through Skimlinks (Amazon is not in the network); calling Merchant API per product request (Redis cache required).

**Research flag:** No deeper research needed — full implementation pattern in `skimlinks-integration.md` §10. Publisher approval policy for AI-generated content is LOW confidence — verify before submitting application.

---

### Phase 4: Conversational UX Upgrade (high-impact, ~3-4 days)

**Rationale:** The LangGraph clarifier agent already collects context correctly. The UX gap is that clarifying questions are returned as prose, while every major competitor uses tappable suggestion chips. This is the single change with the highest conversion impact per hour of engineering effort. The "top pick with reasoning" block is the key product differentiator.

**Delivers:** Suggestion chips on clarifier agent responses; "Top Pick" editorial block type above product carousels; "Help Me Decide" auto-trigger on comparison intent.

**Addresses:**
- Clarifier agent: add `clarifier_chips` field to `GraphState` (with default in `initial_state` in `chat.py` — required by LangGraph channels, see deployment lessons); clarifier returns 2-4 chip options alongside prose question
- Frontend `ChatContainer`: render chip buttons below clarifier messages; chips dispatch `sendSuggestion` custom event on click (existing pattern)
- New `top_pick` UI block type: fields `product`, `headline_reason`, `who_its_for`, `who_should_look_elsewhere`; rendered above `ProductCarousel` in `Message.tsx`
- "Help Me Decide" intent trigger: detect comparison intent follow-ups against active shortlist; auto-return `ComparisonTable` block

**Avoids:** Asking 3+ clarifying questions before showing any products (show shortlist after 1 question); restarting context on follow-up messages (GraphState must persist shortlist); showing 8+ products in comparison tables.

**Research flag:** Frontend chip rendering pattern needs UI design decision — match existing Editorial Luxury theme. No API research needed.

---

### Phase 5: Expanded Provider Network (medium priority, ~1 week)

**Rationale:** After phases 1-4, the core product works correctly and is monetized. Phase 5 adds depth: more affiliate networks for better commission rates and product coverage.

**Delivers:** Impact.com integration (best real-time catalog search, 3,000 req/hour); Viator Basic tier (zero approval barrier, activities/experiences for travel); CJ advertiser expansion (no code change — apply to Best Buy, Dell, HP, Target, Wayfair in CJ dashboard).

**Addresses:**
- `ImpactAffiliateProvider`: HTTP Basic Auth, `/Catalogs/ItemSearch` v12 endpoint, rich GTIN/ASIN cross-refs
- `ViatorProvider`: API key header auth, `/products/search` for activities, cookie-based tracking (append params to viator.com URL)
- CJ advertiser applications: business action, no code change; once approved `advertiser-ids=joined` auto-includes

**Deferred from this phase:** Awin (feed ingestion pipeline required), TravelPayouts (flights complement — lower priority than product search expansion), Booking.com (approval process paused as of March 2026).

**Research flag:** Impact.com catalog v12 requirement and Viator Basic/Full access tier distinction are well-documented. No additional research needed.

---

### Phase Ordering Rationale

- Phase 1 before Phase 2: bugs block product quality for all users today; Amazon migration has a deadline but 8 weeks of runway. Fix visible breakage first.
- Phase 2 before Phase 3: Amazon must work before expanding affiliate coverage; a broken Amazon integration undermines the coverage story.
- Phase 3 (Skimlinks) before Phase 4 (UX): monetization enables revenue from any improved engagement. Getting Skimlinks live means every chip interaction that leads to a purchase is tracked.
- Phase 4 (UX) before Phase 5 (providers): better UX extracts more value from existing providers. Adding 3 more providers with the same broken clarifier UX gives diminishing returns.
- Phase 5 last: incremental coverage improvement, each addition is independent.

### Research Flags

**Phases that need no additional research before implementation:**
- Phase 1 (bug fixes): root causes confirmed, exact code locations identified in `product-search-fixes.md`
- Phase 2 (Amazon migration): full Creators API spec in `affiliate-networks.md`; one verification needed (10-sales activation timeline)
- Phase 3 (Skimlinks): full implementation pattern in `skimlinks-integration.md` §10; confirm AI content policy before publisher application

**Phases that may need design decisions before implementation:**
- Phase 4 (UX): chip rendering needs to match Editorial Luxury theme (DM Sans, warm ivory palette); `top_pick` block needs design mockup before frontend implementation
- Phase 5 (providers): Impact.com catalog search response may have schema differences vs eBay/CJ; verify v12 field mapping against `AffiliateProduct` dataclass before writing provider

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Bug root causes | HIGH | Confirmed by reading actual codebase files; exact line numbers identified |
| Serper shopping endpoint | HIGH | Verified via TypeScript SDK source + SerpApi docs; same key works |
| Amazon Creators API | HIGH | Official docs + third-party migration guides; deadline confirmed |
| Impact.com API | HIGH | Official rate limits and endpoint schema from Impact developer portal |
| Awin | HIGH | Feed-only limitation explicitly stated in Awin documentation |
| Skimlinks link wrapper | HIGH | URL format confirmed via multiple independent sources (Drupal, Datafeedr, SDK) |
| Skimlinks Product Key API | MEDIUM | Apiary docs current; availability/terms require account manager confirmation |
| Skimlinks publisher approval for AI content | LOW | No explicit policy found; verify before submitting application |
| UX pattern benchmarks | MEDIUM-HIGH | Multiple secondary analyses; primary platform design docs not public |
| Booking.com approval status | MEDIUM | Connectivity pause confirmed but terms may have changed |
| amzn.to failure mode | MEDIUM | Root cause inferred from browser security rules; runtime log check needed |
| Rakuten XML schema | MEDIUM | Endpoint documented; field mapping vs `AffiliateProduct` not verified |

**Overall confidence:** HIGH for phases 1-3, MEDIUM-HIGH for phases 4-5.

### Gaps to Address

- **Skimlinks AI content policy**: Before submitting publisher application, confirm with Skimlinks account team that AI-generated shopping recommendations qualify as "original content that adds value." Their stated customer base (Wirecutter, BuzzFeed, Vox) suggests yes, but explicit confirmation reduces rejection risk.

- **Amazon 10-sales activation window**: The Creators API requires 10 qualified shipped sales in trailing 30 days. Confirm with Associates Central whether the existing associate account qualifies or whether a new activation period is needed post-migration. Plan for potential 30-day gap in Amazon API access.

- **Serper.dev shopping ToS at scale**: The shopping endpoint `imageUrl` returns Google-hosted CDN thumbnails. Standard practice in the industry (same images shown in Google Shopping SERP), but verify Serper's ToS for commercial product display before high-volume deployment.

- **amzn.to exact failure mode**: The specific failure in `link_health_checker.py` requires a runtime log check before implementing the fix. Add logging before the health check for amzn.to URLs to confirm whether the failure is in the health checker, the frontend fetch, or URL format.

- **Impact.com catalog field mapping**: Before writing `ImpactAffiliateProvider`, map Impact's v12 response fields to the `AffiliateProduct` dataclass. The research confirms field names (`ImageUrl`, `CurrentPrice`, `StockAvailability`) but the exact nested structure needs validation against a test API call.

---

## Sources

### Primary (HIGH confidence)
- Skimlinks Apiary docs (Merchant, Product Key, Reporting APIs): `jsapi.apiary.io/apis/skimlinks*`
- Impact.com Publisher API docs: `integrations.impact.com/impact-publisher/reference/`
- Amazon Creators API official docs: `affiliate-program.amazon.com/creatorsapi/docs/`
- Serper.dev TypeScript SDK (shopping endpoint field definitions): gist by transitive-bullshit
- Awin Publisher API / Link Builder docs: `help.awin.com/apidocs`, `awin.com/us/how-to-use-awin/link-builder-api`
- Viator Affiliate API access tier docs: `partnerresources.viator.com/travel-commerce/levels-of-access/`

### Secondary (MEDIUM confidence)
- Amazon Rufus behavioral analysis: `retailtechinnovationhub.com`, `aboutamazon.com/news/retail/`
- ChatGPT Shopping product sourcing analysis: `searchengineland.com` (83% Google Shopping finding)
- Perplexity Shopping feature docs: `perplexity.ai/hub/blog/shop-like-a-pro`
- Skimlinks server-side link format: Drupal module issue tracker, Datafeedr documentation
- Skimlinks vs Sovrn comparison: `mrwebcapitalist.com`
- Progressive disclosure UX research: `aiuxdesign.guide`, `aipositive.substack.com`

### Tertiary (LOW confidence, needs verification)
- Skimlinks publisher approval policy for AI-generated content: no primary source found
- amzn.to link expiry behavior: no official Amazon documentation found; behavior inferred
- Booking.com Demand API production rate limits: contact Account Manager required

---

*Research completed: 2026-03-15*
*Ready for roadmap: yes*
