---
phase: 01-response-experience-overhaul
plan: 03
subsystem: api
tags: [product_compose, llm, blog_article, review_sources, performance]

requires: []
provides:
  - "product_compose with opener and conclusion LLM calls removed"
  - "blog_data includes Review source markdown links for inline citation"
  - "blog_article system prompt with inline intro + Our Verdict section"
affects: [product_compose, review_search, blog_article_composer]

tech-stack:
  added: []
  patterns:
    - "blog_article LLM call absorbs opener + verdict inline (single call pattern)"
    - "source_refs appended to blog_data_parts for in-context citation threading"

key-files:
  created: []
  modified:
    - backend/mcp_server/tools/product_compose.py
    - backend/tests/test_product_compose.py

key-decisions:
  - "Removed opener LLM call: blog_article system prompt now starts with warm intro instruction — single call replaces two"
  - "Removed conclusion LLM call: Our Verdict section now instructed inline in blog_article prompt"
  - "Source refs format: '| Reviews: [SiteName](url)' appended to each blog_data product line, top 3 sources per product"
  - "Fallback template path (blog_article LLM failure) also cleaned: removed opener/conclusion _get_result references"

patterns-established:
  - "Source threading pattern: build source_refs in data-assembly loop, append to context string before LLM call"
  - "Single-call consolidation: use rich system prompt to absorb what multiple smaller LLM calls produced"

requirements-completed:
  - RX-06
  - RX-07

duration: 8min
completed: 2026-03-16
---

# Phase 1 Plan 3: Remove Redundant LLM Calls + Thread Review Sources Summary

**Eliminated opener and conclusion LLM calls from product_compose, reducing concurrent calls from 7 to 5, and threaded review source URLs as inline markdown citations into blog_article context**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-16T01:42:49Z
- **Completed:** 2026-03-16T01:51:23Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Removed `llm_tasks['opener']` (product_opener agent) that fired on every review query — blog_article prompt now starts with a warm 1-2 sentence intro instruction
- Removed `llm_tasks['conclusion']` (product_conclusion agent) that fired whenever products_by_provider was populated — Our Verdict section now instructed inline in blog_article system prompt
- Added `source_refs` variable in the review_bundles loop: for each product with sources, top 3 sources with url+site_name are formatted as `[SiteName](url)` and appended as `| Reviews: ...` to each product's blog_data line
- Updated blog_article system prompt to explicitly instruct inline citation usage from `| Reviews:` data, with prohibition on inventing URLs
- Cleaned up fallback template assembly path: removed `_get_result('opener')` and `_get_result('conclusion')` references that were dead code after the removal

## Task Commits

Each task was committed atomically:

1. **RED: Failing tests for RX-06 and RX-07** - `93627b6` (test)
2. **Task 1: Remove opener and conclusion LLM calls** - `62ead2c` (feat)
3. **Task 2: Thread review source URLs into blog_data** - `17d412e` (feat)

_Note: TDD tasks have RED commit (tests) then GREEN commit (implementation)_

## Files Created/Modified

- `backend/mcp_server/tools/product_compose.py` - Removed opener/conclusion LLM tasks, updated blog_article system prompt, added source_refs threading in blog_data_parts loop, cleaned fallback assembly
- `backend/tests/test_product_compose.py` - Added test_no_opener_call, test_no_conclusion_call, test_blog_includes_source_inline_links plus capturing_model_service fixture and _REVIEW_STATE_WITH_DATA shared state

## Decisions Made

- **Single-call consolidation**: The opener (30-word intro) and conclusion (50-word verdict) were folded directly into the blog_article system prompt instructions. The LLM can produce a 500-word article with intro and verdict in one call, removing two sequential-ish slots from asyncio.gather.
- **Source refs format**: Chose `| Reviews: [SiteName](url), [SiteName](url)` appended to the product line (pipe-delimited) to stay consistent with the existing blog_data format. Top 3 sources capped to avoid prompt bloat.
- **Fallback path cleanup**: The `elif review_data and review_bundles` fallback (used only when blog_article LLM call fails) was also cleaned of opener/conclusion references since those keys will never appear in result_map anymore.
- **Patch target for tests**: The `capturing_model_service` fixture patches `app.services.model_service.model_service` (source module) rather than the tool module, because product_compose imports model_service via `from app.services.model_service import model_service` inside the function body.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The test fixture initially patched `mcp_server.tools.product_compose.model_service` (module-level) but the code does a function-level import `from app.services.model_service import model_service`, so the patch wasn't intercepted. Fixed by patching `app.services.model_service.model_service` (the source singleton). This was an implementation detail resolved during TDD RED phase.

4 pre-existing failing test stubs remain in the suite (from plans 01-01 and 01-02, covering RX-01/RX-08 product_affiliate stream_chunk_data and RX-02 blog_article streaming). These are intentionally failing stubs awaiting their respective implementation plans.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- product_compose now fires max 5 concurrent LLM calls for a 3-product review query: concierge OR (consensus x3 + descriptions + blog_article)
- blog_article LLM receives inline review source URLs in its context, enabling natural citation prose like "According to [Wirecutter](url)..."
- RX-06 and RX-07 requirements complete; test coverage in place

## Self-Check: PASSED

- FOUND: `.planning/phases/01-response-experience-overhaul/01-03-SUMMARY.md`
- FOUND: `backend/mcp_server/tools/product_compose.py`
- FOUND: commit 93627b6 (test RED phase)
- FOUND: commit 62ead2c (feat Task 1)
- FOUND: commit 17d412e (feat Task 2)

---
*Phase: 01-response-experience-overhaul*
*Completed: 2026-03-16*
