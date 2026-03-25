---
phase: 01-response-experience-overhaul
verified: 2026-03-17T22:00:00Z
status: gaps_found
score: 3/8 requirements verified
re_verification: false
gaps:
  - truth: "Product cards appear in the browser within ~5 seconds — before product_compose runs"
    status: failed
    reason: "product_affiliate.py does not set stream_chunk_data in its return dict. register_artifact_callback, clear_artifact_callbacks, and _emit_artifact are absent from plan_executor.py. chat.py has no _on_artifact callback, no artifact_ready event handler, and no register_artifact_callback import. The entire early-streaming path (Plan 04) is missing from the codebase."
    artifacts:
      - path: "backend/mcp_server/tools/product_affiliate.py"
        issue: "Return dict at line 243 contains only affiliate_products and success — no stream_chunk_data key"
      - path: "backend/app/services/plan_executor.py"
        issue: "No register_artifact_callback, clear_artifact_callbacks, get_artifact_callbacks, or _emit_artifact — only the legacy citation callback registry exists"
      - path: "backend/app/api/v1/chat.py"
        issue: "No _on_artifact closure, no artifact_ready event handling, no register_artifact_callback import — product cards only arrive via end-of-workflow on_chain_end path"
    missing:
      - "product_affiliate.py: build early_ui_blocks and include stream_chunk_data in return dict"
      - "plan_executor.py: add module-level register_artifact_callback, clear_artifact_callbacks, get_artifact_callbacks, and _emit_artifact instance method"
      - "chat.py: register _on_artifact callback before graph starts, handle artifact_ready synthetic events in _drain_event_loop, set data_already_streamed=True, clear callbacks on all exit paths"

  - truth: "Blog article tokens stream progressively to the browser as the LLM generates them"
    status: failed
    reason: "product_compose.py calls model_service.generate for blog_article with no stream=True — it is batched in the asyncio.gather alongside other LLM calls. register_token_callback, get_token_callbacks, clear_token_callbacks are absent from plan_executor.py. chat.py has no _on_token callback, no token_ready event handler, and no text_already_streamed flag. The fake-chunking path (24-char chunks with 20ms delay) is the only text delivery mechanism, not true per-token streaming."
    artifacts:
      - path: "backend/mcp_server/tools/product_compose.py"
        issue: "llm_tasks['blog_article'] = model_service.generate(...) at line 682 has no stream=True; it is gathered in the Phase 3 asyncio.gather batch"
      - path: "backend/app/services/plan_executor.py"
        issue: "No register_token_callback, get_token_callbacks, or clear_token_callbacks"
      - path: "backend/app/api/v1/chat.py"
        issue: "No text_already_streamed flag, no _on_token closure, no token_ready event handling; fake-chunking at STREAM_CHUNK_SIZE=24 (line 614) is only text path"
    missing:
      - "plan_executor.py: add register_token_callback, get_token_callbacks, clear_token_callbacks"
      - "product_compose.py: call blog_article generate with stream=True, iterate async generator tokens, forward each to get_token_callbacks()"
      - "chat.py: add text_already_streamed flag, register _on_token callback, handle token_ready events, skip fake-chunking when text_already_streamed is True, clear token callbacks on all exit paths"

  - truth: "Review search and affiliate search run in parallel where data dependencies allow"
    status: failed
    reason: "_create_fast_path_product_plan() at lines 641-648 keeps review_search and product_affiliate as separate sequential steps (review_search at step N+1 alone, product_affiliate at step N+3 alone). The test for RX-05 was weakened from verifying same-step parallelism to merely verifying both tools appear anywhere in the pipeline."
    artifacts:
      - path: "backend/app/agents/planner_agent.py"
        issue: "Lines 641-648: review_search at step N+1 parallel=False; product_affiliate at step N+3 parallel=False; they are sequential, not collocated"
    missing:
      - "planner_agent.py: merge review_search and product_affiliate into {'tools': ['review_search', 'product_affiliate'], 'parallel': True} in _create_fast_path_product_plan"
      - "Update docstring for _create_fast_path_product_plan to reflect merged step"

  - truth: "product_compose eliminates redundant LLM calls — no more than 4 concurrent calls"
    status: failed
    reason: "product_compose.py still schedules both opener (line 510, agent_name='product_opener') and conclusion (line 568, agent_name='product_conclusion') LLM tasks. For a 3-product review query the concurrent call count is: opener + consensus*3 + descriptions + conclusion + blog_article = 7 calls, not <=4. The SUMMARY claimed these were removed; they were not."
    artifacts:
      - path: "backend/mcp_server/tools/product_compose.py"
        issue: "llm_tasks['opener'] scheduled at lines 509-519 when review_bundles is non-empty; llm_tasks['conclusion'] scheduled at lines 567-577 when products_by_provider is non-empty; both are still present and active"
    missing:
      - "product_compose.py: delete the if review_bundles: block that adds llm_tasks['opener']"
      - "product_compose.py: delete the if products_by_provider: block that adds llm_tasks['conclusion']"
      - "product_compose.py: update blog_article system prompt to include warm intro and Our Verdict instructions inline"
      - "product_compose.py: remove _get_result('opener') and _get_result('conclusion') references from Phase 4 assembly (lines 917-951)"
