# Sub-3s Response Architecture Design

**Date:** 2026-03-25
**Status:** Approved
**Author:** habib + Claude

## Problem Statement

Current pipeline executes 7 sequential LLM calls before the user sees any content. Measured 15-35s to first visible content. The target is **<3s to first product cards** and **<4s to live typing**.

## Architecture Overview

### Current Flow (Serial, 15-35s)

```
Safety(LLM) -> Intent(LLM) -> Planner(LLM) -> Clarifier(LLM) -> RoutingGate -> PlanExecutor:
  product_search -> evidence -> ranking -> normalize -> affiliate -> compose(LLM) -> suggestions
```

7 LLM round-trips, all serial. Minimum ~15s before first content.

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
| 2 | Embedding similarity against intent exemplars | <50ms | ~25% of queries |
| 3 | Haiku 4.5 single LLM call (intent + slots combined) | ~300ms | ~15% of queries |

**Hardcoded tool chains (eliminates Planner LLM entirely):**

```python
TOOL_CHAINS = {
    "product":    ["product_search", "review_search", "product_affiliate", "product_compose"],
    "comparison": ["product_search", "product_affiliate", "product_comparison"],
    "travel":     ["travel_search_hotels", "travel_search_flights", "travel_itinerary", "travel_compose"],
    "general":    ["general_search", "general_compose"],
    "intro":      ["intro_compose"],
    "unclear":    ["unclear_compose"],
}
```

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
        return blocked_response()

    if router_result.intent in ("product", "comparison"):
        # Speculative search is valid -- await it
        search_results = await search_task
    else:
        # Wrong guess -- cancel and run correct chain
        search_task.cancel()
        search_results = None

    return router_result, search_results
```

**Hit rate:** ~70-80% of queries are product intent (the app's primary use case). Wasted cost of a cancelled Perplexity call: ~$0.001. Acceptable trade-off for 2-3s savings.

### 3. Parallel Tool Executor

**Refactor:** `backend/app/services/plan_executor.py`

**Current sequential chain:**
```
search -> evidence -> ranking -> normalize -> affiliate -> compose
```

**New parallel waves:**
```
Wave 1 (parallel):  product_search + review_search
Wave 2 (parallel):  product_affiliate + product_normalize
Wave 3:             product_compose (needs affiliate + review + normalize)
```

Key changes:
- `review_search` moves to Wave 1 (parallel with product_search). It only needs product names, extractable from the raw query or search results as they arrive.
- `product_compose` starts as soon as it has products + affiliate links. Review citations can be injected as a late-binding step.
- Product cards stream to frontend after Wave 1 completes (before affiliate/compose).

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

**New:** 3 nodes, simple linear flow

```python
def build_workflow():
    graph = StateGraph(GraphState)

    # Node 1: Parallel router + speculative search + safety
    graph.add_node("fast_dispatch", fast_dispatch_node)

    # Node 2: Parallel tool execution with streaming
    graph.add_node("execute_tools", execute_tools_node)

    # Node 3: Compose + stream response
    graph.add_node("compose_stream", compose_stream_node)

    graph.set_entry_point("fast_dispatch")
    graph.add_edge("fast_dispatch", "execute_tools")
    graph.add_edge("execute_tools", "compose_stream")
    graph.add_edge("compose_stream", END)

    return graph.compile()
```

**Node responsibilities:**

**`fast_dispatch`:** Runs fast_router + safety + speculative_search in parallel via `asyncio.gather`. Sets intent, slots, tool_chain on state. If safety blocks, short-circuits to END. If speculative search hit, attaches results to state.

**`execute_tools`:** Runs remaining tools in maximum-parallelism waves. Streams product card artifacts as soon as search results are available. Runs affiliate + review in parallel. Handles tiered escalation logic internally (try free providers first, escalate if insufficient).

**`compose_stream`:** Calls Haiku 4.5 with streaming. Tokens flow directly to SSE as they generate. No batching, no artificial delays.

**Halt/resume preserved:** If travel intent needs dates, `fast_dispatch` sets `status=halted` with clarification questions + suggestion chips. Resume path skips straight to `execute_tools`.

### 7. Frontend Changes

Minimal changes needed:

1. **Handle `cards_update` artifact event:** Merge updated affiliate links into existing product cards (new SSE event type)
2. **Remove artificial typing delay:** Backend streams at natural speed; frontend appends tokens as they arrive
3. **Show skeleton cards:** Display product cards immediately without affiliate links -- show "Finding best price..." placeholder on buy button until `cards_update` arrives

### 8. What We Keep (Unchanged)

- **GraphState schema** -- same TypedDict, same fields, same accumulator pattern
- **MCP tool functions** -- all 20 tools unchanged internally, just called differently
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

**Safety agent stays** but becomes a fast async function, not a LangGraph node.

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

Delete dead agent files. Rewrite LangGraph to 3-node graph. Update all tests. Remove TOON format, tool contracts system.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Speculative search waste (wrong intent) | 20-30% | Low ($0.001/query) | Cancel early; cost is negligible |
| Fast router misclassifies intent | 5-10% initially | Medium | Haiku Tier 3 fallback catches it. Log misclassifications, improve rules over time |
| Haiku compose quality lower than GPT-4o-mini | Low | Medium | A/B test with 20 sample queries before full migration |
| Skipping clarifier degrades results | Medium | Low | Broad search is better than 4s delay. User can refine via follow-up |
| Breaking halt/resume flow | Medium | High | Preserve exact same Redis halt state format. Dedicated test suite for multi-turn |
| LangChain to Anthropic SDK migration | Low | Low | Well-documented. langchain-anthropic package exists |

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time to first product cards | ~15s | <3s |
| Time to first streaming text | ~20s | <4s |
| Full response complete | ~35s | <8s |
| LLM calls per product query | 7 | 1-2 |
| Cost per query | ~$0.01-0.02 | ~$0.005-0.01 |
| Intent classification accuracy | ~95% (LLM) | >93% (deterministic + Haiku fallback) |
