# RFC: Performance, Reliability, and UX Optimization
**Date:** 2026-02-22
**Status:** Draft
**Scope:** Backend latency, frontend streaming, reliability, security, observability
**Source:** Post-deployment technical audit (Gemini review + internal)

---

## Table of Contents

1. [Response-Time Optimization](#1-response-time-optimization)
   1.1 [End-to-End Latency Budget and Stage Contracts](#11-end-to-end-latency-budget-and-stage-contracts)
   1.2 [Planner Cost and Adaptivity Control](#12-planner-cost-and-adaptivity-control)
   1.3 [Tool Execution Engine Hardening](#13-tool-execution-engine-hardening)
   1.4 [Search Context Safety and Efficiency](#14-search-context-safety-and-efficiency)
   1.5 [Model Service Optimization Beyond Instance Caching](#15-model-service-optimization-beyond-instance-caching)
   1.6 [State Payload Control and Serialization Boundaries](#16-state-payload-control-and-serialization-boundaries)
   1.7 [Redis and DB Access Efficiency](#17-redis-and-db-access-efficiency)
   1.8 [Progressive Streaming Architecture](#18-progressive-streaming-architecture)

2. [Frontend UX and Interaction Quality](#2-frontend-ux-and-interaction-quality)
   2.1 [Streaming State Machine Refactor](#21-streaming-state-machine-refactor)
   2.2 [Progressive Rendering of Rich Blocks](#22-progressive-rendering-of-rich-blocks)
   2.3 [Message-Level Recovery UX](#23-message-level-recovery-ux)
   2.4 [Interaction Model for Suggestions and Follow-Ups](#24-interaction-model-for-suggestions-and-follow-ups)
   2.5 [Content Trust and Explainability UI](#25-content-trust-and-explainability-ui)
   2.6 [Design-System Consistency for Luxury Editorial Aesthetic](#26-design-system-consistency-for-luxury-editorial-aesthetic)

3. [Reliability, Security, and Governance](#3-reliability-security-and-governance)
   3.1 [API Trust Boundary Enforcement](#31-api-trust-boundary-enforcement)
   3.2 [Proxy-Aware Rate Limiting Integrity](#32-proxy-aware-rate-limiting-integrity)
   3.3 [Provider Capability Manifest at Startup](#33-provider-capability-manifest-at-startup)
   3.4 [Contract Validation at Tool Boundaries](#34-contract-validation-at-tool-boundaries)

4. [Observability and Continuous Optimization](#4-observability-and-continuous-optimization)
   4.1 [Unified Trace Model](#41-unified-trace-model)
   4.2 [Quality-of-Service Dashboards](#42-quality-of-service-dashboards)
   4.3 [Controlled Degradation Policies](#43-controlled-degradation-policies)

---

## 1. Response-Time Optimization

### 1.1 End-to-End Latency Budget and Stage Contracts

#### Problem Statement
No stage in the LangGraph pipeline has a defined latency budget. A slow tool (e.g. SerpAPI review_search, Perplexity search) stalls the full response with no observable boundary. The backend emits no per-stage timing, making it impossible to attribute latency to a specific stage or detect regressions. A single provider timeout can hold the entire pipeline open for the full REQUEST_TIMEOUT_MS (120 s).

#### Current State
- Request timeout: 120 s (global, frontend-side AbortController only)
- No per-stage timeout exists in `plan_executor.py`, `workflow.py`, or any tool
- Langfuse traces capture LLM call durations but not tool-level or stage-level spans
- A `status_update` SSE event is emitted per tool but carries no timing data

#### Interface Contract

**Stage telemetry payload** (emitted by each stage at completion):
```python
@dataclass
class StageTelemetry:
    stage: str                  # "intent" | "planning" | "tool.<name>" | "composition" | "finalization"
    start_ts: float             # Unix timestamp (time.monotonic() epoch offset)
    end_ts: float
    duration_ms: int
    input_size: int             # bytes or token count, whichever is cheaper to compute
    output_size: int
    timeout_hit: bool           # True if stage completed via timeout path
    degraded_mode: bool         # True if output is partial/fallback
    error_class: str | None     # None | "transient" | "provider" | "schema" | "fatal"
```

**Stage latency budgets** (hard and soft limits, milliseconds):

| Stage | Soft Timeout | Hard Timeout | On Hard Timeout |
|-------|-------------|--------------|-----------------|
| Safety agent | 2 000 | 4 000 | Pass with `policy_status="unchecked"` |
| Intent classification | 3 000 | 6 000 | Default to `intent="general"` |
| Clarifier agent | 4 000 | 8 000 | Skip clarification, proceed with slots as-is |
| Planner (LLM path) | 5 000 | 10 000 | Fall back to fast-path template |
| Per-tool execution | 8 000 | 15 000 | Mark tool output as missing, continue |
| Aggregate plan execution | 25 000 | 45 000 | Return partial results with degraded flag |
| Composition | 6 000 | 12 000 | Return raw tool outputs without formatting |
| Stream finalization | 2 000 | 4 000 | Emit done=true with available data |

#### Acceptance Criteria
- [ ] Every stage wraps its logic in `asyncio.wait_for(coro, timeout=HARD_TIMEOUT_S)`
- [ ] Soft timeout fires a warning log + sets `degraded_mode=True` on the telemetry object
- [ ] Hard timeout fires, stage emits telemetry with `timeout_hit=True`, pipeline continues
- [ ] `StageTelemetry` objects are appended to `GraphState["stage_telemetry"]` list
- [ ] Final SSE `done` event includes `stage_telemetry` array
- [ ] No single request can hold an open SSE connection beyond 60 s total (enforced server-side)
- [ ] p99 intent classification < 4 s measured over 100 real requests in production

---

### 1.2 Planner Cost and Adaptivity Control

#### Problem Statement
The current fast-path product planner is binary: product intent always runs the full 8-step DAG. A query like "what year was the Sony WH-1000XM5 released?" runs SerpAPI review_search, affiliate enrichment, and ranking — steps costing ~$0.02 and ~3 s — when only `product_general_information` is needed. Simple factoid queries pay the same cost as deep research queries.

#### Current State
- `planner_agent._create_fast_path_product_plan()` returns a hardcoded 8-step DAG for all product intent
- No complexity classification exists
- LLM planner path exists but is bypassed for product intent entirely
- No mechanism to skip tools that won't improve the answer for a given query class

#### Query Complexity Classes

| Class | Signals | Template |
|-------|---------|----------|
| `factoid` | Single entity, no comparison, no "best"/"recommend", short query | minimal |
| `comparison` | 2+ named products, "vs", "compare", "difference" | standard |
| `recommendation` | "best", "recommend", "should I buy", no specific product named | standard |
| `deep_research` | Review sentiment, "worth it", "complaints", multi-criteria | full |

#### Execution Templates

**minimal** (factoid):
```
extractor → product_general_information → compose
```

**standard** (comparison / recommendation):
```
extractor → [product_search ∥ evidence] → normalize → affiliate → compose → suggestions
```

**full** (deep research — current fast path):
```
extractor → [search ∥ evidence] → review_search → normalize → affiliate → ranking → compose → suggestions
```

#### Interface Contract

```python
def classify_query_complexity(
    user_message: str,
    slots: dict,
    intent: str,
) -> Literal["factoid", "comparison", "recommendation", "deep_research"]:
    """
    Deterministic heuristic classifier. Returns complexity class.
    Must complete in < 5 ms (no LLM call).
    Signals:
      - factoid: len(tokens) < 10, no comparison keywords, entity_count == 1
      - comparison: product_names count >= 2 OR comparison_keywords present
      - recommendation: recommendation_keywords present AND product_names count == 0
      - deep_research: review_keywords present OR len(tokens) > 20
    Falls back to LLM planner if confidence < 0.7.
    """
```

```python
COMPLEXITY_CONFIDENCE_THRESHOLD = 0.7  # below this, use LLM planner

def get_product_plan(
    complexity: str,
    confidence: float,
) -> ExecutionPlan:
    if confidence < COMPLEXITY_CONFIDENCE_THRESHOLD:
        return await llm_planner.generate_plan(...)
    return PRODUCT_TEMPLATES[complexity]
```

#### Acceptance Criteria
- [ ] `classify_query_complexity` implemented with deterministic heuristics, no LLM call
- [ ] Three product execution templates defined and tested
- [ ] Factoid queries route to minimal template (verified via log inspection)
- [ ] LLM planner fallback triggers when confidence < threshold
- [ ] Unit tests cover each complexity class with ≥ 5 example queries each
- [ ] p50 latency for factoid product queries < 4 s end-to-end

---

### 1.3 Tool Execution Engine Hardening

#### Problem Statement
Tool execution in `plan_executor.py` uses a broad `try/except Exception` that swallows all errors and logs them, but has no per-tool timeout, no retry policy, no circuit state, and no structured error classification. A single provider timeout causes the entire parallel fan-out to wait at its worst case. Client disconnection does not cancel outstanding tool tasks, leaving them running and consuming provider quota.

#### Current State
- `asyncio.gather(..., return_exceptions=True)` is used for parallel steps
- Individual tool calls are wrapped in try/except but not in `asyncio.wait_for`
- No retry logic at the executor layer (some providers retry internally, inconsistently)
- `AbortController` on frontend side does not propagate to backend tool cancellation

#### Interface Contract

**Tool execution envelope:**
```python
@dataclass
class ToolEnvelope:
    tool_name: str
    timeout_s: float = 15.0          # Hard timeout; override per tool in registry
    max_retries: int = 1             # 0 = no retry
    retry_jitter_ms: tuple = (200, 800)
    circuit_state: Literal["closed", "open", "half-open"] = "closed"
    error_class: Literal["transient", "provider", "schema", "fatal"] | None = None
```

**Error classification:**
| Class | Examples | Retry? | Continue pipeline? |
|-------|---------|--------|-------------------|
| `transient` | Network timeout, 503 | Yes (up to max_retries) | Yes, with degraded flag |
| `provider` | 401, 429, provider-specific error | No (except 429 with backoff) | Yes, mark source as missing |
| `schema` | Unexpected response shape, parse failure | No | Yes, log + skip |
| `fatal` | Unrecoverable state corruption, OOM | No | No, abort pipeline |

**Partial-success semantics:**
```python
@dataclass
class PartialResult:
    successful_outputs: dict[str, Any]   # tool_name -> output
    missing_sources: list[MissingSource]

@dataclass
class MissingSource:
    tool: str
    error_class: str
    reason: str
    degraded_fields: list[str]  # which state keys are absent/incomplete
```

**Cancellation contract:**
- `plan_executor` receives a `cancellation_token: asyncio.Event`
- Each tool coroutine checks `cancellation_token.is_set()` at its await boundary
- On client disconnect (detected via `request.is_disconnected()`), `cancellation_token.set()` is called
- All outstanding tool tasks are cancelled via `task.cancel()` within 500 ms

#### Acceptance Criteria
- [ ] Every tool invocation is wrapped in `asyncio.wait_for(tool_coro, timeout=envelope.timeout_s)`
- [ ] Transient errors retry up to `max_retries` with jitter between `retry_jitter_ms`
- [ ] Parallel fan-out with N tools: if K < N succeed, pipeline continues with `PartialResult`
- [ ] `missing_sources` is populated and included in the final SSE `done` event
- [ ] Client disconnect cancels all outstanding tool tasks within 500 ms (verified via test)
- [ ] Circuit breaker: after 3 consecutive fatal failures from a provider, circuit opens for 60 s
- [ ] Integration test: mock one tool to timeout; verify other parallel tools complete and response is returned

---

### 1.4 Search Context Safety and Efficiency

#### Problem Statement
Perplexity search results are injected directly into LLM prompts with no sanitization, no token budget, and no relevance filtering. A Perplexity result containing instruction-like text (e.g., "Ignore previous instructions...") is passed verbatim to the model. Five results are injected regardless of token cost. The same query can trigger repeated Perplexity API calls across tool invocations in the same session.

#### Current State (in product_general_information.py, travel_destination_facts.py, travel_general_information.py):
```python
web_context = "\n".join([f"- {r.title}: {r.snippet}" for r in search_results])
```
No sanitization. No token cap. No deduplication. No caching.

#### Interface Contract

```python
def build_web_context(
    results: list[SearchResult],
    query: str,
    slots: dict,
    max_tokens: int = 800,
    min_relevance_score: float = 0.3,
) -> WebContext:
    """
    Sanitizes, filters, deduplicates, and token-caps search results.
    Returns structured context safe for LLM injection.
    """

@dataclass
class WebContext:
    text: str                     # Formatted, sanitized, token-capped string for prompt injection
    source_count: int             # Number of sources included
    omitted_count: int            # Sources dropped (low relevance or over token budget)
    token_estimate: int           # Estimated tokens consumed by text
    cache_hit: bool               # True if served from Redis cache
```

**Sanitization rules:**
1. Strip any line containing patterns matching instruction injection heuristics (`ignore`, `system:`, `<|`, `[INST]`, etc.)
2. Truncate individual snippets to 300 characters max
3. Remove HTML entities and markdown formatting from snippets
4. Normalize whitespace

**Relevance filter:**
- Compute lexical overlap score between snippet and (query + slot values)
- Discard snippets with overlap score < `min_relevance_score`
- Implementation: simple token Jaccard similarity (no ML model required)

**Token budget:**
- Estimate tokens as `len(text) / 4` (conservative approximation)
- Trim results from lowest-relevance to highest until under `max_tokens`

**Cache key:**
```python
cache_key = f"search:{intent}:{country_code}:{sha256(normalized_query)[:16]}"
# TTL by intent:
#   product: 3600 s (1 hour — prices change)
#   travel: 86400 s (24 hours — destination facts stable)
#   general: 1800 s (30 minutes)
```

#### Acceptance Criteria
- [ ] `build_web_context` replaces raw snippet joining in all three tools
- [ ] Injection sanitization strips known prompt-injection patterns (unit tested with 10 adversarial inputs)
- [ ] Total injected context never exceeds 800 tokens (verified via token count assertion in tests)
- [ ] Snippets with relevance score < 0.3 are excluded (unit tested)
- [ ] Cache hit rate > 20% in production after 24 h (measured via Redis `KEYS search:*` count vs request count)
- [ ] No regression in answer quality vs. baseline (manual eval: 10 queries before/after)

---

### 1.5 Model Service Optimization Beyond Instance Caching

#### Problem Statement
`ModelService._llm_cache` uses a plain dict keyed by `(model, temperature, max_tokens, json_mode, stream)`. This creates separate pools for `max_tokens=None` and `max_tokens=4096` even when the effective limit is identical. Streaming and non-streaming instances share no connection pool separation. No concurrency guard prevents burst collapse if 50 simultaneous requests instantiate new clients. Cache is never invalidated; a rotated API key leaves stale clients in the pool.

#### Current State (`backend/app/services/model_service.py`):
```python
cache_key = (model, temperature, max_tokens, json_mode, stream)
self._llm_cache[cache_key] = ChatOpenAI(**kwargs)
```

#### Interface Contract

**Canonical cache key:**
```python
def _canonical_key(
    model: str,
    temperature: float,
    max_tokens: int | None,
    json_mode: bool,
    stream: bool,
    api_key_fingerprint: str,   # sha256(api_key)[:8] — invalidates on rotation
) -> tuple:
    # Normalize max_tokens: None and model default map to same bucket
    effective_max = max_tokens if max_tokens and max_tokens < MODEL_DEFAULTS[model] else None
    # Normalize temperature: round to 1 decimal to avoid float key divergence
    effective_temp = round(temperature, 1)
    return (model, effective_temp, effective_max, json_mode, stream, api_key_fingerprint)
```

**Separate pools by call mode:**
```python
# Two semaphores — streaming calls are long-lived, non-streaming are short-lived
_streaming_semaphore = asyncio.Semaphore(10)    # max 10 concurrent streaming calls
_sync_semaphore = asyncio.Semaphore(25)          # max 25 concurrent non-streaming calls
```

**Cache invalidation hook:**
```python
def invalidate_cache(self, reason: str = "manual") -> int:
    """Clear all cached instances. Returns count cleared."""
    count = len(self._llm_cache)
    self._llm_cache.clear()
    logger.info(f"[model_service] Cache invalidated: {count} instances cleared, reason={reason}")
    return count

# Called from settings reload / API key rotation event
```

#### Acceptance Criteria
- [ ] `max_tokens=None` and `max_tokens=MODEL_DEFAULT` resolve to the same cache entry
- [ ] `temperature=0.70` and `temperature=0.7` resolve to the same cache entry
- [ ] Streaming calls acquire `_streaming_semaphore` before proceeding; non-streaming acquire `_sync_semaphore`
- [ ] Cache key includes API key fingerprint; key rotation triggers full cache clear
- [ ] `invalidate_cache()` endpoint exposed at `POST /internal/model-cache/invalidate` (internal auth only)
- [ ] Under load test (50 concurrent requests), no `RuntimeError: Session is closed` errors

---

### 1.6 State Payload Control and Serialization Boundaries

#### Problem Statement
`GraphState` is a flat TypedDict with 40+ keys and no ownership constraints. Tools write any key they want. State is serialized to Redis for halt-state persistence, but there is no check that state values are JSON-serializable before serialization. Large transient values (full review text, raw search results) bloat the Redis payload and slow serialization. Key naming is flat, making it impossible to know which tool wrote which key.

#### Current State
GraphState has 40+ flat keys. Tools write directly: `return {"assistant_text": ..., "ui_blocks": ...}`. No size limits. `HaltStateManager` calls `json.dumps(state)` with no pre-serialization validation.

#### Interface Contract

**Segmented state envelope:**
```python
class GraphState(TypedDict):
    # Segment 1: control_state — pipeline routing and metadata
    control: ControlState

    # Segment 2: tool_inputs — resolved inputs for current plan step
    tool_inputs: dict[str, Any]

    # Segment 3: tool_outputs — namespaced by tool name
    # Access: state["tool_outputs"]["product_search"]["results"]
    tool_outputs: dict[str, dict[str, Any]]

    # Segment 4: ui_projection — finalized output for SSE/frontend
    ui_projection: UIProjection
```

**Namespaced tool output key convention:**
```python
# Before (current — collision risk):
return {"search_results": [...], "product_names": [...]}

# After (namespaced):
return {
    "tool_outputs": {
        "product_search": {
            "results": [...],
            "query": "...",
            "provider": "serpapi",
            "result_count": 10,
        }
    }
}
```

**Payload size limits per segment:**
| Segment | Max size | On exceed |
|---------|---------|-----------|
| `control_state` | 10 KB | Raise `StateOverflowError` |
| `tool_inputs` | 50 KB | Raise `StateOverflowError` |
| `tool_outputs` per tool | 200 KB | Truncate + log warning |
| `ui_projection` | 500 KB | Truncate UI blocks beyond first 20 |

**Serialization safety check:**
```python
def safe_serialize_state(state: GraphState) -> str:
    """JSON-serialize state with non-serializable value stripping."""
    # Replace non-serializable objects (callbacks, generators, etc.) with placeholder
    # Log each replacement
    return json.dumps(state, default=_safe_default)
```

#### Acceptance Criteria
- [ ] All 40+ current flat keys migrated to segmented structure (backward-compatible accessor helpers provided for transition)
- [ ] `tool_outputs["<tool_name>"]` convention enforced for all new tools
- [ ] `safe_serialize_state` used exclusively by `HaltStateManager`
- [ ] State size check runs before every Redis write; `StateOverflowError` triggers graceful error response
- [ ] No `json.JSONDecodeError` or `TypeError: Object of type X is not JSON serializable` in production logs

---

### 1.7 Redis and DB Access Efficiency

#### Problem Statement
User and assistant messages are saved in two sequential `await` calls after the SSE stream has already sent the `done` event. This adds unnecessary latency to the perceived response time and risks message loss if the process restarts between the two saves. History is reloaded from DB on every request even for new sessions where no history exists. Redis has no TTL policy — all keys accumulate indefinitely.

#### Current State
```python
# In chat.py — sequential saves after stream complete
await chat_history_manager.save_user_message(...)
await chat_history_manager.save_assistant_message(...)
```

#### Interface Contract

**Batched message persistence:**
```python
async def save_turn(
    session_id: str,
    user_message: ChatMessage,
    assistant_message: ChatMessage,
) -> None:
    """
    Atomically save both messages in one transaction.
    Called as asyncio.create_task() — does not block stream finalization.
    """
    async with db.begin():
        db.add(user_message)
        db.add(assistant_message)
    # Fire and forget — stream already completed before this resolves
```

**New session detection (skip history load):**
```python
async def load_history_if_exists(session_id: str) -> list[ChatMessage] | None:
    """
    Returns None (not empty list) for new/unknown sessions.
    Uses lightweight Redis key existence check before hitting DB.
    """
    if not await redis.exists(f"session:{session_id}:exists"):
        return None
    return await db_load_history(session_id)
```

**Redis TTL policy:**
| Key pattern | TTL | Rationale |
|-------------|-----|-----------|
| `session:*:halt_state` | 3 600 s | Resume window: 1 hour |
| `session:*:exists` | 86 400 s | Session validity: 24 hours |
| `search:product:*` | 3 600 s | Product prices change hourly |
| `search:travel:*` | 86 400 s | Travel facts stable 24 h |
| `search:general:*` | 1 800 s | General: 30 min |
| `ratelimit:*` | Set by window | Managed by rate limiter |

**Stale-while-revalidate for enrichment data:**
- Affiliate link prices: serve cached, trigger background refresh if age > TTL/2
- Search context: serve stale if Perplexity unavailable, tag response with `cache_age_s`

#### Acceptance Criteria
- [ ] User + assistant messages saved in single DB transaction
- [ ] Persistence call is `asyncio.create_task()` — stream finalizes before awaiting it
- [ ] New sessions skip DB history load (verified: DB query count = 0 for first message in session)
- [ ] All Redis keys have explicit TTLs set at write time
- [ ] Redis memory usage stabilizes (no indefinite growth) after 48 h of production traffic
- [ ] p99 time from `done=true` SSE event to function return < 100 ms

---

### 1.8 Progressive Streaming Architecture

#### Problem Statement
The SSE stream mixes ephemeral status updates (which should be replaced) and persistent content (which should be appended) in a single channel. The frontend cannot distinguish them reliably without the `isPlaceholder` flag, which is a boolean convention rather than a protocol contract. If the stream closes unexpectedly (client disconnect, server crash), the frontend has no terminal event and may display a stuck loading state indefinitely.

#### Current State
All SSE events are `data: <json>` on a single channel. `status_update` is identified by field name. `done: true` is the only terminal event.

#### Interface Contract

**Named stream channels (encoded in the SSE event field):**
```
event: status
data: {"text": "Searching reviews...", "agent": "plan_executor", "step": 3, "total_steps": 8}

event: content
data: {"token": "The Sony WH-1000XM5"}

event: artifact
data: {"type": "product_cards", "blocks": [...], "clear": true}

event: done
data: {"session_id": "...", "user_id": 52, "status": "completed", "completeness": "full", "missing_sections": [], "stage_telemetry": [...]}

event: error
data: {"code": "provider_timeout", "message": "Product reviews unavailable; showing available data", "recoverable": true}
```

**Terminal semantics:**
- Every stream MUST end with either `event: done` or `event: error`
- If the server coroutine raises unhandled, a final `event: error` is emitted before the connection closes
- `completeness` field: `"full"` | `"partial"` | `"degraded"` — frontend uses this to decide whether to show the "incomplete results" banner

**Frontend consumption contract:**
```typescript
type StreamEvent =
  | { event: 'status';   data: StatusChunk }
  | { event: 'content';  data: ContentChunk }
  | { event: 'artifact'; data: ArtifactChunk }
  | { event: 'done';     data: DoneChunk }
  | { event: 'error';    data: ErrorChunk }
```

#### Acceptance Criteria
- [ ] Backend emits typed SSE events using `event:` field (not just `data:`)
- [ ] Frontend parses `event` type and routes to appropriate handler
- [ ] `status` events replace (not append) the current status display
- [ ] `content` events always append to the current message
- [ ] `artifact` events trigger `BlockRegistry` render
- [ ] Every stream ends with `done` or `error` — no hanging connections (tested with forced server crash)
- [ ] Frontend transitions to `errored` FSM state on receiving `event: error`

---

## 2. Frontend UX and Interaction Quality

### 2.1 Streaming State Machine Refactor

#### Problem Statement
`ChatContainer` manages streaming state with ad-hoc booleans (`isStreaming`, `isPlaceholder`, `hasContent`). There is no defined state machine; state transitions happen in scattered event handlers. Race conditions occur when a new message arrives while the previous stream is still open. Stale closures in SSE handlers can reference outdated message IDs.

#### Current State
State is managed with `useState` for `messages`, `isLoading`, and streaming content accumulated in refs. `isPlaceholder` is a boolean passed through `onToken`.

#### Interface Contract

**Message stream FSM:**
```typescript
type StreamState =
  | 'idle'
  | 'placeholder'         // Request sent, awaiting first event
  | 'receiving_status'    // status events arriving, no content yet
  | 'receiving_content'   // content events arriving
  | 'finalized'           // done event received
  | 'errored'             // error event received
  | 'interrupted'         // stream closed without terminal event

type StreamAction =
  | { type: 'SEND_MESSAGE' }
  | { type: 'RECEIVE_STATUS'; text: string }
  | { type: 'RECEIVE_CONTENT'; token: string }
  | { type: 'RECEIVE_ARTIFACT'; blocks: UIBlock[] }
  | { type: 'RECEIVE_DONE'; data: DoneChunk }
  | { type: 'RECEIVE_ERROR'; error: ErrorChunk }
  | { type: 'STREAM_INTERRUPTED' }
  | { type: 'RESET' }
```

**State transition table:**

| From | Action | To | Side Effect |
|------|--------|-----|-------------|
| `idle` | `SEND_MESSAGE` | `placeholder` | Create placeholder message |
| `placeholder` | `RECEIVE_STATUS` | `receiving_status` | Update status text |
| `receiving_status` | `RECEIVE_CONTENT` | `receiving_content` | Clear status, start content |
| `receiving_content` | `RECEIVE_STATUS` | `receiving_content` | (no-op — status suppressed during content) |
| `receiving_content` | `RECEIVE_DONE` | `finalized` | Commit message to state |
| Any | `RECEIVE_ERROR` | `errored` | Show error UI |
| Any (no done after 120 s) | `STREAM_INTERRUPTED` | `interrupted` | Show recovery UI |

**Implementation:** Use `useReducer` with the above `StreamAction` union. All SSE event handlers dispatch actions; no direct state mutations.

#### Acceptance Criteria
- [ ] `useReducer` with typed `StreamAction` replaces all ad-hoc streaming booleans
- [ ] Entering `interrupted` state auto-triggers after 120 s without a terminal event
- [ ] No stale closures: all handlers reference state via dispatch, not captured variables
- [ ] `errored` and `interrupted` states render distinct UI (not the same "something went wrong")
- [ ] Unit tests cover all 7 state transitions using `renderHook`

---

### 2.2 Progressive Rendering of Rich Blocks

#### Problem Statement
Rich blocks (product cards, hotel cards, flight cards) only render after the tool execution completes and the artifact SSE event arrives. Users see a blank area for the full pipeline duration (~8–15 s), then all content appears at once. There is no skeleton UI indicating that content is coming.

#### Interface Contract

**Block skeleton contracts** (one per block type):

```typescript
interface BlockSkeleton {
  type: BlockType
  estimatedCount: number   // How many items to show as skeletons
  layout: 'grid' | 'list' | 'horizontal-scroll'
}

const BLOCK_SKELETONS: Record<BlockType, BlockSkeleton> = {
  'product_cards':    { type: 'product_cards',    estimatedCount: 4, layout: 'grid' },
  'hotel_results':    { type: 'hotel_results',     estimatedCount: 3, layout: 'list' },
  'flight_results':   { type: 'flight_results',    estimatedCount: 3, layout: 'list' },
  'comparison_table': { type: 'comparison_table',  estimatedCount: 1, layout: 'list' },
  'itinerary':        { type: 'itinerary',          estimatedCount: 5, layout: 'list' },
}
```

**Rendering contract:**
1. When a `status` event is received mentioning a tool that produces a known block type, render its skeleton immediately
2. When the `artifact` event arrives for that block type, hydrate the skeleton in place
3. Skeleton dimensions must match hydrated component dimensions to prevent CLS (Cumulative Layout Shift)
4. Skeletons use `animate-pulse` Tailwind class with ivory/charcoal palette

**Tool-to-block-type mapping:**
```typescript
const TOOL_BLOCK_MAP: Record<string, BlockType> = {
  'product_search':  'product_cards',
  'product_compose': 'product_cards',
  'travel_search_hotels': 'hotel_results',
  'travel_search_flights': 'flight_results',
  'travel_itinerary': 'itinerary',
}
```

#### Acceptance Criteria
- [ ] Product card skeletons render within 500 ms of the first `status` event for a product query
- [ ] Skeleton → hydrated transition does not shift surrounding layout (CLS score 0 for this transition)
- [ ] Skeletons honor dark/light mode color scheme
- [ ] Hydration replaces skeleton in-place without unmount/remount flicker
- [ ] No skeleton shown for block types with no mapping (graceful no-op)

---

### 2.3 Message-Level Recovery UX

#### Problem Statement
When the SSE stream is interrupted (network drop, server error), the entire message is wiped and an error banner is shown. Users lose partial content. There is no way to resume or retry a single message; the only option is to re-send the full query.

#### Interface Contract

**Message model additions:**
```typescript
interface AssistantMessage {
  // ...existing fields...
  completeness: 'full' | 'partial' | 'degraded'
  interruptionReason?: 'network' | 'server_error' | 'timeout' | 'provider_failure'
  partialContent?: string         // Content accumulated before interruption
  missingSections?: string[]      // e.g. ["affiliate_links", "ranking"]
  recoveryActions?: RecoveryAction[]
}

type RecoveryAction =
  | { type: 'retry_full';       label: 'Retry' }
  | { type: 'show_partial';     label: 'Show what I have' }
  | { type: 'continue';         label: 'Continue from here' }  // Resume stream from partial state
```

**Recovery UI:**
- Interruption appends an inline "message interrupted" indicator to the partial content (not a full-page banner)
- Three action buttons appear inline below the interrupted message
- `show_partial`: reveals `partialContent` immediately, marks message as `degraded`
- `retry_full`: re-sends original query as a new message
- `continue`: sends a special resume request (requires backend halt-state support)

#### Acceptance Criteria
- [ ] Partial content is preserved in message model on stream interruption (not wiped)
- [ ] Inline recovery UI renders within the message bubble, not as a global banner
- [ ] `show_partial` action reveals accumulated content without re-querying backend
- [ ] `retry_full` action sends original message text as a new user turn
- [ ] `completeness: 'degraded'` messages display a subtle "incomplete results" indicator in editorial style

---

### 2.4 Interaction Model for Suggestions and Follow-Ups

#### Problem Statement
Follow-up suggestions are untyped strings. There is no way to distinguish a "clarify" suggestion from a "compare" or "refine" suggestion in the UI. Click provenance is not tracked, making it impossible to measure which suggestion types drive meaningful engagement. Suggestions are generated once and are not context-sensitive to partial results shown.

#### Interface Contract

**Typed suggestion schema:**
```typescript
interface NextSuggestion {
  id: string
  question: string
  category: 'clarify' | 'compare' | 'refine_budget' | 'refine_features' | 'alternate_destination' | 'deeper_research'
  confidence: number     // 0.0–1.0, from backend
  tool_gap?: string      // Which tool's output this addresses (e.g. "product_ranking")
}
```

**Backend change** — `next_step_suggestion` tool adds `category` and `confidence` to each suggestion:
```python
return {
    "next_suggestions": [
        {
            "id": "suggestion_1",
            "question": "What's your budget?",
            "category": "refine_budget",
            "confidence": 0.9,
            "tool_gap": "product_ranking"
        }
    ]
}
```

**Click provenance tracking:**
```typescript
function trackSuggestionClick(suggestion: NextSuggestion, messageId: string) {
  trackAffiliate('suggestion_click', {
    suggestion_id: suggestion.id,
    category: suggestion.category,
    message_id: messageId,
    position: index,   // 0 or 1
  })
}
```

**UI priority:** Show `clarify` suggestions first (highest utility), then `refine_*`, then `compare`, then `deeper_research`.

#### Acceptance Criteria
- [ ] `NextSuggestion` type includes `category` and `confidence` fields
- [ ] Backend populates `category` for all generated suggestions
- [ ] UI renders a subtle category label (e.g. "Refine") above suggestion chips in editorial style
- [ ] All suggestion clicks fire `trackSuggestionClick` with provenance data
- [ ] `clarify` suggestions sort before `compare` suggestions in the rendered list

---

### 2.5 Content Trust and Explainability UI

#### Problem Statement
When responses are partial or degraded (provider timeout, missing affiliate data, Perplexity unavailable), the UI shows the result as if it were complete. Users have no signal that coverage is incomplete. This is a trust issue: a user comparing 10 laptops doesn't know that affiliate prices for 3 of them are missing because eBay timed out.

#### Interface Contract

**Explainability panel (inline, collapsible):**
```typescript
interface ResponseMetadata {
  source_count: number
  provider_coverage: ProviderCoverage[]
  confidence_score: number        // 0.0–1.0 aggregate
  omitted_sections: string[]      // e.g. ["affiliate_links", "review_ranking"]
  degraded: boolean
  missing_sources: MissingSource[]
  web_context_cache_age_s?: number
}

interface ProviderCoverage {
  provider: string      // "ebay" | "amazon" | "perplexity" | "serpapi"
  status: 'ok' | 'partial' | 'unavailable' | 'timed_out'
  result_count?: number
}
```

**UI rendering rules:**
- If `degraded: false` and `missing_sources: []` — no explainability panel shown
- If `degraded: true` or `missing_sources` non-empty — show subtle inline "ⓘ Results may be incomplete" link
- Clicking expands a panel listing: sources used, timed-out providers, omitted sections
- If `confidence_score < 0.6` — show a "Low confidence" badge on the message
- Design: use terracotta (#E85D3A) accent sparingly for warning states, not red

#### Acceptance Criteria
- [ ] `ResponseMetadata` is included in the final SSE `done` event
- [ ] Explainability panel renders only when `degraded: true` or `missing_sources` non-empty
- [ ] Panel lists each timed-out provider with a human-readable name (not internal key)
- [ ] Panel is collapsible and collapsed by default
- [ ] Design matches editorial luxury aesthetic (DM Sans, warm palette, no harsh red warnings)

---

### 2.6 Design-System Consistency for Luxury Editorial Aesthetic

#### Problem Statement
Streaming states (loading, status, content, citations, cards) have inconsistent typography and spacing. Status text appears with different font sizes across components. Transitions during status → content handoff can jitter. Dark mode dynamic states have not been audited for contrast compliance.

#### Token Specification

**Typography tokens for streaming states:**
```css
/* Status / loading text */
--stream-status-font: var(--font-sans);      /* DM Sans */
--stream-status-size: 0.875rem;              /* 14px */
--stream-status-weight: 400;
--stream-status-color: var(--text-muted);    /* Muted, not primary */
--stream-status-opacity: 0.7;

/* Content streaming */
--stream-content-font: var(--font-sans);
--stream-content-size: 1rem;
--stream-content-weight: 400;
--stream-content-color: var(--text-primary);

/* Citation / source labels */
--citation-font: var(--font-sans);
--citation-size: 0.75rem;
--citation-weight: 500;
--citation-color: var(--color-primary);      /* #1B4DFF */
```

**Motion spec:**
- Status text transitions: `opacity 150ms ease-out` only — no position/size animation
- Status → content handoff: crossfade `150ms ease-in-out`
- Skeleton → hydration: `opacity 200ms ease-in` (fade in, no slide)
- Card entrance: `opacity 200ms ease-out, transform 200ms ease-out` (`translateY(4px)` → `translateY(0)`)
- No animation for token-by-token content streaming (no `transform`, no `opacity` per token)
- `prefers-reduced-motion`: all transitions collapse to instant

**Contrast requirements (WCAG AA minimum):**
| State | Element | Light mode | Dark mode |
|-------|---------|-----------|-----------|
| Status text | Body | 4.5:1 minimum | 4.5:1 minimum |
| Skeleton | Background | No text, pulse only | No text |
| Degraded badge | Background + text | 4.5:1 | 4.5:1 |

#### Acceptance Criteria
- [ ] CSS tokens defined in `globals.css` under `:root` and `.dark`
- [ ] All streaming state components reference tokens (no hardcoded colors in streaming states)
- [ ] Motion spec codified in `tailwind.config.ts` as custom animation utilities
- [ ] `prefers-reduced-motion` media query disables all transitions
- [ ] WCAG AA contrast verified for all streaming states in both light and dark mode

---

## 3. Reliability, Security, and Governance

### 3.1 API Trust Boundary Enforcement

#### Problem Statement
The chat endpoint accepts `user_id` and `session_id` from the request body. An unauthenticated client can pass any `user_id` and potentially read or corrupt another user's conversation history. The affiliate click tracking endpoint is unauthenticated — anyone can POST to inflate click counts.

#### Current State
```python
# In chat.py — user_id taken directly from request body
body.user_id = request.user_id  # No ownership check
```

#### Interface Contract

**Server-authoritative identity rules:**
1. If request has valid JWT: `user_id` is derived from JWT claims only. Client-supplied `user_id` is ignored.
2. If request is anonymous: `user_id` is generated server-side (or taken from signed session cookie). Client-supplied `user_id` is ignored.
3. `session_id` must be validated: if the session exists in DB, verify it belongs to the derived `user_id` before loading history.

**Session ownership check:**
```python
async def verify_session_ownership(
    session_id: str,
    user_id: int | None,
    db: AsyncSession,
) -> bool:
    """Returns True if session belongs to user_id, or session is new (no owner)."""
    session = await db.get(ChatSession, session_id)
    if session is None:
        return True   # New session, no ownership conflict
    if session.user_id is None:
        return True   # Anonymous session, no claim
    return session.user_id == user_id
```

**Affiliate click tracking — rate-limited, optionally authenticated:**
```python
# Rate limit: 10 clicks per IP per minute (prevents inflation)
# No auth required, but IP-scoped rate limit enforced
@router.post("/affiliate/click")
@Depends(check_rate_limit_by_ip)
async def track_affiliate_click(...):
```

#### Acceptance Criteria
- [ ] `user_id` from request body is ignored when JWT is present
- [ ] `user_id` from request body is ignored for anonymous requests (server generates)
- [ ] `verify_session_ownership` called on every request with a `session_id`
- [ ] Returning 403 if session belongs to a different user (not a silent data exposure)
- [ ] Affiliate click endpoint has IP-scoped rate limit: 10/min
- [ ] Integration test: assert that passing `user_id=1` as unauthenticated user does not return user 1's history

---

### 3.2 Proxy-Aware Rate Limiting Integrity

#### Problem Statement
Rate limiting uses client IP from `request.client.host`. On Railway behind a reverse proxy, this is always the proxy IP, not the real client IP. This means all requests share the same rate limit bucket, either making rate limiting useless or blocking all users simultaneously.

#### Interface Contract

**Trusted proxy configuration:**
```python
TRUSTED_PROXY_IPS: list[str] = settings.TRUSTED_PROXY_CIDRS  # e.g. ["10.0.0.0/8"]

def get_real_client_ip(request: Request) -> str:
    """
    Extract real client IP, trusting X-Forwarded-For only from known proxy CIDRs.
    Returns request.client.host if proxy is not trusted.
    """
    if request.client and is_trusted_proxy(request.client.host, TRUSTED_PROXY_IPS):
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        # Take the leftmost IP (client), not rightmost (last proxy)
        real_ip = forwarded_for.split(",")[0].strip()
        if real_ip:
            return real_ip
    return request.client.host if request.client else "unknown"
```

**Rate limit identifier strategy:**
| Request type | Identifier |
|-------------|------------|
| Authenticated | `user:{user_id}` |
| Anonymous | `ip:{real_client_ip}` |

#### Acceptance Criteria
- [ ] `TRUSTED_PROXY_CIDRS` env var documented and set on Railway
- [ ] `get_real_client_ip` used everywhere rate limiting reads the client IP
- [ ] `X-Forwarded-For` is only trusted from IPs in `TRUSTED_PROXY_CIDRS`
- [ ] Regression test: assert that two requests from different real IPs do not share a rate limit bucket even behind a proxy

---

### 3.3 Provider Capability Manifest at Startup

#### Problem Statement
When environment variables for optional providers (Booking.com, Viator, Perplexity) are missing, providers silently fail to register. The backend starts normally but returns degraded results without any observable signal. There is no startup report, no readiness endpoint that reflects provider state, and no way to diagnose a partial boot.

#### Interface Contract

**Startup capability report:**
```python
@dataclass
class ProviderCapabilityReport:
    provider: str
    enabled: bool
    status: Literal["ok", "missing_env", "import_error", "init_error"]
    missing_vars: list[str]   # Which env vars are absent
    error_message: str | None

@dataclass
class StartupManifest:
    timestamp: str
    providers: list[ProviderCapabilityReport]
    search_provider: str       # Active search provider name
    llm_model: str             # Active LLM model
    rate_limiting_enabled: bool
    all_critical_providers_ok: bool
```

**Readiness endpoint:**
```
GET /health/ready
```
Response:
```json
{
  "status": "ok",           // "ok" | "degraded" | "unavailable"
  "manifest": { ... },      // StartupManifest
  "timestamp": "2026-02-22T00:00:00Z"
}
```
- Returns `200` for both `ok` and `degraded` (service is up, just limited)
- Returns `503` only if critical providers (LLM, DB) are unavailable

**Logging at startup:**
```
[startup] Provider manifest:
  ✅ openai (llm)         — ok
  ✅ perplexity (search)  — ok
  ✅ serpapi (reviews)    — ok
  ✅ amazon (affiliate)   — ok
  ⚠️  booking (travel)   — missing_env: BOOKING_AFFILIATE_ID
  ❌ viator (travel)      — missing_env: VIATOR_API_KEY, VIATOR_CAMPAIGN_ID
```

#### Acceptance Criteria
- [ ] `StartupManifest` generated and logged at application startup (before first request)
- [ ] `GET /health/ready` returns manifest in response body
- [ ] Missing env var causes `status: "missing_env"` (not a crash)
- [ ] Import error on a provider module causes `status: "import_error"` (not a crash)
- [ ] `all_critical_providers_ok: false` when LLM or DB is unavailable → `GET /health/ready` returns 503
- [ ] `all_critical_providers_ok: true` even when optional providers (Booking, Viator) are absent

---

### 3.4 Contract Validation at Tool Boundaries

#### Problem Statement
Tools write arbitrary keys to `GraphState` with no schema validation. A tool returning `{"search_results": "error string"}` instead of `{"search_results": []}` propagates silently and causes a `TypeError` dozens of steps later, making root cause analysis extremely difficult. There is no runtime enforcement of the tool output contract.

#### Interface Contract

**Tool output schema (using Pydantic):**
```python
from pydantic import BaseModel, field_validator

class ProductSearchOutput(BaseModel):
    results: list[dict]
    query: str
    provider: str
    result_count: int

class ToolOutputValidator:
    _schemas: dict[str, type[BaseModel]] = {
        "product_search": ProductSearchOutput,
        "travel_search_hotels": HotelSearchOutput,
        # ... one schema per tool
    }

    @classmethod
    def validate(cls, tool_name: str, output: dict) -> dict:
        schema = cls._schemas.get(tool_name)
        if schema is None:
            return output  # No schema registered, pass through
        try:
            validated = schema(**output)
            return validated.model_dump()
        except ValidationError as e:
            logger.error(f"[tool_validator] {tool_name} output schema violation: {e}")
            # Quarantine: return empty-but-valid output
            return schema.model_construct().model_dump()
```

**Integration point in plan_executor:**
```python
raw_output = await tool_fn(state)
validated_output = ToolOutputValidator.validate(tool_name, raw_output)
state.update(validated_output)
```

#### Acceptance Criteria
- [ ] Pydantic output schemas defined for the 5 highest-risk tools (product_search, product_compose, travel_search_hotels, travel_search_flights, product_normalize)
- [ ] `ToolOutputValidator.validate` called for every tool invocation in `plan_executor`
- [ ] Schema violation logs `ERROR` with full Pydantic error detail
- [ ] Schema violation returns empty-but-valid output (does not crash pipeline)
- [ ] Unit test: pass malformed tool output through validator, assert pipeline continues

---

## 4. Observability and Continuous Optimization

### 4.1 Unified Trace Model

#### Problem Statement
Frontend interactions have no correlation to backend traces. Langfuse traces are scoped to `session_id` but not to individual request IDs. Tool-level spans are not emitted (only LLM call spans exist). It is impossible to attribute user-perceived latency to a specific backend stage by looking at Langfuse alone.

#### Interface Contract

**Correlation ID chain:**
```
frontend_interaction_id    (generated in browser, UUID4, attached to every SSE request)
    └─ backend_request_id  (generated at API entry, attached to all logs in request scope)
        └─ graph_run_id    (LangGraph execution ID, from astream_events)
            └─ tool_call_ids  (per tool invocation, generated by executor)
```

**Frontend: attach interaction ID to request:**
```typescript
const interactionId = crypto.randomUUID()
// Sent as header:
headers: { 'X-Interaction-ID': interactionId }
// Stored in message metadata for correlation
```

**Backend: propagate IDs through log context:**
```python
# In chat.py, at request entry:
request_id = request.headers.get("X-Interaction-ID") or str(uuid4())
with logger.contextualize(request_id=request_id, session_id=session_id):
    # All logs in this scope automatically include request_id
```

**Frontend: emit render milestones:**
```typescript
const milestones = {
  request_sent_ts: Date.now(),
  first_status_ts: null as number | null,
  first_content_ts: null as number | null,
  first_artifact_ts: null as number | null,
  done_ts: null as number | null,
}
// On done event, POST milestones to /v1/telemetry/render with interaction_id
```

#### Acceptance Criteria
- [ ] `X-Interaction-ID` header sent with every chat request from frontend
- [ ] Backend includes `request_id` in all log lines for a given request
- [ ] Langfuse trace includes `request_id` as a tag
- [ ] `StageTelemetry` (from 1.1) referenced by `tool_call_id` in Langfuse spans
- [ ] Frontend render milestones posted to backend; stored for p95 "time-to-first-content" calculation
- [ ] `GET /v1/admin/trace/:interaction_id` returns full correlated trace (admin only)

---

### 4.2 Quality-of-Service Dashboards

#### Problem Statement
No dashboard exists for production performance metrics. It is unknown what the p50/p95/p99 latency is, what the tool timeout rate is by provider, or what percentage of responses are degraded. Regressions are discovered via user complaints, not proactive monitoring.

#### Core Metrics

**Latency:**
| Metric | Target | Alert threshold |
|--------|--------|----------------|
| p50 total response latency | < 8 s | > 12 s |
| p95 total response latency | < 20 s | > 30 s |
| p99 total response latency | < 45 s | > 60 s |
| Time-to-first-visible-content | < 3 s | > 6 s |

**Reliability:**
| Metric | Target | Alert threshold |
|--------|--------|----------------|
| Stream completion rate | > 98% | < 95% |
| Partial/degraded response rate | < 5% | > 15% |
| Tool timeout rate (per provider) | < 2% | > 5% |
| Provider error rate | < 1% | > 3% |

**Implementation approach:**
- Emit structured JSON log lines per request with all metric fields
- Use Railway log drain → external aggregator (Datadog, Grafana Cloud, or Axiom)
- Alternatively: write metrics to a `request_metrics` Postgres table; query via Metabase

#### Acceptance Criteria
- [ ] Every completed request emits a structured JSON log with: `request_id`, `session_id`, `intent`, `total_duration_ms`, `completeness`, `tool_durations` (dict), `provider_errors` (list)
- [ ] Dashboard exists showing p50/p95/p99 latency over 24 h rolling window
- [ ] Dashboard shows per-provider tool timeout rate
- [ ] Alert fires when p95 > 30 s for 5 consecutive minutes
- [ ] Degraded response rate visible and below 5% in steady state

---

### 4.3 Controlled Degradation Policies

#### Problem Statement
The system has no defined behavior when dependencies fail. Redis going down currently causes an unhandled exception at rate limiting. Perplexity being unavailable silently falls back (via broad try/except) but with no user-visible signal. There is no explicit policy document or enforcement for fail-open vs. fail-closed decisions.

#### Degradation Policy Table

| Dependency | Failure mode | Policy | User signal |
|-----------|-------------|--------|-------------|
| Redis (rate limiting) | Connection error | **Fail open** — allow request, log WARNING | None |
| Redis (halt state) | Connection error | **Fail closed** — return 503, explain multi-turn unavailable | "Conversation memory temporarily unavailable" |
| Redis (search cache) | Connection error | **Fail open** — skip cache, hit provider directly | None |
| Perplexity (search) | Any error | **Fail open** — LLM-only response, set `degraded=True` | "ⓘ Results may be incomplete" |
| SerpAPI (reviews) | Timeout | **Fail open** — continue without review data | `missing_sources: ["review_search"]` |
| eBay affiliate | Error | **Fail open** — omit eBay products | `missing_sources: ["ebay"]` |
| Amazon affiliate | Error | **Fail open** — omit Amazon products | `missing_sources: ["amazon"]` |
| OpenAI (LLM) | Any error | **Fail closed** — return 503 | "AI service temporarily unavailable" |
| PostgreSQL | Connection error | **Fail closed** — return 503 | "Service temporarily unavailable" |

**Policy enforcement:**
```python
class DegradationPolicy:
    FAIL_OPEN = "fail_open"
    FAIL_CLOSED = "fail_closed"

    POLICIES: dict[str, str] = {
        "redis_rate_limit": FAIL_OPEN,
        "redis_halt_state": FAIL_CLOSED,
        "redis_cache": FAIL_OPEN,
        "perplexity": FAIL_OPEN,
        "serpapi": FAIL_OPEN,
        "ebay": FAIL_OPEN,
        "amazon": FAIL_OPEN,
        "openai": FAIL_CLOSED,
        "postgres": FAIL_CLOSED,
    }
```

**Policy switches** (env var overrides for incident response):
```
DEGRADE_PERPLEXITY=fail_closed   # Disable Perplexity entirely during incident
DEGRADE_SERPAPI=fail_closed      # Disable SerpAPI to reduce costs
```

#### Acceptance Criteria
- [ ] `DegradationPolicy` class implemented with all policies from table above
- [ ] Redis rate limit failure is caught and logged as WARNING; request proceeds
- [ ] Redis halt state failure returns 503 with user-readable message
- [ ] Perplexity failure sets `degraded=True` in response; explainability panel shows it
- [ ] OpenAI failure returns 503 (not 500 or silent hang)
- [ ] `DEGRADE_<PROVIDER>=fail_closed` env var overrides policy at runtime (no restart required)
- [ ] Policy table is logged at startup as part of `StartupManifest`

---

## Implementation Priority

### Phase 1 — Critical (address immediately)
| RFC section | Reason |
|-------------|--------|
| 3.1 API Trust Boundary | Live security exposure: client-supplied user_id |
| 1.4 Search Context Safety | Live prompt injection surface |
| 3.2 Proxy-Aware Rate Limiting | Rate limiting is ineffective today |
| 1.3 Tool Execution Timeouts | Any provider timeout stalls all users |

### Phase 2 — High Value (next sprint)
| RFC section | Reason |
|-------------|--------|
| 1.2 Query Complexity Gate | Immediate cost and latency reduction |
| 1.7 Batched DB Writes | Quick win, reduces tail latency |
| 3.3 Startup Manifest | Stops silent partial boots |
| 2.1 Streaming FSM | Eliminates race condition class |
| 4.3 Degradation Policies | Defines behavior during incidents |

### Phase 3 — Architectural
| RFC section | Reason |
|-------------|--------|
| 1.6 State Segmentation | Large migration, high payoff |
| 1.8 Named Stream Channels | Requires frontend + backend coordination |
| 2.2 Block Skeletons | Depends on 1.8 |
| 4.1 Unified Trace Model | Enables all other observability |
| 4.2 QoS Dashboards | Depends on 4.1 |

---

*This RFC is a living document. Each section should be linked to a GitHub Issue when implementation begins. Mark sections with `[IMPLEMENTED]` and the PR number when complete.*
