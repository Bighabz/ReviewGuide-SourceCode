---
phase: 12-navigation-shell
plan: 03
subsystem: ui
tags: [navigation, next.js, framer-motion, ios, safe-area, template, layout]

# Dependency graph
requires:
  - phase: 12-02
    provides: "NavLayout, MobileTabBar, MobileHeader components"
provides:
  - "layout.tsx wires NavLayout as single navigation chrome wrapper"
  - "template.tsx provides 150ms crossfade entry animation for route transitions"
  - "viewport-fit=cover in layout.tsx Viewport export (iOS safe area support)"
  - "UnifiedTopbar updated with Discover/Saved/Ask/Compare/Profile nav labels"
  - "chat/page.tsx and BrowseLayout.tsx no longer render their own UnifiedTopbar"
  - "chat/page.tsx uses h-dvh (iOS keyboard fix)"
affects: [12-04, 12-05, 13-discover-screen, 14-chat-screen]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "template.tsx entry animation — 150ms opacity fade, ease [0.16, 1, 0.3, 1], no exit animation (too fragile for production per RESEARCH.md)"
    - "NavLayout as single navigation wrapper in layout.tsx — removes per-page topbar renders"
    - "Server Component (layout.tsx) can render Client Component (NavLayout) children — valid Next.js pattern"

key-files:
  created:
    - frontend/app/template.tsx
  modified:
    - frontend/app/layout.tsx
    - frontend/components/UnifiedTopbar.tsx
    - frontend/app/chat/page.tsx
    - frontend/components/browse/BrowseLayout.tsx
    - frontend/tests/navLayout.test.tsx

key-decisions:
  - "Entry-only animation in template.tsx — exit animations via AnimatePresence+FrozenRouter assessed as too fragile for production (see RESEARCH.md); 150ms fade-in is fast enough that lack of exit animation is imperceptible"
  - "NavLayout wraps layout.tsx body directly — Footer moved inside NavLayout (desktop-only), per-page topbar renders removed to prevent double navigation bars"
  - "UnifiedTopbar mobile Browse/Chat pill switcher removed — MobileTabBar now handles mobile navigation; hamburger button kept for CategorySidebar toggle"
  - "Desktop CategorySidebar toggle on /chat temporarily unavailable — NavLayout's UnifiedTopbar doesn't wire onMenuClick to chat page state; acceptable for Phase 12, Phase 14 will restructure chat screen"
  - "navLayout.test.tsx updated to use getAllByText/queryAllByText — both UnifiedTopbar (desktop) and MobileTabBar (mobile) now render same nav labels; getByText/queryByText throw on multiple matches"

patterns-established:
  - "Single navigation chrome pattern: layout.tsx wraps all pages in NavLayout; per-page topbar renders are prohibited to prevent double navigation bars"

requirements-completed: [NAV-02, NAV-04, NAV-05]

# Metrics
duration: 6min
completed: 2026-03-17
---

# Phase 12 Plan 03: Navigation Shell Integration Summary

**NavLayout wired into layout.tsx as single navigation wrapper, template.tsx provides 150ms crossfade transitions, UnifiedTopbar updated to Discover/Saved/Ask/Compare/Profile, and per-page topbar renders removed from chat and browse pages — all 33 Phase 12 automated tests GREEN**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-17T07:38:23Z
- **Completed:** 2026-03-17T07:44:18Z
- **Tasks:** 2 automated tasks complete (Task 3 is human-verify checkpoint)
- **Files modified:** 5 files modified, 1 created

## Accomplishments

- layout.tsx: Footer+div replaced with NavLayout wrapper; viewport-fit=cover added for iOS safe area support
- template.tsx: New file providing 150ms opacity fade entry animation using Framer Motion motion.div
- UnifiedTopbar: Desktop nav links updated from Browse/Chat to Discover/Saved/Ask/Compare/Profile; mobile nav pills removed
- chat/page.tsx: Own UnifiedTopbar render removed (NavLayout provides it); h-screen changed to h-dvh (iOS keyboard fix)
- BrowseLayout.tsx: Own UnifiedTopbar render removed (NavLayout provides it)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire NavLayout into layout.tsx, create template.tsx, add viewport-fit=cover** - `d3d1768` (feat)
2. **Task 2: Update UnifiedTopbar labels, remove per-page topbars, fix h-screen** - `a889941` (feat)

