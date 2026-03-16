---
phase: 01-response-experience-overhaul
plan: "04"
subsystem: backend-streaming
tags:
  - streaming
  - artifact-callback
  - product-cards
  - sse
dependency_graph:
  requires:
    - 01-02  # product_affiliate parallel search (must exist before adding stream_chunk_data)
  provides:
    - mid-workflow-artifact-streaming
    - early-product-card-rendering
  affects:
    - plan_executor.py
    - product_affiliate.py
    - chat.py
tech_stack:
  added: []
  patterns:
    - "Module-level callback registry pattern for cross-boundary event emission"
    - "Synthetic event injection into asyncio.Queue for SSE drain loop"
key_files:
  created: []
  modified:
    - backend/app/services/plan_executor.py
    - backend/mcp_server/tools/product_affiliate.py
    - backend/app/api/v1/chat.py
decisions:
  - "Always emit stream_chunk_data from product_affiliate (even empty list) so plan_executor contract is consistent"
  - "Only fire _emit_artifact when early_ui_blocks is non-empty to avoid unnecessary SSE events"
  - "Synthetic artifact_ready events use the same event_queue as LangGraph events — no second queue needed"
  - "data_already_streamed=True after early artifact prevents duplicate end-of-workflow re-emit"
metrics:
  duration: "4m 26s"
  completed_date: "2026-03-16"
  tasks_completed: 3
  files_modified: 3
---

# Phase 01 Plan 04: Mid-Workflow Product Card Streaming Summary

**One-liner:** Artifact callback mechanism in PlanExecutor + stream_chunk_data in product_affiliate enables product cards to reach the browser within ~5s, before product_compose runs.

## What Was Built

Three connected changes wire a new streaming path from product_affiliate -> plan_executor -> SSE:

1. **PlanExecutor artifact callback registry** (`plan_executor.py`): Module-level `register_artifact_callback` / `clear_artifact_callbacks` / `get_artifact_callbacks` functions, plus instance-level `register_artifact_callback_instance` and `_emit_artifact` method. `_emit_artifact` is called after any tool that returns `stream_chunk_data.type == "ui_blocks"` with non-empty data.

2. **product_affiliate early ui_blocks** (`product_affiliate.py`): After building `affiliate_products`, constructs a `stream_chunk_data = {"type": "ui_blocks", "data": [...]}` payload mapping provider groups into typed product card blocks (ebay_products, amazon_products, etc.). This is always included in the return dict so plan_executor can detect it.

3. **chat.py callback registration** (`chat.py`): Before `graph.astream_events()` starts, registers `_on_artifact` closure on the plan_executor module. The closure writes a synthetic `artifact_ready` event to `event_queue`. `_drain_event_loop` handles `artifact_ready` by yielding an SSE `artifact` event immediately. Sets `data_already_streamed=True` to prevent duplicate end-of-workflow emission. `clear_artifact_callbacks()` called in all exit paths.

## Tests Status

| Test | Status | Plan |
|------|--------|------|
| test_product_cards_emitted_before_compose | PASS | RX-01 |
| test_affiliate_search_products_parallel_within_provider | PASS | RX-03 (from 01-02) |
| test_planner_fast_path_review_and_affiliate_in_same_step | PASS | RX-05 (from 01-02) |

Pre-existing failure: `test_blog_article_uses_model_service_stream` (RX-02) — unrelated to this plan, targets product_compose streaming not covered by 01-04.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | e5d4f73 | feat(01-04): add artifact callback mechanism to PlanExecutor |
| Task 2 | e9eead3 | feat(01-04): add stream_chunk_data to product_affiliate return dict |
| Task 3 | de6436b | feat(01-04): register artifact callback in chat.py for early product card streaming |

## Deviations from Plan

### Auto-fixed Issues

None - plan executed exactly as written, with one minor clarification:

**Deviation: stream_chunk_data always set (not conditional on non-empty results)**

- **Found during:** Task 2, GREEN phase
- **Issue:** Test `test_product_cards_emitted_before_compose` uses `get_available_providers.return_value = []` (no providers), which produces empty `affiliate_products = {}`. The original plan conditionally set `stream_chunk = None` when `early_ui_blocks` was empty. Test asserts `stream_chunk is not None` unconditionally.
- **Fix:** Always set `stream_chunk = {"type": "ui_blocks", "data": early_ui_blocks}` (data may be empty list). Added `and stream_data.get("data")` guard in plan_executor `_emit_artifact` calls to skip firing on empty blocks.
- **Files modified:** `product_affiliate.py`, `plan_executor.py`
- **Commit:** e9eead3

## Self-Check: PASSED

- FOUND: backend/app/services/plan_executor.py
- FOUND: backend/mcp_server/tools/product_affiliate.py
- FOUND: backend/app/api/v1/chat.py
- FOUND: .planning/phases/01-response-experience-overhaul/01-04-SUMMARY.md
- FOUND commit: e5d4f73 (Task 1)
- FOUND commit: e9eead3 (Task 2)
- FOUND commit: de6436b (Task 3)
