---
phase: 09-top-pick-block-help-me-decide
plan: 02
subsystem: api
tags: [product_compose, top_pick, comparison, llm, asyncio, python]

requires:
  - phase: 09-01
    provides: RED test contracts for UX-03, UX-04, UX-05
provides:
  - top_pick block generation via parallel LLM call in product_compose
  - 5-product cap on products_by_provider (was 10)
  - Comparison follow-up detection with 14 comparison signals
  - product_comparison block output on follow-up queries
affects: [09-03, frontend BlockRegistry]

tech-stack:
  added: []
  patterns: [_is_comparison_follow_up early intercept pattern, top_pick LLM in parallel batch]

key-files:
  created: []
  modified:
    - backend/mcp_server/tools/product_compose.py

key-decisions:
  - "top_pick LLM call runs in parallel via llm_tasks dict (no sequential latency hit)"
  - "Comparison follow-up intercepts BEFORE the no-data guard to handle empty normalized_products"
  - "products_by_provider cap changed from 10 to 5 per provider"

patterns-established:
  - "Early intercept pattern for follow-up detection before data guards"
  - "Parallel LLM coroutine injection via llm_tasks dict for new block types"

requirements-completed: [UX-03, UX-04, UX-05]

duration: 2min
completed: 2026-03-25
---

# Phase 9 Plan 02: Backend Top Pick, 5-Product Cap, Comparison Follow-up Summary

**product_compose returns top_pick block at index 0, caps products at 5, and auto-detects comparison follow-ups with 14 signal words**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-25T23:59:00Z
- **Completed:** 2026-03-26T00:01:00Z
- **Tasks:** 1 (5 targeted changes)
- **Files modified:** 1

## Accomplishments
- _is_comparison_follow_up() helper with 14 comparison signals detects "how do these compare?", "help me decide", etc.
- Early intercept returns product_comparison block from cached last_search_context
- products_by_provider hard-capped at 5 (was 10)
- top_pick LLM coroutine added to parallel batch (top_pick_composer agent)
- top_pick block assembled at index 0 of ui_blocks with product_name, headline, best_for, not_for, image_url, affiliate_url
- All 11 backend tests pass GREEN (8 existing + 3 new)

## Task Commits

1. **Task 1: Backend implementation** - `c268a41` (feat)

## Files Created/Modified
- `backend/mcp_server/tools/product_compose.py` - Added comparison follow-up detection, 5-product cap, top_pick LLM task and block assembly

## Decisions Made
- top_pick LLM uses response_format json_object for reliable parsing
- Comparison follow-up early return prevents unnecessary LLM calls when products are already known
- Best product selection uses deterministic quality_score sorting (same as editorial "Best Overall" label)

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend produces top_pick blocks for Plan 03 frontend to render
- All backend tests GREEN

---
*Phase: 09-top-pick-block-help-me-decide*
*Completed: 2026-03-25*
