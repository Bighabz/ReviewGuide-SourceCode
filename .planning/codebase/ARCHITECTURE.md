# Backend Architecture

**Analysis Date:** 2026-03-25

## Pattern Overview

**Overall:** Multi-agent LangGraph state machine with MCP tool execution, blackboard-pattern shared state, and plugin-based provider registries.

**Key Characteristics:**
- LangGraph StateGraph drives a 5-agent pipeline (Safety, Intent, Planner, Clarifier, PlanExecutor) plus 2 tiered-routing nodes
- GraphState TypedDict serves as a blackboard -- every agent reads/writes fields on a single shared dict
- MCP tools are called in-process (not via subprocess/JSON-RPC) by PlanExecutor, which resolves dependency DAGs and parallelizes where possible
- Affiliate, search, and travel providers use decorator-based registry/loader patterns for auto-discovery
- Redis provides halt-state persistence, search caching, and chat history caching; PostgreSQL stores conversations and user data
- SSE streaming delivers real-time progress and final results to the frontend

## Layers

**API Layer (FastAPI):**
- Purpose: HTTP endpoints, request validation, SSE streaming, auth, rate limiting
- Location: `backend/app/api/v1/`
- Contains: Route handlers, Pydantic request/response models, SSE event formatting
- Depends on: LangGraph workflow, Redis, PostgreSQL, auth/rate-limit dependencies
- Used by: Frontend Next.js client via `frontend/lib/chatApi.ts`
- Key files:
  - `backend/app/api/v1/chat.py` -- SSE streaming chat endpoint (main entry point, ~750 lines)
  - `backend/app/api/v1/health.py` -- Liveness, health, and readiness probes
  - `backend/app/api/v1/admin.py` -- Admin dashboard APIs
  - `backend/app/api/v1/admin_auth.py` -- Admin authentication (JWT)
  - `backend/app/api/v1/admin_users.py` -- User management
  - `backend/app/api/v1/affiliate.py` -- Click tracking, CJ search proxy
  - `backend/app/api/v1/telemetry.py` -- Telemetry/trace lookup
  - `backend/app/api/v1/qos.py` -- QoS metrics

**Agent Layer (LangGraph Nodes):**
- Purpose: Sequential reasoning pipeline -- safety checks, intent classification, plan generation, clarification, execution
- Location: `backend/app/agents/` (agent classes), `backend/app/services/langgraph/` (workflow wiring)
- Contains: Agent classes inheriting `BaseAgent`, node wrapper functions, routing logic
- Depends on: ModelService (LLM calls via LangChain ChatOpenAI), HaltStateManager, tool contracts
- Used by: LangGraph StateGraph compiled in `backend/app/services/langgraph/workflow.py`
- Key files:
  - `backend/app/agents/base_agent.py` -- Abstract base with `generate()` method wrapping ModelService
  - `backend/app/agents/safety_agent.py` -- OpenAI Moderation API + PII regex + jailbreak detection
  - `backend/app/agents/intent_agent.py` -- LLM-based intent classification (product/travel/general/intro/unclear/service/comparison)
  - `backend/app/agents/planner_agent.py` -- LLM selects entry-point MCP tools; dependency graph auto-expanded
  - `backend/app/agents/clarifier_agent.py` -- Slot extraction, follow-up question generation, halt-state management
  - `backend/app/agents/query_complexity.py` -- Classifies query as simple/moderate/complex for planner optimization

**Tool Layer (MCP Tools):**
- Purpose: Individual task execution units -- searching, ranking, composing responses
- Location: `backend/mcp_server/tools/`
- Contains: 20 tool functions that read from and write to shared state dict
- Depends on: Search providers, affiliate providers, travel providers, ModelService
- Used by: PlanExecutor (in-process direct calls, NOT via MCP JSON-RPC protocol)
- Key files listed in MCP Tools section below

**Provider Layer (Pluggable Backends):**
- Purpose: External API integrations for search, affiliate, and travel data
- Location: `backend/app/services/affiliate/`, `backend/app/services/search/`, `backend/app/services/travel/`
- Contains: Abstract base classes, registries, loaders, provider implementations
- Depends on: External APIs (OpenAI, Perplexity, eBay, Amazon, CJ, Amadeus, Booking, etc.)
- Used by: MCP tools (product_search, product_affiliate, travel_search_hotels, etc.)

