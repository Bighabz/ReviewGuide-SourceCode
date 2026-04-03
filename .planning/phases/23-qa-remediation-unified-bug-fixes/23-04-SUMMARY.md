---
phase: 23-qa-remediation-unified-bug-fixes
plan: "04"
subsystem: api
tags: [python, fastapi, langgraph, product-search, product-compose, tdd, budget-filtering, accessory-suppression]

# Dependency graph
requires:
  - phase: 23-qa-remediation-unified-bug-fixes
    provides: Product compose bug fixes baseline (23-01 through 23-03)
provides:
  - Accessory suppression at product-name level in product_compose.py
  - Budget enforcement via _parse_budget() / _extract_price() helpers
  - Anti-accessory instruction in product_search.py LLM system prompt
  - 2 new passing tests (test_accessory_suppression, test_budget_enforcement)
affects: [product-compose, product-search, qa-remediation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD: RED (failing tests) then GREEN (implementation) commit pattern"
    - "user_message_lower computed once at function scope, reused across all accessory checks"
    - "_parse_budget() handles under/range/around budget string variants"
    - "Budget filtering preserves all offers if ALL exceed budget (honest pricing fallback)"

key-files:
  created: []
  modified:
    - backend/mcp_server/tools/product_compose.py
    - backend/mcp_server/tools/product_search.py
    - backend/tests/test_product_compose.py

key-decisions:
  - "Accessory suppression applied at three layers: products_with_offers loop, review_bundles blog iteration, and fallback card path — not just offer title level"
  - "Budget enforcement keeps all offers when all exceed budget to avoid empty results (honest pricing fallback)"
  - "_parse_budget() returns (None, None) on no match so filtering is only activated when budget string is parseable"
  - "user_message_lower defined at function entry scope — reused in both compose loop and blog iteration to avoid redundant .lower() calls"

patterns-established:
  - "Accessory intent detection: skip suppression when user query itself contains accessory keyword"

requirements-completed:
  - QAR-04
  - QAR-05

# Metrics
duration: 6min
completed: 2026-04-03
---

# Phase 23 Plan 04: Accessory Suppression and Budget Enforcement Summary

**Product-name-level accessory suppression + numeric budget parsing/filtering added to product compose pipeline, verified with 2 new TDD tests (17/17 passing)**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-04-03T06:02:26Z
- **Completed:** 2026-04-03T06:08:12Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added anti-accessory instruction to `product_search.py` LLM system prompt to prevent accessories from being generated as product names
- Added product-name-level accessory suppression in `product_compose.py` at three points: the `products_with_offers` loop, the `review_bundles` blog iteration, and the fallback card path
- Added `_parse_budget()` helper that parses budget strings ("under $500", "$100-$200", "around $500") into numeric bounds
- Added `_extract_price()` helper that robustly parses price from offer dicts (int, float, or "$499.99" strings)
- Applied budget enforcement to `all_offers_for_product` — in-budget offers preferred; if all exceed budget, all are preserved (honest pricing fallback)
- 2 new tests (`test_accessory_suppression`, `test_budget_enforcement`) pass GREEN, 15 pre-existing tests unaffected

## Task Commits

1. **Task 1: Write failing tests (RED)** — `06545bd` (test)
2. **Task 2: Implement fixes (GREEN)** — `f66a32a` (feat)

**Plan metadata:** (docs commit below)

_TDD: RED commit followed by GREEN commit per plan spec_

## Files Created/Modified

- `backend/mcp_server/tools/product_compose.py` — Added `_parse_budget()`, `_extract_price()`, accessory suppression in compose loops, budget enforcement on offer list, `user_message_lower` at function scope
- `backend/mcp_server/tools/product_search.py` — Added anti-accessory sentence to LLM system prompt
- `backend/tests/test_product_compose.py` — Added `test_accessory_suppression` and `test_budget_enforcement`

## Decisions Made

- Accessory suppression applied at three layers (compose loop, blog iteration, fallback path) because accessories in `review_data` could bypass the first filter via the fallback card path
- Budget enforcement uses an "opt-out" approach: if no parseable budget is found, `(None, None)` is returned and no filtering occurs
- Fallback: if all offers exceed the budget max, the full offer list is preserved so the user sees results with honest pricing (not an empty card)
- `user_message_lower` lifted to function entry scope to avoid per-product `.lower()` calls in the tight compose loop

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Accessory suppression also needed in review_bundles blog iteration**
- **Found during:** Task 2 (Implementation) — first test run revealed accessories still appeared via fallback card path
- **Issue:** Accessories with review data entered `blog_product_names` via the `review_bundles` iteration loop, bypassing the `products_with_offers` filter
- **Fix:** Added accessory keyword check at the top of the `review_bundles` for loop (same guard: skip if user message itself contains an accessory keyword)
- **Files modified:** backend/mcp_server/tools/product_compose.py
- **Verification:** `test_accessory_suppression` passed after fix
- **Committed in:** f66a32a (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in initial implementation scope)
**Impact on plan:** Fix was necessary to make the test pass. No scope creep — same feature, additional enforcement point discovered during verification.

## Issues Encountered

None — plan executed cleanly once the three-layer suppression approach was identified during debugging.

## Next Phase Readiness

- All 17 `test_product_compose.py` tests pass
- `_parse_budget()` and `_extract_price()` are importable module-level helpers if needed by other tools
- QAR-04 and QAR-05 requirements fulfilled

## Self-Check: PASSED

- backend/mcp_server/tools/product_compose.py: FOUND
- backend/mcp_server/tools/product_search.py: FOUND
- backend/tests/test_product_compose.py: FOUND
- .planning/phases/23-qa-remediation-unified-bug-fixes/23-04-SUMMARY.md: FOUND
- Commit 06545bd: FOUND
- Commit f66a32a: FOUND

---
*Phase: 23-qa-remediation-unified-bug-fixes*
*Completed: 2026-04-03*
