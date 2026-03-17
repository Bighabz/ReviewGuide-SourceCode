---
phase: 12-navigation-shell
plan: 02
subsystem: navigation
tags: [mobile, tab-bar, navigation, framer-motion, safe-area, ios, keyboard-detection]

# Dependency graph
requires: [12-01]
provides:
  - "MobileTabBar: fixed 5-tab bottom bar with raised FAB, keyboard-aware hiding, safe area padding, long-press Profile popover"
  - "MobileHeader: slim mobile top bar with logo/avatar (default) or back-arrow/title (chat route)"
  - "NavLayout: conditional navigation shell — desktop topbar+footer vs mobile header+tab bar, route exclusions"
affects: [12-03, 12-04, 12-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "calc(0px + env(safe-area-inset-bottom)) for jsdom-compatible safe area testing — calc() is preserved, bare env() is stripped by jsdom CSS parser"
    - "data-keyboard-open attribute on nav element for testable keyboard state — Framer Motion exit animations don't complete in jsdom so attribute-based detection is required"
    - "RefCallback pattern to set paddingBottom after mount, bypassing React style prop normalization"
    - "motion.nav with animate={{ y: keyboardOpen ? '100%' : 0 }} — always present in DOM, slides out when keyboard opens; real behavior + testable state"

key-files:
  created:
    - frontend/components/MobileTabBar.tsx
    - frontend/components/MobileHeader.tsx
    - frontend/components/NavLayout.tsx
  modified: []

key-decisions:
  - "Used calc(0px + env(safe-area-inset-bottom)) instead of bare env() — jsdom strips bare env() values but preserves calc() functions, allowing the NAV-05 safe area test to pass"
  - "Kept nav always in DOM (animate y position) rather than AnimatePresence removal — Framer Motion exit animations don't complete in jsdom, so removed-from-DOM approach fails keyboard-hide test; data-keyboard-open attribute enables test detection"
  - "NavLayout uses min-h-dvh (not min-h-screen) per locked decision — iOS keyboard overlap prevention"

# Metrics
duration: 8min
completed: 2026-03-17
---

# Phase 12 Plan 02: Navigation Shell Components Summary

**Three core navigation shell components built — MobileTabBar (5-tab bottom bar with FAB, keyboard detection, safe area), MobileHeader (slim top bar with logo/avatar or back-arrow), and NavLayout (conditional chrome wrapper with route exclusions) — all 21 Wave 0 tests GREEN**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-17T07:25:27Z
- **Completed:** 2026-03-17T07:33:36Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- MobileTabBar: 5 tabs (Discover, Saved, Ask FAB, Compare, Profile), keyboard detection via visualViewport API, animated slide-out, long-press Profile popover with theme toggle + accent picker, active tab detection
- MobileHeader: dual-mode (logo/avatar on default routes, back-arrow + title on /chat), uses usePathname() for route detection
- NavLayout: route exclusion via EXCLUDED_PREFIXES, desktop UnifiedTopbar + Footer, mobile MobileHeader + MobileTabBar, correct bottom padding for iOS safe area
- All 13 mobileTabBar tests + all 8 navLayout tests GREEN (21 total) — all Plan 01 Wave 0 contracts fulfilled

## Task Commits

Each task was committed atomically:

1. **Task 1: Create MobileTabBar and MobileHeader** - `cb4b052` (feat)
2. **Task 2: Create NavLayout** - `83fbb77` (feat)

**Plan metadata:** _(final commit follows)_

## Files Created/Modified

- `frontend/components/MobileTabBar.tsx` - 5-tab fixed bottom bar, FAB, keyboard detection, long-press popover (238 lines)
- `frontend/components/MobileHeader.tsx` - slim mobile header, logo/avatar + chat back-arrow mode (82 lines)
- `frontend/components/NavLayout.tsx` - conditional navigation shell, route exclusions, desktop/mobile chrome (71 lines)

## Decisions Made

- Used `calc(0px + env(safe-area-inset-bottom))` for safe area padding — jsdom's CSS parser silently drops bare `env()` values but preserves `calc()` functions containing `env()`. The test checks `.toContain('env(safe-area-inset-bottom)')` which the calc() approach satisfies.
- Kept nav always rendered (animate y position) rather than AnimatePresence removal — in jsdom, Framer Motion exit animations don't complete synchronously, so the keyboard-hide test checking `container.querySelector('nav')` would find the element mid-animation. Using `data-keyboard-open="true"` attribute gives the test a reliable signal.
- NavLayout uses `min-h-dvh` per the locked Phase 12 decision (h-dvh prevents iOS keyboard overlap).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] jsdom strips bare env() CSS values**
- **Found during:** Task 1 (safe area padding test)
- **Issue:** `nav!.style.paddingBottom = 'env(safe-area-inset-bottom)'` returns empty string in jsdom — jsdom's CSS parser rejects the `env()` CSS function
- **Fix:** Used `calc(0px + env(safe-area-inset-bottom))` which jsdom's parser preserves while still working identically in real browsers
- **Files modified:** `frontend/components/MobileTabBar.tsx` (navRefCallback)
- **Commit:** cb4b052

**2. [Rule 1 - Bug] Framer Motion AnimatePresence doesn't synchronously remove elements in jsdom**
- **Found during:** Task 1 (keyboard hide test)
- **Issue:** Using `{!keyboardOpen && <motion.nav>}` with AnimatePresence — when keyboard opens, the nav starts its exit animation but remains in DOM in jsdom (no CSS animation support). Test checking `container.querySelector('nav')` finds the element and then checks `data-keyboard-open="true"` which was not set
- **Fix:** Removed AnimatePresence wrapping; nav always renders but animates y position; `data-keyboard-open={keyboardOpen ? 'true' : 'false'}` attribute added for test detection
- **Files modified:** `frontend/components/MobileTabBar.tsx`
- **Commit:** cb4b052

## Issues Encountered

- jsdom CSS limitations required two bug fixes (safe area padding + keyboard hide detection) before all tests passed
- Both fixes are backward-compatible with real browsers — `calc()` with `env()` works the same, and `data-keyboard-open` is just an informational attribute

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- NavLayout, MobileTabBar, MobileHeader all created and tested GREEN
- Plan 03 (layout.tsx integration + viewport-fit=cover) can proceed
- Plan 04 (template.tsx page transitions) can proceed
- No blockers

---
*Phase: 12-navigation-shell*
*Completed: 2026-03-17*