**State and Caching Layer:**
- Purpose: Persistence (PostgreSQL) and ephemeral state (Redis) management
- Location: `backend/app/core/redis_client.py`, `backend/app/core/database.py`, `backend/app/services/halt_state_manager.py`, `backend/app/services/chat_history_manager.py`
- Contains: Connection management, state serialization, cache TTL management
- Depends on: Redis 7, PostgreSQL 15
- Used by: All layers (agents, tools, API endpoints)

**Orchestration Layer (Tiered Routing):**
- Purpose: Deterministic tiered API routing with consent flow, circuit breaking, parallel fetching
- Location: `backend/app/services/tiered_router/`
- Contains: Routing table, API registry, orchestrator, circuit breaker, parallel fetcher, data validator
- Depends on: MCP tools, feature flags, circuit breaker state
- Used by: `routing_gate_node` and `tiered_executor_node` in LangGraph workflow
- Key files:
  - `backend/app/services/tiered_router/router.py` -- `TIER_ROUTING_TABLE` mapping intent x tier to API list
  - `backend/app/services/tiered_router/api_registry.py` -- `API_REGISTRY` with APIConfig for each source
  - `backend/app/services/tiered_router/orchestrator.py` -- `TieredAPIOrchestrator` with escalation loop
  - `backend/app/services/tiered_router/parallel_fetcher.py` -- Concurrent API calls with timeout
  - `backend/app/services/tiered_router/circuit_breaker.py` -- Per-API circuit breaker
  - `backend/app/services/tiered_router/data_validator.py` -- Result sufficiency checks

## LangGraph Workflow (State Machine)

**Entry Point:** `backend/app/services/langgraph/workflow.py` -> `graph = build_workflow()`

**Node Graph:**
```
agent_safety ─┬─> agent_intent ──> agent_planner ──> agent_clarifier ─┬─> agent_plan_executor ──> END
              |                                                        |
              ├─> agent_clarifier (halt resume with followups)         ├─> routing_gate ─┬─> tiered_executor ─┬─> agent_plan_executor ──> END
              |                                                        |                  |                     |
              └─> tiered_executor (consent resume)                     └─> END (halted)   └─> agent_planner    └─> END (consent halt)
```

**Routing Logic:**
- `route_next_agent(state)` reads `state["status"]` and `state["next_agent"]` to determine next node
- Terminal states: `status in ["error", "completed", "halted"]` -> END
- Each node sets `next_agent` to control flow

**Agents (5 main + 2 routing):**

| Node | Class | File | Purpose |
|------|-------|------|---------|
| `agent_safety` | `SafetyAgent` | `backend/app/agents/safety_agent.py` | Content moderation (OpenAI Moderation API), PII redaction, jailbreak detection, halt-state resume check |
| `agent_intent` | `IntentAgent` | `backend/app/agents/intent_agent.py` | LLM-based intent classification: product, service, travel, general, intro, unclear, comparison |
| `agent_planner` | `PlannerAgent` | `backend/app/agents/planner_agent.py` | LLM selects entry-point tools from TOON-formatted catalog; auto-expands dependency DAG via `get_required_tools_from_dependencies()` |
| `agent_clarifier` | `ClarifierAgent` | `backend/app/agents/clarifier_agent.py` | Slot extraction from user message + conversation history; generates follow-up questions; halts workflow if required info missing |
| `agent_plan_executor` | `PlanExecutor` | `backend/app/services/plan_executor.py` | Executes tool DAG with parallel steps, dependency resolution, error handling; returns final assistant_text + ui_blocks |
| `routing_gate` | (function) | `backend/app/services/langgraph/nodes/routing_gate.py` | Routes product/comparison/travel/price_check/review_deep_dive intents to tiered_executor; general/intro/unclear to planner |
| `tiered_executor` | (function) | `backend/app/services/langgraph/nodes/tiered_executor.py` | Wraps TieredAPIOrchestrator; handles consent flow for Tier 3-4 APIs |

## GraphState Schema

**File:** `backend/app/schemas/graph_state.py`

**Key Field Groups:**