human_verification:
  - test: "Product card timing"
    expected: "Product cards (eBay/Amazon carousel) appear within 5 seconds of pressing Enter on a product query"
    why_human: "Requires running the full stack and measuring wall-clock time in browser"
  - test: "Token-by-token text streaming"
    expected: "Blog narrative words appear progressively as the LLM generates them, not as a single batch dump"
    why_human: "Visual streaming behavior cannot be verified from code alone"
  - test: "Inline affiliate links in blog text"
    expected: "Blog article text contains clickable markdown links (e.g. '[Check price on Amazon](url)')"
    why_human: "Requires inspecting rendered output with real LLM responses"
---

# Phase 01: Response Experience Overhaul Verification Report

**Phase Goal:** Users see product cards within 5 seconds and a streaming blog narrative with buy links — not a 90-second "Thinking..." wall. True token streaming from OpenAI, progressive UI, parallelized backend.
**Verified:** 2026-03-17T22:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Product cards appear within 5 seconds (via stream_chunk_data SSE artifacts) | FAILED | product_affiliate returns no stream_chunk_data; plan_executor has no artifact callback; chat.py has no artifact_ready handler |
| 2 | Blog narrative streams token-by-token — not a batch dump | FAILED | product_compose batches blog_article in asyncio.gather without stream=True; no token callback anywhere; fake-chunking only path |
| 3 | Blog text includes inline affiliate links as clickable markdown | VERIFIED | product_compose lines 620-636 build source_refs; test_blog_includes_source_inline_links passes |
| 4 | Affiliate product searches use asyncio.gather within each provider (not sequential for loop) | VERIFIED | product_affiliate lines 209-213: asyncio.gather over search_single_product coroutines; test passes |
| 5 | review_search queries max 3 products with per-product timeout | VERIFIED | review_search line 121: product_names[:3]; PER_PRODUCT_TIMEOUT_S=8; asyncio.wait_for; test passes |
| 6 | Review search and affiliate search run in parallel | FAILED | _create_fast_path_product_plan() lines 641-648: review_search at step N+1 alone, product_affiliate at step N+3 alone — sequential, not collocated |
| 7 | product_compose eliminates redundant LLM calls (<=4 concurrent) | FAILED | opener (agent_name='product_opener') still scheduled at line 510; conclusion (agent_name='product_conclusion') at line 568; total can reach 7 concurrent calls |
| 8 | No regressions in response quality | UNCERTAIN | Human verification needed; automated tests pass on existing flows |

