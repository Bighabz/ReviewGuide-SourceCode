# Phase 21: Chat + Results Card Polish - Research

**Researched:** 2026-04-01
**Domain:** React component styling — Framer Motion spring animations, Tailwind prose typography, CSS variable-driven card redesign
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CHT-01 | AI response bubbles have updated typography (bolder headings, better spacing) | Tailwind `prose` modifier classes + V3 typography tokens already declared in globals.css |
| CHT-02 | Inline product cards have subtle hover animations and bolder price display | `motion.div` with `whileHover` spring transition on InlineProductCard; price font-bold upgrade |
| CARD-01 | ProductReview cards have premium spacing, stronger typography, and subtle entrance animations | ProductReview already uses `motion.div` entrance — augment spacing, typography scale |
| CARD-02 | "Where to Buy" section uses clean 3-column layout with merchant labels derived from URL | Already partially implemented; needs URL-to-merchant extraction to handle more domains + cap at 3 |
| CARD-03 | TopPickBlock has bolder visual treatment — stronger gradient CTA, larger product image | TopPickBlock CTA already has gradient; image area needs size increase; gradient needs bolder stop |
| CARD-04 | Card hover effects use spring animations via Framer Motion (stiffness: 400, damping: 28) | `framer-motion@12.26.2` available; `spring` transition type, `stiffness: 400, damping: 28` |
| RES-07 | Product grid cards match new bold v3.0 visual language | ResultsProductCard uses CSS-only hover today; needs Framer Motion + badge/type upgrades |
| RES-08 | Sources section has stronger visual presence with bolder dot colors | ResultsMainPanel SOURCE_COLORS hardcoded; dots are `w-2 h-2` — enlarge + use `--bold-*` tokens |
</phase_requirements>

---

## Summary

Phase 21 is a pure visual polish phase on six components that already exist and render correctly. No structural changes to the SSE pipeline (Message.tsx render functions, BlockRegistry.tsx) are permitted. Every component touched already imports from `framer-motion` or uses Tailwind classes — the work is upgrading those classes and adding `whileHover` spring transitions where missing.

The typography upgrade (CHT-01) is additive: the `prose` block inside Message.tsx needs stronger heading modifier classes (`prose-h2:text-xl prose-h2:font-bold`, etc.) layered on the existing Tailwind prose configuration. The V3 tokens (`--heading-md`, `--heading-sm`, `--heading-weight`) were declared in Phase 17 and are ready to be consumed.

The most technically nuanced requirement is CARD-04 (spring hover on Framer Motion): `whileHover` with `type: "spring", stiffness: 400, damping: 28` must be applied to `motion.div` wrappers. The critical constraint is that during active SSE streaming, Framer Motion animations running every render frame can cause layout thrash. The safe pattern is `will-change: transform` via Tailwind `will-change-transform`, and avoiding any `layout` prop on streaming card containers.

**Primary recommendation:** Upgrade existing components in place — no new dependencies needed. Add `whileHover` spring transitions to `motion.div` wrappers, upgrade `prose` modifier classes in Message.tsx, expand the merchant URL extractor in ProductReview, and scale up dots/image area in ResultsMainPanel and TopPickBlock.

---

## Standard Stack

### Core (already installed — no new installs needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| framer-motion | ^12.26.2 | Spring hover animations on card components | Already used by ProductReview, ProductCarousel, ReviewSources; consistent with rest of codebase |
| tailwindcss | ^3.3.6 | Utility classes for spacing, typography, color | Project-wide CSS framework |
| @tailwindcss/typography | ^0.5.19 | Prose modifier classes for AI response text | Already configured in tailwind.config.ts |
| clsx | ^2.1.1 | Conditional class composition | Available in project |
| tailwind-merge | ^3.4.0 | Class merge utility | Available in project |

### Not Needed for This Phase

| Considered | Decision | Reason |
|------------|----------|--------|
| class-variance-authority@0.7.1 | Skip for Phase 21 | STATE.md records the decision to add it, but it is NOT in package.json yet. Phase 21 scope does not require multi-mode variant API — defer CVA install to a phase that needs it. The planner should NOT add a CVA install task. |

