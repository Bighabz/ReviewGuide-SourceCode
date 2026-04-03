---
phase: 23-qa-remediation-unified-bug-fixes
plan: 01
subsystem: api
tags: [python, fastapi, langgraph, product-compose, affiliate-links, pytest, tdd]

# Dependency graph
requires:
  - phase: prior product pipeline phases
    provides: product_compose.py with fallback card loop and multi-provider gate

provides:
  - Fallback loop using continue (not break) so all unseen blog products get cards
  - Single-provider products emitting real product cards instead of Amazon search fallback
  - Label-domain parity enforcement (_domain_to_merchant helper + correction pass)
  - Citation URL http validation filter
  - Fixed test fixture generate_compose_with_streaming mock (unblocked 11 pre-existing failures)

affects:
  - product_compose
  - affiliate-links
  - citations
  - product cards

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_domain_to_merchant helper pattern for URL-to-merchant label derivation"
    - "TDD red-green cycle for revenue-impacting backend bugs"

key-files:
  created: []
  modified:
    - backend/mcp_server/tools/product_compose.py
    - backend/tests/test_product_compose.py

key-decisions:
  - "Relaxed multi-provider gate from >=2 providers to >=1 real offer — single-retailer products with valid URLs should not be silently dropped"
  - "Label-domain parity: correct Amazon labels pointing to non-Amazon URLs rather than excluding the offer entirely"
  - "Citation URL filter uses startswith('http') not just truthy check — guards against protocol-relative or malformed fabricated URLs"
  - "Fallback loop split: cap check uses break, duplicate check uses continue — preserves 5-card cap while iterating past duplicates"

patterns-established:
  - "_domain_to_merchant: centralized domain-to-merchant mapping for future label corrections"

requirements-completed: [QAR-01, QAR-02, QAR-03, QAR-07]

# Metrics
duration: 10min
completed: 2026-04-03
---

# Phase 23 Plan 01: QA Remediation — Product Compose Bug Fixes Summary

**Fixed 4 revenue-impacting bugs: fallback loop continue/break, single-provider gate relaxed, Amazon label-domain parity enforced, citation http URL validation added**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-03T05:49:05Z
- **Completed:** 2026-04-03T06:05:54Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Fallback product card loop now uses `continue` on duplicate names and `break` only on cap reached — unseen blog products after a duplicate are no longer silently skipped
- Multi-provider gate relaxed from requiring 2 providers to 1 real offer — single-retailer products with valid buy URLs now emit real product cards (not Amazon search fallback)
- `_domain_to_merchant` helper added; label-domain parity enforced in affiliate_links construction — Amazon labels on BestBuy URLs are automatically corrected
- Citation list now filters with `url.startswith("http")` — empty, None, and non-http fabricated URLs excluded
- Fixed pre-existing `generate_compose_with_streaming` mock omission in both test fixtures — unblocked 11 pre-existing test failures (Rule 1 auto-fix)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for QAR-01, QAR-02, QAR-03, QAR-07** - `54bdc80` (test)
2. **Task 2: Fix product_compose.py** - `1a9ec4c` (fix)

_Note: TDD tasks — test commit (RED) followed by fix commit (GREEN)_

## Files Created/Modified

- `backend/mcp_server/tools/product_compose.py` - 4 bug fixes: fallback loop continue, multi-provider gate, label-domain parity, citation http filter
- `backend/tests/test_product_compose.py` - 4 new tests + fixture fix for generate_compose_with_streaming

## Decisions Made

- Relaxed multi-provider gate from `>=2 providers` to `>=1 real offer` — the original guard was too strict, silently dropping legitimate single-retailer products
- Label-domain parity: correct the label rather than exclude the offer — preserving the buy link is better than losing it entirely
- Citation URL filter: `startswith("http")` rather than just truthy — guards against protocol-relative URLs or other edge cases
- TDD RED test redesign: `test_fallback_loop_continue` needed Products B and C in `review_data` (not just state `blog_data` key) to actually populate `blog_product_names` via `review_bundles`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed missing generate_compose_with_streaming mock in test fixtures**
- **Found during:** Task 1 (writing failing tests)
- **Issue:** Both `capturing_model_service` and `capturing_model_service_v2` fixtures lacked a mock for `generate_compose_with_streaming`, which is called for the blog article LLM task. MagicMock returned a non-awaitable object, causing `asyncio.gather` to fail and `success=False` in 11 pre-existing tests.
- **Fix:** Added `fake_service.generate_compose_with_streaming = AsyncMock(side_effect=fake_generate)` to both fixtures
- **Files modified:** `backend/tests/test_product_compose.py`
- **Verification:** 11 pre-existing tests now pass (were failing before); new tests run correctly
- **Committed in:** `54bdc80` (Task 1 commit)

**2. [Rule 1 - Bug] Redesigned test_fallback_loop_continue to correctly populate blog_product_names**
- **Found during:** Task 2 (verifying GREEN state)
- **Issue:** Initial test used a `blog_data` state key to signal Products B and C, but code builds `blog_product_names` from `review_bundles` and `products_by_provider` — not from a `blog_data` key. Products B and C never appeared in `blog_product_names` so the fallback loop never saw them.
- **Fix:** Added Products B and C to `review_data` (so they populate `blog_product_names` via `review_bundles`) with no affiliate offers (so they go through fallback path, not main review card path)
- **Files modified:** `backend/tests/test_product_compose.py`
- **Verification:** test_fallback_loop_continue PASSES
- **Committed in:** `1a9ec4c` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2x Rule 1 - Bug)
**Impact on plan:** Both auto-fixes necessary for test correctness. No scope creep.

## Issues Encountered

- A linter repeatedly removed the `generate_compose_with_streaming = AsyncMock(...)` line from fixtures during editing. Required re-adding multiple times; eventually the linter accepted the line with a comment explaining its purpose.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 4 QAR bugs fixed and verified with 15 passing tests (0 regressions)
- product_compose.py is ready for Plan 02+ (accessory filtering, etc.)
- The `_domain_to_merchant` helper can be extended with additional retailer domains as needed

---
*Phase: 23-qa-remediation-unified-bug-fixes*
*Completed: 2026-04-03*

## Self-Check: PASSED

- backend/mcp_server/tools/product_compose.py: FOUND
- backend/tests/test_product_compose.py: FOUND
- .planning/phases/23-qa-remediation-unified-bug-fixes/23-01-SUMMARY.md: FOUND
- Commit 54bdc80 (task 1): FOUND
- Commit 1a9ec4c (task 2): FOUND
