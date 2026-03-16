# Phase 1: Response Experience Overhaul - Research

**Researched:** 2026-03-15
**Domain:** FastAPI SSE streaming, OpenAI token streaming, asyncio parallelism, LangGraph mid-workflow artifact emission
**Confidence:** HIGH (all findings verified directly against the codebase)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RX-01 | First visible content (product cards) appears within 5 seconds | stream_chunk_data mechanism already works; need product_affiliate to fire early and emit via stream_chunk_data before product_compose |
| RX-02 | Blog narrative streams token-by-token from OpenAI (not batch-then-chunk) | model_service._stream_response() exists and works; product_compose must call generate(stream=True) and yield tokens through state via stream_chunk_data |
| RX-03 | Affiliate product searches parallelized within each provider (asyncio.gather) | ALREADY DONE — search_provider() already uses asyncio.gather across providers; per-product search within each provider is the sequential for loop at lines 117-118 of product_affiliate.py |
| RX-04 | Review search limited to top 3 products (down from 5) with per-product timeout | review_search.py line 120: `products_to_search = product_names[:5]` — change to [:3]; no per-product timeout exists yet |
| RX-05 | Review search and affiliate search run in parallel where data dependencies allow | plan_executor supports parallel steps via parallel:true flag; planner must put review_search and product_affiliate in same step |
| RX-06 | product_compose eliminates redundant LLM calls (combine where possible) | MAX_CONSENSUS_PRODUCTS already caps LLM consensus at 3; blog_article call is the primary cost; opener + descriptions + conclusion are additive; inline streaming eliminates the wait entirely |
| RX-07 | Blog-style response includes inline affiliate buy links as markdown | Already in system prompt: "Include the price and a markdown link: [Check price on Merchant →](url)" — need to verify URLs reach the LLM context |
| RX-08 | Product cards render above blog narrative, arriving progressively via stream_chunk_data | stream_chunk_data mechanism exists; product_affiliate must call self.state["stream_chunk_data"] after fetching offers, before product_compose runs |
</phase_requirements>

---

## Summary

The 90-second "Thinking..." wall is caused by two distinct problems, not one. First, `product_compose` calls `model_service.generate()` without streaming — it waits for the full blog article completion (up to 800 tokens at 12s timeout × possible retry = 24s) before returning ANY text. Second, product cards are only sent to the frontend after `product_compose` finishes building `ui_blocks`, which is after all LLM calls complete. The entire response — both text and cards — arrives as one batch at the end of the workflow.

The fix architecture has three independent tracks that can be worked in parallel: (1) make `product_affiliate` emit product cards via `stream_chunk_data` immediately after fetching offers — this satisfies RX-01 and RX-08 without touching any LLM code; (2) make `product_compose`'s blog_article call use `stream=True` and pipe tokens through SSE via the content event channel — this satisfies RX-02; (3) parallelise review_search + product_affiliate at the plan step level and reduce review_search's product cap from 5 to 3 — this satisfies RX-03, RX-04, RX-05. RX-06 (eliminate redundant LLM calls) and RX-07 (inline affiliate buy links) are refinements within `product_compose`.

**Primary recommendation:** Implement RX-01/RX-08 first (product card early emission via stream_chunk_data) as it delivers the highest user-visible impact with minimal risk — no LLM code changes. Then implement RX-02 (token streaming). Then RX-04/RX-05 (reduce review_search scope and parallelise). RX-03, RX-06, RX-07 are cleanup fixes within existing structures.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `asyncio` | stdlib | Parallel API calls within tools | Already used throughout; asyncio.gather is the parallelism primitive |
| `openai` (via langchain_openai) | Current | Token streaming | ChatOpenAI.astream() yields chunks; model_service._stream_response() already implements this |
| FastAPI `StreamingResponse` | Current | SSE transport | Already in use; `_sse_event()` helper already formats named events |
| LangGraph `astream_events` | Current | Mid-workflow artifact emission | Already consumes `stream_chunk_data` from node outputs in chat.py lines 455-473 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `asyncio.wait_for` | stdlib | Per-product timeout in review_search | Wrap each `client.search_reviews()` call |
| `asyncio.gather` | stdlib | Parallel per-product searches within a provider | Replace sequential for loop in search_provider() |

---