**Installation:** None required. All dependencies are present.

---

## Architecture Patterns

### Recommended Approach: In-place class and prop upgrades

All six components are standalone leaf components. The correct strategy is surgical edits to each file — upgrade Tailwind classes and add/modify Framer Motion props. Do not restructure component trees or touch BlockRegistry.tsx.

### Pattern 1: Framer Motion spring hover on existing `motion.div`

**What:** Replace a CSS-only hover or a linear Framer Motion `whileHover` with a spring-physics transition.

**When to use:** Any card that needs the CARD-04 spring spec (`stiffness: 400, damping: 28`).

**Correct application:**
```typescript
// Source: framer-motion docs — spring transition
<motion.div
  whileHover={{ y: -4, boxShadow: '0 12px 32px rgba(28,25,23,0.10), 0 0 24px var(--primary-light)' }}
  transition={{ type: 'spring', stiffness: 400, damping: 28 }}
  className="will-change-transform ..."
>
```

**Important:** `will-change-transform` on the outer wrapper tells the browser to promote the layer before any hover starts, preventing composite layer recalculation mid-animation. This is the primary mechanism to keep fps above 55 during streaming.

**What NOT to do:**
- Do not add `layout` prop to any card inside MessageList — it triggers layout animations that recalculate on every SSE token.
- Do not wrap `InlineProductCard` items in `AnimatePresence` — they are not entering/exiting; they are static after render.

### Pattern 2: Stronger Tailwind prose typography for AI responses

**What:** The `prose` block in Message.tsx already has modifier classes. Add larger, bolder heading modifiers.

**Current state in Message.tsx (lines 202-210):**
```
prose prose-sm sm:prose-base max-w-none
prose-headings:font-serif prose-headings:tracking-tight prose-headings:text-[var(--text)]
prose-p:text-[var(--text)] prose-p:leading-relaxed prose-p:text-[15px]
prose-strong:text-[var(--text)] prose-strong:font-semibold
```

**Upgrade target:**
```
prose prose-sm sm:prose-base max-w-none
prose-headings:font-serif prose-headings:tracking-tight prose-headings:text-[var(--text)]
prose-h1:text-[var(--heading-lg)] prose-h1:font-bold prose-h1:leading-[1.15]
prose-h2:text-[var(--heading-md)] prose-h2:font-bold prose-h2:leading-[1.15]
prose-h3:text-[var(--heading-sm)] prose-h3:font-semibold prose-h3:leading-[1.2]
prose-p:text-[var(--text)] prose-p:leading-relaxed prose-p:text-[15px]
prose-p:mb-3
prose-strong:text-[var(--text)] prose-strong:font-semibold
prose-li:text-[var(--text)] prose-li:marker:text-[var(--text-muted)] prose-li:leading-relaxed
```

**Constraint:** Only the className string on the wrapping `<div>` changes. The `<ReactMarkdown>` tag and all surrounding logic are untouched. This is safe per the "never modify ui_blocks logic" rule.

### Pattern 3: URL-to-merchant extraction (CARD-02)

**What:** ProductReview already strips eBay affiliate suffixes. The function must be extended and capped to 3 offers.

**Current extractor in ProductReview.tsx:**
```typescript
const cleanMerchant = link.merchant
  .replace(/\s*\(.*?\)\s*/g, '')
  .replace(/^ebay.*/i, 'eBay')
  .trim() || 'Retailer'
```

**Needed upgrades:**
1. Add URL-based merchant fallback when `link.merchant` is empty/generic
2. Cap `affiliate_links` slice to 3 before rendering
3. Preserve existing grid logic (`grid-cols-1 md:grid-cols-3` is already correct for 3 items)

