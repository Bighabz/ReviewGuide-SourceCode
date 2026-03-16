---
phase: 01-response-experience-overhaul
plan: 05
subsystem: backend-streaming
tags: [streaming, token-callback, sse, blog-article, real-time]
dependency_graph:
  requires: [01-04]
  provides: [blog-article-token-streaming]
  affects: [product_compose, plan_executor, chat.py]
tech_stack:
  added: []
  patterns: [async-generator-streaming, global-callback-registry, SSE-token-forwarding]
key_files:
  created: []
  modified:
    - backend/app/services/plan_executor.py
    - backend/mcp_server/tools/product_compose.py
    - backend/app/api/v1/chat.py
    - backend/tests/test_chat_streaming.py
    - backend/tests/test_product_compose.py
decisions:
  - "Always use stream=True for blog_article LLM call; forward tokens to callbacks only if registered"
  - "Token callbacks share event_queue with artifact callbacks via token_ready synthetic event type"
  - "Module-level model_service import in product_compose enables test patching at mcp_server.tools.product_compose.model_service"
  - "text_already_streamed flag suppresses STREAM_CHUNK_SIZE fake-chunking after real tokens flow"
metrics:
  duration: "533s (~9 minutes)"
  completed: "2026-03-16"
  tasks: 3
  files: 5
---

# Phase 01 Plan 05: Blog Article Token Streaming Summary

Per-token progressive streaming of blog article LLM output from OpenAI through the SSE stream to the browser, eliminating the 60-90 second "Thinking..." wall for returning users.

## What Was Built

**Three-file change implementing RX-02 (blog narrative streams token-by-token):**

1. **Token callback registry in `plan_executor.py`** — Global registry `_token_callbacks_global` with `register_token_callback`, `get_token_callbacks`, `clear_token_callbacks` alongside the existing artifact callback registry (Plan 04 pattern).

2. **Streaming blog_article in `product_compose.py`** — Blog article call always uses `stream=True`; async generator iterates tokens and forwards each to registered callbacks via `get_token_callbacks()`. Module-level `model_service` reference replaces the lazy function-body import.

3. **Token callback wiring in `chat.py`** — `_on_token` closure registered before `graph.astream_events()`; puts `token_ready` synthetic events into `event_queue`; `_drain_event_loop` handles `token_ready` and yields `content` SSE events; `text_already_streamed=True` flag suppresses fake-chunking; callbacks cleared on all exit paths.

## Tasks

| Task | Name | Commit | Key Change |
|------|------|--------|------------|
| 1 | Token callback registry | 7ca8e26 | `register_token_callback`, `get_token_callbacks`, `clear_token_callbacks` added to plan_executor.py |
| 2 | Stream blog_article tokens | 83a3751 | product_compose always calls `generate(stream=True)` for blog_article; Phase 3b streams async generator |
| 3 | Register token callback in chat.py | 9c859eb | `_on_token` closure, `token_ready` event handling, `text_already_streamed` flag |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Module-level model_service import required for test patching**
- **Found during:** Task 2
- **Issue:** Test patches `mcp_server.tools.product_compose.model_service` with `create=True`, but product_compose imported `model_service` inside the function body via `from app.services.model_service import model_service`. The patch had no effect.
- **Fix:** Moved `model_service` to module-level with a try/except fallback; removed the in-function import.
- **Files modified:** `backend/mcp_server/tools/product_compose.py`
- **Commit:** 83a3751

**2. [Rule 1 - Bug] capturing_model_service fixture patch target and async generator**
- **Found during:** Task 2
- **Issue:** `capturing_model_service` in test_product_compose.py patched at `app.services.model_service.model_service` (source module) — no longer effective after module-level import. Also, `fake_generate` returned a plain string for `blog_article_composer`, which broke `async for token in blog_gen` iteration.
- **Fix:** Updated fixture to patch `mcp_server.tools.product_compose.model_service` and return an async generator when `stream=True`.
- **Files modified:** `backend/tests/test_product_compose.py`
- **Commit:** 83a3751

**3. [Rule 2 - Design] Always stream blog_article instead of conditional on callbacks**
- **Found during:** Task 2
- **Issue:** The plan described a conditional approach (stream only if callbacks registered, otherwise batch), but the existing test `test_blog_article_uses_model_service_stream` asserts `stream=True` without registering a callback. Conditional approach would fail the test.
- **Fix:** Always use `stream=True` for blog_article; tokens are forwarded to callbacks only if registered (no-op if no callbacks). Non-generator return (e.g. mock string) handled gracefully via `hasattr(blog_gen, '__aiter__')` check.
- **Files modified:** `backend/mcp_server/tools/product_compose.py`
- **Commit:** 83a3751

**4. [Rule 2 - Design] test_chat_streaming fake_generate returns async generator for stream=True**
- **Found during:** Task 2
- **Issue:** The existing `fake_generate` in `test_chat_streaming.py` returned a plain string for `blog_article_composer`, incompatible with `async for token in blog_gen`.
- **Fix:** Updated `fake_generate` to return `_blog_gen()` async generator when `stream=True` is passed.
- **Files modified:** `backend/tests/test_chat_streaming.py`
- **Commit:** 83a3751

## Pre-existing Failure (Not Related to Plan 05)

`test_review_search.py::TestProductComposeWithReviews::test_compose_with_review_data` — asserts a `review_sources` ui_block that product_compose never generates. This was failing before Plan 05 (already in `deferred-items.md` from Plan 01-02). Not caused by any Plan 05 change.

## Self-Check

### Created/Modified Files

- `backend/app/services/plan_executor.py` — verified token callback registry present
- `backend/mcp_server/tools/product_compose.py` — verified stream=True and Phase 3b
- `backend/app/api/v1/chat.py` — verified _on_token, token_ready, text_already_streamed
- `backend/tests/test_chat_streaming.py` — verified test_token_callback_registry_importable added
- `backend/tests/test_product_compose.py` — verified capturing_model_service fixture updated

### Commits Verified

- 7ca8e26 — Task 1: token callback registry
- 83a3751 — Task 2: blog_article streaming
- 9c859eb — Task 3: chat.py wiring

### Test Results

- 266 passing, 1 pre-existing failure (unrelated to this plan)

## Self-Check: PASSED