## Architecture Patterns

### Current Flow (Slow Path)

```
user message
  → safety → intent → planner → clarifier
  → plan_executor:
      step 1: product_search (sequential)
      step 2: review_search (5 products, parallel via gather)
      step 3: product_normalize
      step 4: product_affiliate (providers parallel, products sequential per-provider)
      step 5: product_compose
                → asyncio.gather(opener, consensus×3, descriptions, blog_article, conclusion)
                → wait ALL done → return assistant_text + ui_blocks
  → chat.py: batch-emit ui_blocks then fake-chunk response_text at 24 chars/chunk
```

Everything arrives at the browser in one burst at ~60-90 seconds.

### Target Flow (Fast Path)

```
user message
  → safety → intent → planner → clarifier
  → plan_executor:
      step 1: product_search (sequential)
      step 2 [parallel=true]:
          review_search (3 products, gather + per-product timeout)
          product_affiliate (providers parallel, products parallel via gather)
              → IMMEDIATELY after affiliate results: emit stream_chunk_data ui_blocks
                (product cards appear in browser at ~5s)
      step 3: product_normalize
      step 4: product_compose
                → blog_article: generate(stream=True) → yield tokens one by one
                  via stream_chunk_data content events as they arrive
                → eliminate: opener call (inline in blog_article prompt)
                → eliminate: conclusion call (inline in blog_article prompt)
                → keep: consensus×3 (parallel, quick)
                → keep: descriptions (parallel, needed for carousel)
  → chat.py: stream_chunk_data events already consumed; text tokens stream in real-time
```

### Pattern 1: Early Product Card Emission via stream_chunk_data

**What:** After product_affiliate fetches offers, write them directly to `self.state["stream_chunk_data"]` with type `"ui_blocks"`. The LangGraph `on_chain_end` handler in chat.py (lines 455-473) picks this up immediately and yields it as an `artifact` SSE event before the node returns.

**When to use:** Any tool that fetches UI-displayable data and runs before product_compose.

**Mechanics — how stream_chunk_data triggers early streaming:**

In `chat.py` `_drain_event_loop()` (lines 455-473):
```python
# STREAM DATA IMMEDIATELY if agent returned stream_chunk_data
if isinstance(output_data, dict):
    stream_data = output_data.get("stream_chunk_data")
    if stream_data:
        data_type = stream_data.get("type")
        data_content = stream_data.get("data")
        if data_type and data_content:
            artifact_payload = {
                "type": data_type,
                "blocks": data_content,
                "clear": True,
            }
            yield _sse_event("artifact", artifact_payload)
            data_already_streamed = True
```

This fires on `on_chain_end` for EACH COMPLETED NODE — not just the final one. So if `product_affiliate` sets `stream_chunk_data` in its return dict, the product cards reach the browser the moment that node finishes.

**Critical constraint:** The tool must include `stream_chunk_data` in its RETURN DICT (not just write to `self.state`). LangGraph captures the node's return value as the `output` in the `on_chain_end` event. The PlanExecutor writes tool results to state, but the `on_chain_end` event for the entire `plan_executor_node` fires when the node function returns — not per tool. Therefore: product_affiliate cannot trigger early streaming by itself via the return value alone.

**The real mechanism:** The `plan_executor._emit_tool_citation()` already does this (lines 378-384 in plan_executor.py):
```python
self.state["stream_chunk_data"] = {
    "type": "tool_citation",
    "data": citation
}
```
This mutation of `self.state` triggers the LangGraph channel update (since plan_executor_node returns the full state at the end). But tool citations are suppressed in the current drain loop.

**Revised approach for product cards:** The `plan_executor_node` wrapper must yield intermediate results. Looking at the current code, the `on_chain_end` for `agent_plan_executor` fires only when `plan_executor_node` returns. There is no per-tool node event.

**Therefore, for RX-01:** The correct path is to have `product_affiliate` set `stream_chunk_data` in the state it returns, then have `plan_executor._write_tool_outputs_to_state()` update `self.state["stream_chunk_data"]`, and then add a mid-execution SSE emit point in the plan_executor loop — after the step containing product_affiliate completes, before proceeding to the next step. The executor can yield a progress event by calling a registered streaming callback.

