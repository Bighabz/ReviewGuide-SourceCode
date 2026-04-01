---
phase: 17-token-foundation-dark-mode-fixes
plan: "02"
subsystem: frontend/components
tags: [dark-mode, design-tokens, css-variables, tailwind, sentiment-labels]
dependency_graph:
  requires: ["17-01"]
  provides: ["TOK-03"]
  affects: ["frontend/components/ProductReview.tsx", "frontend/components/TopPickBlock.tsx", "frontend/components/ProductCards.tsx"]
tech_stack:
  added: []
  patterns: ["text-[var(--success)]", "text-[var(--error)]", "CSS variable token references in Tailwind className"]
key_files:
  created: []
  modified:
    - frontend/components/ProductReview.tsx
    - frontend/components/TopPickBlock.tsx
    - frontend/components/ProductCards.tsx
decisions:
  - "Removed dark:text-emerald-400 from TopPickBlock.tsx — the data-theme strategy renders all Tailwind dark: prefixes silently inert"
metrics:
  duration: "110s"
  completed: "2026-03-31"
  tasks_completed: 3
  files_modified: 3
---

# Phase 17 Plan 02: Pros/Cons Label Token Migration Summary

**One-liner:** Replaced all 9 hardcoded Tailwind green/red palette classes in 3 product card leaf components with `var(--success)` and `var(--error)` CSS variable references.

## What Was Done

Converted sentiment label colors in three product card leaf components from hardcoded Tailwind palette classes to semantic CSS variable token references. This eliminates dark mode regressions where labels would render with light-mode colors on dark backgrounds regardless of theme.

The project uses `[data-theme="dark"]` on the html element — not Tailwind's `dark:` class prefix strategy. This means all `dark:` utility prefixes are silently inert and were also removed.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Convert ProductReview.tsx hardcoded colors | 870b441 | frontend/components/ProductReview.tsx |
| 2 | Convert TopPickBlock.tsx hardcoded colors + remove inert dark: utility | 062d4d3 | frontend/components/TopPickBlock.tsx |
| 3 | Convert ProductCards.tsx hardcoded colors | 78338f3 | frontend/components/ProductCards.tsx |

## Changes by File

### ProductReview.tsx (4 changes)
- Line 108: `text-green-700` → `text-[var(--success)]` (Pros heading)
- Line 115: `text-green-600` → `text-[var(--success)]` (checkmark icon)
- Line 126: `text-red-700` → `text-[var(--error)]` (Cons heading)
- Line 133: `text-red-600` → `text-[var(--error)]` (X icon)

### TopPickBlock.tsx (3 changes + 1 removal)
- Line 135: `text-emerald-600 dark:text-emerald-400` → `text-[var(--success)]` (Best for label + removed inert dark: utility)
- Line 160: `text-green-600` → `text-[var(--success)]` (Pros label)
- Line 166: `text-red-500` → `text-[var(--error)]` (Cons label)

### ProductCards.tsx (2 changes)
- Line 125: `text-green-600` → `text-[var(--success)]` (What we like label)
- Line 131: `text-red-500` → `text-[var(--error)]` (Watch out for label)

## Verification Results

1. Zero hardcoded `text-green-*`, `text-red-*`, `text-emerald-*` in all three files — PASS
2. Zero `dark:` utility prefixes in all three files — PASS
3. `var(--success)` counts: ProductReview=2, TopPickBlock=2, ProductCards=1 (total=5) — PASS
4. `var(--error)` counts: ProductReview=2, TopPickBlock=1, ProductCards=1 (total=4) — PASS
5. designTokens.test.ts: 13/13 pass — PASS
6. Full test suite: 21 failures, 252 passing — no new failures (pre-existing count unchanged) — PASS

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

Files confirmed present:
- frontend/components/ProductReview.tsx — FOUND
- frontend/components/TopPickBlock.tsx — FOUND
- frontend/components/ProductCards.tsx — FOUND

Commits confirmed:
- 870b441 (ProductReview.tsx) — FOUND
- 062d4d3 (TopPickBlock.tsx) — FOUND
- 78338f3 (ProductCards.tsx) — FOUND
