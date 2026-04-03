# Phase 22: Visual QA + Consistency Pass - Research

**Researched:** 2026-04-01
**Domain:** Frontend QA — CSS token coverage, hardcoded color audit, visual consistency verification
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QA-01 | Full site screenshot walk-through on mobile (375px) and desktop (1440px) confirms visual consistency | Four surfaces to cover: homepage (/), browse category page (/browse/[category]), chat session with product results (/chat), results page (/results/[id]). Both viewports. Editorial luxury theme must be coherent across all. |
| QA-02 | designTokens.test.ts updated to cover every CSS variable added in Phase 17 | globals.css already read. All v3.0-specific tokens identified: --bold-blue/green/red/amber, --mosaic-scrim, --heading-hero/xl/lg/md/sm, --heading-weight, --heading-line-height. These are currently UNTESTED in designTokens.test.ts. |
| QA-03 | Grep for hardcoded Tailwind palette utilities in all v3.0-modified components returns zero results | Grep already run. Hardcoded colors found in: AffiliateLinks.tsx, ComparisonTable.tsx, ListBlock.tsx, ProductCarousel.tsx, PriceComparison.tsx, DestinationInfo.tsx, SourceCitations.tsx, StarRating.tsx, SentimentBar.tsx, CategoryNav.tsx, ErrorBoundary.tsx. Must triage: which were modified in v3.0 (must fix) vs. untouched pre-v3.0 (out of scope). |
</phase_requirements>

---

## Summary

Phase 22 is the hard release gate for v3.0. All upstream phases (17-21 and 23) are complete. The work has three distinct tracks: (1) writing new token assertions in designTokens.test.ts to cover the v3.0 CSS variables defined in Phase 17, (2) auditing and remediating hardcoded Tailwind color utilities in components that were modified during v3.0, and (3) performing a structured visual walk-through of four surfaces at two viewport sizes to confirm the editorial luxury aesthetic is coherent.

The test suite currently has 5 failing test files / 19 failing tests — none related to Phase 22's QA requirements. These are pre-existing failures from earlier phases (mobileTabBar, discoverScreen shape changes, resultsScreen rank badge format, inlineProductCard, chatScreen). The planner must decide whether to fix these pre-existing failures as part of Phase 22 or document them as out-of-scope. The 319 passing tests establish the safe floor.

The hardcoded color audit reveals a nuanced split: some files with hardcoded colors (AffiliateLinks, ComparisonTable, ListBlock, ProductCarousel, PriceComparison) were touched in earlier v3.0 phases and need remediation. Others (ErrorBoundary, DestinationInfo, StarRating, SentimentBar, SourceCitations, CategoryNav) require per-file inspection to determine v3.0 modification scope. The v3.0 CSS token system provides direct replacements for every hardcoded semantic color found.

**Primary recommendation:** Structure Phase 22 as three sequential plans: (1) Wave 0 token test expansion — add QA-02 assertions to designTokens.test.ts as a pure test-only PR, (2) hardcoded color remediation — audit, triage, and replace hardcoded Tailwind utilities in v3.0-touched components, (3) visual walk-through checkpoint — document four-surface two-viewport screenshot review as the final human QA gate.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vitest | ^4.0.17 | Test runner | Already configured, all existing tests use it |
| @testing-library/react | ^14.1.2 | Component rendering in tests | Already in use across all test files |
| Node.js `fs` module | built-in | CSS file reading in tests | Already used in designTokens.test.ts and imageAssets.test.ts |

### Test Infrastructure

| File | Purpose | State |
|------|---------|-------|
| `frontend/tests/designTokens.test.ts` | CSS variable and tailwind config assertions | EXISTS — needs 14+ new assertions |
| `frontend/app/globals.css` | Source of truth for token definitions | EXISTS — all v3.0 tokens confirmed present |
| `frontend/tailwind.config.ts` | Tailwind extension configuration | EXISTS — card-enter, stream, stream-out, stream-inout all present |
| `frontend/vitest.config.ts` | Vitest configuration | EXISTS — jsdom, setupFiles, excludes .next |

