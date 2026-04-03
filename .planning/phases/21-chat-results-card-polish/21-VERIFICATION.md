---
phase: 21-chat-results-card-polish
verified: 2026-04-01T00:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
---

# Phase 21: Chat Results Card Polish — Verification Report

**Phase Goal:** Every product card variant across the chat and results screens has premium spacing, bolder typography, spring-physics hover animations, a clean 3-column "Where to Buy" section with merchant labels, and no Framer Motion regressions during active streaming.

**Verified:** 2026-04-01
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | AI response headings in chat are visibly larger and bolder than pre-v3.0 | VERIFIED | `Message.tsx` lines 205–207: `prose-h1:text-[var(--heading-lg)] prose-h1:font-bold`, `prose-h2:text-[var(--heading-md)] prose-h2:font-bold`, `prose-h3:text-[var(--heading-sm)] prose-h3:font-semibold` — all V3 CSS tokens present |
| 2 | Inline product card rows lift on hover with spring physics | VERIFIED | `InlineProductCard.tsx` line 87–93: `motion.div` with `whileHover={{ backgroundColor: 'var(--surface-hover)', x: 2 }}` and `transition={{ type: 'spring', stiffness: 400, damping: 28 }}` |
| 3 | Inline product card price displays in bold text-lg weight | VERIFIED | `InlineProductCard.tsx` line 129: `<span className="font-bold text-lg" style={{ color: 'var(--text)' }}>` |
| 4 | ProductReview cards show maximum 3 "Where to Buy" offers with clean merchant names | VERIFIED | `ProductReview.tsx` lines 153–154: `affiliate_links.slice(0, 3)` and `deriveMerchant(link)` called per link |
| 5 | ProductReview spring hover lifts card with shadow on hover | VERIFIED | `ProductReview.tsx` lines 50–62: `cardVariants` with `hover: { y: -4, boxShadow: '...', transition: { type: 'spring' as const, stiffness: 400, damping: 28 } }` — `whileHover="hover"` at line 109 |
| 6 | TopPickBlock CTA has a bolder 3-stop gradient with box-shadow | VERIFIED | `TopPickBlock.tsx` lines 136–137: `background: 'linear-gradient(135deg, var(--bold-blue) 0%, var(--primary) 40%, var(--accent) 100%)'` and `boxShadow: '0 4px 14px rgba(27, 77, 255, 0.35)'` |
| 7 | TopPickBlock product image area is 200x200px on desktop | VERIFIED | `TopPickBlock.tsx` line 76: `sm:w-[200px]` and `sm:h-[200px]` |
| 8 | TopPickBlock uses Framer Motion spring hover instead of CSS product-card-hover | VERIFIED | `TopPickBlock.tsx` line 8–15: `topPickVariants` with spring; line 63–67: `motion.div` with `whileHover="hover"`. No `product-card-hover` class present in file |
| 9 | Results page product cards have spring hover lift and bolder typography | VERIFIED | `ResultsProductCard.tsx` lines 41–46: `motion.div` with `whileHover={{ y: -4, boxShadow: '...' }}` and spring. Line 85: `text-base font-bold mb-1 font-serif tracking-tight` |
| 10 | Results page source dots are larger (w-3 h-3) with ring emphasis | VERIFIED | `ResultsMainPanel.tsx` line 143: `w-3 h-3 rounded-full flex-shrink-0 ring-2 ring-offset-1`; `ResultsPage` line 136: `w-3 h-3 rounded-full flex-shrink-0` |
| 11 | No Framer Motion regressions during active streaming (no layout prop, no AnimatePresence on streaming path) | VERIFIED | Zero `layout` prop found in `ProductReview.tsx`, `InlineProductCard.tsx`, or `TopPickBlock.tsx`. No `AnimatePresence` added to streaming components. No `will-change-transform` static class introduced |

**Score: 11/11 truths verified**

---

## Required Artifacts

### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/tests/productReviewCard.test.tsx` | Wave 0 test scaffold for CARD-01/02 | VERIFIED | 164 lines, 9 tests covering spacing classes + merchant derivation |
| `frontend/tests/cardAnimations.test.tsx` | Wave 0 test scaffold for CARD-04 | VERIFIED | 156 lines, 6 tests covering spring config + layout guard + product-card-hover contract |
| `frontend/components/Message.tsx` | Upgraded prose modifier classes with V3 heading tokens and bold weights | VERIFIED | Contains `prose-h2:font-bold` (line 206) and all V3 token references `var(--heading-lg/md/sm)` |
| `frontend/components/InlineProductCard.tsx` | motion.div rows with spring whileHover and bold price | VERIFIED | `motion.div` at line 87, `whileHover` at line 88, `font-bold text-lg` price at line 129 |

### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/components/ProductReview.tsx` | Premium ProductReview with `deriveMerchant`, 3-offer cap, spring hover | VERIFIED | `deriveMerchant` function at line 18, `slice(0, 3)` at line 154, `cardVariants` + `whileHover="hover"` |
| `frontend/components/TopPickBlock.tsx` | Bold TopPickBlock with gradient CTA, 200x200 image, motion.div spring | VERIFIED | `motion.div` at line 63, `sm:w-[200px] sm:h-[200px]` at line 76, 3-stop gradient at line 136 |

### Plan 03 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/components/ResultsProductCard.tsx` | Bold v3.0 card with motion.div spring hover | VERIFIED | `motion.div` at line 41, spring config at line 46, `font-bold font-serif` heading at line 85 |
| `frontend/components/ResultsMainPanel.tsx` | Upgraded source dots w-3 h-3 with ring treatment | VERIFIED | `w-3 h-3 ring-2 ring-offset-1` at line 143, `font-semibold` site name at line 150 |
| `frontend/tests/resultsScreen.test.tsx` | Extended test assertions for RES-07/RES-08 | VERIFIED | Lines 495–539 contain 4 new assertions: dot size, font-semibold, no product-card-hover, font-bold heading |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `Message.tsx` | `globals.css` | CSS variable references in prose modifiers | WIRED | `var(--heading-lg)`, `var(--heading-md)`, `var(--heading-sm)` all defined in globals.css lines 80–82 (light) and 206–208 (dark) |
| `InlineProductCard.tsx` | framer-motion | `motion.div` import + `whileHover` prop | WIRED | `import { motion } from 'framer-motion'` at line 4; `whileHover` at line 88 |
| `ProductReview.tsx` | framer-motion | variants pattern with `whileHover="hover"` | WIRED | `import { motion }` at line 3; `whileHover="hover"` at line 109; cardVariants at lines 50–62 |
| `ProductReview.tsx` | URL constructor | `deriveMerchant` function parsing hostname | WIRED | `new URL(link.affiliate_link).hostname` at line 30; domainMap with 8 entries |
| `TopPickBlock.tsx` | framer-motion | `motion.div` + `topPickVariants` | WIRED | `import { motion }` at line 4; `motion.div` with `variants={topPickVariants}` at line 63 |
| `ResultsProductCard.tsx` | framer-motion | `motion.div` + `whileHover` prop | WIRED | `import { motion }` at line 4; `motion.div` + `whileHover` at lines 41–46 |
| `ResultsMainPanel.tsx` | globals.css | `SOURCE_COLORS` array + ring treatment | WIRED | `SOURCE_COLORS` at line 60; ring classes applied at line 143 with inline color vars |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CHT-01 | Plan 01 | AI response bubbles have updated typography (bolder headings, better spacing) | SATISFIED | `Message.tsx` prose-h1/h2/h3 with V3 tokens + `font-bold`/`font-semibold` + `prose-p:mb-3` |
| CHT-02 | Plan 01 | Inline product cards have subtle hover animations and bolder price display | SATISFIED | `InlineProductCard.tsx` motion.div rows with spring hover + `font-bold text-lg` price |
| CARD-01 | Plan 01 (scaffold), Plan 02 (impl) | ProductReview cards have premium spacing, stronger typography, entrance animations | SATISFIED | `ProductReview.tsx` has `rounded-xl p-3 sm:p-6 shadow-card` + `cardVariants` entrance |
| CARD-02 | Plan 01 (scaffold), Plan 02 (impl) | "Where to Buy" section uses clean 3-column layout with merchant labels derived from URL | SATISFIED | `deriveMerchant()` + `slice(0, 3)` + `grid-cols-1 md:grid-cols-3` layout |
| CARD-03 | Plan 02 | TopPickBlock has bolder visual treatment — stronger gradient CTA, larger product image | SATISFIED | 3-stop gradient with `--bold-blue` + `boxShadow`, `sm:w-[200px] sm:h-[200px]` |
| CARD-04 | Plans 01/02/03 | Card hover effects use spring animations via Framer Motion | SATISFIED | All four card types (InlineProductCard, ProductReview, TopPickBlock, ResultsProductCard) use `type: 'spring', stiffness: 400, damping: 28` |
| RES-07 | Plan 03 | Product grid cards match new bold visual language | SATISFIED | `ResultsProductCard.tsx` uses `--bold-amber/blue/green` badge tokens, `font-bold font-serif` heading, no CSS hover classes |
| RES-08 | Plan 03 | Sources section has stronger visual presence with bolder dot colors | SATISFIED | Source dots upgraded to `w-3 h-3` with `ring-2 ring-offset-1` in ResultsMainPanel; `w-3 h-3` in ResultsPage; `font-semibold` site names in both |

