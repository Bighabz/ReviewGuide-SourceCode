---
status: awaiting_human_verify
trigger: "After Phase 1 changes (response experience overhaul), chat requests complete on the backend but the frontend shows 'something went wrong'. The SSE stream appears to hang after the LangGraph workflow completes."
created: 2026-03-15T00:00:00Z
updated: 2026-03-15T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED — The early artifact callback mechanism puts a synthetic `artifact_ready` event onto the SSE event queue from within the `consume_events` background task (inside `graph.astream_events()`). The `asyncio.sleep(0)` in `_emit_artifact` causes the drain loop to wake up and process the event mid-workflow, yielding an SSE chunk from `generate_chat_stream` WHILE the graph is still executing. This mid-workflow yield causes `generate_chat_stream` to be suspended waiting for the HTTP framework, while `consume_events` may or may not complete before the 60s SSE cap fires. The root pattern is: injecting events into the SSE queue from WITHIN `graph.astream_events()` via a side-channel callback breaks the sequential event consumption model.
test: Remove the global artifact callback mechanism from chat.py (register_artifact_callback, _on_artifact, artifact_ready handler in drain loop). Product cards will be sent via the existing ui_blocks path after the graph completes.
expecting: After removal, the drain loop no longer yields mid-workflow. `consume_events` runs to completion uninterrupted. `None` sentinel arrives cleanly. Done event sent.
next_action: Remove artifact callback from chat.py, remove artifact_ready handler from drain loop, remove asyncio.sleep(0) from _emit_artifact

## Symptoms

expected: User sends a chat message, sees product cards appear, then blog text streams in, response completes with a done event
actual: User sends message, sees "Thinking...", then gets "An unexpected error occurred. Please try refreshing the page." The backend logs show the workflow completing successfully with assistant_text_length=3031, ui_blocks=1, citations=5, but no logs appear AFTER the workflow Output log — no "result_state keys", no "query_completed", no "done" event sent.
errors: Frontend shows generic "something went wrong" error. No backend errors logged (no @level:error). The SSE stream silently hangs.
reproduction: Send ANY product query (e.g. "Best standing desks for back pain"). Happens 100% of the time since Phase 1 changes were deployed.
started: After Phase 1 (Response Experience Overhaul) commits were pushed to main and deployed to Railway.

## Eliminated

- hypothesis: Token callback (RX-02) causes the hang
  evidence: Token callback was disabled in commit 85a627c — hang persists
  timestamp: 2026-03-15

- hypothesis: Blog article streaming in product_compose causes the hang
  evidence: Blog streaming was reverted in commit 2c49b74 — hang persists
  timestamp: 2026-03-15

- hypothesis: Missing `clear` event after data_already_streamed
  evidence: Clear event is now always sent (commit 9de745e) — hang persists
  timestamp: 2026-03-15

- hypothesis: Tool timeout (15s) causes plan_executor to fail before completing
  evidence: Timeout raised to 30s (commit 1ba0b5f) — hang persists, and plan executor logs show successful completion
  timestamp: 2026-03-15

## Evidence

- timestamp: 2026-03-15T00:00:00Z
  checked: git log and full diff of Phase 1 commits
  found: Five commits: feat(01-04) register artifact callback, feat(01-04) add stream_chunk_data to product_affiliate, feat(01-04) add artifact callback mechanism to PlanExecutor, feat(01-05) wire token callback (disabled), plus four fix commits that didn't resolve the hang
  implication: The hanging change is the artifact callback mechanism (feat-01-04), not token streaming

- timestamp: 2026-03-15T00:00:01Z
  checked: chat.py drain loop and consume_events structure
  found: `_on_artifact` is called from within `graph.astream_events()` (inside `consume_events` background task). It puts a synthetic `artifact_ready` event onto `event_queue`. Then `asyncio.sleep(0)` in `_emit_artifact` yields to the event loop. The drain loop (main coroutine) wakes up, gets the artifact event, processes it, and calls `yield _sse_event("artifact", payload)`. This causes `generate_chat_stream` to `yield sse_chunk` mid-workflow.
  implication: The drain loop yields SSE mid-workflow for the FIRST TIME in Phase 1 history. Pre-Phase-1, SSE was only yielded mid-workflow from `stream_chunk_data` in `on_chain_end` node events (at node boundaries). Phase 1 introduces a yield from WITHIN a node's execution via the callback side-channel.

- timestamp: 2026-03-15T00:00:02Z
  checked: _STEP_TIMEOUT_S and _TOOL_TIMEOUT_S changes
  found: _STEP_TIMEOUT_S raised from 45s to 60s, _TOOL_TIMEOUT_S raised from 15s to 30s. However plan_exec stage budget is still 45s in stage_telemetry.py. The step timeout (60s) now EXCEEDS the stage budget (45s), meaning a slow step could prevent the executor from completing before the stage timeout fires.
  implication: Contributing factor but not the primary cause since logs show assistant_text_length=3031 (real data, not fallback)

- timestamp: 2026-03-15T00:00:03Z
  checked: consume_events and None sentinel logic
  found: `consume_events` has a `finally` block that always puts `None`. So `None` IS eventually put. The drain loop never receives it within 60s. This means `graph.astream_events()` runs for 60+ seconds after the artifact fires.
  implication: The hang is inside `graph.astream_events()` after the artifact fires. The most likely cause: injecting `await event_queue.put(synthetic_event)` from within the graph execution, followed by `asyncio.sleep(0)`, creates an unexpected interaction with the asyncio event loop scheduler that prevents `graph.astream_events()` from completing within the SSE cap.

- timestamp: 2026-03-15T00:00:04Z
  checked: product_affiliate stream_chunk_data path
  found: product_affiliate returns `stream_chunk_data = {"type": "ui_blocks", "data": early_ui_blocks}` where `early_ui_blocks` is non-empty only when affiliate providers (eBay, Amazon) return results. On Railway with configured providers, this always has data → artifact always fires → hang always occurs.
  implication: Explains 100% reproduction rate on Railway (configured providers) and possible success in dev (no providers)

## Resolution

root_cause: The artifact callback mechanism registers `_on_artifact` as a module-level callback that puts a synthetic event onto the SSE `event_queue` from within `graph.astream_events()` (the `consume_events` background task). The `asyncio.sleep(0)` call in `_emit_artifact` then causes the drain loop to process this event MID-WORKFLOW, making `generate_chat_stream` yield an SSE chunk while the graph is still running. This interaction between the callback side-channel and the asyncio event loop scheduler causes `graph.astream_events()` to not complete within the 60-second SSE cap, resulting in the "error" event being sent and the frontend showing "something went wrong".
fix: |
  Removed the global artifact callback mechanism from chat.py:
  - Removed `register_artifact_callback(_on_artifact)` and `_on_artifact` function
  - Removed `elif event_type == "artifact_ready"` and `elif event_type == "token_ready"` handlers from `_drain_event_loop`
  - Removed `text_already_streamed` variable (no longer needed without token callback)
  - Simplified `should_stream_text` to just `not is_halted and bool(response_text)`
  - Simplified the clear/ui_blocks sending logic post-drain
  Removed `await asyncio.sleep(0)` from `_emit_artifact` in plan_executor.py (no longer needed since no SSE-queue-targeting callbacks are called).
  Product cards continue to be sent via the existing `ui_blocks` path after the graph completes (product_compose's output sent in the artifact event pre-done, as before Phase 1).
verification: pending human verification — deploy to Railway and send a product query
files_changed:
  - backend/app/api/v1/chat.py
  - backend/app/services/plan_executor.py