| Group | Fields | Notes |
|-------|--------|-------|
| Input | `user_message`, `session_id`, `conversation_history` | `conversation_history` is an Annotated accumulator |
| Control | `status`, `current_agent`, `next_agent`, `halt`, `plan`, `extended_search_confirmed` | `status`: running/halted/completed/error |
| Slots | `slots` (Dict), `followups` (List) | Multi-turn conversation state |
| Safety | `policy_status`, `sanitized_text`, `redaction_map` | `policy_status`: allow/block/needs_clarification/unchecked |
| Intent | `intent`, `intro_text` | product/service/travel/general/comparison/intro/unclear |
| Search | `search_results`, `search_query`, `product_names` | |
| Evidence | `review_aspects`, `review_data`, `confidence_score`, `general_product_info` | |
| Products | `normalized_products`, `affiliate_products`, `ranked_items`, `comparison_table`, `entity`, `entity_key` | |
| Travel | `hotels`, `flights`, `cars`, `itinerary`, `travel_info`, `travel_results` | |
| Response | `assistant_text`, `ui_blocks`, `citations`, `next_suggestions` | |
| Streaming | `stream_chunk_data` | For mid-workflow SSE emission |
| Telemetry | `stage_telemetry`, `tool_citations`, `agent_statuses` | All are Annotated accumulators |
| Context | `last_search_context`, `search_history` | For follow-up query context |
| Errors | `errors` | Annotated accumulator |

**Annotated Accumulator Fields** (append across nodes via `operator.add`):
`conversation_history`, `evidence_citations`, `citations`, `agent_statuses`, `tool_citations`, `errors`, `stage_telemetry`

## MCP Tools (20 total)

**Product Tools (8):**
| Tool | File | Reads | Writes |
|------|------|-------|--------|
| `product_search` | `backend/mcp_server/tools/product_search.py` | user_message, slots | search_results, products |
| `review_search` | `backend/mcp_server/tools/review_search.py` | product_names, slots | review_data |
| `product_evidence` | `backend/mcp_server/tools/product_evidence.py` | products | review_aspects |
| `product_ranking` | `backend/mcp_server/tools/product_ranking.py` | search_results, review_aspects | ranked_items |
| `product_normalize` | `backend/mcp_server/tools/product_normalize.py` | search_results, review_aspects, ranked_items | normalized_products |
| `product_affiliate` | `backend/mcp_server/tools/product_affiliate.py` | normalized_products | affiliate_links |
| `product_compose` | `backend/mcp_server/tools/product_compose.py` | user_message, normalized_products, affiliate_links | assistant_text, ui_blocks, citations |
| `product_comparison` | `backend/mcp_server/tools/product_comparison.py` | user_message, affiliate_products, conversation_history | comparison_table, assistant_text, ui_blocks |

**Travel Tools (6):**
| Tool | File | Reads | Writes |
|------|------|-------|--------|
| `travel_itinerary` | `backend/mcp_server/tools/travel_itinerary.py` | destination, duration_days from slots | itinerary |
| `travel_search_hotels` | `backend/mcp_server/tools/travel_search_hotels.py` | destination, check_in, check_out from slots | hotels |
| `travel_search_flights` | `backend/mcp_server/tools/travel_search_flights.py` | origin, destination, dates from slots | flights |
| `travel_search_cars` | `backend/mcp_server/tools/travel_search_cars.py` | destination, dates from slots | cars |
| `travel_destination_facts` | `backend/mcp_server/tools/travel_destination_facts.py` | destination, month from slots | destination_facts |
| `travel_compose` | `backend/mcp_server/tools/travel_compose.py` | user_message, itinerary, hotels, flights | assistant_text, ui_blocks |

**General/Utility Tools (6):**
| Tool | File | Reads | Writes |
|------|------|-------|--------|
| `general_search` | `backend/mcp_server/tools/general_search.py` | user_message | search_results, search_query |
| `general_compose` | `backend/mcp_server/tools/general_compose.py` | user_message, search_results | assistant_text, ui_blocks, citations |
| `intro_compose` | `backend/mcp_server/tools/intro_compose.py` | user_message | assistant_text |
| `unclear_compose` | `backend/mcp_server/tools/unclear_compose.py` | user_message | assistant_text |
| `next_step_suggestion` | `backend/mcp_server/tools/next_step_suggestion.py` | intent, recent_tools | suggestions |

