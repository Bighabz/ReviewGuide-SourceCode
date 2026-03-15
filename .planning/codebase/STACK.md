# Technology Stack

**Analysis Date:** 2026-03-15

## Languages

**Primary:**
- TypeScript 5.3 - Frontend (all components, hooks, lib utilities)
- Python 3.11 - Backend (FastAPI app, agents, services, MCP server)

**Secondary:**
- JavaScript - `next.config.js`, `postcss.config.js`

## Runtime

**Frontend:**
- Node.js 20 (Alpine) - specified in `frontend/Dockerfile`

**Backend:**
- Python 3.11-slim - specified in `backend/Dockerfile`
- ASGI server: Uvicorn 0.38 with standard extras

**Package Manager:**
- Frontend: npm (lockfile: `frontend/package-lock.json` - present)
- Backend: pip (lockfile: none — `requirements.txt` with pinned versions)

## Frameworks

**Core:**
- Next.js 14.2 (`frontend/`) - App router, SSR/SSG, standalone Docker output
- FastAPI 0.121 (`backend/app/main.py`) - Async REST API, SSE streaming
- LangGraph 1.0.2 (`backend/app/services/langgraph/`) - AI agent state machine
- LangChain 1.0.4 + langchain-openai 1.0.2 - LLM abstraction layer
- MCP 1.21.1 (`backend/mcp_server/main.py`) - Model Context Protocol tool server

**UI Component Libraries:**
- React 18.2 - Component framework
- Tailwind CSS 3.3 - Utility-first CSS (`frontend/tailwind.config.ts`)
- MUI (Material UI) 7.3 + Emotion 11.14 - Admin panel components
- Framer Motion 12.26 - Animations
- Lucide React 0.294 - Icons
- React Admin 5.13 - Admin dashboard (`/admin` route)
- Recharts 3.5 - Data visualization

**Content Rendering:**
- react-markdown 9.0 - Markdown rendering in chat
- DOMPurify 3.3 - Sanitizing HTML in rendered content
- @tailwindcss/typography 0.5 - Markdown prose styling

**Testing:**
- Vitest 4.0 - Frontend test runner (`frontend/vitest.config.ts`)
- pytest 8.4 + pytest-asyncio 1.2 - Backend tests (`backend/pytest.ini`)
- @testing-library/react 14.1 - Component testing
- jsdom 23.2 - Browser environment simulation

**Build/Dev:**
- Next.js compiler with `removeConsole: { exclude: ['error', 'warn'] }` in production (`frontend/next.config.js`)
- Multi-stage Docker builds (`backend/Dockerfile`, `frontend/Dockerfile`)
- Alembic 1.17 - Database migration tool

**Code Quality:**
- Ruff 0.14 - Python linting (`requirements.txt`)
- Black 25.9 - Python formatting
- ESLint - Frontend (via `next lint`)

## Key Dependencies

**Critical:**
- LangGraph 1.0.2 - Powers the entire multi-agent workflow (`backend/app/services/langgraph/workflow.py`)
- LangChain-OpenAI 1.0.2 - LLM interface used in `ModelService` (`backend/app/services/model_service.py`)
- SQLAlchemy 2.0 async + asyncpg 0.30 - Async PostgreSQL ORM (`backend/app/core/database.py`)
- redis 7.0 (Python client) + hiredis 3.3 - Cache/state layer (`backend/app/core/redis_client.py`)
- pydantic 2.12 + pydantic-settings 2.11 - All config, schemas, request/response models
- litellm 1.79 - LLM proxy abstraction (imported in `requirements.txt`, used for multi-provider support)
- anthropic 0.72 - Anthropic Claude SDK (available but secondary to OpenAI)

**Infrastructure:**
- amadeus 12.0 - Official Amadeus SDK for hotels/flights (`backend/app/services/travel/providers/amadeus_provider.py`)
- google-search-results 2.4 - SerpAPI/Serper.dev client (`backend/app/services/serpapi/client.py`)
- httpx 0.28 - Async HTTP client used across all external API calls
- aiohttp 3.13 - Async HTTP (secondary, used in some providers)
- apscheduler 3.10 - Background job scheduling for link health checks (`backend/app/services/scheduler.py`)
- langfuse 3.9 - LLM observability/tracing
- opentelemetry-api/sdk/exporter-otlp 1.38 - OTLP traces to Langfuse
- python-jose 3.5 + passlib 1.7 - JWT auth and password hashing
- sharp 0.33 - Next.js image optimization (native module)

## Configuration

**Environment:**
- Backend: `.env` file in `backend/` read by pydantic-settings, all vars defined in `backend/app/core/config.py`
- Frontend: `NEXT_PUBLIC_API_URL` env var (build-time via Docker ARG; runtime via `next.config.js`)
- Config priority: Redis snapshot → Database (`app_configs` table) → `.env` file. See `backend/app/services/config_cache.py`

**Build:**
- `frontend/next.config.js` - Next.js config (standalone output, console removal)
- `frontend/tsconfig.json` - TypeScript strict mode, path alias `@/*` maps to `frontend/`
- `frontend/tailwind.config.ts` - Tailwind config
- `docker-compose.yml` - All service definitions, env injection, health checks

## Platform Requirements

**Development:**
- Docker + Docker Compose (primary dev environment)
- Node.js 20 for frontend standalone runs
- Python 3.11 if running backend outside Docker
- PostgreSQL 15 on port 5432
- Redis 7 on port 6379

**Production:**
- Deployed on Railway (backend) + Vercel (frontend) based on project memory
- Backend container: Python 3.11-slim, runs Alembic migrations then Uvicorn on startup
- Frontend container: Node.js 20-alpine, Next.js standalone output on port 3000
- CORS_ORIGIN_REGEX used to cover Vercel preview deployment URLs

---

*Stack analysis: 2026-03-15*
