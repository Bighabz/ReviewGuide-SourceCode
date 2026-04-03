---
phase: 22-visual-qa-consistency-pass
plan: 01
subsystem: testing
tags: [vitest, testing-library, css-tokens, design-system, v3.0]

# Dependency graph
requires:
  - phase: 21-chat-results-card-polish
    provides: ResultsProductCard with Check Price CTA, rank badges (TOP PICK/BEST VALUE/PREMIUM), upgraded source dots
  - phase: 20-discover-browse-page-upgrades
    provides: CategoryChipRow with For You/Tech/Travel/Kitchen/Fitness/Audio chips, ProductCarousel replacing trending cards, DiscoverSearchBar as form element
  - phase: 19-mosaic-hero
    provides: MosaicHero component, --mosaic-scrim CSS variable
  - phase: 17-token-foundation-dark-mode-fixes
    provides: --bold-blue/green/red/amber, --mosaic-scrim, --heading-* typography tokens declared in both :root and [data-theme="dark"]
provides:
  - Enforced V3.0 CSS token contract via automated assertions (14 new token tests)
  - Zero-failure test suite (352 tests passing) as v3.0 release gate
  - Updated mobileTabBar tests matching current 3-Link + 1-Settings architecture
  - Updated discover screen tests matching Phase 20 CategoryChipRow + ProductCarousel redesign
  - Updated inline product card fallback test matching ProductImage placeholder behavior
  - Updated chat screen Thinking... test matching actual animated-dots-only behavior
  - Updated results screen tests matching Check Price CTA and TOP PICK/number badge format
affects:
  - 22-visual-qa-consistency-pass (plans 02+: baseline is now green)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dark block extraction: globals.slice(darkIdx, darkIdx + 3000) for scoped token assertion"
    - "queryAllByText instead of queryByText when component renders same text in multiple contexts"
    - "Test-only updates: never modify production code to fix tests"

key-files:
  created: []
  modified:
    - frontend/tests/mobileTabBar.test.tsx
    - frontend/tests/discoverScreen.test.tsx
    - frontend/tests/inlineProductCard.test.tsx
    - frontend/tests/chatScreen.test.tsx
    - frontend/tests/resultsScreen.test.tsx
    - frontend/tests/designTokens.test.ts

key-decisions:
  - "MobileTabBar tests updated: 3 Link tabs + 1 Settings button = 4 elements, not 5 buttons; tabs use <Link> not <button>"
  - "discoverScreen DISC-02: use queryAllByText to handle label appearing in both CategorySidebar and CategoryChipRow"
  - "discoverScreen DISC-03: ProductCarousel cards detected via cursor-pointer class + h3, not data-testid='trending-card'"
  - "discoverScreen DISC-04: For You chip is always-visible (first active chip), not conditional on recent searches"
  - "discoverScreen DISC-05: DiscoverSearchBar is a <form> + <input>, not a standalone button; test via form submit"
  - "chatScreen CHAT-03: empty statusText renders dots animation only, no 'Thinking...' text span in DOM"
  - "resultsScreen RES-03: ResultsProductCard CTA is 'Check Price' not 'Buy on Amazon'"
  - "resultsScreen RES-04: rank badge shows plain number '1' in circle + 'TOP PICK' badge, not '#1 Top Pick' string"
  - "designTokens: 15 new token assertions added in 3 describe blocks covering all Phase 17 V3.0 tokens"

patterns-established:
  - "Dark mode token assertion: extract darkBlock via globals.slice(darkIdx, darkIdx + 3000)"
  - "Typography token coverage: forEach loop over token array for DRY iteration"

requirements-completed:
  - QA-02

# Metrics
duration: 5min
completed: 2026-04-01
---

# Phase 22 Plan 01: Visual QA Consistency Pass — Test Suite Green Summary

**Fixed 19 pre-existing test failures and added 15 V3.0 CSS token assertions, achieving 352/352 tests passing as the v3.0 release gate**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-01T00:53:30Z
- **Completed:** 2026-04-01T00:58:51Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Fixed all 19 pre-existing test failures across 5 test files — every failure was a test-vs-component mismatch from Phase 20-21 changes that outpaced test updates
- Added 15 new token assertions to designTokens.test.ts covering all Phase 17 V3.0 tokens (4 bold accents, 1 mosaic scrim, 7 typography scale) including dark mode counterparts
- Full suite went from 338 tests with 19 failures to 352 tests with 0 failures

