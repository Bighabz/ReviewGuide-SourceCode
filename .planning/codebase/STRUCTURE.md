# Codebase Structure

**Analysis Date:** 2026-03-15

## Directory Layout

```
ReviewGuide-SourceCode/
├── backend/                    # FastAPI backend + AI pipeline
│   ├── app/                    # Main application package
│   │   ├── agents/             # LangGraph agent classes
│   │   ├── api/v1/             # FastAPI route handlers
│   │   ├── core/               # Shared infra: config, DB, Redis, logging
│   │   ├── executors/          # (legacy/unused executor stubs)
│   │   ├── lib/                # Third-party Python lib wrappers
│   │   ├── middleware/         # FastAPI middleware (logging, admin auth)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── repositories/       # DB access layer (async SQLAlchemy)
│   │   ├── schemas/            # Pydantic request/response + GraphState
│   │   ├── services/           # Business logic and AI services
│   │   │   ├── affiliate/      # Affiliate link providers (Amazon, eBay, CJ)
│   │   │   ├── langgraph/      # LangGraph workflow + nodes
│   │   │   │   └── nodes/      # tiered_executor, routing_gate nodes
│   │   │   ├── search/         # Search provider abstraction
│   │   │   │   └── providers/  # Perplexity, OpenAI search providers
│   │   │   ├── serpapi/        # SerpAPI review search service
│   │   │   ├── tiered_router/  # Deterministic tiered API routing
│   │   │   └── travel/         # Travel provider abstraction
│   │   │       └── providers/  # Amadeus, Booking, Expedia, Skyscanner, Viator
│   │   └── utils/              # Date utils, auth helpers
│   ├── alembic/                # Database migrations
│   │   └── versions/           # Migration files (timestamped)
│   ├── config/                 # YAML config files (search.yaml, etc.)
│   ├── data/                   # Static data files
│   ├── mcp_server/             # MCP protocol server
│   │   └── tools/              # 19 tool functions (product, travel, general)
│   ├── scripts/                # Utility scripts
│   └── tests/                  # Backend test suite
│       └── test_tiered_router/ # Tiered router unit tests
├── frontend/                   # Next.js 14 frontend (primary)
│   ├── app/                    # Next.js App Router pages
│   │   ├── admin/              # Admin panel pages (dashboard, users, config)
│   │   ├── browse/             # Product browse pages
│   │   │   └── [category]/     # Dynamic category pages
│   │   ├── chat/               # Chat interface page
│   │   ├── login/              # Login page
│   │   ├── affiliate-disclosure/
│   │   ├── privacy/
│   │   └── terms/
│   ├── components/             # React components
│   │   ├── blocks/             # BlockRegistry — maps ui_block types to components
│   │   ├── browse/             # Browse-specific components
│   │   └── ui/                 # Generic UI primitives
│   ├── contexts/               # React contexts (AdminAuthContext)
│   ├── hooks/                  # Custom hooks (useStreamReducer)
│   ├── lib/                    # Utilities, API client, constants
│   ├── public/                 # Static assets
│   │   ├── images/             # App images including browse category images
│   │   └── placeholders/       # Placeholder images
│   └── tests/                  # Frontend test files
├── kishan_frontend/            # Alternate frontend variant (not primary)
├── static/reviewguide-site/    # Astro static marketing/blog site
│   └── src/
│       ├── components/         # Astro components
│       ├── content/blog/       # Blog content files
│       ├── layouts/            # Astro layouts
│       └── pages/              # Static pages
├── docs/                       # Planning documents
│   └── plans/                  # Feature plan markdown files
├── docker-compose.yml          # Docker service definitions (CORS settings here)
├── CLAUDE.md                   # Developer notes and project documentation
└── .planning/                  # GSD planning documents
    └── codebase/               # Codebase analysis documents
```

## Directory Purposes

**`backend/app/agents/`:**
- Purpose: LangGraph agent classes that make LLM calls and return state patches
- Contains: `base_agent.py` (abstract base), `safety_agent.py`, `intent_agent.py`, `planner_agent.py`, `clarifier_agent.py`, `query_complexity.py`
- Key files: `base_agent.py` (must extend for new agents)

**`backend/app/api/v1/`:**
- Purpose: FastAPI route handlers — one file per feature domain
- Contains: `chat.py` (SSE streaming), `health.py`, `admin.py`, `admin_auth.py`, `admin_users.py`, `affiliate.py`, `telemetry.py`, `qos.py`
- Key files: `chat.py` (primary endpoint, SSE stream, halt state management)

**`backend/app/core/`:**
- Purpose: Shared infrastructure used across all layers
- Contains: `config.py`, `database.py`, `redis_client.py`, `centralized_logger.py`, `colored_logging.py`, `rate_limiter.py`, `dependencies.py`, `error_manager.py`
- Key files: `config.py` (300+ settings via pydantic-settings)

**`backend/app/models/`:**
- Purpose: SQLAlchemy ORM table definitions
- Contains: `user.py`, `session.py`, `conversation_message.py`, `affiliate_click.py`, `affiliate_link.py`, `affiliate_merchant.py`, `api_usage_log.py`, `request_metric.py`, `airport_cache.py`, `product_index.py`

