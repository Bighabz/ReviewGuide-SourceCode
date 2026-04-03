---
phase: 22
slug: visual-qa-consistency-pass
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.0.17 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:run -- tests/designTokens.test.ts` |
| **Full suite command** | `cd frontend && npm run test:run` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** `cd frontend && npm run test:run -- tests/designTokens.test.ts`
- **After every plan wave:** `cd frontend && npm run test:run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | QA-02 | unit | `npm run test:run -- tests/designTokens.test.ts` | ✅ extend | ⬜ pending |
| 22-01-02 | 01 | 1 | QA-03 | static | `grep -rn 'text-green-\|text-red-\|...' components/` | N/A (grep) | ⬜ pending |
| 22-01-03 | 01 | 1 | QA-01 | manual | N/A — human visual QA | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None — `designTokens.test.ts` exists. New assertions are additive. No new test infrastructure needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual consistency across 4 surfaces at 375px and 1440px | QA-01 | Requires human visual judgment | Screenshot walk-through: homepage, browse category, chat session, results page at both viewports |
| Bold editorial language coherence | QA-01 | Subjective quality assessment | Side-by-side comparison of all surfaces — fonts, colors, spacing must feel cohesive |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
