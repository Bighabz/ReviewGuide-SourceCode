---
phase: 19
slug: mosaic-hero
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (via next.js) |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:run -- --reporter=verbose mosaicHero` |
| **Full suite command** | `cd frontend && npm run test:run` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run test:run -- --reporter=verbose mosaicHero`
- **After every plan wave:** Run `cd frontend && npm run test:run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 | 0 | HERO-01, HERO-04 | unit | `npm run test:run -- mosaicHero` | ❌ W0 | ⬜ pending |
| 19-02-01 | 02 | 1 | HERO-01, HERO-03 | unit | `npm run test:run -- mosaicHero` | ❌ W0 | ⬜ pending |
| 19-02-02 | 02 | 1 | HERO-02 | unit | `npm run test:run -- mosaicHero` | ❌ W0 | ⬜ pending |
| 19-02-03 | 02 | 1 | HERO-04 | unit | `npm run test:run -- mosaicHero` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/tests/mosaicHero.test.tsx` — test stubs for HERO-01 (renders mosaic tiles), HERO-04 (first img loading="eager"), CLS guard (explicit width/height)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Mosaic tiles visually overlap and rotate | HERO-01 | Visual layout requires browser rendering | Open / in browser, verify tilted overlapping cards |
| Search bar text readable over mosaic | HERO-02 | Contrast perception is visual | Verify headline and search bar legible at 375px and 1440px |
| LCP < 2.5s and CLS < 0.1 | HERO-04 | Lighthouse audit required | Run Lighthouse mobile audit on / |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
