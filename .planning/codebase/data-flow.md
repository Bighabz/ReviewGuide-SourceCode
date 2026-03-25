# Request Lifecycle: User Input to Response

**Analysis Date:** 2026-03-25

## Overview

This document traces the complete lifecycle of a user chat message from the frontend `ChatContainer` through the backend LangGraph pipeline, MCP tool execution, provider API calls, and back to the frontend as an SSE stream.

## Phase 1: Frontend Request

**Files:** `frontend/lib/chatApi.ts`, `frontend/components/ChatContainer.tsx`

1. User types message in `ChatInput` component
2. `ChatContainer` calls `streamChat()` from `frontend/lib/chatApi.ts`
3. Request payload:
   ```json
   {
     "message": "best noise cancelling headphones under $200",
     "session_id": "uuid-string",
     "user_id": 42,
     "country_code": "US",
     "action": null
   }
   ```
4. Frontend opens `fetch()` connection to `POST /v1/chat/stream`
5. Response is an SSE event stream (`text/event-stream`)

## Phase 2: API Endpoint Setup

**File:** `backend/app/api/v1/chat.py` -> `stream_chat()` and `generate_chat_stream()`

1. **Auth and Rate Limiting:**
   - `get_current_user()` dependency extracts user from JWT or creates anonymous user
   - `check_rate_limit()` dependency enforces per-IP/per-session limits
   - Returns `StreamingResponse(generate_chat_stream(...), media_type="text/event-stream")`

2. **Session Context Loading:**
   - `_load_session_context(session_id)` runs concurrently:
     - `HaltStateManager.get_halt_state(session_id)` -- checks process cache, then Redis key `halt_state:{session_id}`
     - `chat_history_manager.get_history(session_id)` -- checks Redis cache `chat_history:{session_id}`, then PostgreSQL
   - Returns `(halt_state_data, conversation_history)`

3. **Halt State Processing:**
   - If halt exists with `halt_reason == "consent_required"`: Check if user confirmed extended search
   - If halt exists with followups: This is a clarification resume
   - If halt exists but no followups: Stale halt state, delete and treat as new query

4. **Initial State Construction:**
   - Builds full `GraphState` TypedDict (~60 fields) with:
     - `user_message`, `session_id`, `conversation_history`
     - Restored `intent`, `slots`, `plan` from halt state (if resuming)
     - `country_code` in initial_slots for regional affiliate links
     - `extended_search_confirmed` flag for consent resume
     - Empty accumulators for `errors`, `citations`, `stage_telemetry`, etc.
   - Key: `initial_state["next_agent"]` is set to `"tiered_executor"` for consent resumes, `None` otherwise

5. **Stream Initiation:**
   - Yields initial `status` SSE event: `{"text": "Thinking...", "agent": "init"}`
   - Creates background `asyncio.Task` running `graph.astream_events(initial_state, version="v2", config={"callbacks": [langfuse_handler]})`
   - Events fed to `asyncio.Queue` for ordered processing

## Phase 3: LangGraph Pipeline

**File:** `backend/app/services/langgraph/workflow.py`

### Node 1: Safety Agent (`agent_safety`)

**File:** `backend/app/agents/safety_agent.py`

**Input:** `user_message`, `session_id`

**Processing:**
1. **Halt Resume Check:** If `session_id` has halt state in Redis with followups, restore intent/slots/plan and route directly to `agent_clarifier` (skips intent/planner)
2. **Content Moderation:** Calls `OpenAI.moderations.create(input=text)`. Only blocks truly harmful categories (violence, self-harm, sexual/minors, hate/threatening). Mild profanity is logged but allowed.
3. **PII Detection:** Regex patterns for email, phone, SSN, credit card, IP address. Detected PII is replaced with `[REDACTED_TYPE_N]` tokens.
4. **Jailbreak Detection:** Keyword matching for "ignore previous", "system prompt", "pretend you are", etc.
5. **Conversation History Update:** Appends user message to `conversation_history` accumulator.
6. **Message Persistence:** Saves user message to PostgreSQL via `ConversationRepository.save_message()`. Invalidates and reloads chat history cache.

