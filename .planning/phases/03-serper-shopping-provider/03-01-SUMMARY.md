---
phase: 03-serper-shopping-provider
plan: 01
subsystem: api
tags: [serper, google-shopping, affiliate, redis-cache, httpx, multi-retailer]

# Dependency graph
requires:
  - phase: 01-response-experience-overhaul
    provides: affiliate provider registry and product compose pipeline
provides:
  - SerperShoppingProvider registered as "serper_shopping" in AffiliateProviderRegistry
  - Multi-retailer Google Shopping results with product images, prices, merchant names
  - Redis-cached Serper API responses (1-hour TTL)
  - serper_shopping entry in PROVIDER_CONFIG (product_compose.py) with order 3
affects: [04-browse-page-fixes, 06-skimlinks-integration]

# Tech tracking
tech-stack:
  added: [serper.dev shopping API]
  patterns: [provider-registry-decorator, redis-cache-with-retry, price-string-parsing]

key-files:
  created:
    - backend/app/services/affiliate/providers/serper_shopping_provider.py
    - backend/tests/test_serper_shopping_provider.py
  modified:
    - backend/app/services/affiliate/loader.py
    - backend/mcp_server/tools/product_compose.py

key-decisions:
  - "Reuse SERPAPI_API_KEY for Serper shopping — no new credentials needed"
  - "Direct retailer URLs (no affiliate wrapping) for MVP — Skimlinks integration deferred to Phase 6"
  - "Cache TTL 3600s (1 hour) matches CJ provider pattern for consistency"

patterns-established:
  - "Serper shopping provider pattern: POST to google.serper.dev/shopping with X-API-KEY header"
  - "Price parsing: strip $ and commas, float() with 0.0 fallback on failure"

requirements-completed: [FIX-02, FIX-03, SRCH-01, SRCH-02, SRCH-03]

# Metrics
duration: 5min
completed: 2026-03-25
---

# Phase 03 Plan 01: Serper Shopping Provider Summary

**SerperShoppingProvider calling Google Shopping via Serper.dev for multi-retailer products with images, prices, and merchant names — cached in Redis for 1 hour**

## Performance

- **Duration:** 4 min 31 sec
- **Started:** 2026-03-25T23:41:49Z
- **Completed:** 2026-03-25T23:46:20Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Implemented SerperShoppingProvider with full BaseAffiliateProvider interface (search_products, generate_affiliate_link, check_link_health, get_provider_name)
- Product search returns results from multiple retailers (Best Buy, Walmart, Amazon, Target, etc.) with product images from Serper imageUrl field
- Redis caching prevents duplicate Serper API calls for identical queries within 1-hour window
- Provider registered in AffiliateProviderRegistry, loader.py, and product_compose.py PROVIDER_CONFIG
- 20 unit tests covering all requirements (SRCH-01/02/03, FIX-02/03)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for SerperShoppingProvider** - `79a8d54` (test)
2. **Task 1 GREEN: Implement SerperShoppingProvider** - `2fa5230` (feat)
3. **Task 2: Register provider in loader.py and product_compose.py** - `b1b8f82` (feat)

_Note: Task 1 followed TDD (RED then GREEN). No refactoring needed._

## Files Created/Modified

- `backend/app/services/affiliate/providers/serper_shopping_provider.py` - New provider: Serper.dev shopping API integration with Redis cache
- `backend/tests/test_serper_shopping_provider.py` - 20 unit tests: API call, multi-retailer, images, cache, price filtering, error handling
- `backend/app/services/affiliate/loader.py` - Added "serper_shopping": lambda: {} to _PROVIDER_INIT_MAP
- `backend/mcp_server/tools/product_compose.py` - Added serper_shopping to PROVIDER_CONFIG with order 3

## Decisions Made

- Reused SERPAPI_API_KEY for Serper shopping endpoint — no new environment variables or API credentials needed
- Direct retailer URLs without affiliate wrapping for MVP (Skimlinks integration planned for Phase 6)
- Cache TTL set to 3600 seconds (1 hour) matching existing CJ provider caching pattern
- Product ID falls back to "serper_{position}" when Serper response lacks productId field

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- product_compose.py serper_shopping entry was already committed by a parallel agent (commit 8052427 in Phase 02 execution), so the Edit was a no-op for that file. loader.py entry was committed normally. No functional impact.

## User Setup Required

None - no external service configuration required. Provider reuses existing SERPAPI_API_KEY environment variable.

## Next Phase Readiness

- SerperShoppingProvider is live and will be auto-discovered by the loader on next backend restart
- Product queries will return multi-retailer results with images when SERPAPI_API_KEY is set
- Phase 6 (Skimlinks) can wrap the direct retailer URLs returned by this provider

## Self-Check: PASSED

All files exist, all commits verified, 20/20 tests passing.

---
*Phase: 03-serper-shopping-provider*
*Completed: 2026-03-25*
