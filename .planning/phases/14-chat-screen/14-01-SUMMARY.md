---
phase: 14-chat-screen
plan: "01"
subsystem: frontend/tests
tags: [tdd, red-tests, chat-screen, behavioral-contracts]
dependency_graph:
  requires: []
  provides: [14-02, 14-03]
  affects: [frontend/tests/chatScreen.test.tsx, frontend/tests/inlineProductCard.test.tsx, frontend/tests/sourceCitations.test.tsx]
tech_stack:
  added: []
  patterns: [vitest, testing-library/react, vi.mock, RED-GREEN-TDD]
key_files:
  created:
    - frontend/tests/chatScreen.test.tsx
    - frontend/tests/inlineProductCard.test.tsx
    - frontend/tests/sourceCitations.test.tsx
  modified: []
decisions:
  - "Tests import non-existent InlineProductCard and SourceCitations as RED state — import failures are the expected signal until Plan 02 creates the components"
  - "chatScreen.test.tsx mocks framer-motion, react-markdown, UIBlocks, normalizeBlocks to isolate Message component structural tests"
  - "Colored dot tests use class AND style attribute fallbacks to allow flexible implementation (Tailwind bg-[#hex] or inline style)"
metrics:
  duration_seconds: 239
  completed_date: "2026-03-17"
  tasks_completed: 2
  files_created: 3
---

# Phase 14 Plan 01: Chat Screen RED Tests Summary

Wave 0 RED test scaffolds for all 6 Phase 14 CHAT requirements — behavioral contracts that Plans 02 and 03 must satisfy.

## What Was Built

Three test files defining executable behavioral contracts for the chat screen redesign:

**frontend/tests/chatScreen.test.tsx** (21 tests)
Tests for CHAT-01, CHAT-03, CHAT-05, CHAT-06 — renders the existing `Message` component directly with heavy mocking to isolate DOM structure checks.

**frontend/tests/inlineProductCard.test.tsx** (15 tests)
Tests for CHAT-02 — defines the InlineProductCard contract: 64px rows, rank badges (Top Pick / Best Value / Premium), Buy on Amazon affiliate links, image fallback, dividers.

**frontend/tests/sourceCitations.test.tsx** (13 tests)
Tests for CHAT-04 — defines the SourceCitations contract: target=_blank links, rel=noopener, colored dot positions (red/blue/green), source name text, Sources header, +X more toggle.

## Test Results (RED State)

```
Test Files  3 failed (3)
Tests       6 failed | 15 passed (21)
```

- **15 passing** — existing Message behaviors (status text, render structure, DOM order already partly correct)
- **6 failing** — new behaviors not yet implemented: bubble pill shape (CHAT-06), primary text color (CHAT-06), horizontal chip row (CHAT-06), AI "ReviewGuide" label (CHAT-05), asymmetric tl corner (CHAT-05), max-width 85% (CHAT-05)
- **2 test files failing at import** — InlineProductCard and SourceCitations don't exist yet (correct RED state)

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | chatScreen.test.tsx — bubble/render/status/chips | 2135316 | frontend/tests/chatScreen.test.tsx |
| 2 | inlineProductCard + sourceCitations tests | 89eba92 | frontend/tests/inlineProductCard.test.tsx, frontend/tests/sourceCitations.test.tsx |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

Files exist:
- FOUND: frontend/tests/chatScreen.test.tsx
- FOUND: frontend/tests/inlineProductCard.test.tsx
- FOUND: frontend/tests/sourceCitations.test.tsx

Commits exist:
- FOUND: 2135316
- FOUND: 89eba92
