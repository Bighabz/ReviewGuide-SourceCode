---
phase: 1
slug: response-experience-overhaul
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), jest 29.x (frontend) |
| **Config file** | `backend/pytest.ini` / `frontend/jest.config.js` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v --timeout=60` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | RX-03 | unit | `pytest tests/test_product_affiliate.py -v` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | RX-04 | unit | `pytest tests/test_review_search.py -v` | ✅ | ⬜ pending |
| 1-01-03 | 01 | 1 | RX-05 | unit | `pytest tests/test_plan_executor.py -v` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | RX-06 | unit | `pytest tests/test_product_compose.py -v` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | RX-07 | unit | `pytest tests/test_product_compose.py -v` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 2 | RX-02 | integration | `pytest tests/test_chat_streaming.py -v` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 2 | RX-01, RX-08 | manual | Browser test | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_product_affiliate.py` — stubs for RX-03 (parallel affiliate searches)
- [ ] `tests/test_product_compose.py` — stubs for RX-06, RX-07 (reduced LLM calls, buy links)
- [ ] `tests/test_chat_streaming.py` — stubs for RX-02 (token streaming)

*Existing infrastructure covers: review_search tests (RX-04)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Product cards appear within 5s | RX-01 | Requires running full stack with live APIs | Send "best noise cancelling headphones", verify cards render within 5s |
| Blog narrative streams token-by-token | RX-02 | Visual UX behavior, timing-dependent | Watch chat for progressive text appearance vs batch dump |
| Product cards render above blog text | RX-08 | Visual layout verification | Confirm card order in rendered chat message |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
