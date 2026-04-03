---
phase: 20
slug: discover-browse-page-upgrades
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.0.17 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:run -- tests/browseHero.test.tsx` |
| **Full suite command** | `cd frontend && npm run test:run` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** `cd frontend && npm run test:run -- tests/browseHero.test.tsx tests/imageAssets.test.ts`
- **After every plan wave:** `cd frontend && npm run test:run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 0 | BRW-01 | unit | `npm run test:run -- tests/browseHero.test.tsx` | ❌ W0 | ⬜ pending |
| 20-01-02 | 01 | 0 | DISC-06 | unit | `npm run test:run -- tests/browseHero.test.tsx` | ❌ W0 | ⬜ pending |
| 20-01-03 | 01 | 0 | DISC-07 | unit | `npm run test:run -- tests/imageAssets.test.ts` | ✅ extend | ⬜ pending |
| 20-01-04 | 01 | 0 | BRW-02 | unit | `npm run test:run -- tests/editorsPicks.test.tsx` | ✅ extend | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/tests/browseHero.test.tsx` — covers BRW-01 (WebP paths), DISC-06 (chip height/accent), BRW-02 (card width)
- [ ] Extend `frontend/tests/imageAssets.test.ts` — add DISC-07 carousel slide image assertions
- [ ] Extend `frontend/tests/editorsPicks.test.tsx` — add BRW-02 visual assertions

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WCAG AA contrast on hero overlay text | BRW-01 | Depends on image luminance | DevTools contrast checker on each category hero |
| Visual coherence of bold chip colors | DISC-06 | Subjective visual assessment | Side-by-side screenshot before/after |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
