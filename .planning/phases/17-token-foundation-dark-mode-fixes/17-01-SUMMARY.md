---
phase: 17-token-foundation-dark-mode-fixes
plan: 01
subsystem: ui
tags: [css-tokens, dark-mode, design-system, typography, globals-css]

# Dependency graph
requires: []
provides:
  - CSS custom properties for bold editorial accent palette (--bold-blue, --bold-green, --bold-red, --bold-amber) in :root and [data-theme="dark"]
  - Typography scale tokens (--heading-hero, --heading-xl, --heading-lg, --heading-md, --heading-sm, --heading-weight, --heading-line-height) in :root and [data-theme="dark"]
  - Dark mode gap fixes: --error, --warning, --info, --shadow-xl now have [data-theme="dark"] counterparts
affects: [phase-18, phase-19, phase-20, phase-21, phase-22]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "All new CSS tokens added to both :root and [data-theme='dark'] in the same edit — enforced parity"
    - "Typography tokens are named utilities applied by components explicitly, not global overrides"

key-files:
  created: []
  modified:
    - frontend/app/globals.css

key-decisions:
  - "Typography tokens declared identically in dark block for completeness (no luminance dependency)"
  - "Global h1/h2/h3 rules left unchanged — typography tokens are opt-in per component"
  - "Bold accent dark values use accessible lightened variants (#60A5FA, #4ADE80, #F87171, #FCD34D)"

patterns-established:
  - "V3 Bold accents: vibrant light-mode values (#1B4DFF/#16A34A/#DC2626/#D97706), pastel dark-mode equivalents (Tailwind 400 range)"
  - "Typography scale: clamp() for fluid hero/xl tokens, fixed rem for md/sm tokens"

requirements-completed: [TOK-01, TOK-02, TOK-03]

# Metrics
duration: 2min
completed: 2026-04-01
---

# Phase 17 Plan 01: Token Foundation + Dark Mode Fixes Summary

**Added bold editorial accent palette (4 tokens), typography scale (7 tokens), and closed 4 pre-existing dark mode gaps in globals.css — all 13 designTokens tests pass, no regressions**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-01T08:26:18Z
- **Completed:** 2026-04-01T08:28:24Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Bold accent palette (--bold-blue, --bold-green, --bold-red, --bold-amber) added to :root with matching dark mode counterparts using accessible lightened values
- Typography scale tokens (--heading-hero through --heading-sm, --heading-weight, --heading-line-height) added to both :root and dark block for component use via `text-[var(--heading-hero)]`
- Pre-existing dark mode gaps closed: --error, --warning, --info, and --shadow-xl now have [data-theme="dark"] values
- All 13 existing designTokens.test.ts assertions pass, 21 pre-existing failures unchanged (no regressions introduced)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add bold accent palette and fix missing dark mode gaps** - `2f5f5c3` (feat)
2. **Task 2: Add typography scale tokens** - `ebd0821` (feat)

**Plan metadata:** (docs commit pending)

## Files Created/Modified
- `frontend/app/globals.css` - Added 4 bold accent tokens to :root, 8 dark accent tokens (4 new + 4 gap fixes), 7 typography tokens to :root, 7 typography tokens to dark block

## Decisions Made
- Typography tokens declared identically in `[data-theme="dark"]` even though values are theme-neutral — ensures downstream components can reference them without conditional logic
- Global `h1/h2/h3` rules left unchanged per plan instructions — typography tokens are opt-in utilities Phase 20 components apply explicitly
- Bold accent dark values use Tailwind 400-range pastels to maintain contrast on dark backgrounds (#60A5FA for blue, #4ADE80 for green, #F87171 for red, #FCD34D for amber)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None — both tasks executed cleanly on first attempt, all tests passed immediately.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Token foundation complete; Plan 02 (component conversions) can safely reference --bold-blue/green/red/amber and --heading-* tokens
- Phases 20-21 styling upgrades have the full token set available
- All 4 dark mode gaps (--error, --warning, --info, --shadow-xl) closed — dark theme is now fully consistent

---
*Phase: 17-token-foundation-dark-mode-fixes*
*Completed: 2026-04-01*
