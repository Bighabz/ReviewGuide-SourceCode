---
phase: 15
slug: results-screen
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.0.x + @testing-library/react 14 + jsdom |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:run -- tests/resultsScreen.test.tsx` |
| **Full suite command** | `cd frontend && npm run test:run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run test:run -- tests/resultsScreen.test.tsx`
- **After every plan wave:** Run `cd frontend && npm run test:run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 0 | RES-01 | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 15-01-02 | 01 | 0 | RES-02, RESP-01, RESP-02 | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 15-01-03 | 01 | 0 | RES-03, RES-04 | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 15-01-04 | 01 | 0 | RES-05 | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 15-01-05 | 01 | 0 | RES-06 | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/tests/resultsScreen.test.tsx` — covers RES-01 through RES-06, RESP-01, RESP-02

*Existing `tests/setup.ts` provides mocks for router, localStorage, CSS variables.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Horizontal scroll peek effect on mobile | RES-02, RESP-01 | Touch scroll physics | Swipe product cards on mobile, verify 2.2 card peek effect |
| Desktop 3-column grid no-scroll viewport | RES-02, RESP-02 | Viewport fit assessment | View results at 1024px+, verify all panels visible without scrolling |
| Share copies URL to clipboard | RES-05 | Clipboard API requires user gesture | Tap Share, verify "Link copied!" toast and URL in clipboard |
| Curated Amazon images load correctly | RES-03 | Real network image loading | Navigate to results with curated products, verify real Amazon images |
| Score bar visual rendering | RES-04 | Visual quality assessment | Verify score bar fill percentage matches rank position |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