**Alternative (simpler):** Since `data_already_streamed` is checked by chat.py and the plan_executor already has `_citation_callbacks`, add a callback that emits an artifact SSE event when product_affiliate writes ui_blocks to state. This requires passing the SSE yield function as a callback, which chat.py already partially supports via `register_tool_citation_callback`.

### Pattern 2: Token Streaming for Blog Article

**What:** Call `model_service.generate(stream=True)` for the blog_article task. Since `generate()` returns an `AsyncGenerator[str, None]` when `stream=True`, iterate the generator and write each token chunk as a `content` SSE event.

**The constraint:** `product_compose` currently awaits ALL LLM tasks via `asyncio.gather(*llm_tasks.values())` at Phase 3. This batches everything including the blog. Streaming requires separating the blog call from the batch gather.

**Implementation pattern:**
```python
# In product_compose, Phase 2: remove blog_article from llm_tasks dict
# In Phase 3: fire all non-blog tasks in parallel
non_blog_tasks = {k: v for k, v in llm_tasks.items() if k != 'blog_article'}
results = await asyncio.gather(*non_blog_tasks.values(), return_exceptions=True)

# Then stream the blog:
blog_stream = model_service.generate(
    messages=[...],
    stream=True,
    ...
)
blog_tokens = []
async for token in await blog_stream:
    blog_tokens.append(token)
    # Emit via stream_chunk_data content event
    # (requires streaming callback mechanism)

assistant_text = "".join(blog_tokens)
```

**The SSE delivery mechanism:** `stream_chunk_data` only triggers on `on_chain_end`. For true per-token streaming, `product_compose` must call the streaming callback directly (via `self.state` mutation checked on each iteration), OR the plan_executor must expose a `yield_token(token)` callback that product_compose calls per token, which the chat.py SSE handler reads.

The cleanest approach: add a `stream_token_callback` to the state (a callable injected by chat.py before workflow start). product_compose calls `stream_token_callback(token)` for each blog token. chat.py registers this callback in `consume_events()` before starting the graph. This is analogous to how Langfuse callbacks work.

**Source:** `model_service._stream_response()` (lines 261-300 of model_service.py) — already implements `async for chunk in llm.astream(messages): yield chunk.content`.

### Pattern 3: Parallelise review_search + product_affiliate

**What:** The planner currently schedules review_search and product_affiliate in separate sequential steps. They have no data dependency on each other (both read from `product_names` written by `product_search`). Set them in a single plan step with `parallel: true`.

**Plan step change (planner agent prompt update):**
```json
{
  "id": "fetch_reviews_and_affiliates",
  "tools": ["review_search", "product_affiliate"],
  "parallel": true,
  "depends_on": ["product_search"]
}
```

**Planner agent location:** `backend/app/agents/planner_agent.py` — the system prompt must explicitly state that review_search and product_affiliate can run in parallel for product intent.

**What PlanExecutor does with parallel steps:** Lines 273-295 of plan_executor.py show it already handles `parallel: true` — wraps all tools in `asyncio.gather`. No code change in plan_executor needed.

### Pattern 4: Per-Product Timeout in review_search

**What:** `review_search` currently runs all products via `asyncio.gather(*tasks)`. If one product's search hangs, all 5 wait. Add a per-product timeout by wrapping each individual search in `asyncio.wait_for`.

**Current code (lines 136-141 of review_search.py):**
```python
tasks = [
    client.search_reviews(name, category)
    for name in products_to_search
]
bundles = await asyncio.gather(*tasks, return_exceptions=True)
```

**Fix:**
```python
PER_PRODUCT_TIMEOUT_S = 8  # per-product Serper call timeout

tasks = [
    asyncio.wait_for(client.search_reviews(name, category), timeout=PER_PRODUCT_TIMEOUT_S)
    for name in products_to_search
]
bundles = await asyncio.gather(*tasks, return_exceptions=True)
# asyncio.TimeoutError is an Exception, handled by the existing isinstance(bundle, Exception) check
```

Also change line 120: `products_to_search = product_names[:5]` → `products_to_search = product_names[:3]`

### Pattern 5: Eliminating Redundant LLM Calls in product_compose

**What:** Currently product_compose fires up to: 1 concierge OR (1 opener + 3 consensus), 1 descriptions, 1 conclusion, 1 blog_article = up to 7 concurrent LLM calls. With streaming, the blog_article IS the assistant_text, so opener and conclusion become redundant.