**Additional Tool Files (not registered in MCP server but available):**
- `backend/mcp_server/tools/product_extractor.py` -- Product name extraction
- `backend/mcp_server/tools/product_general_information.py` -- General product knowledge
- `backend/mcp_server/tools/travel_general_information.py` -- General travel knowledge

## Tool Contract and Execution System

**Contract System:**
- Each tool module exports a `TOOL_CONTRACT` dict with: `name`, `purpose`, `intent`, `requires`, `produces`, `is_default`, `is_required`, `tools.pre`, `tools.post`, `not_for`
- `backend/mcp_server/tool_contracts.py` auto-discovers contracts from all tool modules via filesystem scan
- PlannerAgent formats selectable (non-default) tools in TOON format (token-efficient encoding) for LLM prompt
- `get_required_tools_from_dependencies()` expands LLM-selected tools by following pre/post dependency chains and adding required default tools

**PlanExecutor:**
- Location: `backend/app/services/plan_executor.py`
- Creates a fresh instance per request to prevent cross-session state leaks
- `TOOL_REGISTRY` built at module load via `_load_tool_registry()` -- imports tool functions dynamically from `mcp_server.tools.*`
- Steps executed in dependency order; tools within a step run in parallel via `asyncio.gather`
- Timeouts: `_TOOL_TIMEOUT_S = 30.0` per tool, `_STEP_TIMEOUT_S = 45.0` per step
- Critical tools (`product_compose`, `travel_compose`, `general_compose`, `intro_compose`, `unclear_compose`) abort the pipeline on failure

## SSE Streaming Architecture

**Event Types:**

| Event | Purpose | Content |
|-------|---------|---------|
| `status` | Agent progress messages | `{"text": "Thinking...", "agent": "init"}` |
| `content` | Chunked text tokens | `{"token": "24-char chunk"}` with 20ms delay |
| `artifact` | Structured data blocks | `{"type": "ui_blocks", "blocks": [...], "clear": true}` |
| `done` | Final payload | session_id, intent, citations, followups, ui_blocks, next_suggestions, response_metadata, stage_telemetry |
| `error` | Error events | `{"code": "request_timeout", "message": "...", "recoverable": true}` |

**Implementation:**
- `generate_chat_stream()` in `backend/app/api/v1/chat.py` is an async generator yielding SSE-formatted strings
- `graph.astream_events()` runs in a background `asyncio.Task` feeding an `asyncio.Queue`
- Main loop drains queue, detects node start/end events, streams `stream_chunk_data` immediately when available
- 60-second hard limit (`MAX_TOTAL_REQUEST_S` from stage_telemetry) cancels the event consumer if exceeded
- Text is streamed in 24-char chunks with 20ms delay for typing effect
- `_sse_event()` helper formats events as `event: <type>\ndata: <json>\n\n`

## Tiered API Routing

**Tier Structure:**

| Tier | Cost | Consent | APIs (Product Intent) |
|------|------|---------|----------------------|
| 1 | Free (affiliate) | No | amazon_affiliate, walmart_affiliate, bestbuy_affiliate, ebay_affiliate, google_cse_product |
| 2 | Low cost | No | bing_search, youtube_transcripts |
| 3 | Consent required | Yes | reddit_api |
| 4 | Consent required | Yes | serpapi |

**Travel Intent Tiers:**
- Tier 1: amadeus, booking, expedia, google_cse_travel
- Tier 2: skyscanner, tripadvisor

**API Registry:** `backend/app/services/tiered_router/api_registry.py` -- Each API has `APIConfig` with: name, mcp_tool, provider, cost_cents, timeout_ms, requires_consent, feature_flag

**Orchestration Flow:**
1. `TieredAPIOrchestrator.execute()` starts at tier 1
2. `get_apis_for_tier()` returns APIs filtered by circuit breaker
3. `_filter_by_feature_flags()` removes APIs whose settings flag is disabled
4. `ParallelFetcher.fetch_tier()` calls all APIs concurrently with timeout
5. `DataValidator.validate()` checks result sufficiency
6. Returns `SUFFICIENT`, `ESCALATE`, `CONSENT_REQUIRED`, or `MAX_TIER_REACHED`

## Error Handling

**Strategy:** Graceful degradation with fallbacks at every level

**Stage Telemetry Budgets** (`backend/app/services/stage_telemetry.py`):

| Stage | Soft Timeout | Hard Timeout |
|-------|-------------|-------------|
| safety | 2.0s | 4.0s |
| intent | 3.0s | 6.0s |
| clarifier | 4.0s | 8.0s |
| planner | 5.0s | 10.0s |
| tool | 8.0s | 15.0s |
| plan_exec | 25.0s | 45.0s |
| composition | 6.0s | 12.0s |
| finalization | 2.0s | 4.0s |

**Agent Fallbacks:**
- Safety timeout -> `policy_status="unchecked"` (pass through)
- Intent timeout -> `intent="general"`
- Planner timeout -> Minimal fast-path plan with single compose tool
- Clarifier timeout -> Skip clarification, proceed to execution
- PlanExecutor timeout -> Partial results message

**Provider Fallbacks:**
- AffiliateManager tries fallback providers on primary failure
- Circuit breaker opens after `CIRCUIT_BREAKER_FAILURE_THRESHOLD` failures (default 3), resets after `CIRCUIT_BREAKER_RESET_TIMEOUT` (default 300s)

## Cross-Cutting Concerns

**Logging:**
- Centralized logger: `backend/app/core/centralized_logger.py`
- Colored console output: `backend/app/core/colored_logging.py` (agent-specific colors)
- Structured JSON logging available via `LOG_FORMAT=json`
- HTTP request/response middleware: `backend/app/middleware/logging_middleware.py`

**Validation:**
- Tool output validation: `backend/app/services/tool_validator.py`
- State serialization safety: `backend/app/services/state_serializer.py` (overflow checks, non-serializable stripping)
- Request validation: Pydantic models in route handlers

**Authentication:**
- JWT-based: `backend/app/core/dependencies.py` -> `get_current_user()`
- Admin auth: `backend/app/api/v1/admin_auth.py` (username/password -> JWT token)
- Anonymous users: Auto-created with random email at `@reviewguide.ai` domain
- Rate limiting: Per-IP and per-session, configurable via `RATE_LIMIT_*` settings

**Observability:**
- Langfuse tracing: `CallbackHandler` passed to `graph.astream_events()` config
- OpenTelemetry: OTLP export to Langfuse (configurable batch processor settings)
- Stage telemetry: Per-agent timing in `stage_telemetry` GraphState field, included in SSE `done` event
- QoS metrics: Persisted to `request_metrics` table, logged as structured JSON

**Configuration:**
- Primary: `backend/app/core/config.py` -> `Settings` class (Pydantic BaseSettings loading from `.env`)
- Override: Database config overrides loaded at startup via `load_config_overrides_from_db()`
- Cache: `backend/app/services/config_cache.py` -> Redis snapshot approach (Magento 2 style, single Redis GET loads all configs)
- Encryption: `backend/app/services/config_encryption.py` -> Fernet encryption for sensitive DB configs

## Database Models (PostgreSQL)

| Model | Table | File | Purpose |
|-------|-------|------|---------|
| `User` | `users` | `backend/app/models/user.py` | User accounts (email, locale, preferences JSONB, extended_search_enabled) |
| `Session` | `sessions` | `backend/app/models/session.py` | User sessions (user_id FK, country_code, meta JSON) |
| `ConversationMessage` | `conversation_messages` | `backend/app/models/conversation_message.py` | Chat messages (session_id, role, content, message_metadata JSONB, sequence_number) |
| `AffiliateLink` | `affiliate_links` | `backend/app/models/affiliate_link.py` | Tracked affiliate links |
| `AffiliateMerchant` | `affiliate_merchants` | `backend/app/models/affiliate_merchant.py` | Merchant info |
| `AffiliateClick` | `affiliate_clicks` | `backend/app/models/affiliate_click.py` | Click tracking analytics (session_id, provider, product_name, category, url) |
| `ProductIndex` | `product_index` | `backend/app/models/product_index.py` | Product catalog index |
| `AirportCache` | `airport_cache` | `backend/app/models/airport_cache.py` | City-to-airport-code lookups (configurable expiry) |
| `APIUsageLog` | `api_usage_logs` | `backend/app/models/api_usage_log.py` | API cost tracking |
| `RequestMetric` | `request_metrics` | `backend/app/models/request_metric.py` | QoS request metrics |

