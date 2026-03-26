---
phase: 06-skimlinks-link-wrapper
plan: 01
subsystem: testing
tags: [pytest, skimlinks, tdd, affiliate, redis-cache]

requires:
  - phase: none
    provides: standalone RED test scaffold
provides:
  - RED test scaffold with 11 behavioral contracts for SkimlinksLinkWrapper
  - Test file at backend/tests/test_skimlinks.py
affects: [06-skimlinks-link-wrapper]

tech-stack:
  added: []
  patterns: [TDD RED-first test scaffolding with import-error as expected failure]

key-files:
  created:
    - backend/tests/test_skimlinks.py
  modified: []

key-decisions:
  - "Test file follows existing test_product_affiliate.py bootstrap pattern with os.environ.setdefault block"
  - "Tests use patch.object for internal methods and patch for module-level functions to match Plan 02 implementation contract"

patterns-established:
  - "4-class test organization: TestWrapUrl (core behavior), TestDomainCache (caching), TestFeatureFlag, TestAuth"

requirements-completed: []

duration: 3min
completed: 2026-03-25
---

# Phase 6 Plan 01: RED Test Scaffold for SkimlinksLinkWrapper

**11 failing test methods across 4 classes covering URL wrapping, domain exclusion, Redis caching, feature flag, and OAuth2 auth**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-25T23:56:29Z
- **Completed:** 2026-03-25T23:59:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created 11 test methods across 4 test classes (TestWrapUrl, TestDomainCache, TestFeatureFlag, TestAuth)
- All tests fail RED with ModuleNotFoundError as expected (skimlinks.py does not exist yet)
- Behavioral contracts cover AFFL-01 (URL wrapping), AFFL-02 (Amazon/eBay exclusion), AFFL-03 (Redis cache with 24h TTL)

## Task Commits

1. **Task 1: Create RED test scaffold** - `4d103d6` (test)

## Files Created/Modified
- `backend/tests/test_skimlinks.py` - 11 test methods across 4 classes; RED state (imports fail)

## Decisions Made
- Used git add -f to override blanket `test_*` .gitignore rule (matching existing test_product_affiliate.py pattern)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- .gitignore has a blanket `test_*` rule that blocks all test files; resolved with `git add -f` (same approach used for existing test files)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Test scaffold ready for Plan 02 to implement SkimlinksLinkWrapper and turn tests GREEN

---
*Phase: 06-skimlinks-link-wrapper*
*Completed: 2026-03-25*