**Call audit:**
| Call | Tokens | Keep/Remove | Reason |
|------|--------|------------|--------|
| `concierge` (no review_data path) | 120 | KEEP | Only fires when no review data; fast |
| `opener` (review_data path) | 60 | REMOVE | Blog article starts with intro — duplicated |
| `consensus:product_name` (×3) | 220×3 = 660 | KEEP | Provides product summaries for carousel cards |
| `descriptions` | 600 | KEEP | Needed for carousel card descriptions |
| `conclusion` | 80 | REMOVE | Blog article ends with "## Our Verdict" — duplicated |
| `blog_article` | 800 | KEEP | Primary response text; stream this |

**Net reduction:** Remove opener (60 tokens) + conclusion (80 tokens) = 2 fewer concurrent calls, ~140 tokens fewer, freeing concurrency slots. Inline their content into the blog_article system prompt instead.

**Updated blog_article system prompt addition:**
```
- Start with a warm 1-2 sentence intro addressing what the user is looking for
- End with a "## Our Verdict" section (2 sentences: opinionated recommendation)
```

### Anti-Patterns to Avoid

- **Do NOT use `asyncio.sleep()` polling** to fake streaming. The existing fake-chunk approach at lines 607-610 of chat.py (`for i in range(0, len(response_text), 24)`) should be removed from the code path when true token streaming is active.
- **Do NOT put callbacks in GraphState.** The MEMORY.md explicitly warns: "Do not add langfuse_handler or callbacks to state — causes massive JSON serialization that crashes browser." Use a side-channel (injected callback function in plan_executor) instead.
- **Do NOT await the blog stream inside asyncio.gather.** Generators cannot be awaited by gather. Separate blog streaming from the batch gather.
- **Do NOT add `stream_chunk_data` to Annotated[..., operator.add].** It is `Optional[Dict]` — a single value, overwritten per emission. Do not change its type in GraphState.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE token delivery | Custom WebSocket server | Existing `_sse_event("content", {"token": ...})` in chat.py | Already working, frontend already handles content events |
| OpenAI streaming | Raw httpx streaming | `model_service._stream_response()` / `ChatOpenAI.astream()` | Already implemented with semaphore, error handling, Langfuse tracing |
| Parallel tool execution | Custom thread pool | `asyncio.gather()` | Already used throughout; plan_executor already has parallel step support |
| Per-product timeout | Retry loops with sleep | `asyncio.wait_for(coro, timeout=N)` | Clean cancellation, exception handled by existing isinstance(Exception) check |
| Mid-workflow streaming | New SSE channel | Existing `stream_chunk_data` field in GraphState + on_chain_end detection in chat.py | Mechanism already proven with travel itinerary streaming |

---

## Common Pitfalls

### Pitfall 1: stream_chunk_data only triggers on on_chain_end of the NODE, not of the TOOL

**What goes wrong:** Developer writes `self.state["stream_chunk_data"] = {...}` inside `product_affiliate()` expecting it to stream immediately. It does not. The LangGraph event fires when `plan_executor_node()` returns, not when individual tools inside it return.

**Why it happens:** Tools are called synchronously within `PlanExecutor.execute()`. LangGraph only emits events for graph nodes, not for sub-functions within a node.

**How to avoid:** Use the callback pattern. `plan_executor._emit_tool_citation()` already demonstrates the pattern (writing to state + calling callbacks). Add a `yield_artifact_callback` that chat.py registers, allowing plan_executor to push artifacts mid-execution to the SSE stream without waiting for node completion.

**Warning signs:** Product cards only appear after ALL workflow steps finish, not after product_affiliate step.

### Pitfall 2: GraphState fields must have defaults in initial_state dict

**What goes wrong:** Add new field to GraphState TypedDict. Backend crashes with LangGraph channel error on first request after deploy.

**Why it happens:** LangGraph channels require every declared field to have an initial value in the state dict passed to `graph.astream_events()`. MEMORY.md explicitly documents: "When adding fields to GraphState TypedDict, MUST also add default value to initial_state dict in chat.py (~line 243)."

