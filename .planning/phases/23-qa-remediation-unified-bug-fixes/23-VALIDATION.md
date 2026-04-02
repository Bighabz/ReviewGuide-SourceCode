---
phase: 23
slug: qa-remediation-unified-bug-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Backend Framework** | pytest + pytest-asyncio (existing) |
| **Backend Config** | `backend/tests/conftest.py` (existing) |
| **Backend Quick Run** | `python -m pytest tests/test_product_compose.py -x -v` |
| **Backend Full Suite** | `python -m pytest tests/ -v` |
| **Frontend Framework** | Vitest + @testing-library/react (existing) |
| **Frontend Config** | `frontend/vitest.config.ts` |
| **Frontend Quick Run** | `npm run test -- --run tests/chatScreen.test.tsx` |
| **Frontend Full Suite** | `npm run test -- --run` |
| **Estimated runtime** | ~45 seconds (backend) + ~30 seconds (frontend) |

---

## Sampling Rate

- **After every task commit:** Run the quick command for the modified area (backend or frontend)
- **After every plan wave:** Run both full suites
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 75 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 23-01-01 | 01 | 0 | QAR-01 | unit | `pytest tests/test_product_compose.py::test_fallback_loop_continue -x` | ❌ W0 | ⬜ pending |
| 23-01-02 | 01 | 0 | QAR-02 | unit | `pytest tests/test_product_compose.py::test_single_provider_card -x` | ❌ W0 | ⬜ pending |
| 23-01-03 | 01 | 0 | QAR-03 | unit | `pytest tests/test_product_compose.py::test_label_domain_parity -x` | ❌ W0 | ⬜ pending |
| 23-01-04 | 01 | 0 | QAR-04 | unit | `pytest tests/test_product_compose.py::test_accessory_suppression -x` | ❌ W0 | ⬜ pending |
| 23-01-05 | 01 | 0 | QAR-05 | unit | `pytest tests/test_product_compose.py::test_budget_enforcement -x` | ❌ W0 | ⬜ pending |
| 23-01-06 | 01 | 0 | QAR-06 | unit | `pytest tests/test_travel_compose.py::test_timeout_recovery -x` | ❌ W0 | ⬜ pending |
| 23-01-07 | 01 | 0 | QAR-07 | unit | `pytest tests/test_product_compose.py::test_citations_have_real_urls -x` | ❌ W0 | ⬜ pending |
| 23-01-08 | 01 | 0 | QAR-08 | component | `npm run test -- --run tests/chatScreen.test.tsx` | ✅ partial | ⬜ pending |
| 23-01-09 | 01 | 0 | QAR-09 | unit | `npm run test -- --run tests/layout.test.tsx` | ❌ W0 | ⬜ pending |
| 23-01-10 | 01 | 0 | QAR-10 | component | `npm run test -- --run tests/notFound.test.tsx` | ❌ W0 | ⬜ pending |
| 23-01-11 | 01 | 0 | QAR-11 | component | `npm run test -- --run tests/chatScreen.test.tsx` | ✅ partial | ⬜ pending |
| 23-01-12 | 01 | 0 | QAR-12 | smoke | manual + CI gate | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_product_compose.py` — extend with QAR-01 through QAR-05, QAR-07 test stubs
- [ ] `backend/tests/test_travel_compose.py` — create, covers QAR-06
- [ ] `frontend/tests/notFound.test.tsx` — create, covers QAR-10
- [ ] `frontend/tests/layout.test.tsx` — extend or create, covers QAR-09
- [ ] `frontend/tests/chatScreen.test.tsx` — extend existing, covers QAR-08/QAR-11

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WCAG contrast on 7 elements | QAR-13 | Requires browser rendering + contrast measurement | DevTools Lighthouse audit on /chat with iPhone 14 Pro viewport |
| iOS scroll during streaming | QAR-14 | Requires real iOS device or emulator | Open chat on real iPhone, send query, attempt scroll during streaming |
| Landscape bottom nav visibility | QAR-15 | Requires specific orientation + viewport combo | Rotate to landscape on 844px-width device, verify bottom nav visible |
| Chat history shows conversations | QAR-16 | Requires backend session data | Open sidebar, verify prior conversations listed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 75s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