All 8 requirement IDs from PLAN frontmatter accounted for. No orphaned requirements detected.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `frontend/tests/resultsScreen.test.tsx` | 404–411 | Test expects "Buy on Amazon" but `ResultsProductCard` renders "Check Price" | Info | Pre-existing failure acknowledged in 21-03-SUMMARY.md; not introduced by Phase 21 |
| `frontend/tests/resultsScreen.test.tsx` | 424–431 | Test expects "#1" and "Top Pick" but component renders number-only circle + "TOP PICK" badge separately | Info | Pre-existing failure acknowledged in 21-03-SUMMARY.md; not introduced by Phase 21 |

No blocker anti-patterns found. Both noted items are pre-existing test mismatches that were present before Phase 21 execution, documented explicitly in the SUMMARY.

---

## Human Verification Required

### 1. Spring Animation Feel

**Test:** Open the chat page, send a product query, and hover over each InlineProductCard row, a ProductReview card, a TopPickBlock, and a ResultsProductCard.
**Expected:** Each card lifts with a visually snappy spring bounce (not a linear ease). The InlineProductCard rows shift slightly right (x: 2) with a surface color change. ProductReview and TopPickBlock lift 4px with a shadow bloom.
**Why human:** CSS spring physics cannot be asserted programmatically without a real browser animation runtime.

### 2. Streaming Regression Check

**Test:** Start a product search query and observe the chat response as it streams in. Hover over a ProductReview or TopPickBlock card while the response is still streaming.
**Expected:** No layout shift, no janky reflow, no dropped frames. The streaming text cursor remains smooth.
**Why human:** Framer Motion layout-prop regressions (prevented by guards in code) manifest only at runtime during active SSE streaming.

### 3. 3-Column Where-to-Buy Layout

**Test:** Open a ProductReview card that has 3+ affiliate links. View at desktop breakpoint (>= 768px).
**Expected:** Exactly 3 merchant offer tiles arranged in a clean 3-column grid. Each tile shows the cleaned merchant name (e.g., "Amazon", "Best Buy", "Walmart"), price, and an external link icon.
**Why human:** Responsive grid layout and merchant label rendering require visual confirmation.

### 4. TopPickBlock 200x200 Image on Desktop

**Test:** View a TopPickBlock on a desktop-width viewport.
**Expected:** The product image occupies a 200x200px square area on the left side of the card.
**Why human:** Responsive breakpoint behavior requires a real browser at the correct viewport width.

---

## Gaps Summary

None. All 11 observable truths verified. All 9 required artifacts exist, are substantive, and are correctly wired. All 8 requirement IDs from PLAN frontmatter are satisfied. The two known test failures in `resultsScreen.test.tsx` are pre-existing and explicitly acknowledged — they relate to CTA text ("Check Price" vs "Buy on Amazon") and badge formatting (#1/Top Pick vs 1/TOP PICK) that are presentation choices in the component, not regressions from Phase 21 work.

---

_Verified: 2026-04-01_
_Verifier: Claude (gsd-verifier)_
