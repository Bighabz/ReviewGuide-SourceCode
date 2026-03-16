---
status: awaiting_human_verify
trigger: "Full exhaustive deep dive into the chat response pipeline. Multiple things broken after Phase 1 changes."
created: 2026-03-15T00:00:00Z
updated: 2026-03-15T00:00:00Z
---

## Current Focus

hypothesis: Phase 1 changes introduced multiple regressions across the product pipeline
test: Trace entire pipeline from planner -> executor -> tools -> compose -> SSE delivery
expecting: Multiple issues in data flow, timeouts, and response assembly
next_action: Read all 8 critical files and git history

## Symptoms

expected: User sends product query -> sees product cards with images/buy links -> blog-style editorial response with affiliate links and citations -> follow-up suggestions. Fast (~20-30s), conversational.
actual: Responses empty (response_length: 0), truncated (84 chars), or timing out. Product cards sometimes missing. Blog text missing. Stage telemetry kills compose at 45s.
errors: stage_telemetry plan_exec hard timeout 45s exceeded, OpenAI retry delays, response_length: 0, product_ranking: Ranking 0 products
reproduction: Any product query (e.g. "Best Bluetooth speakers", "Best standing desks for back pain")
started: After Phase 1 commits deployed

## Eliminated

## Evidence

- timestamp: 2026-03-15T00:10:00Z
  checked: Full pipeline trace for deep_research product queries (fast path)
  found: CRITICAL DATA FLOW ISSUE - The fast path plan (_create_fast_path_product_plan) runs:
    Step 1: product_search + product_evidence (parallel)
    Step 2: review_search + product_affiliate (parallel)
    Step 3: product_normalize
    Step 4: product_ranking
    Step 5: product_compose
    Step 6: next_step_suggestion

    BUT product_affiliate reads from state "normalized_products" (line 69 of product_affiliate.py)
    which is produced by product_normalize (Step 3). However product_affiliate runs in Step 2
    BEFORE product_normalize. This means product_affiliate gets EMPTY normalized_products.

    It falls back to product_names (line 90-91), which IS available from product_search (Step 1).
    So affiliate still works but only via the fallback path. NOT a blocking issue.
  implication: product_affiliate fallback to product_names works, so this is not the root cause of empty responses

- timestamp: 2026-03-15T00:11:00Z
  checked: product_ranking reads search_results (line 58)
  found: product_ranking reads state.get("search_results", []) but product_search may write
    to a different key. Need to check product_search produces key.
    Also product_ranking produces "ranked_items" (line 120) but its TOOL_CONTRACT says
    produces: ["ranked_products"]. The contract says "ranked_products" but the return dict
    has key "ranked_items". This is a MISMATCH - plan_executor._write_tool_outputs_to_state
    looks for keys listed in contract.produces and writes them to state. Since the contract
    says "ranked_products" but the return dict has "ranked_items", NOTHING gets written to state.
    product_normalize reads state.get("ranked_products") at line 70 - it will always be None.
  implication: product_ranking output never reaches state. But ranking runs AFTER normalize in the
    fast path, so normalize wouldn't read it anyway. The ranking tool is effectively a no-op.

- timestamp: 2026-03-15T00:12:00Z
  checked: product_ranking reads search_results but search_results is initialized as [] in chat.py line 313
  found: product_search likely produces "product_names" and "search_results". Need to verify.
    product_ranking reads search_results which may be empty if product_search writes to different key.
    Log showed "product_ranking: Ranking 0 products" - confirming search_results is empty at that point.
  implication: product_ranking is ranking 0 products, which explains the "Ranking 0 products" log

