---
phase: 08-clarifier-suggestion-chips
plan: 01
subsystem: test-scaffolds
tags: [tdd, red-tests, clarifier, chips]
dependency_graph:
  requires: []
  provides: [backend-test-contract, frontend-test-contract]
  affects: [08-02, 08-03]
tech_stack:
  added: []
  patterns: [isolated-render-test-pattern, asyncmock-agent-testing]
key_files:
  created:
    - backend/tests/test_clarifier_chips.py
    - frontend/tests/clarifierChips.test.tsx
  modified: []
decisions:
  - "Frontend tests use isolated-render pattern (mirror rendering logic) to avoid importing full Message component tree"
  - "Backend tests mock ClarifierAgent.generate to test _generate_followup_questions in isolation"
metrics:
  duration: ~3 min
  completed: "2026-03-25T23:58:00Z"
---

# Phase 08 Plan 01: RED Test Scaffolds Summary

Backend and frontend test contracts for clarifier suggestion chips -- 4 backend tests (2 RED, 2 GREEN via mock) and 6 frontend tests (all GREEN via isolated render pattern).

## What Was Done

### Task 1: Backend RED tests for clarifier chips
Created `backend/tests/test_clarifier_chips.py` with 4 pytest tests:
- `test_chips_in_followup_response`: Asserts LLM response includes 2-4 chips per question
- `test_chips_are_short_strings`: Asserts chip text <= 30 characters
- `test_fallback_questions_include_empty_chips`: Asserts fallback includes chips: [] (RED -- production code missing)
- `test_graph_state_default`: Asserts clarifier_chips field in GraphState (RED -- field not yet added)

### Task 2: Frontend RED tests for clarifier chip rendering
Created `frontend/tests/clarifierChips.test.tsx` with 6 vitest tests using isolated render pattern:
- Chip buttons render with correct data-testid attributes
- Chip text content displays correctly
- Click dispatches sendSuggestion CustomEvent with chip text
- Empty chips array renders nothing (no crash)
- Missing chips key renders nothing (no crash)
- Multiple questions render chips independently

## Test Results
- Backend: 2 passed, 2 failed (correct RED state -- GraphState field and fallback chips not implemented)
- Frontend: 6 passed (GREEN -- isolated test component validates the rendering pattern)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Backend test file ignored by .gitignore**
- **Found during:** Commit step
- **Issue:** `.gitignore` has `test_*` pattern on line 73 that blocks new backend test files
- **Fix:** Used `git add -f` to force-add the test file (matching behavior of existing tracked test files)
- **Files modified:** none (used git flag)
- **Commit:** b047c28

## Commits
| Task | Commit | Description |
|------|--------|-------------|
| 1-2  | b047c28 | RED test scaffolds for backend and frontend |

## Self-Check: PASSED
