# ReviewGuide.ai

## What This Is

An AI-powered shopping and travel assistant — like Amazon's Rufus, but for the entire web. Users ask questions in natural language ("what's the best mattress for back pain under $800?") and get editorial-quality blog-style responses with product recommendations, comparisons, review summaries, and affiliate links across multiple retailers. Monetized through affiliate commissions from Amazon, CJ, eBay, Skimlinks (48,500+ merchants), Booking.com, Expedia, Viator, and TravelPayouts.

## Core Value

Conversational product discovery that searches live reviews and returns blog-style editorial responses with cross-retailer affiliate links — not locked to any single store.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ LangGraph multi-agent chat pipeline (safety → intent → clarifier → planner → executor) — existing
- ✓ SSE streaming responses with typed ui_blocks — existing
- ✓ eBay affiliate product search with link generation — existing
- ✓ Amazon affiliate provider (infrastructure built, blocked on PA-API key) — existing
- ✓ CJ affiliate provider with XML parsing and Redis cache — existing
- ✓ Live review search via Serper.dev/SerpAPI — existing
- ✓ Blog-style product compose output — existing (Phase 4 rewrite)
- ✓ Product comparison tables — existing
- ✓ Travel: hotel search (Amadeus, Booking.com, Expedia) — existing
- ✓ Travel: flight search (Amadeus, Skyscanner) — existing
- ✓ Travel: excursions/activities (Viator) — existing
- ✓ Travel: itinerary composition — existing
- ✓ Browse pages with 10 category verticals — existing
- ✓ Product category disambiguation for ambiguous queries — existing
- ✓ Multi-turn conversations via Redis halt-state — existing
- ✓ Anonymous user sessions (no login required) — existing
- ✓ Admin panel with React Admin — existing
- ✓ Privacy policy, affiliate disclosure, terms of service — existing
- ✓ Editorial luxury theme (DM Sans + Instrument Serif, warm ivory/charcoal) — existing
- ✓ Rate limiting and tiered API routing (66 tests) — existing
- ✓ Langfuse observability and OpenTelemetry tracing — existing
- ✓ Railway (backend) + Vercel (frontend) deployment — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] Fix: review source links missing from blog-style responses (lost in product_compose refactor)
- [ ] Fix: eBay is only returning actual search results (Amazon PA-API key needed or alternative)
- [ ] Fix: static Amazon amzn.to affiliate links not resolving in curated content
- [ ] Fix: truncated affiliate link in menopause supplements category
- [ ] Re-enable Editor's Picks on browse pages (blocked on product images — need PA-API or Skimlinks)
- [ ] Integrate Skimlinks as catch-all affiliate aggregator (48,500 merchants, one API)
- [ ] Expand vertical coverage: automobiles, car rentals, car parts, mattresses, home goods, appliances
- [ ] Smarter guided discovery: Rufus-style "what do you need?" → narrowing → confident recommendation
- [ ] Better product data: real-time pricing from multiple sources, richer metadata
- [ ] Cross-retailer price comparison: same product across Amazon, Walmart, Best Buy, etc.

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- User accounts / login — anonymous-first for v1, reduces friction
- Price alerts / auto-buy — requires accounts and notification infrastructure, defer to v2
- Mobile app — web-first, responsive design covers mobile
- Real-time chat/messaging — not a social platform
- Stored product database — live search is the differentiator (always fresh data)
- Post-purchase support — we're an affiliate, not a retailer

## Current Milestone: v3.0 Visual Overhaul — "Bold Editorial"

**Goal:** Full site visual refresh with Shopify-level polish — bold colors, AI-generated product imagery, premium product cards — while keeping the warm editorial foundation.

**Target features:**
- Shopify-style mosaic hero on landing page with bold & colorful AI-generated product images
- Full site visual refresh: landing, browse, chat, results, product cards
- Keep light/ivory base but inject bold accent colors, stronger typography, more visual punch
- Rich info product cards: keep pros/cons/ratings but premium polish, better spacing, subtle animations
- Cleaner "Where to Buy" section (max 3 deduped offers, proper merchant labels)
- Image priority: Serper/Google > Amazon > eBay (highest quality first)
- AI-generated product category images (bold, colorful, editorial) for hero, browse, and fallbacks

**Design reference:** Shopify free-trial page (product mosaic collage), adapted to ReviewGuide editorial voice

## Context

ReviewGuide.ai is a brownfield project with a working full-stack deployment. The core chat pipeline, travel features, and browse experience are functional. The main gaps are:

1. **Affiliate coverage is thin** — only eBay returns real results. Amazon PA-API key isn't available yet, CJ has limited advertisers (Apple Vacations + Audiobooks). Skimlinks would solve this in one integration.
2. **Blog-style responses lost review links** — the product_compose Phase 4 rewrite (`bd4b5c3`) broke review source attribution.
3. **Curated content disabled** — Editor's Picks and Staff Picks were removed from browse pages because Amazon ASIN images broke without PA-API. The curated link data still exists in `curatedLinks.ts`.
4. **Vertical coverage** — currently electronics + travel + health/wellness/fashion/home browse categories, but the AI can only search effectively for products eBay carries. Need broader affiliate network coverage before adding auto/rental/car parts verticals.

The existing plan doc (`docs/plans/2026-02-27-cj-integration-and-curated-content.md`) partially implemented CJ integration — config, provider, loader, and API endpoint are done. Frontend curated picks were built then disabled.

**Tech environment:** FastAPI + LangGraph backend on Railway, Next.js 14 frontend on Vercel, PostgreSQL + Redis, OpenAI GPT-4o for LLM, Serper.dev for live review search.

**Affiliate networks mentioned for future:** Impact.com, Rakuten Advertising, Awin, Skimlinks (priority), Booking.com (direct), TravelPayouts, eBay, Amazon Associates. Full ideas list in `docs/ideas.md`.

## Constraints

- **Amazon PA-API**: Don't have full API key yet — limits product images and metadata. Can't rely on Amazon as primary product source.
- **Affiliate approvals**: CJ, Impact, Rakuten, Awin require publisher applications per advertiser. Coverage grows over time, not instantly.
- **No stored inventory**: All product data comes from live search (SerpAPI/Serper.dev) and affiliate API calls. No product database to maintain, but dependent on external API availability.
- **Budget**: Skimlinks takes a commission cut (~25% of affiliate revenue) — tradeoff for coverage breadth.
- **Tech stack**: Committed to FastAPI + Next.js 14 + LangGraph. No stack changes.
- **Deployment**: Railway (backend) + Vercel (frontend). CORS regex required for Vercel preview URLs.

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Live search over stored DB | Always-fresh reviews, no data pipeline to maintain | ✓ Good — core differentiator |
| Skimlinks as catch-all affiliate layer | One integration covers 48,500 merchants vs integrating each network | — Pending |
| Fix-first before expanding | Broken features undermine trust; fix review links, Amazon, eBay-only before adding verticals | — Pending |
| Anonymous-first (no accounts v1) | Reduces friction, faster to ship, accounts add complexity | — Pending |
| Blog-style editorial responses | Differentiates from generic product cards; matches editorial luxury brand | ✓ Good |
| Keep direct relationships for top programs | Amazon, Booking, Viator, Expedia get better commission rates than through Skimlinks | — Pending |

| Frontend UX redesign as v2.0 milestone | Editorial luxury evolution + app-like fluidity, mobile-first | — Pending |
| Use curated static Amazon data for product cards | 120+ products with verified images/prices/affiliate links already exist | ✓ Good |

---
*Last updated: 2026-04-01 after v3.0 milestone start*
