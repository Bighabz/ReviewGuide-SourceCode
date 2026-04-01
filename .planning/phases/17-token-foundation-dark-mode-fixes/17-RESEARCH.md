# Phase 17: Token Foundation + Dark Mode Fixes — Research

**Researched:** 2026-03-31
**Domain:** CSS custom property design token system, Tailwind CSS 3, dark mode via data-theme attribute
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TOK-01 | Bold accent color palette added to CSS variables (vibrant blues, terracotta, energetic greens) with light mode values | New tokens added to `:root` in globals.css following established pattern; token naming convention documented below |
| TOK-02 | Typography scale upgraded — larger/bolder headings, tighter line heights, stronger visual hierarchy | Current heading sizes pinpointed (h1: 2.5rem, h2: 1.875rem, h3: 1.375rem); upgrade path to clamp() tokens documented |
| TOK-03 | All new tokens have matching `[data-theme="dark"]` counterparts (no dark mode regressions) | Dark mode block structure fully audited; missing token gaps (--error, --warning, --info, --shadow-xl) identified; correct dark values specified |

</phase_requirements>

---

## Summary

Phase 17 is a pure CSS token surgery on two files: `frontend/app/globals.css` and three leaf components (`ProductReview.tsx`, `TopPickBlock.tsx`, `ProductCards.tsx`). No new libraries, no new components, no backend changes.

The existing token system is well-structured with a `[data-theme="dark"]` attribute strategy (not Tailwind `dark:` class). The dark mode block is mostly complete but has four known gaps: `--error`, `--warning`, `--info`, and `--shadow-xl` are defined in `:root` but have no counterpart in `[data-theme="dark"]`. This phase adds those missing counterparts and adds new bold editorial tokens (all with dark mode pairs), then converts nine hardcoded Tailwind palette classes across the three leaf components to `var()` references.

The `designTokens.test.ts` contract is the critical guard rail. All 13 existing tests pass on the current codebase. The test file checks for presence of specific CSS variable names and utility class names by string search — it never validates values, only presence. This means the approach is safe: add new tokens, never rename existing ones. The test must be extended in Phase 22 (QA gate) to cover the new tokens added here.

The baseline test suite has 21 failing tests across 7 files (pre-existing failures unrelated to tokens: mobileTabBar, discoverScreen, chatScreen, resultsScreen, editorsPicks, inlineProductCard, topPickBlock). The `designTokens.test.ts` suite passes 100% (13/13). Phase 17 must not break the 13 passing design token tests and should not introduce new test failures.

**Primary recommendation:** Add all new tokens to `:root` and `[data-theme="dark"]` in a single atomic commit, verify with `npm run test:run` before touching any component, then convert hardcoded classes in one component at a time.

---

## Standard Stack

