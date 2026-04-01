---
phase: 17
slug: token-foundation-dark-mode-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (via next.js) |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:run -- --reporter=verbose designTokens` |
| **Full suite command** | `cd frontend && npm run test:run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run test:run -- --reporter=verbose designTokens`
- **After every plan wave:** Run `cd frontend && npm run test:run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | TOK-01 | unit | `npm run test:run -- designTokens` | ✅ | ⬜ pending |
| 17-01-02 | 01 | 1 | TOK-02 | unit | `npm run test:run -- designTokens` | ✅ | ⬜ pending |
| 17-01-03 | 01 | 1 | TOK-03 | unit | `npm run test:run -- designTokens` | ✅ | ⬜ pending |
| 17-02-01 | 02 | 1 | TOK-03 | grep | `grep -rn "text-green-\|text-red-\|text-emerald-" frontend/components/ProductReview.tsx` | N/A | ⬜ pending |
| 17-02-02 | 02 | 1 | TOK-03 | grep | `grep -rn "text-green-\|text-red-\|text-emerald-" frontend/components/TopPickBlock.tsx` | N/A | ⬜ pending |
| 17-02-03 | 02 | 1 | TOK-03 | grep | `grep -rn "text-green-\|text-red-\|text-emerald-" frontend/components/ProductCards.tsx` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. `designTokens.test.ts` already exists and passes 13/13.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dark mode toggle produces no light-color flashes | TOK-03 | Visual regression requires browser | Toggle dark mode on /chat with product cards visible, inspect for hardcoded colors |
| Typography scale visible in browser | TOK-02 | Visual measurement | Inspect category hero h1 in DevTools, verify clamp(2.5rem, 5vw, 4.5rem) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
