---
phase: 01-response-experience-overhaul
plan: 02
subsystem: api
tags: [asyncio, parallelism, performance, fastapi, python, serpapi, langchain]

# Dependency graph
requires:
  - phase: 01-response-experience-overhaul
    provides: Research identifying sequential bottlenecks in product_affiliate, review_search, and planner_agent

provides:
  - Parallel per-product search within product_affiliate using asyncio.gather
  - review_search capped at 3 products with 8s per-product timeout via asyncio.wait_for
  - review_search and product_affiliate merged into a single parallel step in fast-path plan

affects:
  - 01-response-experience-overhaul
  - Any phase touching product_affiliate, review_search, or planner_agent

# Tech tracking
tech-stack:
  added: []
  patterns:
    - asyncio.gather for fan-out parallelism within a single provider's per-product searches
    - asyncio.wait_for for per-item timeout enforcement in gather loops
    - Collocation of independent tools in a single parallel plan step to eliminate sequential gaps

key-files:
  created: []
  modified:
    - backend/mcp_server/tools/product_affiliate.py
    - backend/mcp_server/tools/review_search.py
    - backend/app/agents/planner_agent.py
    - backend/tests/test_product_affiliate.py
    - backend/tests/test_review_search.py

key-decisions:
  - "review_search reduced from [:5] to [:3] products — eliminates 2 extra Serper calls on the critical path without meaningfully impacting recommendation quality"
  - "PER_PRODUCT_TIMEOUT_S = 8 — sufficient for Serper review searches; prevents one slow product from blocking all others"
  - "review_search and product_affiliate share the same parallel plan step — both read product_names from the prior product_search step and have no mutual dependency, so no correctness risk"

patterns-established:
  - "Per-item parallelism pattern: use asyncio.gather(*[coro(item) for item in items]) instead of for loops inside async helpers"
  - "Per-item timeout pattern: wrap individual coroutines with asyncio.wait_for before gathering"

requirements-completed:
  - RX-03
  - RX-04
  - RX-05

# Metrics
duration: 5min
completed: 2026-03-16
---

# Phase 1 Plan 02: Backend Parallelism Improvements Summary

**asyncio.gather for per-product searches in product_affiliate, 3-product cap with 8s timeout in review_search, and review_search + product_affiliate collocated in one parallel fast-path step**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-16T01:43:04Z
- **Completed:** 2026-03-16T01:48:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Replaced sequential `for product_name in products_to_search` loop in `product_affiliate.search_provider()` with `asyncio.gather` over per-product coroutines — all provider calls for a given provider now start concurrently
- Reduced `review_search` from searching 5 products to 3, and wrapped each `client.search_reviews()` call with `asyncio.wait_for(timeout=8)` so a single slow Serper request cannot delay all others
- Merged the previously-sequential `review_search` and `product_affiliate` steps into a single `parallel=True` step in `_create_fast_path_product_plan()` — combined estimated latency saving of ~20-30s on the critical path

## Task Commits

Each task was committed atomically:

1. **Task 1: Parallelize per-product search within product_affiliate** - `9292604` (feat)
2. **Task 2: Reduce review_search to 3 products with per-product timeout** - `7e65739` (feat)
3. **Task 3: Put review_search + product_affiliate in same parallel step** - `ce30f45` (feat)

## Files Created/Modified

- `backend/mcp_server/tools/product_affiliate.py` - Replaced for-loop in `search_provider()` with `asyncio.gather(*search_tasks)` via `search_single_product()` inner coroutine
- `backend/mcp_server/tools/review_search.py` - Changed `[:5]` to `[:3]`, added `PER_PRODUCT_TIMEOUT_S = 8`, wrapped each task with `asyncio.wait_for`
- `backend/app/agents/planner_agent.py` - Merged review_search and product_affiliate into a single parallel step in `_create_fast_path_product_plan()`; step count reduced from 6 to 5
- `backend/tests/test_product_affiliate.py` - Updated RED stubs (RX-03, RX-05) to real GREEN assertions
- `backend/tests/test_review_search.py` - Updated RED stub (RX-04) to source-code inspection test

## Decisions Made

- Used a `search_single_product()` inner coroutine within `search_provider()` so the `base_search_kwargs` dict (including optional `country_code` detection) is computed once and shared across all per-product tasks, avoiding redundant `inspect.signature()` calls
- Chose source-code inspection (via `inspect.getsource`) for the RX-04 test rather than a full integration mock — simpler and sufficient to verify the slice and timeout constant are in place
- Pre-existing failure `test_compose_with_review_data` (review_sources block not emitted by product_compose) documented in `deferred-items.md`; confirmed it was failing before this plan's changes

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Pre-existing test failure in `TestProductComposeWithReviews::test_compose_with_review_data` (product_compose does not emit `review_sources` UI block). Confirmed pre-existing by stashing changes and re-running. Documented in `.planning/phases/01-response-experience-overhaul/deferred-items.md`.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- RX-03, RX-04, RX-05 complete and GREEN
- Fast-path product plan now has 5 steps instead of 6
- Plan 01-03 can proceed — no blockers from this plan

---
*Phase: 01-response-experience-overhaul*
*Completed: 2026-03-16*

## Self-Check: PASSED

- All 5 modified/created files confirmed on disk
- All 3 task commits confirmed in git log (9292604, 7e65739, ce30f45)
- 35 tests pass, 1 pre-existing failure excluded (test_compose_with_review_data — documented in deferred-items.md)
