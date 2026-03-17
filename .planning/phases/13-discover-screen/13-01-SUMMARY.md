---
phase: 13-discover-screen
plan: "01"
subsystem: frontend/tests
tags: [tdd, red-tests, discover-screen, behavioral-contracts]
dependency_graph:
  requires: []
  provides: [discoverScreen.test.tsx behavioral contracts]
  affects: [frontend/app/page.tsx]
tech_stack:
  added: []
  patterns: [vitest, testing-library, vi.mock, RED-phase TDD]
key_files:
  created:
    - frontend/tests/discoverScreen.test.tsx
  modified: []
decisions:
  - Import @/app/page (current redirect stub) — tests fail because DiscoverPage does not exist yet; correct RED state
  - Mock next/navigation at module level with captured mockPush — matches mobileTabBar.test.tsx pattern
  - Mock @/lib/recentSearches via vi.mock so DISC-04 tests can control return value per-test
  - Use data-testid/aria-label selectors for search bar and trending cards to give Plan 02 a clear contract
metrics:
  duration_seconds: 77
  completed_date: "2026-03-17"
  tasks_completed: 1
  files_created: 1
---

# Phase 13 Plan 01: Discover Screen RED Tests Summary

**One-liner:** 10 failing behavioral contracts for DiscoverPage covering hero, category chips, trending cards, personalised "For You" chip, and search bar navigation.

## What Was Built

Created `frontend/tests/discoverScreen.test.tsx` with 10 failing tests organised into 5 describe blocks, one per DISC requirement. All 10 tests fail in RED state because the current `app/page.tsx` is a redirect stub (not the Discover screen implementation). This is expected and correct.

## Tasks Completed

| Task | Description | Commit | Files |
| ---- | ----------- | ------ | ----- |
| 1 | Write 10 failing behavioral test contracts for Discover screen | 18fe4c1 | frontend/tests/discoverScreen.test.tsx |

## Test Coverage

| Requirement | Tests | Contract |
| ----------- | ----- | -------- |
| DISC-01 (Hero) | 2 | Italic "researching" heading + subline text |
| DISC-02 (Category Chips) | 2 | 8+ chips render, chip tap → /chat?q=...&new=1 |
| DISC-03 (Trending Cards) | 2 | 3+ cards with title/subtitle, card tap → encoded query |
| DISC-04 (For You) | 2 | Absent with no history, present with recent searches |
| DISC-05 (Search Bar) | 2 | Button (not input), click → /chat?new=1 |

## RED State Verification

```
Tests   10 failed (10)
```

All 10 tests fail with: "No 'redirect' export is defined on the next/navigation mock" — because `app/page.tsx` currently calls `redirect('/browse')` rather than rendering DiscoverPage. Plan 02 will replace the page implementation, turning these RED tests GREEN.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `frontend/tests/discoverScreen.test.tsx` exists and has 219 lines (above the 80 line minimum)
- Commit 18fe4c1 exists in git log
- All 10 tests fail in RED state as required
- No modifications to `frontend/tests/setup.ts`