```typescript
function deriveMerchant(link: AffiliateLink): string {
  // 1. Try cleaning the merchant field
  const cleaned = link.merchant
    .replace(/\s*\(.*?\)\s*/g, '')
    .trim()
  if (cleaned && cleaned.toLowerCase() !== 'retailer') {
    if (/^ebay/i.test(cleaned)) return 'eBay'
    return cleaned
  }
  // 2. Fall back to URL parsing
  if (!link.affiliate_link) return 'Retailer'
  try {
    const host = new URL(link.affiliate_link).hostname.replace(/^www\./, '')
    const domainMap: Record<string, string> = {
      'amazon.com': 'Amazon', 'amzn.to': 'Amazon',
      'ebay.com': 'eBay',
      'walmart.com': 'Walmart',
      'bestbuy.com': 'Best Buy',
      'target.com': 'Target',
      'newegg.com': 'Newegg',
      'bhphotovideo.com': 'B&H Photo',
      'costco.com': 'Costco',
    }
    for (const [domain, label] of Object.entries(domainMap)) {
      if (host.includes(domain)) return label
    }
    // Capitalize first segment: "b-and-h.com" → "B-And-H"
    return host.split('.')[0].replace(/(^|\-)(\w)/g, (_, sep, c) => (sep ? ' ' : '') + c.toUpperCase()).trim()
  } catch {
    return 'Retailer'
  }
}
```

### Pattern 4: TopPickBlock gradient CTA upgrade (CARD-03)

**Current CTA:**
```typescript
style={{ background: 'linear-gradient(135deg, var(--primary), var(--accent))' }}
```

**Bold upgrade:**
```typescript
style={{
  background: 'linear-gradient(135deg, var(--bold-blue) 0%, var(--primary) 40%, var(--accent) 100%)',
  boxShadow: '0 4px 14px rgba(27, 77, 255, 0.35)',
}}
```

**Image area upgrade:** Current image container is `w-full sm:w-[160px] h-[120px] sm:h-[160px]`. Upgrade to `w-full sm:w-[200px] h-[140px] sm:h-[200px]` to match "larger product image" success criterion.

### Pattern 5: Results page source dots upgrade (RES-08)

**Current:** `w-2 h-2 rounded-full` dots with hardcoded `SOURCE_COLORS` hex array.

**Bold upgrade:** `w-3 h-3 rounded-full ring-2 ring-offset-1` with the same colors (or map to `--bold-*` tokens). The `ring` adds visual weight without changing semantic color.

### Anti-Patterns to Avoid

- **Adding `layout` prop to streaming card containers:** Causes every SSE token to trigger a layout animation pass. Never use `layout` on any component that re-renders during streaming.
- **Wrapping `InlineProductCard` in `motion.div` at the list level:** The hover must be on each individual row, not the outer container.
- **Using CSS-only `product-card-hover` class AND Framer Motion `whileHover` simultaneously on the same element:** They fight. Choose one. For CARD-04 compliance, use only Framer Motion's `whileHover` and remove the CSS transition from the element's className.
- **Touching `<ReactMarkdown>` props or any `renderXxx` function inside Message.tsx:** Protected per project rules.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Spring hover animation | Custom CSS keyframes or requestAnimationFrame | `framer-motion` `whileHover` with `type: "spring"` | Hardware-accelerated, cancels correctly on mouse-leave, already in bundle |
| Merchant name from URL | Custom regex | The `URL` constructor + a domain map (Pattern 3 above) | `new URL()` handles edge cases (port, path prefix, query); regex misses them |
| Utility class merging | String concatenation | `clsx` + `tailwind-merge` | Already in package.json; avoids conflicting Tailwind utility collisions |
| Prose typography override | New CSS file | Tailwind `prose-h2:text-xl` modifier syntax | Stays in the component class string, no cascade conflicts |

---

## Common Pitfalls

### Pitfall 1: Framer Motion `layout` prop causes streaming frame drops

**What goes wrong:** Adding `layout` to a `motion.div` inside `MessageList` causes Framer Motion to perform a full layout measurement on every re-render — which happens on every SSE token (potentially 20-50 times per second).

