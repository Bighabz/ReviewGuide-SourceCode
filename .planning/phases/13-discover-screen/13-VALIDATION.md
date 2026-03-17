---
phase: 13
slug: discover-screen
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.0.17 + @testing-library/react 14 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run tests/discoverScreen.test.tsx` |
| **Full suite command** | `cd frontend && npx vitest run` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run tests/discoverScreen.test.tsx`
- **After every plan wave:** Run `cd frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 0 | DISC-01 | unit | `npx vitest run tests/discoverScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 13-01-02 | 01 | 0 | DISC-02 | unit | `npx vitest run tests/discoverScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 13-01-03 | 01 | 0 | DISC-03 | unit | `npx vitest run tests/discoverScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 13-01-04 | 01 | 0 | DISC-04 | unit | `npx vitest run tests/discoverScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 13-01-05 | 01 | 0 | DISC-05 | unit | `npx vitest run tests/discoverScreen.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/tests/discoverScreen.test.tsx` — 10 behavioral contracts covering DISC-01 through DISC-05

*Existing `tests/setup.ts` already mocks localStorage, router, and CSS variables — no additions needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Category chip horizontal scrolling feel | DISC-02 | Scroll physics require real touch input | Swipe chip row on mobile, verify smooth scroll with no visible scrollbar |
| Trending card tap navigation | DISC-03 | Visual navigation confirmation | Tap a trending card, verify it navigates to chat with query pre-loaded |
| "For You" chip appearance with real searches | DISC-04 | Requires real localStorage state from prior sessions | Do a search, return to /, verify "For You" chip appears first |
| Desktop trending grid layout | DISC-03 | Visual layout assessment | View / at 1024px+, verify trending cards in 2-3 column grid |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