### Commands

```bash
# Quick test run
cd frontend && npm run test:run

# Watch mode during development
cd frontend && npm test

# Coverage
cd frontend && npm run test:run -- --coverage
```

---

## Architecture Patterns

### Pattern 1: CSS File Assertion Tests (designTokens.test.ts)

The existing designTokens.test.ts pattern reads globals.css and tailwind.config.ts as raw strings and asserts string containment. This is the correct pattern — no imports, no DOM, just file-system assertions.

```typescript
// Source: frontend/tests/designTokens.test.ts (existing pattern)
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

describe('RFC §2.6 design tokens', () => {
  const globalsPath = path.resolve(__dirname, '../app/globals.css')
  const globals = fs.readFileSync(globalsPath, 'utf-8')

  it('defines --bold-blue token', () => {
    expect(globals).toContain('--bold-blue')
  })
})
```

New v3.0 token assertions follow this exact pattern. No new imports, no framer-motion mocks, no jsdom needed.

### Pattern 2: CSS Variable Substitution for Hardcoded Colors

The project uses `style={{ color: 'var(--token)' }}` for dynamic values and Tailwind `text-[var(--token)]` for class-based usage. The v3.0 CSS token system has direct semantic replacements:

| Hardcoded | Semantic Meaning | CSS Token Replacement |
|-----------|-----------------|----------------------|
| `text-green-600` / `text-emerald-600` | Positive / price deal | `text-[var(--bold-green)]` or `style={{ color: 'var(--price-deal)' }}` |
| `bg-green-100` | Positive background | `style={{ backgroundColor: 'var(--success-light)' }}` |
| `text-red-500` / `text-red-600` | Error / negative | `text-[var(--bold-red)]` or `style={{ color: 'var(--error)' }}` |
| `bg-red-100` | Error background | `style={{ backgroundColor: 'color-mix(in srgb, var(--error) 10%, transparent)' }}` |
| `text-blue-600` / `bg-blue-100` | Info / primary | `text-[var(--bold-blue)]` or `style={{ color: 'var(--primary)' }}` |
| `text-yellow-400` / `text-yellow-500` | Star rating | `text-[var(--rating-star)]` or `style={{ color: 'var(--rating-star)' }}` |
| `text-emerald-600` (price discount) | Price deal | `style={{ color: 'var(--price-deal)' }}` |
| `bg-emerald-500/10` | Discount badge bg | `style={{ backgroundColor: 'var(--success-light)' }}` |
| `text-orange-500` | Source dot orange | Use `var(--accent)` or `var(--bold-amber)` |

**IMPORTANT: The `dark:` prefix is INERT** in this codebase. The project uses `data-theme="dark"` on the root element. Any `dark:text-emerald-400`, `dark:bg-emerald-900/30` etc. variants currently do nothing. CSS variable replacements automatically handle dark mode via the `[data-theme="dark"]` overrides in globals.css.

### Pattern 3: When to Keep vs. Replace Hardcoded Colors

Not all hardcoded colors in the codebase are in scope. QA-03 explicitly targets "all components modified during v3.0". Decision matrix:

| Component | Modified in v3.0? | Action |
|-----------|------------------|--------|
| AffiliateLinks.tsx | VERIFY — check git log | Fix if touched |
| ComparisonTable.tsx | VERIFY — check git log | Fix if touched |
| ListBlock.tsx | VERIFY — check git log | Fix if touched |
| ProductCarousel.tsx | VERIFY — check git log | Fix if touched |
| PriceComparison.tsx | VERIFY — check git log | Fix if touched |
| StarRating.tsx | Yes — MEMORY.md confirms v3.0 updates | Fix |
| SentimentBar.tsx | Yes — MEMORY.md confirms v3.0 updates | Fix |
| SourceCitations.tsx | VERIFY | Fix if touched |
| ErrorBoundary.tsx | No — MEMORY.md "remaining non-editorial, no --gpt-* vars" | Out of scope |
| DestinationInfo.tsx | VERIFY | Fix if touched |
| CategoryNav.tsx | VERIFY | Fix if touched |

