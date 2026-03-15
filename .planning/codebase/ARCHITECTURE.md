# Architecture

**Analysis Date:** 2026-03-15

## Pattern Overview

**Overall:** Multi-agent AI pipeline with event-driven SSE streaming

**Key Characteristics:**
- LangGraph state machine orchestrates 5 sequential agents via a shared `GraphState` blackboard
- Tools are defined as Model Context Protocol (MCP) tools but executed in-process via `PlanExecutor` (not over MCP protocol at runtime)
- Two-track execution: LangGraph LLM-driven planner OR deterministic tiered API router
- Frontend consumes a single SSE stream (`/v1/chat/stream`) and renders typed `ui_blocks` via a registry pattern
- Multi-turn conversations managed through Redis halt-state persistence

## Layers

**Presentation (Frontend):**
- Purpose: Chat UI, browse discovery, admin panel
- Location: `frontend/app/`, `frontend/components/`
- Contains: Next.js 14 pages, React client components, SSE stream consumer
- Depends on: Backend REST/SSE API at `NEXT_PUBLIC_API_URL`
- Used by: End users via browser

**API Gateway:**
- Purpose: FastAPI HTTP layer, CORS, rate limiting, auth
- Location: `backend/app/api/v1/`
- Contains: Route handlers for `chat`, `health`, `admin`, `affiliate`, `telemetry`, `qos`
- Depends on: LangGraph workflow, repositories, Redis
- Used by: Frontend, external callers

**Agent Orchestration:**
- Purpose: LangGraph state machine coordinating 5 agents plus tiered routing nodes
- Location: `backend/app/services/langgraph/workflow.py`
- Contains: Node wrapper functions, conditional edge routing, graph compilation
- Depends on: Agent classes, PlanExecutor, HaltStateManager
- Used by: `chat.py` API route via `graph.astream_events()`

**Agents:**
- Purpose: Specialized LLM-driven reasoning units with single responsibilities
- Location: `backend/app/agents/`
- Contains: `safety_agent.py`, `intent_agent.py`, `planner_agent.py`, `clarifier_agent.py`
- Depends on: `BaseAgent`, `model_service`, OpenAI API
- Used by: LangGraph node wrappers

**MCP Tools / Plan Executor:**
- Purpose: Domain-specific tool functions that read/write `GraphState` fields; executed in-process by `PlanExecutor`
- Location: `backend/mcp_server/tools/`, `backend/app/services/plan_executor.py`
- Contains: 19 tool functions across product, travel, general, and utility categories
- Depends on: Search providers, affiliate providers, travel providers, LLM via model_service
- Used by: `plan_executor_node` in the LangGraph workflow

**Tiered Router:**
- Purpose: Deterministic cost-tiered API routing as an alternative path for product/travel intents
- Location: `backend/app/services/tiered_router/`
- Contains: `router.py` (routing table), `orchestrator.py`, `parallel_fetcher.py`, `circuit_breaker.py`
- Depends on: External APIs (Amazon, eBay, Amadeus, etc.), `TieredAPIOrchestrator`
- Used by: `tiered_executor_node` and `routing_gate_node` in the LangGraph workflow

**Services:**
- Purpose: Cross-cutting infrastructure: state persistence, search, affiliate, travel, session management
- Location: `backend/app/services/`
- Contains: `halt_state_manager.py`, `chat_history_manager.py`, `search/`, `affiliate/`, `travel/`
- Depends on: Redis, PostgreSQL, external provider APIs
- Used by: Agents, tools, API routes

**Repositories / Data:**
- Purpose: Database access layer via async SQLAlchemy
- Location: `backend/app/repositories/`, `backend/app/models/`
- Contains: ORM models for sessions, users, conversations, affiliate clicks, request metrics
- Depends on: PostgreSQL via `AsyncSession`
- Used by: API routes and services that require persistence

**Core:**
- Purpose: Shared infrastructure: config, DB, Redis, logging, rate limiting
- Location: `backend/app/core/`
- Contains: `config.py` (pydantic-settings), `database.py`, `redis_client.py`, `centralized_logger.py`, `rate_limiter.py`
- Depends on: Environment variables, PostgreSQL, Redis
- Used by: All other backend layers

