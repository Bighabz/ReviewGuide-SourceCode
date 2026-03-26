---
phase: 11-viator-cj-expansion
plan: 03
subsystem: api
tags: [viator, mcp, graphstate, travel-compose, langgraph]

requires:
  - phase: 11-02
    provides: "ViatorActivityProvider class"
provides:
  - "travel_search_activities MCP tool"
  - "activities field in GraphState TypedDict"
  - "activities default in initial_state (chat.py)"
  - "activities_viator UI block type in travel_compose"
  - "Complete end-to-end Viator activity search pipeline"
affects: [frontend-activity-card]

tech-stack:
  added: []
  patterns: [mcp-tool-activities, activities-viator-ui-block]

key-files:
  created:
    - backend/mcp_server/tools/travel_search_activities.py
  modified:
    - backend/mcp_server/main.py
    - backend/app/schemas/graph_state.py
    - backend/app/api/v1/chat.py
    - backend/mcp_server/tools/travel_compose.py

key-decisions:
  - "Use activities_viator UI block type (not activities) to avoid conflict with existing plain-text activities from destination_facts"
  - "activities field added to both GraphState AND initial_state to prevent LangGraph channel crash"
  - "MCP tool converts AffiliateProduct to activity dicts with name, price_from, booking_url, image_url keys"

patterns-established:
  - "activities_viator UI block type for Viator-sourced activity data (vs plain activities from destination_facts)"
  - "MCP tool pattern: read slots.destination, instantiate provider, convert results to state dicts"

requirements-completed: [PROV-02]

duration: 3min
completed: 2026-03-26
---

# Phase 11 Plan 03: MCP Tool + GraphState Wiring Summary

**travel_search_activities MCP tool wired end-to-end: slots.destination -> Viator API -> activities_viator UI block**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-26T00:09:00Z
- **Completed:** 2026-03-26T00:12:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created travel_search_activities MCP tool following travel_search_cars pattern
- Added activities field to GraphState TypedDict and initial_state in chat.py (critical for LangGraph)
- Registered tool in main.py (import, list_tools, call_tool routing)
- Updated travel_compose to render activities_viator UI block
- All 9/9 Viator tests pass GREEN including TestViatorMCPTool
- No regressions in CJ provider tests (12/12 pass)

## Task Commits

1. **Task 1+2: GraphState + MCP tool + travel_compose** - `a866994` (feat)

## Files Created/Modified
- `backend/mcp_server/tools/travel_search_activities.py` - MCP tool with TOOL_CONTRACT and search function
- `backend/mcp_server/main.py` - import + Tool registration + call_tool routing
- `backend/app/schemas/graph_state.py` - activities: List[Dict[str, Any]] field
- `backend/app/api/v1/chat.py` - "activities": [] in initial_state
- `backend/mcp_server/tools/travel_compose.py` - activities_viator UI block generation

## Decisions Made
- Used activities_viator as UI block type to avoid conflict with existing plain-text activities from destination_facts
- TOOL_CONTRACT tool_order=100 (same priority as travel_search_cars)
- Activities capped at 5 in UI block (activities[:5]) matching hotels/flights pattern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Complete Viator pipeline working: user query -> destination slot -> Viator API -> activities state -> activities_viator UI block
- Plan 11-04 (CJ applications + Viator credentials) requires human action

---
*Phase: 11-viator-cj-expansion*
*Completed: 2026-03-26*