**How to avoid:** Any new fields (e.g., `stream_token_callback`) added to GraphState must also appear in `initial_state` in chat.py lines 295-353. However, callables cannot be serialized to Redis for halt state — use None as default and inject callback via side-channel, not GraphState.

**Warning signs:** KeyError or validation error in LangGraph on first message after adding new state field.

### Pitfall 3: model_service.generate(stream=True) returns a coroutine that returns a generator

**What goes wrong:** Developer writes `async for token in model_service.generate(..., stream=True)` and gets a TypeError. `generate()` is an `async def` that returns either a `str` or an `AsyncGenerator`. When `stream=True`, it returns `self._stream_response(...)` — which is itself an async generator. So the call pattern is:
```python
gen = await model_service.generate(..., stream=True)
async for token in gen:
    ...
```
NOT:
```python
async for token in model_service.generate(..., stream=True):  # WRONG
    ...
```

**Why it happens:** `generate()` is typed as returning `str | AsyncGenerator`. The caller must await it first to get the generator, then iterate.

**How to avoid:** Always `result = await model_service.generate(stream=True)` then `async for token in result`.

### Pitfall 4: Fake-chunking and true streaming running simultaneously creates duplicate text

**What goes wrong:** chat.py lines 605-610 emit fake chunks from `response_text` after the workflow ends. If product_compose already streamed tokens via content events during the workflow, the same text gets sent twice.

**Why it happens:** `data_already_streamed` flag exists for ui_blocks (set at line 472) but the `should_stream_text` check at line 603 only skips text if `data_already_streamed` is True. Text streaming (true tokens) needs its own flag.

**How to avoid:** Add a separate flag `text_already_streamed` (or extend `data_already_streamed` semantics) that is set when product_compose streams tokens. Check it at line 603.

### Pitfall 5: asyncio.gather return_exceptions=True masks product_affiliate provider failures silently

**What goes wrong:** A provider times out, returns an Exception, which is treated as no results — user gets fewer product cards with no indication.

**Why it happens:** Current pattern in product_affiliate lines 174-181 skips exceptions silently.

**How to avoid:** Log the exception with provider name before skipping. Already done — line 177: `logger.warning(...)`. Acceptable behavior; just ensure timeout value is not so short it cuts off valid results.

### Pitfall 6: review_search and product_affiliate parallel execution requires product_names to be in state BEFORE both run

**What goes wrong:** parallel step runs both tools simultaneously, but product_names is written by product_search which is a prior step. If the step ordering is wrong, one of the parallel tools reads empty product_names.

**Why it happens:** Parallel tools both read from state simultaneously. If a preceding tool hasn't written yet, both read empty.

**How to avoid:** Verify plan step `depends_on: ["product_search"]` is set for the parallel step. PlanExecutor's topological sort ensures prior steps complete before dependent steps begin.

---

## Code Examples

### Streaming Callback Registration (chat.py pattern)

```python
# Source: verified from plan_executor.py lines 365-398 and chat.py lines 364-388
# In chat.py, before consume_events():
async def on_artifact(artifact_data: dict):
    # Called mid-workflow by plan_executor when a tool produces streamable data
    yield _sse_event("artifact", {
        "type": artifact_data.get("type", "ui_blocks"),
        "blocks": artifact_data.get("blocks", []),
        "clear": True,
    })

plan_executor_instance.register_citation_callback(on_artifact)
```

Note: Since consume_events() is an async task running in background, the callback must write to a shared asyncio.Queue, not yield directly. The existing `event_queue` in chat.py is the correct target.

### Correct Token Streaming Call Pattern

```python
# Source: verified from model_service.py lines 146-159, 261-300
# generate() with stream=True returns a coroutine that yields an AsyncGenerator
blog_gen = await model_service.generate(
    messages=[...],
    model=settings.COMPOSER_MODEL,
    temperature=0.7,
    max_tokens=800,
    stream=True,
    agent_name="blog_article_streamer"
)

tokens = []
async for token in blog_gen:
    tokens.append(token)
    # Emit token to SSE stream via callback
    await emit_token_callback(token)

assistant_text = "".join(tokens)
```

### review_search Reduction (3 products + per-product timeout)

