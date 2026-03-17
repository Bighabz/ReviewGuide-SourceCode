---
phase: 12-navigation-shell
plan: 01
subsystem: testing
tags: [vitest, react-testing-library, navigation, mobile, tab-bar, framer-motion, next-js]

# Dependency graph
requires: []
provides:
  - "RED test scaffolds for NavLayout component (route exclusion, tab visibility, desktop topbar)"
  - "RED test scaffolds for MobileTabBar component (5 tabs, FAB navigation, active state, safe area, keyboard hide)"
  - "RED test scaffolds for template.tsx page transitions (motion.div children rendering)"
  - "RED test scaffolds for layout.tsx viewport-fit: cover export"
affects: [12-02, 12-03, 12-04, 12-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Wave 0 RED tests: behavioral contracts written before production code so subsequent plans have automated verification"
    - "Module-level pathname variable with vi.mock factory for per-test route mocking"
    - "File-read approach for Server Component tests (mirrors designTokens.test.ts pattern)"
    - "visualViewport mock with manual listener invocation to simulate keyboard open/close"

key-files:
  created:
    - frontend/tests/navLayout.test.tsx
    - frontend/tests/mobileTabBar.test.tsx
    - frontend/tests/pageTransition.test.tsx
    - frontend/tests/layout.test.tsx
  modified: []

key-decisions:
  - "File-read approach used for layout.test.tsx because layout.tsx is a Next.js Server Component that cannot be rendered in jsdom"
  - "mockPush defined at module level in mobileTabBar.test.tsx so all FAB router.push assertions share one spy instance"
  - "visualViewport keyboard-hide test accepts either dom removal or style/class-based hiding — implementation flexibility preserved for Plan 02"

patterns-established:
  - "Per-test pathname override: module-level currentPathname variable set in beforeEach, consumed by vi.mock factory"
  - "Active tab detection: test accepts aria-current='page', data-active='true', or className containing 'active'/'blue'"

requirements-completed: [NAV-01, NAV-02, NAV-03, NAV-04, NAV-05]

# Metrics
duration: 12min
completed: 2026-03-17
---

# Phase 12 Plan 01: Navigation Shell Test Scaffolds Summary

**Wave 0 RED test suite for NavLayout, MobileTabBar, page transitions, and viewport-fit — 4 test files with 24 tests establishing behavioral contracts before production code exists**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-17T07:19:58Z
- **Completed:** 2026-03-17T07:31:30Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Created 4 test files covering all 5 NAV requirements (NAV-01 through NAV-05)
- All 4 test files fail in RED state as required — components do not yet exist
- Established per-test route mocking pattern (module-level currentPathname variable) for clean test isolation
- layout.test.tsx uses file-read approach (same as designTokens.test.ts) to safely test Server Component exports

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test scaffolds for NavLayout and MobileTabBar** - `d6b3428` (test)
2. **Task 2: Create test scaffolds for page transitions and layout viewport** - `7f0ddb4` (test)

**Plan metadata:** _(final commit follows)_

## Files Created/Modified
- `frontend/tests/navLayout.test.tsx` - 8 tests: tab visibility, route exclusions for /admin/* and /privacy /terms /affiliate-disclosure, child rendering
- `frontend/tests/mobileTabBar.test.tsx` - 13 tests: 5 tabs, all labels, FAB /chat?new=1 routing, active Discover tab on /browse, safe-area padding, keyboard hide/show
- `frontend/tests/pageTransition.test.tsx` - 3 tests: template.tsx children rendering via motion.div
- `frontend/tests/layout.test.tsx` - 3 tests: viewport named export, Viewport type import, viewportFit: 'cover' value

## Decisions Made
- Used file-read approach for `layout.test.tsx` (not component render) because layout.tsx is a Next.js Server Component — same approach as `designTokens.test.ts` already in the test suite
- `mockPush` defined at module level in `mobileTabBar.test.tsx` so the FAB router.push assertion captures the right spy (global setup.ts mock would shadow it otherwise)
- Keyboard-hide test accepts multiple valid implementations (DOM removal, style display:none, aria-hidden, className) to give Plan 02 implementation flexibility while still enforcing the behavioral contract

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- None. Tests ran cleanly, all 4 files fail on "Cannot find module" (navLayout, mobileTabBar, pageTransition) or assertion failure (layout.test.tsx viewportFit: 'cover' not yet present). This is the correct RED state.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 test files ready — Plan 02 can target GREEN for navLayout, mobileTabBar, and pageTransition tests
- Plan 03 targets GREEN for layout.test.tsx (adding viewportFit: 'cover' to layout.tsx)
- No blockers

---
*Phase: 12-navigation-shell*
*Completed: 2026-03-17*
