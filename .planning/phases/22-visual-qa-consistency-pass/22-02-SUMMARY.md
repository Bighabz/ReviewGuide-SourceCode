---
phase: 22-visual-qa-consistency-pass
plan: "02"
subsystem: frontend-components
tags: [css-variables, tailwind-cleanup, dark-mode, qa, visual-consistency]
dependency_graph:
  requires: [17-token-foundation-dark-mode-fixes]
  provides: [QA-03-zero-hardcoded-colors]
  affects: [AffiliateLinks, ComparisonTable, ListBlock, ProductCarousel, PriceComparison, StarRating, SentimentBar, SourceCitations, DestinationInfo, CategoryNav, InlineProductCard]
tech_stack:
  added: []
  patterns: [css-variable-inline-styles, style-object-map-pattern, color-mix-in-srgb]
key_files:
  created: []
  modified:
    - frontend/components/AffiliateLinks.tsx
    - frontend/components/ComparisonTable.tsx
    - frontend/components/ListBlock.tsx
    - frontend/components/ProductCarousel.tsx
    - frontend/components/PriceComparison.tsx
    - frontend/components/StarRating.tsx
    - frontend/components/browse/SentimentBar.tsx
    - frontend/components/SourceCitations.tsx
    - frontend/components/DestinationInfo.tsx
    - frontend/components/browse/CategoryNav.tsx
    - frontend/components/InlineProductCard.tsx
    - frontend/tests/sourceCitations.test.tsx
decisions:
  - "ListBlock colorMap refactored to styleMap using React.CSSProperties objects instead of Tailwind class strings — cleaner approach that avoids arbitrary value syntax"
  - "DestinationInfo amber and violet sections also converted (not just blue/emerald) — consistent treatment of all hardcoded palette colors in the file"
  - "SentimentBar rose-500 (negative bar label) converted to --bold-red — closest semantic equivalent"
  - "StarRating gray-300 empty stars converted to --border-strong — semantically correct neutral token"
  - "SourceCitations DOT_COLORS array changed from hex literals to CSS variable strings — allows theme-aware dot colors"
  - "sourceCitations test assertions updated to query [style*=\"--bold-red/blue/green\"] instead of class-based selectors"
metrics:
  duration: "291s"
  completed_date: "2026-04-01"
  tasks_completed: 2
  files_modified: 12
requirements_met: [QA-03]
---

# Phase 22 Plan 02: CSS Variable Consistency Pass (Hardcoded Tailwind Colors) Summary

Replace all hardcoded Tailwind palette utilities across 11 v3.0-modified components with CSS variable references; remove inert dark: prefixes; fix phantom --text-primary token in two components.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Replace hardcoded colors in AffiliateLinks, ComparisonTable, ListBlock, ProductCarousel, PriceComparison | 5d072b7 | 5 components |
| 2 | Replace hardcoded colors in StarRating, SentimentBar, SourceCitations, DestinationInfo, CategoryNav, InlineProductCard + fix phantom --text-primary + update tests | c4a3206 | 6 components + 1 test |

## Verification Results

### QA-03 grep audit (all 11 files) — PASSED
```
grep -rn 'text-green-|text-red-|text-emerald-|bg-blue-|text-blue-|bg-green-|bg-red-|bg-emerald-|text-yellow-|fill-yellow-|bg-orange-|dark:text-|dark:bg-' [11 files]
```
Result: **zero matches**

### Phantom token audit — PASSED
```
grep -rn '\-\-text-primary' components/ --include='*.tsx'
```
Result: **zero matches**

### Test suite
- SourceCitations: 15/15 passed
- Overall: 336/337 passed (1 pre-existing failure in discoverScreen.test.tsx — unrelated to this plan)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] DestinationInfo amber and violet sections converted alongside blue/emerald**
- **Found during:** Task 2
- **Issue:** Plan specified lines 23 and 61 (blue, emerald), but amber (best_season) and violet (local_customs) sections had the same dark: prefix pattern
- **Fix:** Applied CSS variable inline styles to all four icon containers for consistency — amber->var(--bold-amber), violet->var(--secondary)
- **Files modified:** frontend/components/DestinationInfo.tsx
- **Commit:** c4a3206

**2. [Rule 2 - Missing] SentimentBar rose-500 label also converted**
- **Found during:** Task 2
- **Issue:** Plan specified bg-emerald-500 (positive bar) but the negative label `text-rose-500` was an additional hardcoded color
- **Fix:** Changed to `style={{ color: 'var(--bold-red)' }}`
- **Files modified:** frontend/components/browse/SentimentBar.tsx
- **Commit:** c4a3206

### Deferred Issues (pre-existing, out of scope)

- `tests/discoverScreen.test.tsx` — 1 test failure: "renders at least 4 category chips (Tech, Travel, Kitchen, Fitness)" — pre-existing failure unrelated to this plan's changes, logged to deferred-items.md

## Key Implementation Patterns

**Pattern 1: Conditional inline border style (AffiliateLinks)**
```tsx
style={isLowest ? {
  borderColor: 'color-mix(in srgb, var(--bold-green) 30%, transparent)',
  backgroundColor: 'var(--success-light)',
} : undefined}
```

**Pattern 2: Style object map replacing className map (ListBlock)**
```tsx
const styleMap: Record<string, { bg: CSSProperties; text: CSSProperties; bullet: CSSProperties }> = {
  activities: {
    bg: { backgroundColor: 'color-mix(in srgb, var(--bold-blue) 10%, transparent)' },
    text: { color: 'var(--bold-blue)' },
    bullet: { backgroundColor: 'var(--bold-blue)' },
  },
  ...
}
```

**Pattern 3: CSS variable dot colors (SourceCitations)**
```tsx
const DOT_COLORS = ['var(--bold-red)', 'var(--bold-blue)', 'var(--bold-green)', 'var(--bold-amber)']
// Rendered as:
style={{ backgroundColor: DOT_COLORS[index % DOT_COLORS.length] }}
```

## Self-Check: PASSED

All 12 modified files confirmed present. Both task commits (5d072b7, c4a3206) confirmed in git log. Zero hardcoded Tailwind color utilities in all 11 components. Zero phantom --text-primary tokens. 336/337 tests pass (1 pre-existing unrelated failure).