```python
# Source: verified from review_search.py lines 119-141
# Change line 120:
products_to_search = product_names[:3]  # was [:5]

PER_PRODUCT_TIMEOUT_S = 8

tasks = [
    asyncio.wait_for(
        client.search_reviews(name, category),
        timeout=PER_PRODUCT_TIMEOUT_S
    )
    for name in products_to_search
]
bundles = await asyncio.gather(*tasks, return_exceptions=True)
# asyncio.TimeoutError is a subclass of Exception — handled by existing check
```

### Planner Prompt Update for Parallel Step

```
# The planner agent system prompt must include:
For product intent, schedule review_search and product_affiliate in the same step with parallel=true.
They both read from product_names which is written by product_search. Example:

{
  "id": "fetch_data",
  "tools": ["review_search", "product_affiliate"],
  "parallel": true,
  "depends_on": ["product_search"]
}
```

### product_compose: Remove opener + conclusion, inline into blog_article prompt

```python
# Remove from llm_tasks:
# llm_tasks['opener'] = ...  (DELETE)
# llm_tasks['conclusion'] = ...  (DELETE)

# Update blog_article system prompt to include:
system_prompt = """You are an expert product journalist writing a blog-style review article.
...
- Start with a warm 1-2 sentence intro addressing what the user is looking for (their budget, use case, features)
- For each product, write a ## heading with product name and editorial label in italics
- Under each heading, write 2-4 sentences reviewing the product
- Include the price and a markdown link: [Check price on Merchant →](url)
- For each product, if review source links are provided in the data, include 1-2 inline citations
  using the format: [Wirecutter](url) or [Tom's Guide](url). Only link to sources in the data.
- End with a ## Our Verdict section (2 sentences: opinionated top recommendation)
- Keep total response under 500 words"""
```

### Inline Affiliate Link Fix (RX-07): Thread source URLs into blog context

```python
# Source: verified from product_compose.py lines 576-598
# In the review_bundles loop, extend blog_data_parts line:
source_refs = ""
if bundle.get("sources"):
    top_sources = bundle["sources"][:3]
    source_refs = " | Reviews: " + ", ".join(
        f"[{s.get('site_name', 'source')}]({s.get('url', '')})"
        for s in top_sources if s.get("url")
    )
blog_data_parts.append(
    f"Product: {pname}{label_str} | Rating: {rating}/5 ({total} reviews)"
    f" | Price: {price_str} on {merchant_str} | Link: {link_str}"
    f" | Image: {image_str}{source_refs}"
)
```

---

## State of the Art

| Old Approach | Current Approach | Target Approach | Impact |
|--------------|-----------------|-----------------|--------|
| Wait for full LLM completion | Batch-then-fake-chunk at 24 chars/tick | True token streaming via AsyncGenerator | Text appears progressively; no 90s wait |
| Product cards after product_compose | Product cards after product_compose | Product cards after product_affiliate (earlier step) | Cards visible ~5s vs ~60-90s |
| 5 products in review_search | 5 products in review_search | 3 products with per-product timeout | ~40% fewer Serper API calls; faster |
| review_search → product_affiliate (sequential) | review_search → product_affiliate (sequential) | review_search + product_affiliate (parallel) | Saves one full review_search duration |
| 7 concurrent LLM calls in product_compose | 7 concurrent LLM calls | 5 concurrent (remove opener + conclusion) | Fewer API calls; tokens inline in blog |

---

## Open Questions

1. **Streaming callback delivery mechanism through asyncio task boundary**
   - What we know: chat.py runs `consume_events()` as a background asyncio task that puts events in `event_queue`. The SSE generator drains event_queue. A streaming callback from product_compose needs to reach the event_queue.
   - What's unclear: Can a callback registered on plan_executor safely `await event_queue.put(event)` from within the plan_executor coroutine (which runs inside the consume_events background task)?
   - Recommendation: Yes — all code runs in the same event loop. The callback can be a closure over `event_queue` created in chat.py and passed to plan_executor before starting the graph. This is the correct pattern.

2. **Whether planner agent currently schedules review_search and product_affiliate in parallel**
   - What we know: plan_executor supports parallel steps (parallel:true flag). The planner LLM generates the plan dynamically.
   - What's unclear: What the planner's current system prompt says about step ordering for product intent.
   - Recommendation: Read `backend/app/agents/planner_agent.py` before writing the plan task. The prompt likely needs an explicit instruction to schedule these two tools in parallel.

