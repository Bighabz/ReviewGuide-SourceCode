---
phase: 24-travel-response-ui-overhaul
plan: 01
subsystem: frontend/components
tags: [travel-ui, resort-cards, block-registry, tdd, test-scaffold]
dependency_graph:
  requires: []
  provides: [ResortCards component, travelUI test scaffold, attractions block renderer]
  affects: [frontend/components/blocks/BlockRegistry.tsx, frontend/tests/travelUI.test.tsx]
tech_stack:
  added: []
  patterns: [deterministic image lookup, name-fragment matching, RESORT_IMAGE_MAP, overflow-clip, eager/lazy image loading]
key_files:
  created:
    - frontend/components/ResortCards.tsx
    - frontend/tests/travelUI.test.tsx
  modified:
    - frontend/components/blocks/BlockRegistry.tsx
decisions:
  - "ResortCards splits comma-separated attraction names (e.g. 'Seven Mile Beach, Negril') into primary heading + location hint paragraph — cleaner card layout than showing the full raw string as one blob"
  - "RESORT_IMAGE_MAP uses substring matching on lowercase name to handle partial matches — robust against backend string variations"
  - "Used overflow-clip (not overflow-hidden) on resort cards — consistent with Phase 23 decision to avoid scroll containment BFC issues"
metrics:
  duration: 310s
  completed_date: "2026-04-03"
  tasks_completed: 2
  files_changed: 3
---

# Phase 24 Plan 01: ResortCards Component and Travel UI Test Scaffold Summary

**One-liner:** Visual resort card grid with deterministic image lookup replacing flat bullet-list attractions renderer, plus 11-test TDD scaffold covering all Phase 24 travel UI requirements.

## What Was Built

### ResortCards Component (`frontend/components/ResortCards.tsx`)

New component replacing the `ListBlock` for the `attractions` block type. Key design decisions:

- **RESORT_IMAGE_MAP**: 8 Caribbean-specific fragment entries (lowercase substring matching) — will be upgraded to AI-generated images in Plan 03
- **getResortImage()**: Deterministic lookup — no `Math.random()`, no hydration mismatch
- **parseName()**: Splits "Seven Mile Beach, Negril" into `{ primary: "Seven Mile Beach", location: "Negril" }` for cleaner card display
- **Grid layout**: `grid-cols-1 sm:grid-cols-2` — single column mobile, 2-column on sm+
- **Hero image**: 140px mobile / 160px desktop, `loading="eager"` for first card (LCP), `lazy` for rest
- **Styling**: `overflow-clip`, `shadow-card`, `product-card-hover`, amber MapPin icon pill header (matching ListBlock attractions aesthetic)
- **Guard**: Returns `null` when `items` is empty or undefined

### BlockRegistry Update (`frontend/components/blocks/BlockRegistry.tsx`)

- Added `import ResortCards from '@/components/ResortCards'`
- Changed `attractions` renderer from `ListBlock` to `ResortCards`
- `activities` and `restaurants` renderers unchanged (still use `ListBlock`)

### Test Scaffold (`frontend/tests/travelUI.test.tsx`)

11 tests covering TRVL-01 through TRVL-07. All 11 pass GREEN:

| Test | Requirement | Status |
|------|-------------|--------|
| TRVL-01 (3 tests) | ResortCards renders cards not bullet list items | GREEN |
| TRVL-02 (3 tests) | ResortCards fallback image for unknown resorts | GREEN |
| TRVL-03 | HotelCards PLPLinkCard has img element | GREEN |
| TRVL-04 | HotelCards CTA text "Search on Expedia" | GREEN |
| TRVL-05 | FlightCards CTA text "Search on Expedia" | GREEN |
| TRVL-06 | FlightCards destination no tracking-wider | GREEN |
| TRVL-07 | Conclusion block has color-mix background | GREEN |

Note: TRVL-03 through TRVL-07 were expected to be RED until Plan 02, but the linter/formatter applied concurrent changes to BlockRegistry that also updated the conclusion block with `color-mix`. All 11 tests pass.

## Commits

| Hash | Message |
|------|---------|
| b249b8f | test(24-01): add failing test scaffold for travel UI TRVL-01 through TRVL-07 |
| ee79b3b | feat(24-01): create ResortCards component and wire to BlockRegistry attractions |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test assertion for parsed name**
- **Found during:** Task 1 GREEN verification
- **Issue:** Test TRVL-01 used `screen.getByText('Seven Mile Beach, Negril')` but ResortCards splits comma-separated names into primary + location — the full string is never present as one text node
- **Fix:** Updated assertion to check for `'Seven Mile Beach'` and `'Negril'` separately, matching the component's intended design
- **Files modified:** `frontend/tests/travelUI.test.tsx`
- **Commit:** ee79b3b (bundled with Task 2 commit)

## Self-Check

- [x] `frontend/components/ResortCards.tsx` exists — 113 lines (min 60)
- [x] `frontend/tests/travelUI.test.tsx` exists — 204 lines (min 40)
- [x] `frontend/components/blocks/BlockRegistry.tsx` contains `ResortCards`
- [x] `RESORT_IMAGE_MAP` present in ResortCards.tsx
- [x] No `Math.random()` in ResortCards.tsx
- [x] `activities` and `restaurants` still use `ListBlock` (no regression)
- [x] Build passes: `npm run build` clean
- [x] All 11 tests pass GREEN