**`backend/app/repositories/`:**
- Purpose: Async database query functions, one file per domain
- Contains: `conversation_repository.py`, `config_repository.py`, `admin_user_repository.py`

**`backend/app/schemas/`:**
- Purpose: Pydantic models for API contracts and GraphState definition
- Key files: `graph_state.py` (the core `GraphState` TypedDict — add new fields here when extending the pipeline)

**`backend/app/services/langgraph/`:**
- Purpose: LangGraph workflow assembly and node wrappers
- Key files: `workflow.py` (graph compilation, all node functions, edge routing), `nodes/routing_gate.py`, `nodes/tiered_executor.py`

**`backend/app/services/tiered_router/`:**
- Purpose: Deterministic tiered API routing system
- Contains: `router.py` (routing table per intent), `orchestrator.py` (tier execution coordinator), `parallel_fetcher.py`, `circuit_breaker.py`, `data_validator.py`, `api_registry.py`, `api_logger.py`

**`backend/app/services/` (root-level files):**
- Purpose: Core AI services and state management
- Key files: `plan_executor.py` (tool runner with dependency/parallel execution), `halt_state_manager.py` (Redis halt state), `chat_history_manager.py` (Redis+DB history), `model_service.py` (LLM client abstraction), `stage_telemetry.py` (per-stage timeout budgets)

**`backend/mcp_server/tools/`:**
- Purpose: 19 domain tool functions — the leaf nodes of the AI pipeline
- Contains: `product_search.py`, `product_evidence.py`, `product_affiliate.py`, `product_ranking.py`, `product_normalize.py`, `product_compose.py`, `product_comparison.py`, `product_extractor.py`, `product_general_information.py`, `review_search.py`, `general_search.py`, `general_compose.py`, `travel_itinerary.py`, `travel_search_hotels.py`, `travel_search_flights.py`, `travel_search_cars.py`, `travel_destination_facts.py`, `travel_compose.py`, `travel_general_information.py`, `intro_compose.py`, `unclear_compose.py`, `next_step_suggestion.py`
- Key files: `base_tool.py` (tool base class if extending)

**`backend/alembic/versions/`:**
- Purpose: Database migration files, timestamped and sequential
- Generated: Yes (via `alembic revision`)
- Committed: Yes

**`frontend/app/`:**
- Purpose: Next.js App Router pages; each subdirectory is a route
- Key files: `layout.tsx` (root layout, fonts), `page.tsx` (redirects to `/browse`), `chat/page.tsx` (main chat UI page), `browse/page.tsx` (browse page)

**`frontend/components/`:**
- Purpose: All React components
- Key files: `ChatContainer.tsx` (chat state machine + streaming), `Message.tsx` (message renderer + suggestion chips), `UnifiedTopbar.tsx` (nav bar), `blocks/BlockRegistry.tsx` (ui_block dispatcher)

**`frontend/components/blocks/`:**
- Purpose: `BlockRegistry.tsx` only — maps `ui_block.type` strings to React render components
- Key files: `BlockRegistry.tsx`

**`frontend/components/browse/`:**
- Purpose: Browse-specific UI components
- Contains: `BrowseLayout.tsx`, `CategoryHero.tsx`, `CategoryNav.tsx`, `FilterSidebar.tsx`, `SearchInput.tsx`, `QuickQuestion.tsx`, `SourceBadge.tsx`, `SourceStack.tsx`, `SourcesModal.tsx`, `SentimentBar.tsx`

**`frontend/lib/`:**
- Purpose: Utilities, API client, constants, helper functions
- Key files: `chatApi.ts` (SSE streaming client, all TypeScript interfaces for stream events), `constants.ts` (config constants, storage keys), `normalizeBlocks.ts` (ui_block schema normalizer), `categoryConfig.ts` (browse category definitions)

**`frontend/hooks/`:**
- Purpose: Custom React hooks
- Key files: `useStreamReducer.ts` (SSE stream state reducer — do not modify streaming logic)

**`frontend/contexts/`:**
- Purpose: React context providers
- Contains: `AdminAuthContext.tsx`

## Key File Locations

**Entry Points:**
- `frontend/app/page.tsx`: Root route — redirects to `/browse`
- `frontend/app/browse/page.tsx`: Browse/discovery landing page
- `frontend/app/chat/page.tsx`: Chat interface, URL param handling
- `backend/app/main.py`: FastAPI application factory and startup

**Configuration:**
- `docker-compose.yml`: Docker services, CORS settings (critical — update when changing frontend port)
- `backend/app/core/config.py`: All backend settings (pydantic-settings, 300+ options)
- `backend/config/search.yaml`: Search provider YAML config (overrides env vars)

