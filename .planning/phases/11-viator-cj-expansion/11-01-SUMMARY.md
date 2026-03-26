---
phase: 11-viator-cj-expansion
plan: 01
subsystem: testing
tags: [viator, pytest, tdd, affiliate, travel]

requires: []
provides:
  - "RED test scaffolds for all PROV-02 Viator behaviors"
  - "6 test classes with 9 test methods covering search, parsing, caching, fallback, registration, MCP tool"
affects: [11-02, 11-03]

tech-stack:
  added: []
  patterns: [viator-provider-test-pattern]

key-files:
  created:
    - backend/tests/test_viator_provider.py
  modified: []

key-decisions:
  - "Follow test_cj_provider.py conventions exactly for consistency"
  - "Use JSON fixtures (not XML like CJ) since Viator uses JSON API"

patterns-established:
  - "Viator test fixture pattern: SAMPLE_VIATOR_RESPONSE dict mimicking /search/freetext JSON"

requirements-completed: []

duration: 2min
completed: 2026-03-26
---

# Phase 11 Plan 01: Viator RED Test Scaffolds Summary

**TDD RED test scaffolds for Viator activity provider: 6 test classes, 9 methods, all failing on import**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-26T00:03:57Z
- **Completed:** 2026-03-26T00:06:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created backend/tests/test_viator_provider.py with 6 test classes covering all PROV-02 sub-requirements
- Sample Viator /search/freetext JSON fixtures with 2 activity products
- All tests fail with ImportError (RED state) because viator_provider.py does not exist

## Task Commits

1. **Task 1: Create RED test scaffolds** - `f9a87a6` (test)

## Files Created/Modified
- `backend/tests/test_viator_provider.py` - 6 test classes: Registration, Search, ResponseParsing, Caching, Fallback, MCPTool

## Decisions Made
- Used JSON fixtures instead of XML (Viator API returns JSON, unlike CJ which returns XML)
- Timeout test expects PLP fallback (1 result) instead of empty list, matching Viator's fallback behavior

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- test_viator_provider.py was ignored by .gitignore `test_*` rule; used `git add -f` to force-track (same as existing test_cj_provider.py)

## Next Phase Readiness
- RED tests ready for Plan 11-02 to implement ViatorActivityProvider and turn GREEN

---
*Phase: 11-viator-cj-expansion*
*Completed: 2026-03-26*