**Special case: SourceCitations.tsx** — the `DOT_BG_CLASSES = ['bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-orange-500']` array is tested in sourceCitations.test.tsx. The test explicitly queries for `[class*="bg-red-"]` and `[class*="bg-blue-"]`. If these classes are replaced with `style={}` inline values, the existing tests will break. The planner must either update the tests alongside the component OR keep the Tailwind classes and add `!important` v3.0 overrides.

### Pattern 4: Screenshot Walk-Through Structure (QA-01)

The visual walk-through is a human QA task, not an automated test. The correct deliverable is:
1. Chrome DevTools device emulation (F12 → Ctrl+Shift+M) at 375px (mobile) and 1440px (desktop)
2. Four surfaces: `/` (homepage), `/browse/[category]` (e.g. `/browse/headphones`), `/chat` with a product query sent, `/results/[id]`
3. Document findings as a checklist or screenshot manifest committed to `.planning/phases/22-visual-qa-consistency-pass/`
4. Pass/fail against the v3.0 editorial luxury language: DM Sans body, Instrument Serif headings, warm ivory background, bold accent colors

**MEMORY.md note:** Always use Chrome DevTools device emulation, not window resize.

---

## V3.0 Token Inventory: What designTokens.test.ts Currently Misses

The current designTokens.test.ts covers only RFC §2.6 streaming tokens. The following Phase 17 tokens are UNTESTED:

### Bold Accent Tokens (light + dark, both need assertions)
- `--bold-blue`
- `--bold-green`
- `--bold-red`
- `--bold-amber`

### Mosaic Scrim Token
- `--mosaic-scrim`

### Typography Scale Tokens
- `--heading-hero`
- `--heading-xl`
- `--heading-lg`
- `--heading-md`
- `--heading-sm`
- `--heading-weight`
- `--heading-line-height`

### Dark Mode Counterparts
All seven of the above token groups must have `[data-theme="dark"]` counterparts. The test should assert that the dark theme block also contains each token name.

### Already Tested (do not re-test)
- `--stream-status-size`, `--stream-status-color`, `--stream-content-color`, `--citation-color`
- `.stream-status-text`, `.stream-content-text`, `.citation-text`
- `card-enter`, `'stream'`, `'stream-out'`, `'stream-inout'`
- `--gpt-accent`, `--gpt-text`, `--gpt-background`

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSS token existence test | Custom CSS parser | `fs.readFileSync` + `string.toContain()` | Pattern already established in designTokens.test.ts |
| Hardcoded color scanner | Custom grep script | Direct Vitest test + git grep command | grep command is already the QA-03 success criterion |
| Dark mode test | JSDOM with `data-theme="dark"` | String assertion for `[data-theme="dark"]` block in globals.css | JSDOM doesn't process CSS; reading the file is sufficient |
| Screenshot automation | Playwright/Cypress | Chrome DevTools manual emulation | Phase explicitly requires human visual QA, not automation |

---

## Common Pitfalls

### Pitfall 1: Replacing SourceCitations Dot Classes Breaks Existing Tests

**What goes wrong:** sourceCitations.test.tsx queries for `[class*="bg-red-"]` and `[class*="bg-blue-"]` and `[class*="bg-green-"]` to find colored dots. Replacing `bg-red-500` with an inline `style={{ backgroundColor: 'var(--error)' }}` will cause 3 tests to fail.

**Why it happens:** The test was written to match the class-based dot pattern. QA-03 wants no hardcoded Tailwind palette utilities.

**How to avoid:** Either (a) keep Tailwind classes for the dots (they are decorative semantic color indicators, not theme-critical) and document as intentional exception, or (b) replace classes with inline styles AND update the test assertions to query by `[style*="--error"]` or use data-color attributes.

