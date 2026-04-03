---
phase: 23-qa-remediation-unified-bug-fixes
plan: "03"
subsystem: travel-tools
tags: [travel, instrumentation, streaming, recovery, tdd]
dependency_graph:
  requires: []
  provides:
    - tool_timing field in GraphState TypedDict
    - tool_timing default in initial_state (chat.py)
    - per-tool execution timing for all 5 travel tools
    - streaming status updates for all 5 travel tools
    - recovery path in travel_compose for all-empty state
    - partial-data note in travel_compose
  affects:
    - backend/app/schemas/graph_state.py
    - backend/app/api/v1/chat.py
    - backend/mcp_server/tools/travel_*
tech_stack:
  added: []
  patterns:
    - time.monotonic() timing capture per tool
    - stream_chunk_data with type "tool_citation" for status SSE events
    - early-return guard pattern in compose tools (mirroring product_compose)
key_files:
  created:
    - backend/tests/test_travel_compose.py
  modified:
    - backend/app/schemas/graph_state.py
    - backend/app/api/v1/chat.py
    - backend/mcp_server/tools/travel_itinerary.py
    - backend/mcp_server/tools/travel_search_hotels.py
    - backend/mcp_server/tools/travel_search_flights.py
    - backend/mcp_server/tools/travel_search_activities.py
    - backend/mcp_server/tools/travel_search_cars.py
    - backend/mcp_server/tools/travel_compose.py
decisions:
  - tool_timing uses Dict[str, float] (not Annotated with operator.add) — tools merge via {**state.get("tool_timing", {}), "tool_name": elapsed} pattern, consistent with how other dict fields are handled
  - Partial data note only shown when fewer than 3 keys are missing — avoids verbose list when everything failed (recovery path handles that case)
  - start timer placed after stream_chunk_data emit — timing captures actual work, not status update overhead
metrics:
  duration: "382s"
  completed_date: "2026-04-03"
  tasks_completed: 2
  files_modified: 8
  files_created: 1
---

# Phase 23 Plan 03: Travel Tool Instrumentation and Recovery Summary

Per-tool timing via `time.monotonic()`, named SSE status streaming via `stream_chunk_data`, and a graceful recovery path in `travel_compose` when all upstream travel tools fail.

## What Was Built

### Tool Timing (`tool_timing`)
- Added `tool_timing: Dict[str, float]` to `GraphState` TypedDict in `graph_state.py`
- Added `"tool_timing": {}` default to `initial_state` dict in `chat.py` (critical — prevents LangGraph channel crash on first travel request)
- All 5 travel tools now record elapsed time using `time.monotonic()` and merge into `state["tool_timing"]` before returning

### Streaming Status Updates (`stream_chunk_data`)
Each travel tool now emits a named status message at the START of execution via `stream_chunk_data`:
- `travel_itinerary` → "Building your itinerary..."
- `travel_search_hotels` → "Searching for hotels..."
- `travel_search_flights` → "Looking up flights..."
- `travel_search_activities` → "Finding activities..."
- `travel_search_cars` → "Checking car rentals..."

These route through the existing SSE pipeline in `chat.py` (type=`tool_citation`) as status events to the frontend.

### Recovery Path in `travel_compose`
- **All-empty guard**: When `itinerary`, `hotels`, `flights`, `activities`, `cars`, `destination_facts`, and `general_travel_info` are all falsy, returns an actionable recovery message ("I ran into an issue... You can try again, or ask for a specific piece") with `ui_blocks=[]`
- **Partial data note**: When some keys succeeded but others didn't (fewer than 3 missing), appends a note like "I couldn't find flights and hotels for this trip -- you can ask me to search for those specifically"

## Test Results

| Test | Status |
|------|--------|
| `test_timeout_recovery` | PASSED |
| `test_partial_response` | PASSED |

Pre-existing test failures in `test_fast_router`, `test_product_compose`, `test_cj_provider`, `test_serper_shopping_provider`, and `test_speculative` were confirmed pre-existing (same failures present before any changes in this plan).

## Commits

| Hash | Description |
|------|-------------|
| `d53c481` | test(23-03): add failing tests for travel_compose timeout recovery (RED) |
| `0bd88eb` | feat(23-03): add tool_timing, status streaming, and recovery path to travel tools (GREEN) |

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- `backend/tests/test_travel_compose.py` — exists and contains 2 tests
- `backend/app/schemas/graph_state.py` — contains `tool_timing`
- `backend/app/api/v1/chat.py` — contains `tool_timing`
- `backend/mcp_server/tools/travel_compose.py` — contains recovery path
- Commits `d53c481` and `0bd88eb` both present in git log