## Data Flow

**Normal Chat Request:**

1. User sends POST to `/v1/chat/stream` with `user_message` and `session_id`
2. `chat.py` builds initial `GraphState`, loads halt state + conversation history concurrently from Redis/DB
3. `graph.astream_events()` begins streaming — LangGraph enters `agent_safety` node
4. Safety node checks for existing Redis halt state; if found and has followups, resumes to clarifier
5. Intent node classifies message (product, travel, general, comparison, intro, unclear)
6. Planner node generates a dynamic execution plan (list of tool steps with dependencies)
7. Clarifier node checks slot completeness; halts workflow if required slots missing (saves to Redis, streams question to user)
8. `routing_gate_node` decides: LLM plan executor OR tiered router (based on `ENABLE_TIERED_ROUTER` flag)
9. `PlanExecutor` runs plan steps in dependency order, executing tools in parallel where `parallel: true`
10. Each tool reads from `GraphState`, performs work, returns state patch
11. Final `*_compose` tool writes `assistant_text` and `ui_blocks` to state
12. `chat.py` streams SSE events to frontend as `astream_events()` yields them
13. Frontend `ChatContainer` → `useStreamReducer` dispatches events to accumulate message state
14. `Message.tsx` renders `ui_blocks` through `BlockRegistry.tsx` → typed React components

**Halt/Resume Flow (Multi-turn):**

1. Clarifier or executor sets `halt=True`, `followups=[...]` in state
2. `chat.py` detects halt, saves `GraphState` to Redis via `HaltStateManager`
3. Streams clarification question to user, closes SSE connection
4. User answers; next request arrives with same `session_id`
5. Safety node loads halt state from Redis, restores `intent`, `slots`, `plan`
6. Routes directly to clarifier (skipping safety/intent/planner), resumes from saved state

**Tiered API Routing Path:**

1. `routing_gate_node` decides tiered path based on intent and config
2. `TieredAPIOrchestrator.execute()` starts at Tier 1 (affiliate APIs)
3. `ParallelFetcher` calls all APIs in the tier concurrently
4. `DataValidator` evaluates result quality; if insufficient, escalates to next tier
5. Tier 3-4 escalation requires user consent (halts, prompts user)
6. On success, returns `search_results` and `snippets` to be synthesized by `agent_plan_executor`

**State Management:**
- `GraphState` TypedDict flows as the shared blackboard through all LangGraph nodes
- Annotated fields with `operator.add` accumulate (not overwrite) across nodes: `citations`, `errors`, `agent_statuses`, `stage_telemetry`
- Halt state persisted to Redis key `halt_state:{session_id}` via `HaltStateManager`
- Conversation history cached in Redis key `chat_history:{session_id}`, falls back to PostgreSQL

## Key Abstractions

**GraphState:**
- Purpose: Shared blackboard for the entire agent pipeline
- Examples: `backend/app/schemas/graph_state.py`
- Pattern: TypedDict with annotated accumulator fields; every agent node receives the full state and returns only the fields it modifies

**BaseAgent:**
- Purpose: Abstract base providing LLM generation, standardized error handling, and logging
- Examples: `backend/app/agents/base_agent.py`; extended by `SafetyAgent`, `IntentAgent`, `PlannerAgent`, `ClarifierAgent`
- Pattern: Abstract `run()` method; `generate()` delegates to `model_service`

**MCP Tool Pattern:**
- Purpose: Stateless functions that take the full `GraphState` dict and return a partial state patch
- Examples: `backend/mcp_server/tools/product_search.py`, `product_compose.py`, `travel_itinerary.py`
- Pattern: `async def tool_name(state: dict) -> dict` — reads named keys, writes named keys; listed in tool contracts for auto-discovery

**BlockRegistry:**
- Purpose: Maps normalized `ui_block.type` strings to React render components
- Examples: `frontend/components/blocks/BlockRegistry.tsx`
- Pattern: `BLOCK_RENDERERS: Record<string, BlockRenderer>` dictionary; `UIBlocks` component iterates blocks and dispatches to renderer

**Provider Pattern (Search / Affiliate / Travel):**
- Purpose: Pluggable external API adapters behind a common interface
- Examples: `backend/app/services/search/providers/`, `backend/app/services/affiliate/providers/`, `backend/app/services/travel/providers/`
- Pattern: `BaseProvider` → concrete provider class registered in a `Registry`; loaded via YAML config or env var at startup

**HaltStateManager:**
- Purpose: Persists and restores mid-workflow state across HTTP requests for multi-turn conversations
- Examples: `backend/app/services/halt_state_manager.py`
- Pattern: Static methods with a process-level `_cache` dict; write-through to Redis with TTL; keyed by `halt_state:{session_id}`

## Entry Points

**Frontend Root:**
- Location: `frontend/app/page.tsx`
- Triggers: Browser navigation to `/`
- Responsibilities: Immediately redirects to `/browse`

**Frontend Chat:**
- Location: `frontend/app/chat/page.tsx`
- Triggers: User navigates to `/chat` (directly or from browse search bar)
- Responsibilities: Session management, URL param processing (`?q=`, `?new=1`), mounting `ChatContainer`

**Backend Application:**
- Location: `backend/app/main.py`
- Triggers: Uvicorn startup (via Docker or `uvicorn app.main:app`)
- Responsibilities: DB/Redis init, config overrides load, provider setup, router registration, background scheduler start

**Chat Stream Endpoint:**
- Location: `backend/app/api/v1/chat.py` → `POST /v1/chat/stream`
- Triggers: Frontend `streamChat()` in `frontend/lib/chatApi.ts`
- Responsibilities: Build initial state, invoke `graph.astream_events()`, stream SSE chunks, persist messages to DB, save halt state

**MCP Server:**
- Location: `backend/mcp_server/main.py`
- Triggers: Stdio invocation (for MCP protocol clients) — note: tools are called in-process at runtime, not via this server
- Responsibilities: Exposes 19 tools over Model Context Protocol for external consumption

## Error Handling

**Strategy:** Per-stage budgets with graceful degradation fallbacks; global exception handler at FastAPI layer

**Patterns:**
- Every LangGraph node is wrapped in `run_stage_with_budget()` from `backend/app/services/stage_telemetry.py`; on timeout, a predefined `fallback_result` is returned instead of failing
- Safety agent timeout falls back to `policy_status="unchecked"` and passes through
- Planner agent timeout falls back to a single `general_compose` step
- Clarifier timeout falls back to skipping clarification and proceeding to execution
- `PlanExecutor` enforces `_TOOL_TIMEOUT_S = 15.0` per tool and `_STEP_TIMEOUT_S = 45.0` per step; compose tools are in `_CRITICAL_TOOLS` and abort the pipeline on failure
- Frontend: `streamChat()` has exponential backoff reconnect (up to 3 retries); `ErrorBanner` surfaces errors; `Message.tsx` renders `completeness: 'partial' | 'degraded'` states via `MessageRecoveryUI`

## Cross-Cutting Concerns

**Logging:** Centralized structured logger (`backend/app/core/centralized_logger.py`) wraps Python's logging; `colored_logging.py` provides per-agent colored console output; JSON mode for production. MCP server uses stderr to avoid breaking JSON-RPC on stdout.

**Validation:** Pydantic models for all API request/response schemas (`backend/app/schemas/`); pydantic-settings for config (`backend/app/core/config.py`). Tool output validation via `ToolOutputValidator` (`backend/app/services/tool_validator.py`).

**Authentication:** JWT-based admin auth via `admin_auth_middleware.py`; anonymous users get session IDs only; `check_rate_limit` dependency on chat endpoint.

**Stage Telemetry:** Every agent node appends a `StageTelemetry` dict to `state["stage_telemetry"]` (accumulator list), recording duration_ms and timeout_hit per stage.

---

*Architecture analysis: 2026-03-15*
