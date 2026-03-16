---
phase: 1
slug: response-experience-overhaul
status: draft
nyquist_compliant: true
wave_0_complete: true
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
| 1-01-01 | 01 | 1 | RX-03, RX-04, RX-05 | unit | `pytest tests/test_product_affiliate.py tests/test_review_search.py -v` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | RX-01, RX-02, RX-06, RX-07, RX-08 | unit | `pytest tests/test_product_compose.py tests/test_chat_streaming.py -v` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | RX-03 | unit | `pytest tests/test_product_affiliate.py::test_affiliate_search_products_parallel_within_provider -v` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | RX-04 | unit | `pytest tests/test_review_search.py -v` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 1 | RX-05 | unit | `pytest tests/test_product_affiliate.py::test_planner_fast_path_review_and_affiliate_in_same_step -v` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 1 | RX-06 | unit | `pytest tests/test_product_compose.py -v` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 1 | RX-07 | unit | `pytest tests/test_product_compose.py -v` | ❌ W0 | ⬜ pending |
| 1-04-01 | 04 | 2 | RX-01, RX-08 | unit | `pytest tests/test_chat_streaming.py::test_product_cards_emitted_before_compose -v` | ❌ W0 | ⬜ pending |
| 1-04-02 | 04 | 2 | RX-01, RX-08 | unit | `pytest tests/test_product_affiliate.py -v` | ❌ W0 | ⬜ pending |
| 1-04-03 | 04 | 2 | RX-01, RX-08 | import-check | `python -c "from app.api.v1.chat import stream_chat; print('OK')"` | ✅ | ⬜ pending |
| 1-05-01 | 05 | 3 | RX-02 | import-check | `python -c "from app.services.plan_executor import register_token_callback; print('OK')"` | ✅ | ⬜ pending |
| 1-05-02 | 05 | 3 | RX-02 | unit | `pytest tests/test_chat_streaming.py::test_blog_article_uses_model_service_stream -v` | ❌ W0 | ⬜ pending |
| 1-05-03 | 05 | 3 | RX-02 | import-check | `python -c "from app.api.v1.chat import stream_chat; print('OK')"` | ✅ | ⬜ pending |
| 1-06-01 | 06 | 4 | all RX | manual | Browser test (full stack) | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 is Plan 01-01. The following test files must exist with failing stubs before any implementation plan runs:

- [ ] `tests/test_product_affiliate.py` — stubs for RX-03 (parallel affiliate), RX-05 (fast path plan)
- [ ] `tests/test_product_compose.py` — stubs for RX-06, RX-07, RX-08/RX-01 (reduced LLM calls, buy links, stream_chunk_data)
- [ ] `tests/test_chat_streaming.py` — stubs for RX-01 (artifact callback), RX-02 (token streaming)
- [ ] `tests/test_review_search.py` — stub appended for RX-04 (caps at 3 products)

*Existing infrastructure covers: test_review_search.py (existing tests — preserved, RX-04 stub appended)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Product cards appear within 5s | RX-01 | Requires running full stack with live APIs | Send "best noise cancelling headphones", verify cards render within 5s |
| Blog narrative streams token-by-token | RX-02 | Visual UX behavior, timing-dependent | Watch chat for progressive text appearance vs batch dump |
| Product cards render above blog text | RX-08 | Visual layout verification | Confirm card order in rendered chat message |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (test_product_affiliate.py, test_product_compose.py additions, test_chat_streaming.py, test_review_search.py stub)
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
