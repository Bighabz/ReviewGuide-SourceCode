---
phase: 21-chat-results-card-polish
plan: 02
subsystem: ui
tags: [framer-motion, react, typescript, spring-animation, affiliate-links]

# Dependency graph
requires:
  - phase: 21-chat-results-card-polish
    provides: Plan 01 — InlineProductCard spring hover and bold price (CARD-04 baseline)
provides:
  - ProductReview with deriveMerchant URL extraction, 3-offer cap, spring hover variants
  - TopPickBlock with motion.div spring hover, 200x200px image, bold 3-stop gradient CTA

affects: [Message.tsx rendering, BlockRegistry product_review and top_pick blocks]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Framer Motion variants object with as const for TypeScript Easing literal types"
    - "Separate entrance (easeOut) from hover (spring) via named variants: hidden/visible/hover"
    - "Merchant name derivation: clean merchant field first, fall back to URL hostname parsing"

key-files:
  created: []
  modified:
    - frontend/components/ProductReview.tsx
    - frontend/components/TopPickBlock.tsx
    - frontend/tests/topPickBlock.test.tsx

key-decisions:
  - "Use as const on 'spring' and 'easeOut' string literals in variants — Framer Motion Variants type requires Easing union not bare string"
  - "TopPickBlock test fixed to use getAllByRole('link') + filter — component has always rendered product name + CTA as two links when affiliateUrl provided"
  - "Pre-existing cardAnimations InlineProductCard RED tests not fixed — comment says 'Task 3 will make green'; out of scope for plan 02"

patterns-established:
  - "cardVariants pattern: hidden/visible (easeOut entrance) + hover (spring stiffness:400 damping:28) — reuse in future card components"
  - "deriveMerchant: clean merchant field → URL hostname domainMap fallback → capitalize first subdomain segment"

requirements-completed: [CARD-01, CARD-02, CARD-03, CARD-04]

# Metrics
duration: 13min
completed: 2026-04-03
---

# Phase 21 Plan 02: Chat Results Card Polish Summary

**ProductReview upgraded with deriveMerchant URL extraction, 3-offer cap, and Framer Motion spring variants (stiffness 400, damping 28); TopPickBlock converted to motion.div with 200x200px image and bold 3-stop gradient CTA**

## Performance

- **Duration:** 13 min
- **Started:** 2026-04-03T07:00:41Z
- **Completed:** 2026-04-03T07:13:57Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- ProductReview: `deriveMerchant()` extracts clean merchant names from URL hostname (Amazon, eBay, Walmart, Best Buy, Target, Newegg, B&H Photo, Costco) with generic fallback
- ProductReview: affiliate_links capped at 3 via `.slice(0, 3)`; Framer Motion variants separate entrance animation from spring hover
- TopPickBlock: outer `<div>` replaced with `<motion.div>` + `topPickVariants`; `product-card-hover` CSS class removed; image enlarged from 160x160 to 200x200px on desktop; CTA gradient upgraded to 3-stop `--bold-blue → --primary → --accent` with box-shadow

## Task Commits

Each task was committed atomically:

1. **Task 1: Upgrade ProductReview** - `7d68d3f` (feat)
2. **Task 2: Upgrade TopPickBlock** - `2115c7c` (feat)
3. **TypeScript fix: as const for Variants** - `1c41040` (fix)

**Plan metadata:** (this commit)

## Files Created/Modified

- `frontend/components/ProductReview.tsx` — deriveMerchant helper, 3-offer cap, cardVariants with spring hover
- `frontend/components/TopPickBlock.tsx` — motion.div spring hover, 200x200 image, 3-stop CTA gradient
- `frontend/tests/topPickBlock.test.tsx` — fix: use getAllByRole + filter (pre-existing double-link issue)

## Decisions Made

- Used `as const` on string literal `'spring'` and `'easeOut'` in Framer Motion variants objects — TypeScript's `Easing` union type does not accept bare `string`
- TopPickBlock test required fix for `getByRole('link')` → `getAllByRole + filter` — the component has always rendered two links (product name + CTA) when `affiliateUrl` is provided; this was a pre-existing test weakness
- Pre-existing failing `cardAnimations.test.tsx` InlineProductCard RED tests left untouched — test file comment explicitly states "Task 3 will make green"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TypeScript `Easing` type mismatch in Framer Motion variants**
- **Found during:** Task 1 and 2 (build verification)
- **Issue:** `ease: 'easeOut'` and `type: 'spring'` inferred as `string` fail TypeScript's `Easing` union type check in `Variants`
- **Fix:** Added `as const` assertion: `ease: 'easeOut' as const`, `type: 'spring' as const`
- **Files modified:** `frontend/components/ProductReview.tsx`, `frontend/components/TopPickBlock.tsx`
- **Verification:** `npm run build` shows "Compiled successfully" with no type errors
- **Committed in:** `1c41040` (fix commit)

**2. [Rule 1 - Bug] topPickBlock test using `getByRole('link')` with ambiguous match**
- **Found during:** Task 2 (test run)
- **Issue:** Pre-existing test used `getByRole('link')` expecting exactly 1 link, but component renders 2 links when `affiliateUrl` is provided (product name + CTA)
- **Fix:** Changed to `getAllByRole('link')` + `.find()` by href attribute
- **Files modified:** `frontend/tests/topPickBlock.test.tsx`
- **Verification:** All 6 TopPickBlock tests pass
- **Committed in:** `2115c7c` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 bugs)
**Impact on plan:** Both fixes required for build success and test correctness. No scope creep.

## Issues Encountered

- Windows Next.js build shows ENOENT errors during "Collecting page data" phase — pre-existing Windows file system race condition in `.next` directory. TypeScript compilation passes cleanly ("Compiled successfully").

## Next Phase Readiness

- Plan 02 complete: ProductReview and TopPickBlock both upgraded with spring hover and premium visual polish
- Plan 03 (InlineProductCard) tests (cardAnimations.test.tsx) have pre-scaffolded RED tests waiting for implementation

---
*Phase: 21-chat-results-card-polish*
*Completed: 2026-04-03*