**Output:** `policy_status` (allow/block/unchecked), `sanitized_text`, `redaction_map`, `next_agent` (intent/clarifier/END)

**Timeout Budget:** 2s soft, 4s hard. Fallback: `policy_status="unchecked"`, pass through to intent.

### Node 2: Intent Agent (`agent_intent`)

**File:** `backend/app/agents/intent_agent.py`

**Input:** `sanitized_text`, `conversation_history`, `last_search_context`

**Processing:**
1. **Cache Check:** MD5 hash of text -> in-memory cache with 5-min TTL (only for standalone messages without conversation context)
2. **Context Building:** If `last_search_context` has category/products, adds "ACTIVE PRODUCT CONTEXT" hint to system prompt
3. **LLM Call:** GPT-4o-mini with JSON mode, system prompt lists categories (intro, product, service, travel, general, unclear). Includes conversation history for context.
4. **Fallback:** Keyword-based classification if LLM fails (travel keywords, product keywords, etc.)

**Output:** `intent` (product/service/travel/general/intro/unclear/comparison), `next_agent` = "planner"

**Timeout Budget:** 3s soft, 6s hard. Fallback: `intent="general"`

### Node 3: Planner Agent (`agent_planner`)

**File:** `backend/app/agents/planner_agent.py`

**Input:** `user_message`, `intent`, `slots`

**Processing:**
1. **Query Complexity Classification:** `classify_query_complexity()` determines simple/moderate/complex
2. **Tool Catalog Generation:** `format_non_default_contracts_for_prompt(intent)` generates TOON-formatted list of selectable tools (non-default tools for the intent)
3. **LLM Call:** GPT-4o-mini selects entry-point tools from catalog based on user request and tool purpose/not_for fields
4. **Dependency Expansion:** `get_required_tools_from_dependencies(selected_tools, intent)` follows pre/post chains and adds required default tools
5. **Plan Construction:** Builds a plan dict with `steps` array, each step having `id`, `tools`, `description`, `parallel`, `depends_on`

**Output:** `plan` dict, `next_agent` = "clarifier"

**Timeout Budget:** 5s soft, 10s hard. Fallback: Minimal plan with single `{intent}_compose` tool.

### Node 4: Clarifier Agent (`agent_clarifier`)

**File:** `backend/app/agents/clarifier_agent.py` (48K lines -- the largest agent)

**Input:** `plan`, `slots`, `user_message`, `conversation_history`

**Processing:**
1. **Slot Extraction:** LLM extracts structured data from user message + history (product name, category, budget, brand, destination, dates, etc.)
2. **Required Slot Check:** Determines which slots are required based on intent and plan tools
3. **Missing Slot Detection:** If required slots are missing, generates follow-up questions
4. **Halt Decision:** If follow-up questions needed:
   - Sets `status="halted"`, `halt=True`
   - Writes `assistant_text` with the clarification question
   - Saves state to Redis via `HaltStateManager`
   - `next_agent=None` -> workflow ends, SSE stream closes
5. **Proceed Decision:** If all slots filled, sets `next_agent="plan_executor"` or `"routing_gate"`

**Output:** Updated `slots`, `followups`, `next_agent` (plan_executor/routing_gate/None), `status`

**Timeout Budget:** 4s soft, 8s hard. Fallback: Skip clarification, proceed to execution.

### Node 5a: Routing Gate (conditional)

**File:** `backend/app/services/langgraph/nodes/routing_gate.py`

**Deterministic Intents** (route to tiered executor): product, comparison, price_check, travel, review_deep_dive

**LLM Intents** (route to planner): general, unclear, intro, service

**Output:** `routing_mode` (tiered/llm), `next_agent` (tiered_executor/planner)

### Node 5b: Tiered Executor (conditional)

**File:** `backend/app/services/langgraph/nodes/tiered_executor.py`

**Wraps:** `TieredAPIOrchestrator.execute()` from `backend/app/services/tiered_router/orchestrator.py`