**Warning signs:** Test failures in sourceCitations.test.tsx after changing SourceCitations.tsx.

### Pitfall 2: `--text-primary` Is Not a Defined Token

**What goes wrong:** InlineProductCard.tsx and SourceCitations.tsx use `var(--text-primary)` which does NOT exist in globals.css. This silently falls back to browser default (typically black). On dark backgrounds this causes invisible text.

**Why it happens:** The correct token is `var(--text)` (the primary text color). `--text-primary` was never defined in the v3.0 token system.

**How to avoid:** When auditing hardcoded colors, also grep for `--text-primary` usage and replace with `var(--text)`.

**Warning signs:** Text invisible or defaulting to black in dark mode even though `data-theme="dark"` is applied.

### Pitfall 3: `dark:` Tailwind Prefix Is Silently Inert

**What goes wrong:** Components like AffiliateLinks.tsx have `dark:text-green-400 dark:bg-green-900/30` which appear to handle dark mode but do nothing. The v3.0 strategy uses `[data-theme="dark"]` CSS selector, not the Tailwind `dark:` variant. These classes provide false confidence that dark mode is handled.

**Why it happens:** The project explicitly chose `data-theme="dark"` over Tailwind's `prefers-color-scheme` or `class` dark mode strategies.

**How to avoid:** When removing hardcoded `text-green-600`, also remove the paired `dark:text-green-400` — it was already a no-op. Replace the entire `isLowest ? 'text-green-600 dark:text-green-400' : 'text-[var(--text)]'` pattern with `isLowest ? 'text-[var(--price-deal)]' : 'text-[var(--text)]'`.

**Warning signs:** Visual inspection in dark mode shows color unchanged despite `dark:` classes being present.

### Pitfall 4: designTokens.test.ts Dark Mode Block Assertion Fragility

**What goes wrong:** A naive `globals.toContain('[data-theme="dark"]')` does not confirm the token is inside the dark block. A token might be defined once in `:root` and the test passes even if the dark block is missing the override.

**Why it happens:** `string.toContain()` matches anywhere in the file.

**How to avoid:** Extract the dark block substring first using `indexOf('[data-theme="dark"]')` then assert on the substring — same pattern as the existing `prefers-reduced-motion` block test in the file:

```typescript
// Source: frontend/tests/designTokens.test.ts (existing block-scoped pattern)
const darkIdx = globals.indexOf('[data-theme="dark"]')
const darkBlock = globals.slice(darkIdx, darkIdx + 3000)
expect(darkBlock).toContain('--bold-blue')
```

**Warning signs:** Test passes but visual dark mode inspection shows wrong colors.

### Pitfall 5: Pre-Existing Test Failures Are Not Phase 22 Bugs

**What goes wrong:** `npm run test:run` currently shows 19 failing tests across mobileTabBar, discoverScreen, inlineProductCard, chatScreen, and resultsScreen. These are NOT caused by v3.0 work. If Phase 22 tasks try to fix all failing tests, scope explodes.

**Why it happens:** Those tests test behavior contracts (label text, route patterns) that were changed in Phase 23 bug fixes without updating the test assertions.

**How to avoid:** The Phase 22 planner must decide: (a) explicitly list these as out-of-scope pre-existing failures with a note, or (b) include a focused wave to fix the failing assertion contracts. The QA-02 success criterion only requires `npm run test:run` to pass with NEW assertions — it does not say the whole suite must be green. However, the v3.0 release gate would be stronger if the full suite is green.

**Warning signs:** Conflating "Phase 23 test debt" with "Phase 22 regressions."

---

## Code Examples

### Expanding designTokens.test.ts for v3.0 Bold Accent Tokens