**Why it happens:** Developers add `layout` to get smooth card-insert animations. But during streaming, cards are not being inserted — text content is updating — so `layout` runs pointlessly.

**How to avoid:** Never use `layout` on any element that is a descendant of the SSE streaming container. Spring `whileHover` is safe because it only runs on user interaction.

**Warning signs:** Chrome DevTools Performance panel shows "Layout" tasks running in tight sequence during streaming.

---

### Pitfall 2: `product-card-hover` CSS class conflicts with Framer Motion `whileHover`

**What goes wrong:** `product-card-hover` applies `transition: transform 250ms ...` via CSS. When Framer Motion also applies a `transform` via `whileHover`, the CSS transition fights Framer Motion's spring, producing a jittery non-spring motion.

**Why it happens:** Both systems write to the same CSS `transform` property.

**How to avoid:** When upgrading a component to CARD-04 spring spec, remove `product-card-hover` from className and let Framer Motion own the transform entirely. The shadow/border-color parts of the hover can remain as CSS transitions (they do not conflict with transform).

**Current affected components:** TopPickBlock already has `product-card-hover` in its className. ResultsProductCard uses CSS-only hover (`hover:-translate-y-0.5`). Both must be audited.

---

### Pitfall 3: Framer Motion `whileHover` on a non-`motion.*` element

**What goes wrong:** Developer adds `whileHover` prop to a plain `<div>`. React renders it as an unknown attribute warning; no animation occurs.

**How to avoid:** `InlineProductCard` currently uses plain `<div>` for each product row. Each row must be converted to `<motion.div>` before `whileHover` is added. Only the individual row needs conversion — the outer container stays as `<div>`.

---

### Pitfall 4: `will-change: transform` left on permanently

**What goes wrong:** `will-change-transform` promotes every card to its own GPU layer on page load, increasing VRAM usage and causing paint overhead on low-end devices.

**How to avoid:** Use `hover:will-change-transform` (Tailwind responsive prefix) so the hint is only applied after the first hover, or use Framer Motion's built-in `willChange` on `whileHover` (Framer sets this automatically). Do not add `will-change-transform` as a static class.

---

### Pitfall 5: `prose` modifier class specificity overridden by existing styles

**What goes wrong:** New `prose-h2:font-bold` class added, but existing inline `style` attribute or a more specific selector wins.

**Why it happens:** The `prose-*` modifiers work via the `[data-attribute]` descendant selector generated by `@tailwindcss/typography`. Inline `style` attributes always win.

**How to avoid:** The prose block in Message.tsx uses only className modifiers, no inline styles on headings. The upgrade is safe. Verify by checking that `<ReactMarkdown>` does not pass components with inline styles.

---

## Code Examples

Verified patterns from direct codebase inspection:

### Framer Motion spring hover — correct form for this project

```typescript
// For ProductReview.tsx — augment existing whileHover
<motion.div
  initial={{ opacity: 0, y: 12 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3, ease: 'easeOut' }}
  whileHover={{
    y: -4,
    boxShadow: '0 12px 32px rgba(28,25,23,0.10), 0 0 24px var(--primary-light)',
    borderColor: 'color-mix(in srgb, var(--primary) 30%, transparent)',
  }}
  // Note: separate transition for whileHover to use spring
  // framer-motion v12 supports per-state transition overrides via variants
  className="border border-[var(--border)] rounded-xl p-3 sm:p-6 bg-[var(--surface-elevated)] shadow-card will-change-auto"
>
```

**Framer Motion v12 per-hover transition override:**
```typescript
// framer-motion v12 supports variants for per-state transition
const cardVariants = {
  rest: { y: 0 },
  hover: {
    y: -4,
    transition: { type: 'spring', stiffness: 400, damping: 28 },
  },
}
<motion.div initial="rest" whileHover="hover" variants={cardVariants} ...>
```

OR using the `transition` override directly on whileHover (simpler, framer-motion v12 supports this):
```typescript
<motion.div
  whileHover={{ y: -4 }}
  transition={{ type: 'spring', stiffness: 400, damping: 28 }}
>
```