**Processing:**
1. Starts at Tier 1 (free affiliate APIs)
2. For each tier: get APIs -> filter by feature flags -> parallel fetch -> validate results
3. If `ValidationResult.SUFFICIENT`: return results + `next_agent="synthesizer"` (maps to plan_executor)
4. If `ValidationResult.ESCALATE`: move to next tier
5. If `ValidationResult.CONSENT_REQUIRED`: halt workflow, prompt user for consent
6. If `ValidationResult.MAX_TIER_REACHED`: return partial results

### Node 6: Plan Executor (`agent_plan_executor`)

**File:** `backend/app/services/plan_executor.py`

**Input:** `plan` (from planner), full GraphState

**Processing:**
1. **Fresh Instance:** Creates new `PlanExecutor()` per request to prevent cross-session state leaks
2. **Tool Registry:** `TOOL_REGISTRY` maps tool name -> function, loaded at module import from `mcp_server.tools.*`
3. **Dependency Resolution:** Topological sort of plan steps based on `depends_on` fields
4. **Step Execution:** For each step:
   - Merge state with results from previous steps
   - Execute all tools in the step in parallel via `asyncio.gather`
   - Each tool receives the full state dict
   - Each tool returns a partial state update dict
   - Results are merged into the running state
5. **Tool Timeouts:** 30s per tool, 45s per step
6. **Critical Tools:** If a compose tool (`product_compose`, `travel_compose`, `general_compose`, `intro_compose`, `unclear_compose`) fails, pipeline aborts

**Tool Execution Example (Product Intent):**
```
Step 1: product_search(state) -> {search_results, products}
Step 2: product_evidence(state) -> {review_aspects}  [parallel with:]
        product_ranking(state) -> {ranked_items}
Step 3: product_normalize(state) -> {normalized_products}
Step 4: product_affiliate(state) -> {affiliate_links}
Step 5: product_compose(state) -> {assistant_text, ui_blocks, citations}
Step 6: next_step_suggestion(state) -> {next_suggestions}
```

**Output:** `assistant_text`, `ui_blocks`, `citations`, `next_suggestions`, `status="completed"`

**Timeout Budget:** 25s soft, 45s hard. Fallback: Partial results message.

## Phase 4: Tool Execution Details

### product_search

**File:** `backend/mcp_server/tools/product_search.py`

1. Reads `user_message`, `slots` (category, brand, budget)
2. Builds search query from slots or uses LLM generation (`ENABLE_LLM_SEARCH_QUERY`)
3. Calls `search_manager.get_provider().search()` (Perplexity or OpenAI search provider)
4. Perplexity: Uses `sonar` model with domain filters per intent
5. OpenAI: Uses web search with citations
6. Returns `search_results` list and `search_query`

### product_affiliate

**File:** `backend/mcp_server/tools/product_affiliate.py`

1. Reads `normalized_products` from state
2. If `USE_CURATED_LINKS=True`: Matches against `CURATED_LINKS` keyword patterns first
3. For each product, calls `affiliate_manager.search_products()` with product name
4. Runs eBay + Amazon (+ CJ if enabled) in parallel
5. Returns `affiliate_products` dict: `{"ebay": [...], "amazon": [...], "cj": [...]}`

### product_compose

**File:** `backend/mcp_server/tools/product_compose.py` (~51K, largest tool)

1. Reads `user_message`, `normalized_products`, `affiliate_links`, `review_data`
2. Merges affiliate links into product data
3. Generates LLM response in "Uncle Mike" persona format
4. Builds `ui_blocks` with product cards, affiliate links, review sources
5. Returns `assistant_text`, `ui_blocks`, `citations`

### travel_search_hotels

**File:** `backend/mcp_server/tools/travel_search_hotels.py`

1. Reads `destination`, `check_in`, `check_out` from `slots`
2. Calls `TravelManager.search_hotels()` from `backend/app/services/travel/manager.py`
3. TravelManager routes to configured hotel providers (Amadeus, Booking, Expedia, or Mock)
4. Returns `hotels` list of `HotelCard` objects

