---
phase: 22
slug: visual-qa-consistency-pass
status: draft
nyquist_compliant: true
wave_0_complete: true
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
| 22-01-01 | 01 | 1 | QA-02 | unit | `cd frontend && npm run test:run 2>&1 \| tail -5` | existing (fix) | pending |
| 22-01-02 | 01 | 1 | QA-02 | unit | `cd frontend && npm run test:run -- --reporter=verbose tests/designTokens.test.ts 2>&1 \| tail -20` | existing (extend) | pending |
| 22-02-01 | 02 | 1 | QA-03 | static | `cd frontend && ! grep -rn 'text-green-\|...' components/{5 files}` | N/A (grep) | pending |
| 22-02-02 | 02 | 1 | QA-03 | static | `cd frontend && ! grep -rn 'text-green-\|...' components/{6 files} && ! grep -rn 'text-primary' components/{2 files}` | N/A (grep) | pending |
| 22-03-01 | 03 | 2 | QA-01 | integration | `cd frontend && npm run test:run 2>&1 \| tail -3` + `! grep` audit | N/A (read-only) | pending |
| 22-03-02 | 03 | 2 | QA-01 | manual | `echo "Human visual verification checkpoint"` | N/A (checkpoint) | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

None -- `designTokens.test.ts` exists. New assertions are additive. No new test infrastructure needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual consistency across 4 surfaces at 375px and 1440px | QA-01 | Requires human visual judgment | Screenshot walk-through: homepage, browse category, chat session, results page at both viewports |
| Bold editorial language coherence | QA-01 | Subjective quality assessment | Side-by-side comparison of all surfaces -- fonts, colors, spacing must feel cohesive |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated
