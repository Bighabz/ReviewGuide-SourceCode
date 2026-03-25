# Sub-3s Response Architecture Design

**Date:** 2026-03-25
**Status:** Approved
**Author:** habib + Claude

## Problem Statement

Current pipeline executes 4 sequential LLM generation calls (Intent, Planner, Clarifier, Compose) plus the OpenAI Moderation API and sequential tool API calls before the user sees any content. Measured 15-35s to first visible content. The target is **<3s to first product cards** and **<4s to live typing**.

## Architecture Overview

### Current Flow (Serial, 15-35s)

```
Safety(API) -> Intent(LLM) -> Planner(LLM) -> Clarifier(LLM) -> RoutingGate -> PlanExecutor:
  product_search -> product_evidence -> product_ranking -> product_normalize -> product_affiliate -> product_compose(LLM) -> suggestions
```

4 serial LLM calls + 1 API call + 6 sequential tool steps. Minimum ~15s before first content.

### New Flow (Parallel + Speculative, <3s)

```
T=0ms    USER SENDS QUERY
         +-- [A] speculative_search(raw_query)      <- fires immediately, no classification
         +-- [B] fast_router(query)                  <- deterministic rules, Haiku fallback (<300ms)
         +-- [C] safety_check(query)                 <- OpenAI Moderation API (fire-and-forget)

T=300ms  fast_router resolves intent + slots
         safety_check resolves (non-blocking, 99% pass)
         merge_gate confirms speculative search is valid

T=2-3s   product_search results arrive
         +-- STREAM PRODUCT CARDS -> frontend (artifact SSE)
         +-- [D] product_affiliate(products)          <- parallel
         +-- [E] review_search(product_names)         <- parallel

T=2.5s   USER SEES PRODUCT CARDS (target: <3s)

T=3-4s   affiliate + review data arrive
         +-- [F] compose_stream(all_data)             <- Haiku 4.5 streaming

T=3.5s   USER SEES LIVE TYPING (blog narrative streaming token-by-token)

T=6-8s   Full response complete: blog text, affiliate links, citations, follow-up chips
```

## Component Design

### 1. Fast Router

**Replaces:** Safety Agent, Intent Agent, Planner Agent, Clarifier Agent (4 serial LLM nodes).

**New file:** `backend/app/services/fast_router.py`

**Interface:**
```python
async def fast_router(
    query: str,
    conversation_history: list,
    last_search_context: dict | None
) -> FastRouterResult:
    """
    Returns:
        intent: str (product/comparison/travel/general/intro/unclear)
        slots: dict (category, brand, budget, destination, dates, etc.)
        tool_chain: list[str] (hardcoded per intent)
        needs_clarification: bool
        confidence: float
    """
```

**Tiered classification:**

| Tier | Method | Latency | Coverage |
|------|--------|---------|----------|
| 1 | Keyword + regex rules | <5ms | ~60% of queries |
| 2 | Haiku 4.5 single LLM call (intent + slots combined) | ~300ms | ~40% of queries |

Note: Embedding similarity (Tier 2 in earlier drafts) was removed. Local embedding models add memory footprint and complexity; API-based embeddings add 100-300ms latency which negates the benefit vs just calling Haiku directly. Two tiers (deterministic + Haiku fallback) is simpler and sufficient.

**Hardcoded tool chains (eliminates Planner LLM entirely):**

```python
TOOL_CHAINS = {
    "product":    ["product_search", "product_normalize", "review_search", "product_affiliate", "product_compose"],
    "comparison": ["product_search", "product_normalize", "product_affiliate", "product_comparison"],
    "service":    ["product_search", "product_normalize", "product_affiliate", "product_compose"],
    "travel":     ["travel_search_hotels", "travel_search_flights", "travel_itinerary", "travel_compose"],
    "general":    ["general_search", "general_compose"],
    "intro":      ["intro_compose"],
    "unclear":    ["unclear_compose"],
}
```

**Dropped tools:**
- `product_evidence` -- absorbed into product_compose (evidence extraction happens inline during compose, not as a separate LLM call)
- `product_ranking` -- absorbed into product_normalize (ranking by quality_score applied during normalization, not as a separate step)

These tools are not deleted from the codebase in Phase A-C (backward compatibility). They are removed in Phase D cleanup after validation.

**Slot extraction:** Regex-first for common patterns:
- Budget: `/under\s*\$?(\d+)/`, `/\$(\d+)\s*-\s*\$(\d+)/`, `/budget.*?(\d+)/`
- Category: Match against known category list from categoryConfig
- Brand: Match against known brand list
- Travel: destination, dates, duration patterns
- Haiku fallback for complex multi-slot extraction only

**Clarification strategy:**
- **First message:** Never clarify. Execute with whatever slots we have. Missing budget? Search without it. Missing brand? Search broadly. Broad results are better than a 4s delay asking "what brand?"
- **Follow-up messages:** If results were poor AND we can identify why (too broad), clarify via suggestion chips (Phase 8)
- **Travel only:** Clarify dates if completely missing (cannot search flights without dates)

### 2. Speculative Execution Engine

**New file:** `backend/app/services/speculative_executor.py`

**What it does:** Starts the most likely tool (product_search) before intent classification completes. Discards results if intent was wrong.

```python
async def execute_speculative(query: str, session_id: str):
    search_task = asyncio.create_task(speculative_search(query))
    router_task = asyncio.create_task(fast_router(query, history))
    safety_task = asyncio.create_task(safety_check(query))

    router_result, safety_result = await asyncio.gather(router_task, safety_task)

    if safety_result.blocked:
        search_task.cancel()
        # Suppress CancelledError -- task may have completed between cancel() and await
        with contextlib.suppress(asyncio.CancelledError):
            await search_task
        return blocked_response()

    if router_result.intent in ("product", "comparison", "service"):
        # Speculative search is valid -- await with timeout
        try:
            search_results = await asyncio.wait_for(search_task, timeout=10.0)
        except asyncio.TimeoutError:
            search_results = None  # proceed without, will re-search in execute_tools
    else:
        # Wrong guess -- cancel and cleanup
        search_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await search_task  # ensure task is fully cleaned up, httpx connection released
        search_results = None

    return router_result, search_results
```

**Cancellation safety:** `asyncio.Task.cancel()` is not immediate -- it raises `CancelledError` at the next `await` inside the task. We must `await` the cancelled task (suppressing the error) to ensure the httpx HTTP connection is properly released. A 10s timeout on the speculative await prevents hanging if the search provider is slow.

**Hit rate:** ~70-80% of queries are product/comparison/service intent. Wasted cost of a cancelled Perplexity call: ~$0.001. Acceptable trade-off for 2-3s savings. Monitor Perplexity API rate limits -- speculative execution increases call volume by ~20-30%.

### 3. Parallel Tool Executor

**Refactor:** `backend/app/services/plan_executor.py`

**Current sequential chain:**
```
search -> evidence -> ranking -> normalize -> affiliate -> compose
```

**New parallel waves:**
```
Wave 1:             product_search (or use speculative result if available)
                    -> STREAM SKELETON CARDS to frontend
Wave 2 (parallel):  product_normalize + review_search (both need product_search output)
Wave 3 (parallel):  product_affiliate (needs normalized_products)
                    -> STREAM ENRICHED CARDS with affiliate links
Wave 4:             product_compose (needs affiliate + review + normalize)
                    -> STREAM blog text token-by-token
```

Key changes:
- `review_search` runs in Wave 2 (parallel with product_normalize). It needs `product_names` which are produced by `product_search` in Wave 1 -- it CANNOT run in parallel with product_search.
- Skeleton product cards stream to frontend immediately after Wave 1 (product name, image, price -- no affiliate links yet).
- Enriched cards with affiliate links stream after Wave 3.
- `product_compose` starts as soon as it has all data from Waves 2-3. Review citations are included in the compose prompt, not late-bound.
- `product_evidence` and `product_ranking` are absorbed into product_normalize and product_compose respectively (see Dropped Tools above).

### 4. Model Migration: GPT-4o-mini to Claude Haiku 4.5

| Component | Current | New | Reason |
|-----------|---------|-----|--------|
| Intent classification | GPT-4o-mini via LangChain | Deterministic + Haiku fallback | Eliminate LLM call for 85% of queries |
| Slot extraction | GPT-4o-mini via LangChain | Regex + Haiku fallback | Same |
| Planner | GPT-4o-mini via LangChain | Hardcoded tool chains | Eliminated entirely |
| Clarifier | GPT-4o-mini via LangChain | Deferred / regex | Eliminated for first message |
| product_compose | GPT-4o-mini via LangChain | Haiku 4.5 streaming | Better TTFT, native streaming |
| travel_compose | GPT-4o-mini via LangChain | Haiku 4.5 streaming | Same |
| general_compose | GPT-4o-mini via LangChain | Haiku 4.5 streaming | Same |
| Safety | OpenAI Moderation API | Keep as-is | API call, not LLM generation |

**LangChain migration:**
- Replace `ChatOpenAI` with `ChatAnthropic` in `ModelService`
- Update system prompt format (Anthropic uses `system` parameter, not system message)
- Switch from `json_mode` to Haiku's native JSON output
- Update streaming to use Anthropic's `stream()` API

**New config settings:**
```python
ANTHROPIC_API_KEY: str = ""
COMPOSE_MODEL: str = "claude-haiku-4-5-20251001"
ROUTER_MODEL: str = "claude-haiku-4-5-20251001"  # Tier 3 ambiguous queries only
```

### 5. Streaming Architecture Overhaul

**Problems with current streaming:**
- Text chunked into 24-char pieces with artificial 20ms delays
- Product cards only stream AFTER compose is done
- No streaming during tool execution

**New streaming events:**

| Event | When | Content |
|-------|------|---------|
| `status` | T=0ms | "Searching..." |
| `status` | T=300ms | "Found {intent}, searching products..." |
| `artifact` (cards) | T=2-3s | Product cards with images, prices (skeleton -- no affiliate links yet) |
| `artifact` (cards_update) | T=3-4s | Updated cards with affiliate links injected |
| `content` (streaming) | T=3-4s | Blog narrative tokens streaming live from Haiku |
| `artifact` (citations) | T=5-6s | Review source citations |
| `done` | T=6-8s | Final payload with everything |

**Two-phase card streaming:**
1. **Skeleton cards** at T=2-3s: product name, image, price from search results
2. **Enriched cards** at T=3-4s: affiliate links, review scores, buy buttons added

**Remove artificial delays:**
- Kill the 24-char chunking + 20ms delay in `generate_chat_stream()`
- Stream Haiku tokens directly as they arrive (real TTFT ~200-400ms)
- Frontend already handles SSE `content` events -- just send tokens faster

### 6. LangGraph Workflow Rewrite

**Current:** 7 nodes, complex conditional routing

**New:** 3 nodes with conditional routing for halt/resume/error

```python
def build_workflow():
    graph = StateGraph(GraphState)

    graph.add_node("fast_dispatch", fast_dispatch_node)
    graph.add_node("execute_tools", execute_tools_node)
    graph.add_node("compose_stream", compose_stream_node)

    graph.set_entry_point("fast_dispatch")

    # Conditional routing from fast_dispatch
    graph.add_conditional_edges("fast_dispatch", route_after_dispatch, {
        "execute":  "execute_tools",   # normal flow
        "halt":     END,               # safety blocked or clarification needed (travel dates)
        "error":    END,               # fatal error
    })

    # Conditional routing from execute_tools
    graph.add_conditional_edges("execute_tools", route_after_tools, {
        "compose":  "compose_stream",  # normal flow
        "halt":     END,               # consent required (tiered escalation)
        "error":    END,               # all tools failed
    })

    graph.add_edge("compose_stream", END)

    return graph.compile()
```

**Routing functions:**
```python
def route_after_dispatch(state: GraphState) -> str:
    if state.get("status") == "blocked":
        return "error"
    if state.get("halt"):
        return "halt"  # travel needs dates, or safety flagged
    return "execute"

def route_after_tools(state: GraphState) -> str:
    if state.get("halt"):
        return "halt"  # consent required for tier 3-4
    if not state.get("normalized_products") and not state.get("search_results"):
        return "error"  # all tools failed
    return "compose"
```

**Node responsibilities:**

**`fast_dispatch`:** Runs fast_router + safety + speculative_search in parallel via `asyncio.gather`. Sets intent, slots, tool_chain on state. If safety blocks, sets `status=blocked` -> routes to END. If speculative search hit, attaches results to state. For halt resume (existing halt_state in Redis), restores intent/slots and routes directly to `execute_tools`.

**`execute_tools`:** Runs remaining tools in maximum-parallelism waves. Streams skeleton product cards as soon as search results are available. Runs normalize + review_search in parallel (Wave 2), then affiliate (Wave 3). Handles tiered escalation logic internally. If consent required, sets `halt=True` -> routes to END.

**`compose_stream`:** Calls Haiku 4.5 with streaming. Tokens flow directly to SSE as they generate. No batching, no artificial delays.

**Halt/resume paths:**
- **Travel clarification:** `fast_dispatch` detects missing required dates -> sets `halt=True`, `followups` with question + chips -> END. Resume: safety node loads halt state, skips to `execute_tools`.
- **Consent flow:** `execute_tools` hits tier 3-4 -> sets `halt=True`, `consent_prompt` -> END. Resume: `fast_dispatch` detects `extended_search_confirmed=True`, routes to `execute_tools` with partial results restored.
- **Safety block:** `fast_dispatch` sets `status=blocked` -> END. No resume.

### 7. Frontend Changes

Changes needed:

1. **Handle `cards_update` artifact event:** When a `cards_update` artifact arrives, match each card by `product_id` (stable identifier from product_search) and patch the `affiliate_link`, `review_score`, and `buy_url` fields onto the existing card component state. If a card cannot be matched (product_id missing), replace the entire card list. This requires product cards to be stored in React state (not just rendered from props) so they can be updated in-place.

2. **Skeleton card buy button:** Before `cards_update` arrives, display the buy button as a muted "Finding best price..." text in `var(--text-muted)`. On `cards_update`, replace with the live affiliate link and active button styling.

3. **Remove artificial typing delay:** Kill the 20ms-per-chunk delay in ChatContainer SSE handler. Backend streams Haiku tokens at natural speed; frontend appends each `content` event token immediately.

4. **Handle race conditions:** If the user scrolls, clicks a product card, or sends a follow-up message while `cards_update` hasn't arrived yet, the skeleton card must not crash. Buy button click on skeleton card should either be disabled or navigate to the Amazon search fallback URL (existing pattern in InlineProductCard.tsx).

### 8. What We Keep (Unchanged)

- **GraphState schema** -- same TypedDict, same fields, same accumulator pattern. Note: `stage_telemetry` will report new stage names ("fast_dispatch", "execute_tools", "compose_stream" instead of "safety", "intent", "planner", "clarifier"). Admin dashboards parsing stage_telemetry must be updated.
- **MCP tool functions** -- all tool functions unchanged internally, just called in different order
- **Affiliate provider system** -- AffiliateProviderRegistry, all providers, loader, manager
- **Redis caching** -- halt state, search cache, chat history
- **SSE event format** -- same event types plus one new `cards_update` type
- **Frontend Message.tsx / BlockRegistry** -- protected, unchanged
- **Tiered routing logic** -- preserved, runs inside execute_tools
- **PostgreSQL models** -- all models unchanged
- **Auth / rate limiting** -- unchanged

### 9. What We Delete

| File | Replaced By |
|------|-------------|
| `backend/app/agents/intent_agent.py` | fast_router deterministic rules |
| `backend/app/agents/planner_agent.py` | hardcoded TOOL_CHAINS |
| `backend/app/agents/clarifier_agent.py` | regex slot extraction + deferred clarification |
| `backend/app/agents/query_complexity.py` | no longer needed |
| `backend/app/services/langgraph/nodes/routing_gate.py` | absorbed into fast_dispatch |
| `backend/app/services/langgraph/nodes/tiered_executor.py` | absorbed into execute_tools |
| `backend/mcp_server/tool_contracts.py` | hardcoded chains, no TOON prompt needed |

**Safety agent stays** but becomes a fast async function called within `fast_dispatch`, not a standalone LangGraph node.

**Absorbed tools (not deleted, logic merged):**

| Tool | Absorbed Into | What Happens |
|------|--------------|--------------|
| `product_evidence` | `product_compose` | Evidence extraction happens inline during compose prompt construction |
| `product_ranking` | `product_normalize` | Quality-score ranking applied during normalization step |

These tool files remain in the codebase through Phases A-C for backward compatibility. Deleted in Phase D after validation.

## Observability Migration

**Langfuse tracing:** The current system uses `langfuse-langchain` `CallbackHandler` passed to `graph.astream_events()`. When compose tools migrate from LangChain `ChatOpenAI` to Anthropic SDK:
- Option A: Use `langchain-anthropic` `ChatAnthropic` wrapper to maintain LangChain callback compatibility
- Option B: Use Langfuse's native `@observe` decorator on the compose functions directly

**Recommendation:** Option A for Phase C (less migration work), migrate to Option B in Phase D (cleaner, no LangChain dependency for Anthropic calls).

## Migration Strategy

### Phase A: Fast Router + Eliminate LLM Calls

Biggest win, lowest risk. Build fast_router with deterministic rules. Hardcode tool chains. Keep existing LangGraph but bypass intent/planner/clarifier for product queries via a feature flag.

**Expected improvement: 15s -> 5-8s**

### Phase B: Speculative Execution + Parallel Tools

Add speculative search. Restructure tool execution into parallel waves. Stream product cards early (skeleton cards before affiliate links).

**Expected improvement: 5-8s -> 3-4s**

### Phase C: Haiku Migration + Streaming Overhaul

Swap ModelService from OpenAI to Anthropic. Remove artificial 20ms streaming delays. Native Haiku token streaming for compose tools.

**Expected improvement: 3-4s -> 2-3s to first content**

### Phase D: Cleanup + New Workflow

Delete dead agent files. Rewrite LangGraph to 3-node graph. Update all tests. Remove TOON format, tool contracts system. Delete absorbed tool files (product_evidence, product_ranking).

### Rollback Strategy

Each phase is additive and feature-flagged:
- **Phase A:** `USE_FAST_ROUTER=true/false` in config. When false, falls back to existing intent/planner/clarifier agents. Old workflow code is NOT deleted until Phase D.
- **Phase B:** `USE_SPECULATIVE_SEARCH=true/false`. When false, product_search runs after fast_router completes (still faster than before, just not speculative).
- **Phase C:** `USE_ANTHROPIC_COMPOSE=true/false`. When false, compose tools use existing GPT-4o-mini via LangChain. Both API keys configured during transition.
- **Phase D (one-way door):** Old agent files deleted. Only execute after Phases A-C are validated in production for at least 1 week. Git revert is the rollback.

### Test Strategy

**Phase A tests:**
- Fast router accuracy: 100+ labeled queries (from production logs) classified by new router vs old IntentAgent. Target: >93% agreement.
- Hardcoded tool chain regression: Run existing test suite with new chains. All product/travel/general flows must produce equivalent output.
- Latency measurement: stage_telemetry comparison before/after for 50 real queries.

**Phase B tests:**
- Speculative hit rate: Log speculative search outcomes (hit/miss/cancel) for 1 week. Target: >70% hit rate.
- Cancellation safety: Unit tests for task cancel + await cleanup. Verify no httpx connection leaks.
- Skeleton card rendering: Frontend integration test -- cards render without affiliate data, update correctly on cards_update event.

**Phase C tests:**
- Compose quality A/B: 20 sample queries run through both GPT-4o-mini and Haiku 4.5. Human review for quality parity.
- Streaming latency: Measure TTFT (time to first token) for Haiku compose vs GPT-4o-mini compose. Target: <400ms TTFT.
- Langfuse traces: Verify all LLM calls appear in Langfuse after migration.

**Phase D tests:**
- Full regression suite. All existing tests pass with new 3-node workflow.
- Multi-turn halt/resume: Dedicated test suite for travel clarification and consent flows.
- Load test: 10 concurrent requests to verify no cross-session state leaks.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Speculative search waste (wrong intent) | 20-30% | Low ($0.001/query) | Cancel early; cost is negligible |
| Fast router misclassifies intent | 5-10% initially | Medium | Haiku Tier 3 fallback catches it. Log misclassifications, improve rules over time |
| Haiku compose quality lower than GPT-4o-mini | Low | Medium | A/B test with 20 sample queries before full migration |
| Skipping clarifier degrades results | Medium | Low | Broad search is better than 4s delay. User can refine via follow-up |
| Breaking halt/resume flow | Medium | High | Preserve exact same Redis halt state format. Dedicated test suite for multi-turn |
| LangChain to Anthropic SDK migration | Low | Low | Well-documented. langchain-anthropic package exists |
| Multi-turn context regression | Medium | High | Fast router handles ALL context that 4 agents previously processed. Test with 20+ multi-turn conversations. Log and review misrouted follow-ups. |
| Perplexity rate limits under speculative execution | Low | Medium | 20-30% more API calls. Monitor rate limit headers. Add backoff if approaching limits. |
| Cold start latency on first request after deploy | Low | Medium | Pre-warm regex patterns and Anthropic SDK client at startup. First request may be 1-2s slower than steady state. |
| Dual-provider cost during migration | Low | Low | Both OpenAI and Anthropic billed during Phases A-C. Net cost still lower due to fewer LLM calls. |

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time to first product cards | ~15s | <3s |
| Time to first streaming text | ~20s | <4s |
| Full response complete | ~35s | <8s |
| LLM calls per product query | 4 (+ 1 moderation API) | 1-2 (compose + optional router fallback) |
| Cost per query | ~$0.01-0.02 | ~$0.005-0.01 |
| Intent classification accuracy | ~95% (LLM) | >93% (deterministic + Haiku fallback) |