### review_search

**File:** `backend/mcp_server/tools/review_search.py`

1. Reads `product_names` from state
2. If `ENABLE_SERPAPI=True`: Calls `SerpAPIClient` from `backend/app/services/serpapi/client.py`
3. Runs parallel searches across Google, Google Shopping, Reddit (via Serper.dev)
4. Applies authority scoring based on `TRUSTED_SOURCES` dict
5. Redis-cached with 24h TTL
6. Returns `review_data` dict: `{product_name: ReviewBundle}`

## Phase 5: SSE Response Streaming

**File:** `backend/app/api/v1/chat.py` -> `generate_chat_stream()` -> `_drain_event_loop()`

### During Workflow Execution:

1. **Agent Start Events:** Logged but not streamed to frontend (progress messages suppressed)
2. **Mid-Workflow Streaming:** If a node returns `stream_chunk_data`:
   - `type="tool_citation"`: Streamed as `status` event (e.g., "Searching for hotels...")
   - Other types (itinerary, hotel cards): Streamed as `artifact` event immediately
3. **60-Second Hard Limit:** `time.time() >= deadline` check on every queue drain iteration

### After Workflow Completes:

1. **Clear Placeholder:** Sends `artifact` event with `{"clear": true}` to remove "Thinking..." message
2. **UI Blocks (Product):** For product intent, sends `artifact` event with `ui_blocks` combined with `clear` flag
3. **Text Streaming:** Chunks `assistant_text` into 24-char pieces with 20ms delay per chunk
4. **Response Metadata:** Builds `response_metadata` with:
   - `source_count`: Number of citations
   - `provider_coverage`: Array of `{provider, status, result_count}` per provider
   - `confidence_score`: 1.0 (all ok), 0.5 (some failed), 0.3 (critical failed)
   - `degraded`: Boolean flag
5. **Done Event:** Final `done` event with full payload:
   ```json
   {
     "session_id": "...",
     "request_id": "...",
     "status": "completed",
     "intent": "product",
     "ui_blocks": [...],
     "citations": [...],
     "followups": null,
     "next_suggestions": [...],
     "user_id": 42,
     "completeness": "full",
     "response_metadata": {...},
     "stage_telemetry": [...]
   }
   ```

### Post-Stream Cleanup:

1. **Halt State:** If workflow completed (not halted), delete halt state from Redis
2. **Message Persistence:** Save assistant response to PostgreSQL (fire-and-forget)
3. **QoS Logging:** Log structured QoS payload with `request_id`, duration, intent
4. **QoS Persistence:** Write `RequestMetric` to database (fire-and-forget)
5. **Langfuse:** Tag trace with `request_id` for lookup

## Phase 6: Frontend Processing

**Files:** `frontend/lib/chatApi.ts`, `frontend/components/ChatContainer.tsx`, `frontend/components/Message.tsx`

1. **SSE Parsing:** `streamChat()` reads SSE events and dispatches to callback handlers
2. **Status Events:** Update loading indicator text
3. **Content Events:** Append text tokens to message content (typing effect)
4. **Artifact Events:** Handle `clear` (remove placeholder), `ui_blocks` (render cards)
5. **Done Event:** Finalize message with citations, followups, next_suggestions, response_metadata
6. **Message Rendering:** `Message.tsx` dispatches `ui_blocks` through `BlockRegistry.tsx` to typed components (ProductCards, HotelCards, FlightCards, ComparisonTable, etc.)

## Halt/Resume Flow (Multi-Turn)

### Halt:
1. Clarifier determines required slots are missing
2. Sets `status="halted"`, `halt=True`, `assistant_text="What's your budget?"`
3. `chat.py` detects halt in result_state
4. `HaltStateManager.update_halt_state()` saves intent, slots, followups, plan to Redis
5. Streams `done` event with `followups` field
6. Frontend renders clarification question in styled bubble