## Task Commits

1. **Task 1: Fix 19 pre-existing test failures across 5 test files** - `681ef2a` (fix)
2. **Task 2: Add V3.0 token coverage assertions to designTokens.test.ts** - `9fac8ae` (feat)

## Files Created/Modified

- `frontend/tests/mobileTabBar.test.tsx` - Updated: 3 Link tabs + 1 Settings button (not 5 buttons), Home/History/Saved/Settings labels, active state via data-active/aria-current, keyboard-visible test queries 'Home' not 'Discover'
- `frontend/tests/discoverScreen.test.tsx` - Updated: queryAllByText for chip row, ProductCarousel h3/cursor-pointer pattern for DISC-03, For You always-visible, form submit for DISC-05 search bar
- `frontend/tests/inlineProductCard.test.tsx` - Updated: image fallback checks data-testid='product-image-placeholder' first, handles inner decorative img with empty alt
- `frontend/tests/chatScreen.test.tsx` - Updated: empty statusText shows dots animation only (no 'Thinking...' text span), test asserts stream-status-text absent + animate-bounce-dot present
- `frontend/tests/resultsScreen.test.tsx` - Updated: CTA text changed from 'Buy on Amazon' to 'Check Price', rank badge from '#1 Top Pick' to '1' + 'TOP PICK'
- `frontend/tests/designTokens.test.ts` - Added 3 new describe blocks: v3.0 Bold Accent tokens, v3.0 Mosaic scrim token, v3.0 Typography scale tokens (15 new assertions total)

## Decisions Made

- MobileTabBar: component uses Link elements (renders as `<a>`) not `<button>` for tabs — test queries changed from `getAllByRole('button')` to `getAllByRole('link')` + `getAllByRole('button')`
- DiscoverSearchBar: component is a `<form>` with `<input>` — DISC-05 test changed from click-based to submit-based, and element type assertion changed from button to form
- For You chip: CategoryChipRow always renders it as first chip with `activeIndex = 0`, not conditional on recent searches — test DISC-04 updated to assert always-present
- chatScreen: Message.tsx only renders status text span when `message.statusText && message.statusText !== 'Thinking...'` — empty string shows dots only
- resultsScreen: ResultsProductCard uses "Check Price" CTA button (not "Buy on Amazon") and a plain number circle (not "#1") with uppercase "TOP PICK" badge
- designTokens: dark block extracted via `globals.indexOf('[data-theme="dark"]')` + 3000-char slice — sufficient to cover all V3.0 token declarations at lines 194-210

## Deviations from Plan

None - plan executed exactly as written. All 19 failures were correctly described in the plan. All token locations matched the plan's CSS interface block.

## Issues Encountered

One additional fix needed beyond the plan description:
- discoverScreen DISC-02 used `screen.queryByText(label)` which throws when multiple elements match ('Travel' appears in both CategorySidebar navigation and CategoryChipRow). Fixed by switching to `screen.queryAllByText(label).length > 0`. This was a deviation within the task (fixing the fix), not a pre-existing condition described in the plan.

## Self-Check

- `frontend/tests/mobileTabBar.test.tsx` — FOUND (modified)
- `frontend/tests/discoverScreen.test.tsx` — FOUND (modified)
- `frontend/tests/inlineProductCard.test.tsx` — FOUND (modified)
- `frontend/tests/chatScreen.test.tsx` — FOUND (modified)
- `frontend/tests/resultsScreen.test.tsx` — FOUND (modified)
- `frontend/tests/designTokens.test.ts` — FOUND (modified)
- Commit `681ef2a` — FOUND (Task 1)
- Commit `9fac8ae` — FOUND (Task 2)
- Test suite: 352 passed, 0 failed — VERIFIED

## Self-Check: PASSED

## Next Phase Readiness

- Test suite is fully green at 352 tests — ready for Phase 22 Plan 02 (CSS variable consistency audit)
- V3.0 token contract is enforced — no token can regress undetected
- No blockers

---
*Phase: 22-visual-qa-consistency-pass*
*Completed: 2026-04-01*