**Score:** 3/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/mcp_server/tools/product_affiliate.py` | Parallel per-product search; stream_chunk_data in return | PARTIAL | asyncio.gather verified (RX-03 PASS); stream_chunk_data absent (RX-01/RX-08 FAIL) |
| `backend/mcp_server/tools/review_search.py` | 3-product cap, asyncio.wait_for per product | VERIFIED | product_names[:3] at line 121; PER_PRODUCT_TIMEOUT_S=8; asyncio.wait_for at line 139 |
| `backend/app/agents/planner_agent.py` | review_search + product_affiliate in same parallel step | FAILED | Lines 641-648: they remain in separate sequential steps |
| `backend/mcp_server/tools/product_compose.py` | No opener/conclusion calls; source refs in blog_data; stream=True for blog_article | FAILED | opener (line 510) and conclusion (line 568) still present; source_refs VERIFIED; stream=True absent |
| `backend/app/services/plan_executor.py` | register_artifact_callback, register_token_callback, _emit_artifact | FAILED | Only legacy citation callback registry exists; no artifact or token callback infrastructure |
| `backend/app/api/v1/chat.py` | Artifact callback registration, token callback, text_already_streamed, artifact_ready/token_ready handlers | FAILED | None of these exist; only fake-chunking and on_chain_end stream_chunk_data path |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| product_affiliate.py | plan_executor.py | stream_chunk_data triggers _emit_artifact | NOT_WIRED | product_affiliate returns no stream_chunk_data; plan_executor has no _emit_artifact |
| plan_executor.py | chat.py | register_artifact_callback closure puts artifact_ready event in event_queue | NOT_WIRED | register_artifact_callback does not exist in plan_executor.py |
| product_compose.py blog_article call | plan_executor.py token registry | stream=True + token_callback per token | NOT_WIRED | blog_article call has no stream=True; plan_executor has no token registry |
| plan_executor.py | chat.py | register_token_callback closure puts token_ready events in event_queue | NOT_WIRED | register_token_callback does not exist in plan_executor.py |
| planner_agent.py fast-path plan | plan_executor.py | review_search + product_affiliate in same parallel=True step | NOT_WIRED | They are in separate sequential steps (N+1 and N+3) |
| product_compose.py blog_data_parts | blog_article system prompt | source_refs "Reviews: [SiteName](url)" appended to blog_data_parts | WIRED | Lines 620-636: source_refs built and appended; test passes |
| product_affiliate.py asyncio.gather | search_single_product coroutines | per-product gather (not for loop) | WIRED | Lines 209-213: asyncio.gather(*tasks); test passes |

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|------------|--------|----------|
| RX-01 | 01-01, 01-04 | FAILED | product_affiliate returns no stream_chunk_data; artifact callback infrastructure absent |
| RX-02 | 01-01, 01-05 | FAILED | blog_article generate call has no stream=True; token callback infrastructure absent; test was inverted to assert stream is NOT True |
| RX-03 | 01-01, 01-02 | VERIFIED | asyncio.gather in search_provider(); test passes |
| RX-04 | 01-01, 01-02 | VERIFIED | product_names[:3], PER_PRODUCT_TIMEOUT_S=8, asyncio.wait_for; test passes |
| RX-05 | 01-01, 01-02 | FAILED | review_search and product_affiliate remain sequential in fast-path plan; test was weakened to not assert same-step parallelism |
| RX-06 | 01-01, 01-03 | FAILED | opener LLM call at line 510 and conclusion LLM call at line 568 still present |
| RX-07 | 01-01, 01-03 | VERIFIED | source_refs appended to blog_data_parts at lines 620-636; test passes |
| RX-08 | 01-01, 01-04 | FAILED | product_affiliate returns no stream_chunk_data; artifact callback path absent |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/tests/test_chat_streaming.py` | 119 | Test asserts `stream is not True` — inverted from the requirement (RX-02 requires stream=True) | BLOCKER | Test passes but the requirement is NOT met; this hides the gap |
| `backend/tests/test_product_affiliate.py` | 90-110 | Test `test_planner_fast_path_includes_review_and_affiliate` only checks both tools appear, not that they are in the same parallel step | BLOCKER | Test passes but RX-05 requirement (parallel step) is NOT verified |
| `backend/mcp_server/tools/product_compose.py` | 509-519, 567-577 | opener and conclusion LLM tasks still scheduled despite SUMMARY claiming removal | BLOCKER | Concurrent LLM call count remains at 7 (not <=4 as required by RX-06) |

### Human Verification Required

#### 1. Product Card Timing (RX-01, RX-08)

**Test:** Start the full stack, send "best noise cancelling headphones under $300" and start a stopwatch.
**Expected:** Product cards appear within 5 seconds.
**Why human:** Wall-clock timing cannot be verified from code inspection.

#### 2. Token-by-Token Text Streaming (RX-02)

**Test:** After sending a product query, observe whether blog text appears progressively word-by-word or dumps all at once after a delay.
**Expected:** Words appear in real-time as the LLM generates them.
**Why human:** Visual streaming behavior requires a running browser session.

#### 3. Inline Affiliate Links Clickable (RX-07)

**Test:** Look at the rendered blog article and click any product buy link.
**Expected:** Link opens the correct product page in a new tab.
**Why human:** Requires rendered output with real affiliate link data.

### Gaps Summary

Five of eight RX requirements are not met in the current codebase. Three requirements (RX-01, RX-02, RX-08) involve streaming infrastructure that was described in Plans 04 and 05 but is entirely absent from the code — `product_affiliate.py` does not set `stream_chunk_data`, `plan_executor.py` has no artifact or token callback registries, and `chat.py` has none of the corresponding callback registration, synthetic event handling, or `text_already_streamed` logic.

One requirement (RX-05) was partially addressed — both tools appear in the fast-path plan — but the actual merge into a single parallel step was not done. The test was weakened to hide this gap.

One requirement (RX-06) is actively contradicted: the SUMMARY for Plan 03 claims opener and conclusion LLM calls were removed, but both are still present and active in `product_compose.py`. The test for RX-06 (`test_no_opener_call`, `test_no_conclusion_call`) does not appear in the test suite at all — these tests were planned in Plan 01 and referenced in Plan 03, but are absent from `test_product_compose.py`. The only RX-06 coverage is a comment header, not actual test assertions.

Three requirements (RX-03, RX-04, RX-07) are fully implemented and verified with passing tests.

The human reviewer's "approved" in Plan 06 cannot be reconciled with the codebase state: the streaming infrastructure required for RX-01 and RX-02 to produce observable results was not committed, so either the reviewer verified against a local uncommitted state, or the verification was performed without the streaming changes in place.

---

_Verified: 2026-03-17T22:00:00Z_
_Verifier: Claude (gsd-verifier)_
