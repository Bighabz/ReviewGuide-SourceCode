---
phase: 02-fix-review-source-links
plan: 01
subsystem: api
tags: [product-compose, citations, review-sources, llm-prompt, mcp-tools]

# Dependency graph
requires: []
provides:
  - Review source URLs (Wirecutter, RTINGS, Tom's Guide) threaded into blog LLM context
  - Citations array populated from review sources instead of product buy-page URLs
  - System prompt guard against fabricating URLs
affects: [phase-09-top-pick, phase-14-chat-screen]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "review_source_urls fallback pattern: prefer review sources, fall back to normalized_products"

key-files:
  created: []
  modified:
    - backend/mcp_server/tools/product_compose.py
    - backend/tests/test_product_compose.py

key-decisions:
  - "source_refs and review_excerpts were already threaded into blog_data_parts from prior Phase 1 work — no duplication needed"
  - "Added explicit 'NEVER invent URLs' guard to system prompt alongside existing 'NEVER invent features or specs' line"
  - "Citations prefer review_source_urls[:5] with or-fallback to normalized_products — backward compatible"

patterns-established:
  - "Review source citation pattern: collect from review_bundles.values().sources[:2], prefer over product URLs"

requirements-completed: [FIX-01]

# Metrics
duration: 4min
completed: 2026-03-25
---

# Phase 2 Plan 01: Fix Review Source Links Summary

**Blog system prompt guards against fabricated URLs, citations array populated from review sources (Wirecutter, RTINGS) with fallback to product URLs**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-25T23:41:47Z
- **Completed:** 2026-03-25T23:45:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Citations array now contains review source URLs (Wirecutter, Tom's Guide, RTINGS, Reddit) instead of product buy-page URLs
- System prompt explicitly forbids inventing URLs — LLM can only link to sources in the data
- Backward compatible: citations fall back to normalized_products URLs when no review sources exist
- 3 new behavioral tests verify FIX-01 requirements; all 8 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Add failing tests** - `f44ce3e` (test)
2. **Task 1 (GREEN): Fix review source links** - `8052427` (feat)

_TDD task with RED/GREEN commits._

## Files Created/Modified
- `backend/mcp_server/tools/product_compose.py` - Added "NEVER invent URLs" system prompt guard; replaced citations collection to prefer review_source_urls over normalized_products
- `backend/tests/test_product_compose.py` - Added 3 FIX-01 tests: system prompt URL guard, citations from review sources, citations fallback

## Decisions Made
- source_refs threading into blog_data_parts was already implemented from Phase 1 work (lines 614-635) -- no duplicate Edit 1 needed
- The blog system prompt already had inline citation instructions (lines 683-686) -- only the "never invent URLs" guard was missing
- Used `review_bundles.values()` (not `review_data.values()`) for citations to match the same scope as the blog LLM context

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test fixture mismatch for fallback test**
- **Found during:** Task 1 RED phase
- **Issue:** `test_citations_fallback_to_product_urls_without_review_sources` used `mock_model_service` fixture which lacks `generate_compose` mock, causing the concierge LLM path to fail
- **Fix:** Switched to `capturing_model_service` fixture which properly mocks `generate_compose`
- **Files modified:** backend/tests/test_product_compose.py
- **Verification:** Test passes in both RED (when citations fix not applied) and GREEN states
- **Committed in:** f44ce3e (RED test commit)

**2. [Rule 1 - Bug] Test assertion too fragile for multi-occurrence prompt text**
- **Found during:** Task 1 GREEN phase
- **Issue:** `test_system_prompt_forbids_inventing_urls` split on first "never invent" occurrence which matched "features or specs" not "URLs"
- **Fix:** Updated assertion to scan all "never invent" occurrences for URL mention
- **Files modified:** backend/tests/test_product_compose.py
- **Verification:** Test correctly passes with "NEVER invent URLs" line present
- **Committed in:** 8052427 (GREEN commit)

---

**Total deviations:** 2 auto-fixed (2 bugs in test code)
**Impact on plan:** Minor test fixture and assertion adjustments. No scope creep.

## Issues Encountered
- Edit 1 from the plan (source_refs in blog_data_parts) was already implemented in the codebase from prior Phase 1 work. Skipped to avoid duplication.
- Edit 2 from the plan (system prompt citation format) was partially implemented. Only the "never invent URLs" guard was missing.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Review source links are now threaded into blog context, cited by the LLM, and present in the citations array
- Phase 3 (Serper Shopping Provider) can proceed independently
- Phase 9 (Top Pick Block) will benefit from the review source citation pattern established here

## Self-Check: PASSED

- All files exist on disk
- All commit hashes found in git log
- All 8 tests pass

---
*Phase: 02-fix-review-source-links*
*Completed: 2026-03-25*
