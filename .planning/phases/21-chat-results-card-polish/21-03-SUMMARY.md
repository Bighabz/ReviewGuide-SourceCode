---
phase: 21-chat-results-card-polish
plan: 03
subsystem: ui
tags: [framer-motion, react, typescript, tailwind, results-page, vitest]

requires:
  - phase: 21-chat-results-card-polish
    provides: Wave 0 scaffolds, InlineProductCard spring hover, TopPickBlock spring hover

provides:
  - ResultsProductCard with Framer Motion spring hover (stiffness 400, damping 28)
  - ResultsProductCard bold v3.0 typography (font-bold font-serif) and badge colors (--bold-* tokens)
  - ResultsMainPanel and ResultsPage source dots upgraded to w-3 h-3 with ring emphasis
  - Source site names upgraded to font-semibold in both ResultsMainPanel and ResultsPage
  - 4 new test assertions in resultsScreen.test.tsx covering RES-07 and RES-08

affects:
  - results-page
  - visual-polish
  - card-animations

tech-stack:
  added: []
  patterns:
    - "ResultsProductCard uses motion.div from framer-motion for spring hover — same stiffness/damping as InlineProductCard"
    - "Badge colors use --bold-amber/--bold-blue/--bold-green CSS tokens with white (#FFFFFF) text for WCAG contrast"
    - "Source dots use w-3 h-3 consistently across ResultsMainPanel and ResultsPage"

key-files:
  created: []
  modified:
    - frontend/components/ResultsProductCard.tsx
    - frontend/components/ResultsMainPanel.tsx
    - frontend/app/results/[id]/page.tsx
    - frontend/tests/resultsScreen.test.tsx

key-decisions:
  - "ResultsPage source dots upgraded alongside ResultsMainPanel for visual consistency — both rendered the same source list"
  - "Ring treatment (ring-2 ring-offset-1 with CSS custom properties) applied in ResultsMainPanel; ResultsPage keeps clean w-3 h-3 without ring to avoid custom-property complexity in inline styles"
  - "Pre-existing test failures (2) in resultsScreen.test.tsx are unrelated to plan changes — Buy on Amazon vs Check Price text mismatch and #1/#Top Pick case mismatch were present before Plan 03"

patterns-established:
  - "Spring hover pattern: motion.div with whileHover={{ y: -4, boxShadow }} + transition type spring stiffness 400 damping 28"
  - "V3 badge pattern: --bold-amber/--bold-blue/--bold-green bg with white text + px-2.5 py-1 rounded-md font-bold tracking-wider"

requirements-completed: [RES-07, RES-08, CARD-04]

duration: 12min
completed: 2026-04-03
---

# Phase 21 Plan 03: Chat Results Card Polish Summary

**ResultsProductCard upgraded with Framer Motion spring hover and V3 bold editorial tokens; source dots enlarged to w-3 h-3 across ResultsMainPanel and ResultsPage; 4 new test assertions added**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-03T07:03:00Z
- **Completed:** 2026-04-03T07:15:30Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Converted `ResultsProductCard` outer div to `motion.div` with spring hover (y: -4, stiffness: 400, damping: 28) — matching InlineProductCard animation pattern
- Upgraded product name heading to `text-base font-bold font-serif tracking-tight` for editorial feel
- Upgraded badge colors from hardcoded hex to `--bold-amber`/`--bold-blue`/`--bold-green` CSS tokens with white text; badge sizing to `px-2.5 py-1 rounded-md font-bold tracking-wider`
- Upgraded source dots from `w-2 h-2` to `w-3 h-3` in both `ResultsMainPanel` and `ResultsPage`, plus ring emphasis in ResultsMainPanel
- Upgraded source site names from `font-medium` to `font-semibold` in both components
- Added 4 new test assertions in `resultsScreen.test.tsx` for RES-07 + RES-08 (all pass)
- Build passes cleanly; no regressions introduced

## Task Commits

1. **Task 1: Upgrade ResultsProductCard with bold v3.0 visual language and spring hover** - `44b2aa6` (feat)
2. **Task 2: Upgrade source dots and extend results screen tests** - `17bd843` (feat)

## Files Created/Modified

- `frontend/components/ResultsProductCard.tsx` - motion.div spring hover, V3 badge tokens, bold font-serif heading
- `frontend/components/ResultsMainPanel.tsx` - source dots w-3 h-3 with ring, font-semibold site names
- `frontend/app/results/[id]/page.tsx` - source dots w-3 h-3, font-semibold site names for test coverage
- `frontend/tests/resultsScreen.test.tsx` - 4 new assertions: dot size, font-semibold, no product-card-hover, font-bold heading

## Decisions Made

- Upgraded `ResultsPage` (`/app/results/[id]/page.tsx`) source dots alongside `ResultsMainPanel` because the test suite tests `ResultsPage` directly — ensuring test assertions are verifiable against the rendered output.
- Ring treatment uses `--tw-ring-color` and `--tw-ring-offset-color` CSS custom properties on the inline style object in `ResultsMainPanel`. `ResultsPage` uses simpler `w-3 h-3` without ring to avoid TypeScript complexity with inline style custom properties in a non-component context.
- Removed all CSS hover classes (`product-card-hover`, `transition-all`, `duration-200`, `hover:shadow-card-hover`, `hover:-translate-y-0.5`) from `ResultsProductCard` — Framer Motion owns all hover behaviour.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Applied dot upgrade to ResultsPage in addition to ResultsMainPanel**

- **Found during:** Task 2 (source dot upgrade)
- **Issue:** The test suite (`resultsScreen.test.tsx`) renders `ResultsPage` not `ResultsMainPanel`. The new tests asserting `w-3 h-3` dot size would fail unless `ResultsPage` dots were also upgraded.
- **Fix:** Upgraded source dots in `ResultsPage` (`/app/results/[id]/page.tsx`) to `w-3 h-3` and `font-semibold` to match the `ResultsMainPanel` treatment.
- **Files modified:** `frontend/app/results/[id]/page.tsx`
- **Verification:** All 4 new test assertions pass.
- **Committed in:** `17bd843` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical / correctness for test coverage)
**Impact on plan:** Necessary for test assertions to be valid; consistent visual treatment across both result-display surfaces. No scope creep.

## Issues Encountered

- Two pre-existing test failures in `resultsScreen.test.tsx` (present before Plan 03): "Buy on Amazon" CTA text mismatch (component says "Check Price") and rank badge text mismatch ("#1"/"Top Pick" expected vs "1"/"TOP PICK" rendered). These are not regressions from this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 21 Plan 03 complete — all results page visual polish done (RES-07, RES-08, CARD-04)
- `ResultsProductCard` now has full spring hover parity with `InlineProductCard`
- V3 bold editorial token usage consistent across all card types
- Source citations use enlarged w-3 h-3 dots across the results page surface

---
*Phase: 21-chat-results-card-polish*
*Completed: 2026-04-03*