**Note:** The `transition` prop on a `motion.div` applies to ALL animation states including `whileHover` when no per-state transition is specified. If the component also has `initial`/`animate`, use variants to avoid the entrance animation also becoming a spring.

### Safe pattern: separate entrance from hover transition

```typescript
// Entrance: ease-out (fast, non-bouncy)
// Hover: spring physics (stiffness: 400, damping: 28)
const variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: 'easeOut' },
  },
  hover: {
    y: -4,
    boxShadow: '0 12px 32px rgba(28,25,23,0.10)',
    transition: { type: 'spring', stiffness: 400, damping: 28 },
  },
}

<motion.div
  variants={variants}
  initial="hidden"
  animate="visible"
  whileHover="hover"
  className="border border-[var(--border)] rounded-xl ..."
>
```

### InlineProductCard row — upgrade to motion.div

```typescript
// Before: plain <div> row
<div key={index} className="h-16 flex flex-row items-center gap-3 px-1 overflow-hidden border-b ...">

// After: motion.div with spring hover on individual row
<motion.div
  key={index}
  whileHover={{ backgroundColor: 'var(--surface-hover)', x: 2 }}
  transition={{ type: 'spring', stiffness: 400, damping: 28 }}
  className="h-16 flex flex-row items-center gap-3 px-1 overflow-hidden border-b ..."
>
```

### Price bold upgrade in InlineProductCard

```typescript
// Before
<span className="font-semibold text-base" style={{ color: 'var(--text-primary)' }}>

// After — larger, bolder, uses semantic token
<span className="font-bold text-lg" style={{ color: 'var(--text)' }}>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CSS transition for card hover | Framer Motion `whileHover` spring | CARD-04 target | Smooth spring deceleration instead of linear ease |
| `prose-sm` only | `prose-sm sm:prose-base` + explicit heading modifiers | Phase 21 | Visually larger headings in chat at sm+ breakpoints |
| `product-card-hover` CSS class | Framer Motion `whileHover` owns transform | Phase 21 | No more CSS/Framer transform conflict |

**Deprecated/outdated:**
- `product-card-hover` CSS class: Still present in globals.css and used by TopPickBlock. For components upgraded to CARD-04, remove this class from their className. The class itself stays in globals.css for backward compatibility with non-upgraded components.

---

## Open Questions

1. **Framer Motion v12 `transition` prop scoping**
   - What we know: In framer-motion v11+, the `transition` prop on a `motion.div` applies to all animated properties unless per-property overrides are specified.
   - What's unclear: Whether a top-level `transition` prop conflicts with `whileHover`'s implicit transition in framer-motion v12.26.x specifically.
   - Recommendation: Use the variants pattern (Pattern 3 in Code Examples above) which explicitly scopes transitions per state. This is safe across all v12 versions.

2. **`ResultsProductCard` Framer Motion conversion**
   - What we know: It is currently a plain `<div>` with CSS `hover:-translate-y-0.5` and `product-card-hover` class.
   - What's unclear: Whether RES-07 requires a full `motion.div` conversion or if a CSS-only bold typography upgrade is sufficient.
   - Recommendation: The success criterion says "match bold v3.0 visual language" — typography, badge colors, and border treatment. Spring hover (CARD-04) is specified for "card hover effects" broadly. Convert to `motion.div` for consistency with ProductReview. This is a leaf component with no streaming dependency.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 4.0.17 + @testing-library/react 14.1.2 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test -- --run tests/topPickBlock.test.tsx tests/inlineProductCard.test.tsx tests/sourceCitations.test.tsx` |