### Core
| File | Role | Constraint |
|------|------|-----------|
| `frontend/app/globals.css` | Single source of truth for all CSS custom properties | Only ADD tokens; never rename existing `--gpt-*` vars or `--stream-*` vars |
| `frontend/tailwind.config.ts` | Maps CSS variables to Tailwind utility classes | No changes required for this phase (token additions don't need Tailwind aliases) |
| `frontend/tests/designTokens.test.ts` | Contract guard — verifies token and utility class presence | Must stay 100% green after every globals.css edit |

### Supporting
| Tool | Version | Purpose |
|------|---------|---------|
| Vitest | ^4.0.17 | Test runner; `npm run test:run` for one-shot verification |
| `@testing-library/react` | ^14 | Component rendering used in existing tests — no new test dependencies needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CSS custom properties in globals.css | Tailwind CSS variables plugin | Tailwind plugin generates build-time classes; CSS vars are runtime-switchable — the `data-theme` dark mode strategy requires runtime-switchable values |
| `var(--success)` for pros color | `text-emerald-500` Tailwind class | Tailwind palette classes ignore `data-theme` entirely; `var()` respects the dark mode override |

**Installation:** No new packages required for this phase.

---

## Architecture Patterns

### Recommended Project Structure

No new files created. Edits are in-place to:

```
frontend/
├── app/
│   └── globals.css          # Add tokens to :root AND [data-theme="dark"]
└── components/
    ├── ProductReview.tsx     # Convert 4 hardcoded color classes
    ├── TopPickBlock.tsx      # Convert 4 hardcoded color classes + 1 dark: utility
    └── ProductCards.tsx      # Convert 2 hardcoded color classes
```

### Pattern 1: Token Pair Addition (root + dark mode together)

**What:** Every new CSS variable is added to both `:root` and `[data-theme="dark"]` in the same file edit.
**When to use:** Always — no exceptions. An `:root`-only token is a silent dark mode regression.
**Example:**
```css
/* In :root */
--heading-xl: clamp(2.5rem, 5vw, 4.5rem);
--bold-blue: #1B4DFF;
--bold-green: #16A34A;
--bold-red: #DC2626;

/* In [data-theme="dark"] — same commit */
--heading-xl: clamp(2.5rem, 5vw, 4.5rem);   /* typography is theme-neutral */
--bold-blue: #60A5FA;
--bold-green: #4ADE80;
--bold-red: #F87171;
```

### Pattern 2: Hardcoded Class Conversion

**What:** Replace Tailwind static color classes with `var()` inline style references or Tailwind aliases that resolve to CSS variables.
**When to use:** For the four confirmed regressions in the three leaf components.

The safest conversion for className-based usage is the `style` prop approach for one-off inline uses, but `var()` in className string works with Tailwind's arbitrary value syntax:

```tsx
// Before (broken in dark mode):
<span className="font-semibold text-green-700">Pros</span>
<span className="font-semibold text-red-700">Cons</span>

// After (respects [data-theme="dark"]):
<span className="font-semibold" style={{ color: 'var(--success)' }}>Pros</span>
<span className="font-semibold" style={{ color: 'var(--error)' }}>Cons</span>

// OR with Tailwind arbitrary value (also valid — JIT generates the class):
<span className="font-semibold text-[var(--success)]">Pros</span>
<span className="font-semibold text-[var(--error)]">Cons</span>
```

Both approaches work. The `text-[var(--token)]` arbitrary value syntax is preferred for consistency with other components in this codebase (already used throughout: `text-[var(--text)]`, `text-[var(--primary)]`).

### Pattern 3: Typography Scale Tokens

**What:** Named heading tokens decouple font sizes from inline magic numbers.
**When to use:** For the bold heading scale required by TOK-02.

```css
/* :root — light and dark share the same clamp values (no luminance change needed) */
--heading-hero: clamp(2.5rem, 5vw, 4.5rem);   /* category hero h1 */
--heading-xl:   clamp(1.875rem, 3vw, 2.5rem);  /* page-level h1 */
--heading-lg:   1.875rem;                       /* section h2 */
--heading-md:   1.375rem;                       /* card h3 */
--heading-sm:   1.125rem;                       /* sub-section h4 */
--heading-weight: 700;
--heading-line-height: 1.15;
```

### Anti-Patterns to Avoid

- **Renaming `--gpt-*` variables:** `designTokens.test.ts` asserts their presence; removing breaks CI and live streaming UI.
- **Adding `:root` token without `[data-theme="dark"]` counterpart:** The `dark:` Tailwind utility prefix does nothing in this project (attribute-based strategy, not class-based). New tokens without dark values appear as light-mode values on dark backgrounds.
- **Using `dark:text-*` Tailwind utilities on new classes:** The project uses `data-theme="dark"` on `<html>`, not the `dark` CSS class. Tailwind's `.dark` selector never matches. These are silently inert.
- **Touching `Message.tsx` or `BlockRegistry.tsx`:** Protected per CLAUDE.md and MEMORY.md — streaming pipeline must not be modified.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dark mode value switching | Runtime JS that reads/writes color values | CSS custom properties with `[data-theme="dark"]` | Already the project's established strategy; zero JS overhead |
| Token presence verification | Manual checklist | `designTokens.test.ts` via `npm run test:run` | Already built; extend it rather than a separate process |
| Responsive font sizes | Media query font-size overrides | `clamp()` in CSS variable value | Single declaration handles all viewport widths |

---

## Common Pitfalls

### Pitfall 1: Adding Tokens to `:root` Only

**What goes wrong:** New token `--bold-green: #16A34A` appears correct in light mode. In dark mode, no override exists, so the light-mode value (#16A34A, a dark saturated green) renders on a near-black background — visually broken and low contrast.
**Why it happens:** The dark mode block (`[data-theme="dark"]`) is not automatically kept in sync; it requires a deliberate parallel edit.
**How to avoid:** Edit `:root` and `[data-theme="dark"]` in the same save operation. Use the pre-submission check: after any globals.css edit, `git diff frontend/app/globals.css` and confirm every new `--var-name` in `:root` has a counterpart in the dark block.
**Warning signs:** Running the app with dark mode active and seeing oversaturated or illegible colors on newly styled elements.

### Pitfall 2: Breaking the `designTokens.test.ts` Contract

**What goes wrong:** A "cleanup" renames `--stream-status-size` to `--status-size`; the test `expect(globals).toContain('--stream-status-size')` fails; CI goes red; the live streaming UI font size reference breaks.
**Why it happens:** The token names are baked into both the test and the production utility classes (`.stream-status-text` uses `var(--stream-status-size)`). Renaming one without the other silently breaks functionality.
**How to avoid:** Only ADD new tokens. Never rename existing ones. Run `npm run test:run` after every globals.css edit. The test suite takes under 6 seconds to complete.
**Warning signs:** A test failure in `designTokens.test.ts` after a globals.css edit.

### Pitfall 3: Using `dark:` Tailwind Utilities on New Code

**What goes wrong:** A developer writes `className="text-green-700 dark:text-green-400"` — this looks correct but `.dark` never matches because the project sets `data-theme="dark"` on `<html>`, not the `dark` class. The dark override is silently ignored.
**Why it happens:** Tailwind's dark mode strategy defaults to `class`-based; this project uses `attribute`-based (`data-theme`). The tailwind.config.ts does not configure `darkMode: ['attribute', '[data-theme="dark"]']`, so `dark:` utilities use the class selector.
**How to avoid:** Use `[data-theme="dark"] .my-class` in CSS or `var(--token)` in className. Never use `dark:` utilities.
**Warning signs:** The component looks correct in DevTools "Force dark colors" but wrong when using the actual app dark mode toggle.

### Pitfall 4: Converting Wrong Components (Protected Files)

**What goes wrong:** A developer edits `Message.tsx` to convert hardcoded colors, accidentally modifies the ui_blocks dispatch logic, and breaks the SSE streaming pipeline.
**Why it happens:** `Message.tsx` and `BlockRegistry.tsx` are large files with protected render logic; visual edits creep into structural areas.
**How to avoid:** Phase 17 ONLY touches `ProductReview.tsx`, `TopPickBlock.tsx`, and `ProductCards.tsx`. These are confirmed leaf components with no streaming logic. Do not open `Message.tsx` during this phase.
**Warning signs:** Any change to a switch/case block or object spread in a chat component.

### Pitfall 5: TopPickBlock `dark:` Utility Already Present

**What goes wrong:** TopPickBlock line 135 already has `dark:text-emerald-400` — a developer might think this means dark mode is working and leave it in place.
**Why it happens:** The `dark:` utility was written with good intent but is silently inert with this project's `data-theme` dark mode strategy. The `dark:text-emerald-400` class never activates.
**How to avoid:** Remove the `dark:` utility and replace the entire `text-emerald-600 dark:text-emerald-400` with `text-[var(--success)]`. The `--success` token is already overridden correctly in `[data-theme="dark"]` to `#22C55E`.
**Warning signs:** Seeing `dark:` in any className string in the three target components after this phase.

---

## Code Examples

Verified patterns from codebase inspection:

### Current Hardcoded Color Inventory (Complete)

```
ProductReview.tsx:108  — text-green-700    (Pros heading)
ProductReview.tsx:115  — text-green-600    (Pros checkmark icons)
ProductReview.tsx:126  — text-red-700      (Cons heading)
ProductReview.tsx:133  — text-red-600      (Cons X icons)

TopPickBlock.tsx:135   — text-emerald-600 dark:text-emerald-400  (Best for label)
TopPickBlock.tsx:160   — text-green-600    (Pros label)
TopPickBlock.tsx:166   — text-red-500      (Cons label)

ProductCards.tsx:125   — text-green-600    (What we like label)
ProductCards.tsx:131   — text-red-500      (Watch out for label)
```

Total: 9 instances across 3 files. All are label/icon colors for pros/cons sentiment.

### Correct Conversion Pattern

```tsx
// Source: codebase convention — same pattern used in these files already
// e.g. ProductCards.tsx line 93: text-[var(--accent)]
// e.g. ProductReview.tsx line 76: text-[var(--text)]

// Pros (green → success token)
// Before:
<h4 className="text-sm font-semibold font-serif text-green-700 mb-2 flex items-center gap-1">
<span className="text-green-600 mt-0.5">&#10003;</span>

// After:
<h4 className="text-sm font-semibold font-serif text-[var(--success)] mb-2 flex items-center gap-1">
<span className="text-[var(--success)] mt-0.5">&#10003;</span>

// Cons (red → error token)
// Before:
<h4 className="text-sm font-semibold font-serif text-red-700 mb-2 flex items-center gap-1">
<span className="text-red-600 mt-0.5">&#10007;</span>

// After:
<h4 className="text-sm font-semibold font-serif text-[var(--error)] mb-2 flex items-center gap-1">
<span className="text-[var(--error)] mt-0.5">&#10007;</span>
```

### New Token Block Structure in globals.css

```css
/* ═══════════════════════════════════════════
   V3 BOLD EDITORIAL ACCENTS
   Vibrant, energetic — for product card labels, badges, CTAs
   ═══════════════════════════════════════════ */

/* In :root — light mode values */
--bold-blue: #1B4DFF;           /* same as --primary, explicit alias for v3 components */
--bold-green: #16A34A;          /* energetic green — deal badges, positive signals */
--bold-red: #DC2626;            /* strong red — warning, negative signals */
--bold-amber: #D97706;          /* warm amber — rating stars, caution */

/* Typography Scale (shared — no luminance dependence) */
--heading-hero: clamp(2.5rem, 5vw, 4.5rem);
--heading-xl: clamp(1.875rem, 3vw, 2.5rem);
--heading-lg: 1.875rem;
--heading-md: 1.375rem;
--heading-sm: 1.125rem;
--heading-weight: 700;
--heading-line-height: 1.15;

/* Also add missing dark-mode overrides for existing tokens: */
/* In [data-theme="dark"] */
--error: #F87171;          /* bright red — readable on dark background */
--warning: #FCD34D;        /* bright amber */
--info: #60A5FA;           /* electric blue */
--shadow-xl: 0 20px 48px rgba(0, 0, 0, 0.7), 0 8px 16px rgba(0, 0, 0, 0.4);
--bold-blue: #60A5FA;
--bold-green: #4ADE80;
--bold-red: #F87171;
--bold-amber: #FCD34D;
```

### Existing Token Usage Reference (already correct)

```tsx
// These patterns already work in the codebase — new code follows the same style:
className="text-[var(--text)]"
className="text-[var(--primary)]"
className="text-[var(--accent)]"
className="text-[var(--text-muted)]"
className="border-[var(--border)]"
className="bg-[var(--surface-elevated)]"
```

---

## State of the Art

| Old Approach | Current Approach | Impact for Phase 17 |
|--------------|------------------|---------------------|
| `text-green-700` Tailwind palette | `text-[var(--success)]` CSS variable | Converts in this phase |
| `dark:text-*` Tailwind utilities | `[data-theme="dark"]` CSS block | `dark:` utilities are silently inert — remove them |
| Hardcoded h1: 2.5rem | `var(--heading-hero)` with clamp | Upgrade in this phase |
| No bold accent palette | `--bold-green`, `--bold-red`, `--bold-amber` tokens | Add in this phase |

**Missing dark mode tokens to fix (pre-existing gaps in globals.css):**

- `--error`: defined in `:root` as `#D93025`, NOT in `[data-theme="dark"]` — add `#F87171`
- `--warning`: defined in `:root` as `#E5A100`, NOT in dark mode — add `#FCD34D`
- `--info`: defined in `:root` as `#1A73E8`, NOT in dark mode — add `#60A5FA`
- `--shadow-xl`: defined in `:root`, NOT in dark mode — add appropriate dark shadow

---

## Open Questions

1. **Should `--success` be the token for pros labels?**
   - What we know: `--success` is `#1A8754` in light (dark forest green) and `#22C55E` in dark (bright green). Pros labels are currently `text-green-700` (#15803D) / `text-green-600` (#16A34A).
   - What's unclear: Whether the lighter dark value (`#22C55E`) is visually appropriate for prose-level label text, or whether it should be more muted.
   - Recommendation: Use `var(--success)` — it already has dark mode counterpart and the values are close enough to the current hardcoded greens. If the success color needs fine-tuning later, that is a single token edit.

2. **Should new bold accent tokens alias existing tokens or be independent?**
   - What we know: `--bold-blue` would be the same value as `--primary` in both modes.
   - What's unclear: Whether duplicate aliases create confusion or helpful explicitness.
   - Recommendation: Make them independent with their own names to support future divergence. The SUMMARY.md research confirms Phase 20 uses per-category accent injection — having named bold tokens gives that phase a cleaner API.

3. **Typography token scope for TOK-02**
   - What we know: Phase 20's category hero h1 needs `clamp(2.5rem, 5vw, 4.5rem)`. The current `h1 { font-size: 2.5rem; }` in globals.css is a global override.
   - What's unclear: Whether the token should replace the global `h1` rule or be a named utility token that Phase 20 applies explicitly.
   - Recommendation: Add the `--heading-*` tokens without modifying the global `h1` rule. Phase 20 applies `text-[var(--heading-hero)]` explicitly to the CategoryHero component. This avoids unintended visual changes to chat h1 elements.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest ^4.0.17 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test:run -- --reporter=dot tests/designTokens.test.ts` |
| Full suite command | `cd frontend && npm run test:run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TOK-01 | Bold accent tokens visible in globals.css | unit (string search) | `npm run test:run -- tests/designTokens.test.ts` | ✅ (extend existing file) |
| TOK-02 | Typography scale tokens present in globals.css | unit (string search) | `npm run test:run -- tests/designTokens.test.ts` | ✅ (extend existing file) |
| TOK-03 | New tokens have `[data-theme="dark"]` counterparts | unit (string search) | `npm run test:run -- tests/designTokens.test.ts` | ✅ (extend existing file) |

All three requirements map to extending `designTokens.test.ts`. The test pattern (string-search on the CSS file) is already established. New assertions follow the same pattern:

```ts
// Extension additions to designTokens.test.ts for Phase 17
it('defines --bold-green bold editorial token', () => {
  expect(globals).toContain('--bold-green')
})
it('defines --heading-hero typography token', () => {
  expect(globals).toContain('--heading-hero')
})
it('defines --error in dark mode block', () => {
  const darkIdx = globals.indexOf('[data-theme="dark"]')
  const darkBlock = globals.slice(darkIdx, darkIdx + 2000)
  expect(darkBlock).toContain('--error')
})
```

Note: These new test assertions belong to Phase 22 (QA-02 requirement) per the REQUIREMENTS.md traceability table, NOT Phase 17. Phase 17 only adds the tokens and converts components. The test additions are a Phase 22 deliverable. **Phase 17 must not break the 13 existing design token tests.**

### Sampling Rate

- **Per task commit:** `cd frontend && npm run test:run -- tests/designTokens.test.ts` (< 2s, checks the contract)
- **Per wave merge:** `cd frontend && npm run test:run` (< 6s full suite)
- **Phase gate:** Full suite must not introduce new failures (21 pre-existing failures are the baseline; do not increase this count)

### Wave 0 Gaps

None — existing test infrastructure covers all phase requirements. No new test files required for Phase 17 itself. The test extension deliverable is Phase 22.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `frontend/app/globals.css` — all 508 lines read and audited
- Direct codebase inspection: `frontend/tailwind.config.ts` — complete file read
- Direct codebase inspection: `frontend/tests/designTokens.test.ts` — all 13 tests read
- Direct codebase inspection: `frontend/components/ProductReview.tsx` — all 9 hardcoded color occurrences identified at exact line numbers
- Direct codebase inspection: `frontend/components/TopPickBlock.tsx` — all 9 hardcoded color occurrences identified
- Direct codebase inspection: `frontend/components/ProductCards.tsx` — all occurrences identified
- Live test run confirming `designTokens.test.ts` passes 13/13 and total suite state is 252 passing / 21 failing (pre-existing)
- `.planning/research/SUMMARY.md` — prior comprehensive research on this codebase

### Secondary (MEDIUM confidence)
- Tailwind CSS 3 arbitrary value syntax `text-[var(--token)]` — confirmed by existing codebase usage patterns (10+ instances in reviewed files)
- `data-theme` attribute dark mode strategy confirmed working from layout.tsx line 39 inspection

### Tertiary (LOW confidence)
- None — all findings for this phase are verifiable by direct file inspection

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; two file paths fully audited from disk
- Architecture: HIGH — token pattern, dark mode mechanism, and test contract all verified against live files
- Pitfalls: HIGH — every pitfall is grounded in a specific line-number observation from the codebase (not theoretical)
- Hardcoded color inventory: HIGH — verified by grep across all three target component files

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable domain — CSS, no external dependencies)