**Core Logic:**
- `backend/app/services/langgraph/workflow.py`: Full LangGraph graph definition
- `backend/app/schemas/graph_state.py`: `GraphState` TypedDict — canonical data contract
- `backend/app/services/plan_executor.py`: Tool pipeline executor with dependency/parallel support
- `backend/mcp_server/main.py`: MCP server + tool registry
- `backend/app/api/v1/chat.py`: SSE streaming endpoint + halt state orchestration
- `frontend/lib/chatApi.ts`: Frontend SSE client + all TypeScript stream interfaces
- `frontend/components/ChatContainer.tsx`: Chat component state management
- `frontend/components/Message.tsx`: Message render logic + suggestion chips
- `frontend/components/blocks/BlockRegistry.tsx`: UI block type → component mapping

**Testing:**
- `backend/tests/`: Backend pytest suite
- `backend/tests/conftest.py`: Fixtures and mocks
- `backend/tests/test_tiered_router/`: Tiered router unit tests (66 tests)
- `frontend/tests/`: Frontend test files

## Naming Conventions

**Files (Backend Python):**
- Snake_case for all files: `plan_executor.py`, `halt_state_manager.py`
- Agent files: `{name}_agent.py` → `safety_agent.py`, `intent_agent.py`
- Tool files: `{domain}_{action}.py` → `product_search.py`, `travel_compose.py`
- Provider files: `{name}_provider.py` → `amazon_provider.py`, `amadeus_provider.py`
- Migration files: `{timestamp}_{hash}_{description}.py`

**Files (Frontend TypeScript):**
- PascalCase for components: `ChatContainer.tsx`, `ProductCarousel.tsx`
- camelCase for utilities and hooks: `chatApi.ts`, `normalizeBlocks.ts`, `useStreamReducer.ts`
- camelCase for lib files: `constants.ts`, `categoryConfig.ts`

**Directories:**
- Backend: snake_case (`tiered_router/`, `plan_executor/`)
- Frontend: camelCase (`components/`, `hooks/`, `lib/`)

## Where to Add New Code

**New Agent:**
- Implementation: `backend/app/agents/{name}_agent.py` (extend `BaseAgent`)
- Register node in: `backend/app/services/langgraph/workflow.py` (add node, add conditional edges)

**New MCP Tool:**
- Tool function: `backend/mcp_server/tools/{domain}_{action}.py`
- Signature: `async def tool_name(state: dict) -> dict`
- Register in: `backend/mcp_server/main.py` (list_tools + call_tool router)
- Add contract to: `backend/mcp_server/tool_contracts.py` (for auto-discovery by PlanExecutor)

**New API Endpoint:**
- Route file: `backend/app/api/v1/{feature}.py`
- Register in: `backend/app/main.py` (`app.include_router(...)`)
- Add Pydantic schemas to: `backend/app/schemas/`

**New Frontend Page:**
- Page file: `frontend/app/{route}/page.tsx`
- Layout (if needed): `frontend/app/{route}/layout.tsx`

**New Frontend Component:**
- General component: `frontend/components/{ComponentName}.tsx`
- Browse-specific: `frontend/components/browse/{ComponentName}.tsx`
- Primitive UI: `frontend/components/ui/{ComponentName}.tsx`

**New UI Block Type:**
- Add block renderer to: `frontend/components/blocks/BlockRegistry.tsx` (add key to `BLOCK_RENDERERS`)
- Add normalization mapping to: `frontend/lib/normalizeBlocks.ts` (if using old block_type format)

**New Database Model:**
- Model: `backend/app/models/{name}.py` (extend `Base` from `database.py`)
- Repository: `backend/app/repositories/{name}_repository.py`
- Migration: `cd backend && alembic revision --autogenerate -m "description"`

**New Search Provider:**
- Provider: `backend/app/services/search/providers/{name}_provider.py`
- Extend base class in `backend/app/services/search/base.py`
- Configure in `backend/config/search.yaml` or via `SEARCH_PROVIDER` env var

**New Affiliate Provider:**
- Provider: `backend/app/services/affiliate/providers/{name}_provider.py`
- Register in: `backend/app/services/affiliate/registry.py`

**New Travel Provider:**
- Provider: `backend/app/services/travel/providers/{name}_provider.py`
- Register in: `backend/app/services/travel/registry.py`

**Utilities:**
- Shared Python helpers: `backend/app/utils/`
- Shared TypeScript helpers: `frontend/lib/utils.ts`

## Special Directories

**`backend/alembic/`:**
- Purpose: Database schema migration history
- Generated: Migration files generated by Alembic
- Committed: Yes — all migration files must be committed

**`backend/mcp_server/`:**
- Purpose: MCP protocol server definition; tools called in-process at runtime via `PlanExecutor`, not over stdio
- Generated: No
- Committed: Yes

**`kishan_frontend/`:**
- Purpose: Alternate frontend variant — not the active production frontend
- Generated: No
- Committed: Yes (keep but do not modify; primary work goes in `frontend/`)

**`static/reviewguide-site/`:**
- Purpose: Astro static marketing and blog site, deployed separately from the main app
- Generated: `dist/` is the build output
- Committed: Yes (source committed; `dist/` and `node_modules/` excluded)

**`frontend/.next/`:**
- Purpose: Next.js build cache and output
- Generated: Yes
- Committed: No

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents for AI-assisted development
- Generated: By `/gsd:map-codebase` commands
- Committed: Yes

---

*Structure analysis: 2026-03-15*
