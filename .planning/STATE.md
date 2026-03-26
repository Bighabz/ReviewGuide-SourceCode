---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: Core Platform
status: executing
stopped_at: Completed 11-04-PLAN.md
last_updated: "2026-03-26T00:15:00.000Z"
last_activity: "2026-03-26 — Phase 11 complete: Viator + CJ Expansion (4 plans)"
progress:
  total_phases: 16
  completed_phases: 12
  total_plans: 42
  completed_plans: 35
  percent: 83
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-16)

**Core value:** Conversational product discovery that searches live reviews and returns blog-style editorial responses with cross-retailer affiliate links.
**Current focus:** Milestone v2.0 — Frontend UX Redesign (Phase 15 next)

## Current Position

Phase: 11 of 16 (Viator + CJ Expansion) — COMPLETE
Plan: 04 of 04 — COMPLETE
Status: Phase 11 complete — Viator activity search via /search/freetext with Redis caching and PLP fallback, MCP tool wired to travel workflow, CJ expansion documented as human action.
Last activity: 2026-03-26 — Phase 11 complete: Viator + CJ Expansion

Progress: [█████████░] 83%

## Performance Metrics

**Velocity:**
- Total plans completed: 13
- Average duration: ~3 min
- Total execution time: 0.46 hours

## Accumulated Context

### Decisions