| Full suite command | `cd frontend && npm run test -- --run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CHT-01 | AI response prose headings use bolder sizing | unit | `npm run test -- --run tests/designTokens.test.ts` | Yes (designTokens.test.ts — needs new assertions) |
| CHT-02 | InlineProductCard has hover motion + bold price | unit | `npm run test -- --run tests/inlineProductCard.test.tsx` | Yes (existing; needs hover/price assertions) |
| CARD-01 | ProductReview entrance animation + premium spacing | unit | `npm run test -- --run tests/blockRegistryTopPick.test.tsx` | Yes (partial — no spacing assertions yet) |
| CARD-02 | "Where to Buy" capped at 3, merchant from URL | unit | Wave 0 gap — new test file needed | No |
| CARD-03 | TopPickBlock larger image + bolder CTA | unit | `npm run test -- --run tests/topPickBlock.test.tsx` | Yes (existing; needs image size + CTA assertions) |
| CARD-04 | spring transition stiffness=400, damping=28 | unit | Wave 0 gap — new test file needed | No |
| RES-07 | ResultsProductCard bold visual language | unit | `npm run test -- --run tests/resultsScreen.test.tsx` | Yes (existing; badge color assertions needed) |
| RES-08 | Sources dots larger/bolder colored | unit | `npm run test -- --run tests/resultsScreen.test.tsx` | Yes (existing; dot size assertions needed) |

### Sampling Rate

- **Per task commit:** `cd frontend && npm run test -- --run tests/inlineProductCard.test.tsx tests/topPickBlock.test.tsx tests/sourceCitations.test.tsx`
- **Per wave merge:** `cd frontend && npm run test -- --run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/tests/productReviewCard.test.tsx` — covers CARD-01, CARD-02 (merchant extraction, 3-offer cap, spring animation class presence)
- [ ] `frontend/tests/cardAnimations.test.tsx` — covers CARD-04 (verifies `whileHover` prop presence on `motion.div` and no `layout` prop on streaming containers)

*(Existing tests for inlineProductCard, topPickBlock, sourceCitations, resultsScreen need additive assertions for new visual properties but do not need to be created from scratch.)*

---

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection — `frontend/components/ProductReview.tsx`, `InlineProductCard.tsx`, `TopPickBlock.tsx`, `ResultsProductCard.tsx`, `ResultsMainPanel.tsx`, `SourceCitations.tsx`, `Message.tsx` (lines 200-216)
- `frontend/app/globals.css` — V3 token declarations (`--heading-*`, `--bold-*`, `.product-card-hover`)
- `frontend/tailwind.config.ts` — `shadow-card`, `shadow-card-hover`, `font-serif` mapping
- `frontend/package.json` — framer-motion@^12.26.2, @tailwindcss/typography@^0.5.19 confirmed present
- `.planning/REQUIREMENTS.md` — Phase 21 requirement definitions (CHT-01, CHT-02, CARD-01..04, RES-07, RES-08)
- `.planning/ROADMAP.md` — Phase 21 success criteria (7 criteria, including fps floor of 55)
- `.planning/STATE.md` — Accumulated decisions (CVA deferred, protected components list)

### Secondary (MEDIUM confidence)

- Framer Motion spring transition API inferred from existing usage in `ProductCarousel.tsx` (uses `motion` from framer-motion), `ProductReview.tsx` (uses `whileHover`), `ReviewSources.tsx` (uses `motion.div` with `transition`)
- `@tailwindcss/typography` prose modifier class syntax inferred from existing usage in Message.tsx and Tailwind Typography v0.5 API (stable since 2022)

### Tertiary (LOW confidence — needs validation)

- Framer Motion v12 `transition` prop scoping for `whileHover` — behavior inferred from v11 docs and project usage; framer-motion v12 changelog not inspected directly

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all dependencies confirmed in package.json
- Architecture: HIGH — all components read directly; current implementation state known precisely
- Pitfalls: HIGH — identified from direct code inspection (CSS/FM conflict, `layout` prop risk, `will-change` overuse)
- Framer Motion v12 per-state transition scoping: MEDIUM — inferred from v11/v12 API patterns; use variants to be safe

**Research date:** 2026-04-01
**Valid until:** 2026-05-01 (stable stack; framer-motion v12 API unlikely to change in 30 days)