**Plan metadata:** _(final commit follows)_

## Files Created/Modified

- `frontend/app/template.tsx` - 150ms opacity fade entry animation wrapping every page route
- `frontend/app/layout.tsx` - NavLayout replaces Footer+div wrapper; viewportFit: 'cover' added
- `frontend/components/UnifiedTopbar.tsx` - Desktop nav updated to 5 labels; mobile pill switcher removed
- `frontend/app/chat/page.tsx` - UnifiedTopbar removed; h-screen changed to h-dvh; Suspense fallback h-screen also fixed
- `frontend/components/browse/BrowseLayout.tsx` - UnifiedTopbar removed; useRouter import removed
- `frontend/tests/navLayout.test.tsx` - queryByText updated to queryAllByText to handle both topbar+tabbar having same labels

## Decisions Made

- Entry-only animation in template.tsx — exit animation via AnimatePresence+FrozenRouter was assessed as too fragile for production (see RESEARCH.md); 150ms fade-in is perceptually sufficient
- Mobile CategorySidebar hamburger toggle on /chat is temporarily unavailable (NavLayout's UnifiedTopbar doesn't wire onMenuClick to chat page state) — accepted for Phase 12, Phase 14 will restructure chat screen entirely
- test.tsx updated to use `getAllByText` — both UnifiedTopbar desktop nav and MobileTabBar now share the same Discover/Saved/Ask/Compare/Profile labels, making `getByText` throw on multiple matches

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] navLayout.test.tsx queryByText fails on multiple elements after UnifiedTopbar label update**
- **Found during:** Task 2 (update UnifiedTopbar labels)
- **Issue:** Both UnifiedTopbar desktop nav and MobileTabBar render the same nav labels (Discover, Saved, Ask, Compare, Profile). Testing Library's `queryByText` and `getByText` throw when multiple elements match the same text. The two tests `renders MobileTabBar on mobile viewport` and `renders Discover, Saved, Ask, Compare, Profile tab labels` both threw "Found multiple elements".
- **Fix:** Changed `screen.queryByText(label) !== null` to `screen.queryAllByText(label).length > 0` and `screen.getByText(X)` to `screen.getAllByText(X).length > 0`
- **Files modified:** `frontend/tests/navLayout.test.tsx`
- **Verification:** All 8 navLayout tests pass GREEN
- **Committed in:** a889941 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - test bug caused by intentional production change)
**Impact on plan:** Fix is correct — test was asserting presence of nav labels; the underlying behavioral contract is satisfied. No scope creep.

## Issues Encountered

- Pre-existing test failures (unrelated to this plan): `chatApi.test.ts` "retries on network error with exponential backoff" (flaky timing-based test) and 3 `explainabilityPanel.test.tsx` confidence badge tests — both were failing before this plan's changes, confirmed via git stash verification. Logged to deferred-items.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Navigation shell integration is complete — NavLayout is live in layout.tsx
- template.tsx provides animated page transitions
- Human visual verification checkpoint (Task 3) is pending — awaiting user confirmation
- Phase 12 Plans 04 and 05 can proceed after Task 3 approval
- Pre-existing test failures in chatApi and explainabilityPanel should be investigated in a future plan

## Self-Check: PASSED

- FOUND: frontend/app/template.tsx
- FOUND: frontend/app/layout.tsx
- FOUND: .planning/phases/12-navigation-shell/12-03-SUMMARY.md
- FOUND: commit d3d1768 (Task 1)
- FOUND: commit a889941 (Task 2)

---
*Phase: 12-navigation-shell*
*Completed: 2026-03-17*