- [v1.0]: Fix-first before expanding — broken features undermine trust
- [v1.0]: Skimlinks as catch-all affiliate layer — one integration covers 48,500 merchants
- [v2.0 Init]: Use curated static Amazon data (120+ products) for product images/prices/links — no PA-API needed
- [v2.0 Init]: Frontend UX redesign as major milestone — editorial luxury evolution + app-like fluidity
- [v2.0 Phase 12]: SSE stream-on-tab-switch architecture decision must be made in Phase 12 before Chat screen is modified
- [v2.0 Phase 12]: Use CSS variables exclusively (var(--*)) in all new components — Tailwind dark: utilities are inert with data-theme strategy
- [v2.0 Phase 12]: Use h-dvh (not h-screen) on all full-height containers — iOS keyboard overlap prevention
- [Phase 12-navigation-shell]: Wave 0 RED tests written before production code: behavioral contracts for NavLayout, MobileTabBar, template.tsx, and viewport-fit established in 4 test files
- [Phase 12]: Used calc(0px + env(safe-area-inset-bottom)) for safe area padding — jsdom drops bare env() but preserves calc(), enabling NAV-05 test to pass
- [Phase 12]: MobileTabBar keeps nav always in DOM (animate y) with data-keyboard-open attribute — Framer Motion exit animations don't complete in jsdom so AnimatePresence removal fails keyboard-hide test
- [Phase 12-navigation-shell]: Entry-only animation in template.tsx — exit animations via AnimatePresence+FrozenRouter assessed as too fragile for production
- [Phase 12-navigation-shell]: NavLayout is the single navigation wrapper in layout.tsx — per-page topbar renders prohibited to prevent double navigation bars
- [Phase 12-navigation-shell]: Human verification of navigation shell APPROVED: mobile bottom tab bar, desktop topbar, page transitions, and route exclusions all confirmed working
- [Phase 13-discover-screen]: Discover screen tests import @/app/page — tests fail because DiscoverPage does not exist yet; Plan 02 will implement it
- [Phase 13-02]: Popular chip given default query 'Best products of 2026' so all chip clicks produce /chat?q=...&new=1 per DISC-02 test contract
- [Phase 13-03]: /browse redirects to / permanently via next/navigation redirect() — backward bookmark compatibility
- [Phase 13-03]: Saved, Compare, Profile nav hrefs intentionally kept as /browse placeholders — Phase 16 will assign real routes
- [Phase 13-03]: Human verification of complete Discover screen APPROVED on mobile and desktop — DISC-01, DISC-02, DISC-05 satisfied
- [Phase 14-01]: InlineProductCard and SourceCitations import failures are the correct RED state — components do not exist until Plan 02
- [Phase 14-01]: Colored dot tests use class AND style fallbacks to allow flexible Tailwind/inline implementation choices
- [Phase 14-chat-screen]: review_sources consensus intentionally empty string — blog assistant_text handles editorial prose to avoid Pitfall 3 redundancy
- [Phase 14-chat-screen]: Dual color approach for dots: inline style sets actual color, Tailwind bg- class enables test DOM queryability
- [Phase 14-chat-screen]: Suggestion chips render OUTSIDE the AI bubble — visual independence from content per CHAT-06 spec
- [Phase 14-chat-screen]: MobileHeader back button navigates to / (Discover) not /browse — consistent with Phase 13 route migration
- [Phase 14-chat-screen]: Human verification of complete Phase 14 chat screen APPROVED — all 6 CHAT requirements confirmed on mobile and desktop
- [Phase 15-01]: Wave 0 stub page exports null so Vite resolves import at transform time; component tests fail RED with React "Element type is invalid: null" error — correct Wave 0 state
- [Phase 15-01]: extractResultsData checks both block.data.products and flat block.products to handle normalized and flat block structures from localStorage
- [Phase 15-01]: CSS card accent tints (--card-accent-1 through --card-accent-4) added in both :root and [data-theme="dark"] following established dual-section pattern
- [Phase 15-02]: useState lazy initializer for localStorage avoids useEffect async timing in tests — synchronous init ensures data available on first render
- [Phase 15-02]: Single-grid responsive pattern: combine grid-cols-3 + overflow-x-auto + snap-x on one container — jsdom renders all hidden elements so avoid desktop/mobile duplicates
- [Phase 15-02]: ResultsHeader Share relabeled Copy Link to avoid duplicate getByText conflict with ResultsQuickActions Share button
- [Phase 15-03]: Results page uses 'use client' with useEffect localStorage read — avoids SSR/hydration issues since session data is client-side only
- [Phase 15-03]: MobileHeader expand icon hidden on /results route (already on results page), wired to /results/:sessionId on /chat
- [Phase 15-03]: MobileHeader back arrow navigates to /chat when on /results route — preserves chat→results flow
- [Phase 15-03]: Human verification of complete Phase 15 Results screen APPROVED — all 8 requirements (RES-01 through RES-06, RESP-01, RESP-02) confirmed on mobile and desktop
- [Phase 16-placeholder-routes-and-build-qa]: Placeholder pages use only CSS variables (var(--*)) — no Tailwind dark: utilities, per Phase 12 locked decision
- [Phase 16-placeholder-routes-and-build-qa]: Placeholder pages are pure Server Components (no use-client) — zero interactivity means Static prerender at 189 B each
- [Phase 01-response-experience-overhaul]: All 8 RX requirements verified passing against live stack — no gap-closure plans required
- [Phase 01-response-experience-overhaul]: Phase 1 Response Experience Overhaul accepted as complete by human reviewer on 2026-03-17
- [Phase 04-browse-page-fixes]: amzn.to URLs skip health checker HEAD requests — Amazon returns 403 to bot User-Agents, treated as always-healthy
- [Phase 04-browse-page-fixes]: Added 5th product to menopause supplements topic from existing weight loss topic for parity
- [Phase 04-browse-page-fixes]: Editor's Picks section inserted between editorial rule and Popular Questions on category pages
- [Phase 02-fix-review-source-links]: Citations prefer review_source_urls (Wirecutter, RTINGS) with fallback to normalized_products — backward compatible
- [Phase 02-fix-review-source-links]: source_refs already threaded from Phase 1 work — only "never invent URLs" guard and citations fix were missing
- [Phase 03]: Reuse SERPAPI_API_KEY for Serper shopping — no new credentials needed
- [Phase 03]: Direct retailer URLs without affiliate wrapping for MVP — Skimlinks wrapping deferred to Phase 6
- [Phase 10]: Rate limit set to 2500/hour (safety margin below 3000 actual Impact.com limit)
- [Phase 10]: Impact.com feature flag checked at search_products() call time, not at registration time
- [Phase 10]: Impact.com Url field contains pre-built affiliate tracking links — no manual link construction needed
- [Phase 08]: clarifier_chips is plain List (not Annotated with operator.add) — chips replaced each turn, not accumulated
- [Phase 08]: Fallback and backfill questions include chips: [] — frontend never receives undefined
- [Phase 08]: Chip rendering uses text-[12px] (smaller than next_suggestions text-[13px]) for visual nesting hierarchy
- [Phase 06]: SkimlinksLinkWrapper is standalone service (not BaseAffiliateProvider) -- wraps URLs, does not search for products
- [Phase 06]: 21 excluded domains: 13 Amazon + 8 eBay -- never passed through Skimlinks
- [Phase 06]: Three-tier domain cache: in-memory -> Redis (24h TTL) -> Merchant API
- [Phase 06]: Skimlinks post-processing wired as last step in product_affiliate before return
- [Phase 09]: top_pick LLM call runs in parallel via llm_tasks dict -- no sequential latency hit
- [Phase 09]: Comparison follow-up intercepts before no-data guard to handle empty normalized_products
- [Phase 09]: products_by_provider cap changed from 10 to 5 per provider
- [Phase 09]: New block types added via BLOCK_RENDERERS entry + dedicated component -- no Message.tsx changes needed
- [Phase 11]: Viator uses POST /search/freetext with exp-api-key header (API v2 format, not v1 query param)
- [Phase 11]: activities_viator UI block type avoids conflict with existing plain-text activities from destination_facts
- [Phase 11]: PLP fallback on connection/timeout exceptions; empty list on API error status codes (non-200)
- [Phase 11]: CJ advertiser_ids=joined means approved advertisers auto-appear with zero code change

### Pending Todos

None yet.

### Blockers/Concerns

- [v1.0 Phase 5]: Amazon PA-API v5 retires May 15, 2026 — hard deadline (paused, not cancelled)
- [v1.0 Phase 6-7]: Skimlinks publisher application still pending
- [v2.0 Phase 14]: review_sources bug RESOLVED in Plan 02 — backend now emits review_sources block

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Uncle Mike Response Format and Curated Links Fallback | 2026-03-25 | c3ddebb | [1-uncle-mike-response-format-and-curated-l](./quick/1-uncle-mike-response-format-and-curated-l/) |
| Phase 03 P01 | 5min | 2 tasks | 4 files |

## Session Continuity

Last session: 2026-03-26T00:15:00.000Z
Stopped at: Completed 11-04-PLAN.md
Resume file: None