3. **Token streaming interaction with Langfuse tracing**
   - What we know: Langfuse tracing works via callbacks passed in LangGraph config. Streaming calls do not pass callbacks in the current model_service code (line 277: `async for chunk in llm.astream(messages)` — no config parameter).
   - What's unclear: Whether streaming tokens will appear in Langfuse traces without the callback.
   - Recommendation: Acceptable regression — Langfuse token counting may be incomplete for streamed blog calls. Not a blocker for this phase; fix in a follow-up.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `backend/pytest.ini` or implicit (conftest.py pattern in backend/tests/) |
| Quick run command | `cd backend && python -m pytest tests/test_product_compose.py tests/test_review_search.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RX-01 | Product cards emitted within 5s via stream_chunk_data | unit | `pytest tests/test_product_compose.py::test_product_affiliate_emits_stream_chunk_data -x` | Wave 0 |
| RX-02 | Blog article streams tokens (model_service called with stream=True) | unit | `pytest tests/test_product_compose.py::test_blog_article_uses_streaming -x` | Wave 0 |
| RX-03 | Per-provider search uses asyncio.gather for products | unit | `pytest tests/test_product_compose.py::test_affiliate_search_parallel -x` | Wave 0 |
| RX-04 | review_search caps at 3 products, applies per-product timeout | unit | `pytest tests/test_review_search.py::test_review_search_caps_at_3_products -x` | Wave 0 |
| RX-05 | Planner generates parallel step for review_search + product_affiliate | unit | `pytest tests/test_product_compose.py::test_planner_parallel_step -x` | Wave 0 |
| RX-06 | product_compose fires at most 5 concurrent LLM calls (no opener/conclusion) | unit | `pytest tests/test_product_compose.py::test_no_redundant_llm_calls -x` | Wave 0 |
| RX-07 | Blog narrative includes inline affiliate markdown links | unit | `pytest tests/test_product_compose.py::test_blog_includes_affiliate_links -x` | Wave 0 |
| RX-08 | stream_chunk_data carries ui_blocks type with product cards | unit | `pytest tests/test_product_compose.py::test_stream_chunk_data_ui_blocks -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_product_compose.py tests/test_review_search.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_product_compose.py` — extend existing file with RX-01 through RX-08 test cases (file exists but lacks streaming and parallelism tests)
- [ ] `tests/test_review_search.py` — add test for 3-product cap and per-product timeout (file exists but may lack timeout tests)
- [ ] No new test infrastructure needed — conftest.py is comprehensive

---

## Sources

### Primary (HIGH confidence)
- `backend/app/api/v1/chat.py` lines 455-473, 580-612 — stream_chunk_data consumption, fake-chunking pattern
- `backend/mcp_server/tools/product_compose.py` lines 300-900 — LLM task structure, blog_article call, all async.gather usage
- `backend/mcp_server/tools/review_search.py` lines 119-141 — current 5-product cap, parallel gather pattern
- `backend/mcp_server/tools/product_affiliate.py` lines 109-170 — search_provider inner function, asyncio.gather across providers, sequential for loop per product within provider
- `backend/app/services/model_service.py` lines 146-300 — generate() signature, _stream_response() implementation
- `backend/app/services/plan_executor.py` lines 257-398 — parallel step execution, stream_chunk_data mutation pattern
- `backend/app/schemas/graph_state.py` — stream_chunk_data field type (Optional[Dict]), all state fields
- `frontend/lib/chatApi.ts` lines 309-319 — content event handling, token delivery to onToken callback

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — RX-01 through RX-08 canonical definitions
- `.planning/research/SUMMARY.md` — prior research confirming no streaming infrastructure gaps

---

## Metadata

**Confidence breakdown:**
- Streaming mechanism: HIGH — verified by reading the actual LangGraph event loop in chat.py; model_service streaming confirmed implemented
- Parallelism: HIGH — asyncio.gather already used; parallel step support confirmed in plan_executor
- Token streaming delivery: MEDIUM — callback-over-event-queue pattern is standard but requires careful implementation to avoid asyncio task boundary issues
- LLM call reduction: HIGH — calls enumerated by reading product_compose directly

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable codebase; no external API changes for this phase)