```typescript
// Source: Pattern derived from existing designTokens.test.ts structure
describe('v3.0 Bold Accent tokens', () => {
  it('defines --bold-blue in :root', () => {
    expect(globals).toContain('--bold-blue')
  })

  it('defines --bold-green in :root', () => {
    expect(globals).toContain('--bold-green')
  })

  it('defines --bold-red in :root', () => {
    expect(globals).toContain('--bold-red')
  })

  it('defines --bold-amber in :root', () => {
    expect(globals).toContain('--bold-amber')
  })

  it('bold accent tokens have dark mode counterparts', () => {
    const darkIdx = globals.indexOf('[data-theme="dark"]')
    expect(darkIdx).toBeGreaterThan(-1)
    const darkBlock = globals.slice(darkIdx, darkIdx + 3000)
    expect(darkBlock).toContain('--bold-blue')
    expect(darkBlock).toContain('--bold-green')
    expect(darkBlock).toContain('--bold-red')
    expect(darkBlock).toContain('--bold-amber')
  })
})

describe('v3.0 Mosaic scrim token', () => {
  it('defines --mosaic-scrim in :root', () => {
    expect(globals).toContain('--mosaic-scrim')
  })

  it('--mosaic-scrim has dark mode counterpart', () => {
    const darkIdx = globals.indexOf('[data-theme="dark"]')
    const darkBlock = globals.slice(darkIdx, darkIdx + 3000)
    expect(darkBlock).toContain('--mosaic-scrim')
  })
})

describe('v3.0 Typography scale tokens', () => {
  const typographyTokens = [
    '--heading-hero',
    '--heading-xl',
    '--heading-lg',
    '--heading-md',
    '--heading-sm',
    '--heading-weight',
    '--heading-line-height',
  ]

  typographyTokens.forEach((token) => {
    it(`defines ${token}`, () => {
      expect(globals).toContain(token)
    })
  })

  it('typography tokens declared in dark theme block for completeness', () => {
    const darkIdx = globals.indexOf('[data-theme="dark"]')
    const darkBlock = globals.slice(darkIdx, darkIdx + 3000)
    typographyTokens.forEach((token) => {
      expect(darkBlock).toContain(token)
    })
  })
})
```

### Hardcoded Color Replacement Pattern

```typescript
// Before (from SentimentBar.tsx — hardcoded, dark: variants are inert)
<div className="bg-emerald-500" />
<span className="text-emerald-600">{Math.round(posPct)}% Positive</span>

// After (use CSS variables — dark mode handled automatically via data-theme)
<div style={{ backgroundColor: 'var(--bold-green)' }} />
<span style={{ color: 'var(--bold-green)' }}>{Math.round(posPct)}% Positive</span>

// Or using Tailwind arbitrary value syntax:
<div className="text-[var(--price-deal)]" />
```

### Visual Walk-Through Checklist Template

