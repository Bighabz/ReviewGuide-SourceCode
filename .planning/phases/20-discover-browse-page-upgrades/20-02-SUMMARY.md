---
phase: 20-discover-browse-page-upgrades
plan: 02
subsystem: ui
tags: [react, typescript, css-variables, color-mix, vitest, tailwind, discover-page]

# Dependency graph
requires:
  - phase: 17-token-foundation-dark-mode-fixes
    provides: Bold accent CSS variables (--bold-blue, --bold-amber, --bold-green, --accent) used for per-chip accent tinting
  - phase: 18-ai-image-generation
    provides: Product WebP images in public/images/products/ used by TrendingCards and verified by DISC-07

provides:
  - CategoryChipRow with 44px height, per-chip accentColor field, color-mix tinted backgrounds using Phase 17 bold tokens
  - TrendingCards with 80px thumbnails, accent border rings using topic.iconColor, proportional padding/typography
  - DISC-06 automated tests confirming chip height and color-mix backgrounds
  - DISC-07 automated tests confirming all 6 carousel slide WebP files exist on disk

affects:
  - discover-page
  - phase-20-plan-03
  - phase-20-plan-04

# Tech tracking
tech-stack:
  added: []
  patterns:
    - color-mix(in srgb, var(--bold-*) N%, var(--surface)) for tinted chip backgrounds without extra CSS classes
    - topic.iconBg as image fallback background color while lazy-loaded images load
    - topic.iconColor with color-mix for accessible, low-opacity accent border rings on thumbnails

key-files:
  created:
    - frontend/tests/browseHero.test.tsx (DISC-06 tests appended; file created by Plan 01)
  modified:
    - frontend/components/discover/CategoryChipRow.tsx
    - frontend/components/discover/TrendingCards.tsx
    - frontend/tests/imageAssets.test.ts

key-decisions:
  - "color-mix(in srgb) used for tinted chip backgrounds — avoids adding new CSS classes, works inline with CSS variables"
  - "TrendingCards thumbnail uses topic.iconBg as CSS background fallback while lazy images load — prevents empty white box"
  - "DISC-07 smart-home.webp included in expected list — file confirmed present on disk before writing test"
  - "Pre-existing ProductReview.tsx TypeScript build error (Framer Motion Variants type) is out of scope — not introduced by Phase 20"

patterns-established:
  - "Per-item accent color as data field (accentColor in ChipConfig) rather than hardcoded CSS class map"
  - "color-mix for inline style accent tinting: `color-mix(in srgb, ${accentColor} 12%, var(--surface))`"

requirements-completed: [DISC-06, DISC-07]

# Metrics
duration: 6min
completed: 2026-04-03
---

# Phase 20 Plan 02: Discover Page Bold Accent Treatment Summary

**CategoryChipRow upgraded to 44px tinted chips using Phase 17 bold CSS variable tokens via color-mix, TrendingCards upgraded to 80px accent-bordered thumbnails, with DISC-06 + DISC-07 test coverage.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-03T07:00:47Z
- **Completed:** 2026-04-03T07:07:12Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- CategoryChipRow: chips grow from 38px to 44px, each chip gets a per-category accent color from Phase 17 bold tokens, inactive chips use `color-mix(in srgb, accentColor 12%, var(--surface))` for tinted background and matching accent border/text
- TrendingCards: thumbnails grow from 48px to 80px, borderRadius 12px -> 14px, accent border ring via `color-mix(in srgb, topic.iconColor 25%, transparent)`, fallback background uses `topic.iconBg` while images lazy-load
- DISC-06 tests added to browseHero.test.tsx: 44px height assertion on all chips, color-mix background on inactive chips, 80px width assertion on trending card thumbnails
- DISC-07 test added to imageAssets.test.ts: all 6 expected carousel slide WebPs (headphones, laptop, tokyo, vacuum, shoes, smart-home) confirmed to exist on disk

## Task Commits

Each task was committed atomically:

1. **Task 1: CategoryChipRow bold accent colors + TrendingCards thumbnail upsize** - `b0438f8` (feat)
2. **Task 2: DISC-07 carousel slide image existence assertions** - `83e92aa` (test)

Note: DISC-06 tests in browseHero.test.tsx were already committed in Plan 01 commit `b3d74a7` — the file was written by Plan 01 and included the DISC-06 test groups. The Task 2 commit captures the DISC-07 addition to imageAssets.test.ts.

## Files Created/Modified

- `frontend/components/discover/CategoryChipRow.tsx` - Added accentColor to ChipConfig, updated CHIPS array with per-chip colors, restyled to 44px with color-mix tinted inactive backgrounds
- `frontend/components/discover/TrendingCards.tsx` - Thumbnail 48px -> 80px, accent border ring, iconBg fallback, padding 12->14px, title fontSize 15->16px
- `frontend/tests/browseHero.test.tsx` - DISC-06 tests for chip height and color-mix backgrounds, and 80px thumbnail width (file created by Plan 01)
- `frontend/tests/imageAssets.test.ts` - DISC-07 block asserting 6 carousel WebP files exist in public/images/products/

## Decisions Made

- color-mix(in srgb) used for tinted chip backgrounds — avoids adding new CSS classes, works inline with CSS variables
- TrendingCards thumbnail uses topic.iconBg as CSS background fallback while lazy images load — prevents empty white box while network loads
- DISC-07 smart-home.webp included in expected list (confirmed present on disk before writing test)
- Pre-existing ProductReview.tsx TypeScript build error (Framer Motion Variants type mismatch) is out of scope — not introduced by Phase 20

## Deviations from Plan

None - plan executed exactly as written. browseHero.test.tsx existed (created by Plan 01) and DISC-06 tests were appended; file was already committed by Plan 01. DISC-07 imageAssets addition committed separately.

## Issues Encountered

- browseHero.test.tsx was already committed by Plan 01 (b3d74a7) including the DISC-06 tests — the file needed appending rather than creation. The append was already in place when this plan ran.
- Pre-existing build failure in ProductReview.tsx (Framer Motion Variants type) is not caused by Phase 20 — logged out of scope per deviation rules.
- Full test suite shows 25 pre-existing failures (cardAnimations, editorsPicks, topPickBlock, etc.) — none in Phase 20 files. All 18 targeted tests pass.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Discover page category chips and trending cards now have bold visual presence with per-category accent colors
- Phase 17 bold token CSS variables (--bold-blue, --bold-amber, --bold-green, --accent) are now actively used in discover page components
- DISC-06 and DISC-07 requirements satisfied and committed
- Ready for Phase 20 Plan 03 (product carousel and scroll upgrades)

---
*Phase: 20-discover-browse-page-upgrades*
*Completed: 2026-04-03*