### Resume:
1. User answers ("under $200"), sends new request with same `session_id`
2. `chat.py` loads halt state and conversation history concurrently
3. Safety node detects halt state has followups -> restores intent/slots/plan
4. Sets `next_agent="clarifier"` (skips intent/planner re-execution)
5. Clarifier merges new answer into existing slots
6. If all slots filled: proceeds to execution
7. If still missing: halts again with next question

## Consent Flow (Tiered Routing)

### Consent Required:
1. Tiered executor reaches Tier 3-4 boundary
2. DataValidator returns `CONSENT_REQUIRED`
3. Tiered executor halts: `status="halted"`, `halt_reason="consent_required"`, `consent_prompt={...}`
4. Partial results saved to halt state
5. Frontend shows consent prompt with "Search Deeper" button

### Consent Confirmed:
1. User clicks "Search Deeper" (sends `action="consent_confirm"` or text "yes")
2. `is_consent_confirmation()` detects consent
3. `initial_state["extended_search_confirmed"] = True`
4. `initial_state["next_agent"] = "tiered_executor"` (resume directly)
5. Tiered executor continues to Tier 3-4 with consent flag
6. Results flow to plan_executor for synthesis

## Search Provider Data Flow

### Perplexity Provider

**File:** `backend/app/services/search/providers/perplexity_provider.py`

```
product_search tool
  -> search_manager.get_provider()  [PerplexitySearchProvider]
  -> search(query, intent="product", max_results=10, search_domain_filter=["ebay.com"])
  -> POST https://api.perplexity.ai/chat/completions
     model: "sonar"
     messages: [{role: "system", content: "..."}, {role: "user", content: query}]
  -> Parse response, extract URLs, titles, snippets
  -> Return List[SearchResult]
```

### OpenAI Provider

**File:** `backend/app/services/search/providers/openai_provider.py`

```
product_search tool
  -> search_manager.get_provider()  [OpenAISearchProvider]
  -> search(query, intent="product", max_results=10)
  -> POST https://api.openai.com/v1/chat/completions
     model: "gpt-4o-mini"
     web_search_options: {search_context_size: "medium"}
  -> Parse response with citations
  -> Return List[SearchResult]
```

## External Integration Map

| Integration | SDK/Client | Config Vars | Used By |
|-------------|-----------|-------------|---------|
| OpenAI GPT-4o/mini | `langchain-openai` ChatOpenAI | `OPENAI_API_KEY`, `DEFAULT_MODEL` | All agents via ModelService |
| OpenAI Moderation | `openai` AsyncOpenAI | `OPENAI_API_KEY` | SafetyAgent |
| Perplexity Sonar | `httpx` | `PERPLEXITY_API_KEY`, `PERPLEXITY_MODEL` | product_search, general_search |
| OpenAI Web Search | `httpx` | `OPENAI_API_KEY`, `OPENAI_SEARCH_*` | product_search (alternative) |
| Amazon PA-API v5 | `httpx` (signed) | `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY` | AmazonAffiliateProvider |
| eBay Browse API | `httpx` | `EBAY_APP_ID`, `EBAY_CERT_ID` | EbayAffiliateProvider |
| CJ Product Search | `httpx` (XML) | `CJ_API_KEY`, `CJ_WEBSITE_ID` | CJAffiliateProvider |
| Serper.dev | `httpx` | `SERPAPI_API_KEY` | SerpAPIClient (review_search) |
| Amadeus | `httpx` | `AMADEUS_API_KEY`, `AMADEUS_API_SECRET` | AmadeusProvider (flights) |
| Booking.com | `httpx` | `BOOKING_API_KEY` | BookingProvider (hotels) |
| Skyscanner | `httpx` | `SKYSCANNER_API_KEY` | SkyscannerProvider (flights) |
| Langfuse | `langfuse` + `langfuse.langchain` | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | Tracing in chat.py |
| Redis | `redis.asyncio` | `REDIS_URL` | HaltState, ChatHistory, Cache |
| PostgreSQL | `sqlalchemy.ext.asyncio` (asyncpg) | `DATABASE_URL` | All models |

---

*Data flow analysis: 2026-03-25*