## Redis Key Patterns

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `halt_state:{session_id}` | Halt state persistence for multi-turn conversations | `HALT_STATE_TTL` (default 3600s) |
| `chat_history:{session_id}` | Conversation history cache | `CHAT_HISTORY_CACHE_TTL` (default 3600s) |
| `session:{session_id}:has_history` | Fast existence check for new sessions | -- |
| `cj:search:{hash}` | CJ product search cache | `CJ_CACHE_TTL` (default 28800s / 8h) |
| `serpapi:{hash}` | SerpAPI review search cache | `SERPAPI_CACHE_TTL` (default 86400s / 24h) |
| `config:snapshot` | Full config snapshot | Invalidated on startup |
| Rate limit keys | Per-IP and per-session rate limiting | Window-based |

## API Routes

| Method | Path | Handler File | Purpose |
|--------|------|-------------|---------|
| GET | `/` | `backend/app/api/v1/health.py` | ALB liveness probe |
| GET | `/health` | `backend/app/api/v1/health.py` | DB + Redis health check |
| GET | `/health/ready` | `backend/app/api/v1/health.py` | Provider capability readiness |
| POST | `/v1/chat/stream` | `backend/app/api/v1/chat.py` | Main SSE streaming chat endpoint |
| GET | `/v1/chat/history/{session_id}` | `backend/app/api/v1/chat.py` | Load conversation history |
| GET | `/v1/chat/sessions` | `backend/app/api/v1/chat.py` | List user sessions |
| POST | `/v1/auth/login` | `backend/app/api/v1/admin_auth.py` | Admin JWT login |
| POST | `/v1/affiliate/click` | `backend/app/api/v1/affiliate.py` | Affiliate click tracking |
| POST | `/v1/affiliate/event` | `backend/app/api/v1/affiliate.py` | UI event tracking |
| POST | `/v1/affiliate/cj/search` | `backend/app/api/v1/affiliate.py` | CJ product search proxy |
| GET/POST | `/v1/admin/*` | `backend/app/api/v1/admin.py` | Admin dashboard APIs |
| GET/POST | `/v1/admin/users/*` | `backend/app/api/v1/admin_users.py` | User management |
| GET | `/v1/telemetry/*` | `backend/app/api/v1/telemetry.py` | Trace lookup |
| GET | `/v1/qos/*` | `backend/app/api/v1/qos.py` | QoS metrics |

## Configuration Reference

**Model Configuration** (per-agent overrides in `backend/app/core/config.py`):

| Setting | Default | Purpose |
|---------|---------|---------|
| `DEFAULT_MODEL` | gpt-4o-mini | Fallback model for all agents |
| `PLANNER_MODEL` | gpt-4o-mini | Planner agent model |
| `INTENT_MODEL` | gpt-4o-mini | Intent classification model |
| `CLARIFIER_MODEL` | gpt-4o-mini | Clarifier agent model |
| `COMPOSER_MODEL` | gpt-4o-mini | Composer agents model |
| `PRODUCT_SEARCH_MODEL` | gpt-4o-mini | Product search model |

**Key Feature Flags:**

| Flag | Default | Purpose |
|------|---------|---------|
| `USE_CURATED_LINKS` | True | Use curated Amazon affiliate links (bypasses live search) |
| `USE_MOCK_AFFILIATE` | True | Use mock affiliate provider |
| `USE_MOCK_TRAVEL` | True | Use mock travel providers |
| `AMAZON_API_ENABLED` | False | Enable real Amazon PA-API |
| `CJ_API_ENABLED` | False | Enable CJ Product Search API |
| `ENABLE_SERPAPI` | False | Enable SerpAPI for review search |
| `ENABLE_REDDIT_API` | False | Enable Reddit API (Tier 3) |
| `ENABLE_YOUTUBE_TRANSCRIPTS` | True | Enable YouTube transcript extraction |
| `MAX_AUTO_TIER` | 2 | Highest tier to auto-escalate without consent |
| `ENABLE_LLM_SEARCH_QUERY` | False | LLM-based search query generation vs simple slot concatenation |
| `ENABLE_SEARCH_CACHE` | True | Redis caching for search results |

---

*Architecture analysis: 2026-03-25*