```markdown
## QA-01 Visual Walk-Through

| Surface | Viewport | Headings (Serif) | Cards | Colors | Result |
|---------|----------|-----------------|-------|--------|--------|
| / (homepage) | 375px mobile | | | | |
| / (homepage) | 1440px desktop | | | | |
| /browse/headphones | 375px mobile | | | | |
| /browse/headphones | 1440px desktop | | | | |
| /chat (product query) | 375px mobile | | | | |
| /chat (product query) | 1440px desktop | | | | |
| /results/[id] | 375px mobile | | | | |
| /results/[id] | 1440px desktop | | | | |
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind `dark:` variant | `data-theme="dark"` attribute + CSS selector | Phase 17 | All `dark:` classes are silently no-ops; CSS variables handle dark mode |
| Hardcoded Tailwind palette utilities (`text-green-600`) | CSS variable references (`var(--bold-green)`) | v3.0 mandate | Enables theme-aware dark mode and accent theme switching |
| CSS stream tokens only | Full v3.0 typography + accent + scrim token suite | Phase 17 | 14+ new tokens added, none yet covered by test assertions |

**Deprecated/outdated:**
- `dark:text-*` / `dark:bg-*` Tailwind variants: Present in several components but produce no visual effect. Must be removed alongside hardcoded color replacements to avoid confusion.
- `--text-primary`: Used in two components (InlineProductCard.tsx, SourceCitations.tsx) but never defined. Replace with `--text`.

---

## Open Questions

1. **Pre-existing test failures scope**
   - What we know: 19 tests failing across 5 files (mobileTabBar, discoverScreen, inlineProductCard, chatScreen, resultsScreen)
   - What's unclear: Whether QA-02's "npm run test:run passes" means ALL tests must pass or only that NEW token tests pass
   - Recommendation: Include a plan step to fix the 19 pre-existing failures as a "clean suite gate" — the v3.0 release is stronger with a fully green suite. These are quick assertion-only fixes (no new component work needed).

2. **SourceCitations dot color migration**
   - What we know: `DOT_BG_CLASSES = ['bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-orange-500']` is used AND tested by class name
   - What's unclear: Whether QA-03 considers these in scope (SourceCitations may not have been modified in v3.0)
   - Recommendation: Verify git history for SourceCitations.tsx. If not modified in v3.0 phases, mark as out-of-scope. If modified, fix dots + update tests.

3. **Scope of "modified during v3.0"**
   - What we know: MEMORY.md confirms StarRating and SentimentBar were updated in v3.0. EditorsPicks, ProductCarousel, ComparisonTable, AffiliateLinks, ListBlock are listed in MEMORY.md as updated.
   - What's unclear: Exact list of files touched in Phases 17-21 (git log would confirm)
   - Recommendation: `git log --name-only --since="2026-04-01" --diff-filter=M -- frontend/` to get definitive list at plan time.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest ^4.0.17 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test:run` |
| Full suite command | `cd frontend && npm run test:run -- --coverage` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QA-02 | Every Phase 17 CSS token is asserted in designTokens.test.ts | unit | `cd frontend && npm run test:run -- --reporter=verbose tests/designTokens.test.ts` | Partial — file exists, new assertions needed |
| QA-03 | No hardcoded Tailwind color utilities in v3.0 components | static analysis | `cd frontend && grep -rn 'text-green-\|text-red-\|text-emerald-\|bg-blue-\|text-blue-\|bg-green-\|bg-red-\|bg-emerald-' components/ --include='*.tsx'` | N/A (grep command, not test file) |
| QA-01 | Visual consistency confirmed at 375px and 1440px | manual | N/A — human visual QA only | N/A |

### Sampling Rate

- **Per task commit:** `cd frontend && npm run test:run -- tests/designTokens.test.ts`
- **Per wave merge:** `cd frontend && npm run test:run`
- **Phase gate:** Full suite green (or pre-existing failures documented) before `/gsd:verify-work`

### Wave 0 Gaps

None — designTokens.test.ts exists. New assertions are additive to the existing file, not new files. No new infrastructure needed.

---

## Sources

### Primary (HIGH confidence)

- Direct file read: `frontend/app/globals.css` — all v3.0 token names confirmed from source
- Direct file read: `frontend/tests/designTokens.test.ts` — existing test structure confirmed
- Direct file read: `frontend/vitest.config.ts` — test configuration confirmed
- Direct grep: `frontend/components/**/*.tsx` — hardcoded color inventory confirmed

### Secondary (MEDIUM confidence)

- `.planning/STATE.md` — v3.0 decisions and phase history
- `.planning/REQUIREMENTS.md` — QA-01/02/03 requirement definitions
- `.planning/ROADMAP.md` — Phase 22 success criteria (verbatim)
- `CLAUDE.md` + `MEMORY.md` — project conventions (dark mode strategy, protected components)

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Token inventory (QA-02): HIGH — read globals.css directly, all tokens catalogued
- Hardcoded color audit (QA-03): HIGH — grep run, results confirmed with line numbers
- Visual walk-through requirements (QA-01): HIGH — success criteria are verbatim from ROADMAP.md
- Pre-existing test failures: HIGH — npm run test:run executed, 19 failures confirmed with file names

**Research date:** 2026-04-01
**Valid until:** Stable (globals.css is unlikely to change; token inventory is definitive)
