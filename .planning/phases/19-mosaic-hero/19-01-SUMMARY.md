---
phase: 19-mosaic-hero
plan: 01
subsystem: ui
tags: [react, tailwind, css, mosaic, hero, webp, lcp, cls, core-web-vitals]

# Dependency graph
requires:
  - phase: 18-ai-image-generation
    provides: 8 mosaic-*.webp product images in frontend/public/images/products/
  - phase: 17-token-foundation-dark-mode-fixes
    provides: CSS variable token system in globals.css (--background, --shadow-md, --bold-amber)
provides:
  - MosaicHero component rendering 8 tilted/overlapping product image tiles with pure CSS transforms
  - --mosaic-scrim CSS variable in both light and dark themes for gradient overlay
  - Test suite (5 tests) covering HERO-01, HERO-03, HERO-04 behavioral contracts
affects:
  - 19-02 (page.tsx wiring — imports MosaicHero and uses --mosaic-scrim)
  - 19-03 (visual QA — validates mosaic composition)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Pure CSS absolute-position + transform:rotate() mosaic collage (no JS animation library)
    - MOSAIC_TILES static const array — rotation/offset values co-located with image src data
    - loading="eager" + fetchPriority="high" on first above-fold image for LCP optimization
    - hidden sm:block on outer tiles (index 4-7) to prevent mobile overcrowding
    - --mosaic-scrim CSS variable with both :root and [data-theme="dark"] values

key-files:
  created:
    - frontend/components/discover/MosaicHero.tsx
    - frontend/tests/mosaicHero.test.tsx
  modified:
    - frontend/app/globals.css

key-decisions:
  - "Use raw <img> tags (not next/image) — consistent with entire codebase convention"
  - "Static MOSAIC_TILES const array (not Math.random()) — avoids SSR hydration mismatch"
  - "overflow: visible on mosaic container — rotated tile edges should not clip; outer wrapper clips in Plan 02"
  - "Tiles[4-7] hidden on mobile via hidden sm:block — 4 center tiles sufficient at 375px"

patterns-established:
  - "Pattern: Decorative background elements use aria-hidden='true'"
  - "Pattern: Mosaic tile component uses MOSAIC_TILES static array with per-tile eager/rotate/offset data"
  - "Pattern: --mosaic-scrim theme variable enables CSS-only dark/light gradient without JS"

requirements-completed: [HERO-01, HERO-03, HERO-04]

# Metrics
duration: 12min
completed: 2026-03-31
---

# Phase 19 Plan 01: Mosaic Hero Component Summary

**Pure CSS mosaic collage component with 8 tilted product image tiles, loading="eager" LCP optimization, and theme-aware --mosaic-scrim gradient variable**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-31T02:51:00Z
- **Completed:** 2026-03-31T03:03:00Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 3

## Accomplishments
- Created MosaicHero.tsx with 8 absolutely-positioned, rotated product image tiles using pure CSS transforms (no JS library)
- First tile (mosaic-headphones) uses loading="eager" + fetchPriority="high" for LCP optimization (HERO-04)
- Added --mosaic-scrim CSS variable to globals.css for both light mode (#FAFAF7 ivory gradient) and dark mode (#0A0C12 navy-black gradient)
- Created 5-test Vitest suite covering HERO-01 (8 img elements), HERO-03 (pure CSS, no JS library), HERO-04 (eager loading + fetchPriority), CLS guard (explicit width/height), and aria-hidden (accessibility)
- Mobile-responsive: tiles 4-7 hidden below sm breakpoint to prevent crowding at 375px

## Task Commits

Each task was committed atomically:

1. **Task 1: Test scaffold + MosaicHero component + --mosaic-scrim token** - `be2052c` (feat)

**Plan metadata:** (pending — docs commit)

## Files Created/Modified
- `frontend/components/discover/MosaicHero.tsx` - 8-tile mosaic collage component with MOSAIC_TILES static array and pure CSS transforms
- `frontend/tests/mosaicHero.test.tsx` - 5 Vitest tests covering HERO-01, HERO-03, HERO-04 + CLS/a11y guards
- `frontend/app/globals.css` - Added --mosaic-scrim gradient variable to :root and [data-theme="dark"] blocks

## Decisions Made
- Used raw `<img>` tags (not `next/image`) — consistent with entire codebase convention; avoids next.config.js remotePatterns changes
- Static MOSAIC_TILES const array with deterministic rotation/offset values — avoids SSR hydration mismatch from Math.random()
- Set `overflow: visible` on mosaic container (not `overflow: hidden`) — rotated tile edges should bleed naturally; the outer wrapper in Plan 02 will handle overflow clipping
- Tiles at indexes 4-7 (smartwatch, camera, fitness-gear, speaker) use `hidden sm:block` — 4 center tiles are sufficient for mobile; the wider outer tiles only look good at sm+ widths

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `fetchPriority` React prop emits a jsdom console warning ("React does not recognize the `fetchPriority` prop"). This is expected behavior: React renders it as lowercase `fetchpriority` in the DOM, which is what the test correctly asserts via `getAttribute('fetchpriority')`. Not a bug.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- MosaicHero.tsx is ready to import in Plan 02 (page.tsx wiring)
- --mosaic-scrim token is available for the gradient overlay div in Plan 02
- All 5 mosaicHero tests pass; DISC-01 hero section tests pass (no page.tsx changes)
- Pre-existing DISC-02 through DISC-05 failures are unrelated to this plan (confirmed via git stash verification)

---
*Phase: 19-mosaic-hero*
*Completed: 2026-03-31*
