---
phase: 21
slug: chat-results-card-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.0.17 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:run -- tests/inlineProductCard.test.tsx tests/topPickBlock.test.tsx` |
| **Full suite command** | `cd frontend && npm run test:run` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** `cd frontend && npm run test:run -- tests/inlineProductCard.test.tsx tests/topPickBlock.test.tsx tests/sourceCitations.test.tsx`
- **After every plan wave:** `cd frontend && npm run test:run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 0 | CHT-01 | unit | `npm run test:run -- tests/designTokens.test.ts` | ✅ extend | ⬜ pending |
| 21-01-02 | 01 | 0 | CHT-02 | unit | `npm run test:run -- tests/inlineProductCard.test.tsx` | ✅ extend | ⬜ pending |
| 21-01-03 | 01 | 0 | CARD-01 | unit | `npm run test:run -- tests/blockRegistryTopPick.test.tsx` | ✅ partial | ⬜ pending |
| 21-01-04 | 01 | 0 | CARD-02 | unit | `npm run test:run -- tests/productReviewCard.test.tsx` | ❌ W0 | ⬜ pending |
| 21-01-05 | 01 | 0 | CARD-03 | unit | `npm run test:run -- tests/topPickBlock.test.tsx` | ✅ extend | ⬜ pending |
| 21-01-06 | 01 | 0 | CARD-04 | unit | `npm run test:run -- tests/cardAnimations.test.tsx` | ❌ W0 | ⬜ pending |
| 21-01-07 | 01 | 0 | RES-07 | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ✅ extend | ⬜ pending |
| 21-01-08 | 01 | 0 | RES-08 | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ✅ extend | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/tests/productReviewCard.test.tsx` — covers CARD-01, CARD-02 (merchant extraction, 3-offer cap, spring animation)
- [ ] `frontend/tests/cardAnimations.test.tsx` — covers CARD-04 (whileHover prop, no layout prop on streaming containers)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No frame drops below 55fps during streaming | CARD-04 | Requires Chrome DevTools Performance panel | Send product query, record Performance trace during streaming, check for frame drops |
| Visual coherence of card hover animations | CARD-01 | Subjective animation quality | Hover over cards in chat and results, verify smooth spring lift |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