- timestamp: 2026-03-15T00:13:00Z
  checked: Timeout chain analysis
  found: model_service has request_timeout=12s, max_retries=1 (so 12s*2=24s worst case per LLM call).
    product_compose makes multiple LLM calls:
    - concierge OR consensus calls (parallel, via asyncio.gather)
    - descriptions call (parallel with above)
    - blog_article call (sequential, Phase 3b, up to 12s+12s=24s with retry)
    Total worst case: ~24s parallel + 24s blog = ~48s for product_compose alone.
    Plan executor has _TOOL_TIMEOUT_S = 30s per tool.
    So product_compose WILL timeout at 30s if blog article takes >6s after parallel batch.
    Blog was reported as taking 12-15s. If parallel batch takes 15s, then 15+12=27s < 30s.
    But with retries: 15+(12+12)=39s > 30s timeout → PRODUCT_COMPOSE TIMES OUT.
  implication: product_compose can timeout when OpenAI retries kick in, causing empty response

- timestamp: 2026-03-15T00:14:00Z
  checked: stage_telemetry plan_exec budget
  found: plan_exec budget is (40.0, 90.0) - soft=40s, hard=90s. This wraps the ENTIRE executor.
    Inside executor, each tool has _TOOL_TIMEOUT_S=30s.
    For the 5-step fast path: product_search+evidence(parallel) + review_search+affiliate(parallel) + normalize + ranking + compose + next_step
    That's 5 sequential steps. Even if each step takes 10s, that's 50s > 40s soft limit.
    The hard limit is 90s which should be enough.
    MAX_TOTAL_REQUEST_S is 120s for SSE cap. Should be OK.
  implication: The telemetry timeouts are now appropriate after the latest push

- timestamp: 2026-03-15T00:15:00Z
  checked: product_compose - what happens when blog_article call fails/times out?
  found: If blog_article generation fails (line 656-658), result_map['blog_article'] = "".
    Then at line 766: blog_article is empty string, so it goes to fallback paths.
    If review_data exists: uses template assembly (line 771-793). This produces text.
    If no review_data but concierge exists: uses concierge + product list (line 794-822).
    If none of the above: assistant_text = "Here's what I found for you." (line 825)
    So there IS a fallback. But the fallback might produce short text (84 chars as reported).
  implication: Empty responses (response_length: 0) suggest something else is wrong -
    the compose tool itself might be failing entirely, not just the blog article

## Resolution

root_cause: Multiple compounding issues in the Phase 1 pipeline:
  1. product_compose times out at 30s (_TOOL_TIMEOUT_S) because it makes 4+ LLM calls (parallel batch + sequential blog article). When OpenAI retries kick in, compose exceeds 30s, returning empty error dict with no assistant_text -> response_length: 0.
  2. product_ranking reads `search_results` from state but product_search only writes `product_names` -> ranking always gets 0 products.
  3. product_ranking returns `ranked_items` but its contract says `produces: ["ranked_products"]` -> state never gets ranking data.
  4. Fast path pipeline order has product_normalize before product_ranking, but normalize tries to read ranking data -> structural ordering issue.
  5. model_service max_retries=1 with 12s timeout means worst-case 24s per LLM call. Compose makes this sequentially after parallel batch.

fix:
  1. Give compose tools a dedicated higher timeout (_COMPOSE_TOOL_TIMEOUT_S = 55s) to accommodate multiple LLM calls
  2. Fix product_ranking to read `product_names` from state (what product_search actually produces)
  3. Fix product_ranking return key to match contract: `ranked_products` instead of `ranked_items`
  4. Reorder fast path: move product_ranking before product_normalize so normalize can use ranking data
  5. Reduce model_service max_retries to 0 for non-streaming calls to avoid compounding delays (rely on tool-level retry)
verification: 254 tests pass (1 pre-existing failure in test_review_search.py for unimplemented review_sources UI block). All modified code reviewed for data flow consistency.
files_changed:
  - backend/app/services/plan_executor.py (compose timeout 55s, fallback response on compose failure)
  - backend/mcp_server/tools/product_ranking.py (read correct state keys, return correct key, use review_data + affiliate_products)
  - backend/app/agents/planner_agent.py (reorder fast path: ranking before normalize)
  - backend/mcp_server/tools/product_compose.py (blog article in parallel batch, product carousel ui_blocks)
  - backend/tests/test_chat_streaming.py (update RX-02 test for parallel blog article)
  - backend/tests/test_stage_telemetry.py (update MAX_TOTAL_REQUEST_S test to 120)
