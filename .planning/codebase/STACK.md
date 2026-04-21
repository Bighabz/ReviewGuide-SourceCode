# Technology Stack

**Analysis Date:** 2026-04-16
**Branch:** `v2-with-swipe` (deployed as production main)
**Scope:** Full-stack AI shopping/travel assistant — frontend (Next.js on Vercel), backend (FastAPI on Railway), Postgres + Redis data layer

---

## Languages

**Primary:**
- **TypeScript 5.3.3** — All frontend code (`frontend/tsconfig.json:6` strict mode on, `target: ES2020`, `moduleResolution: bundler`)
- **Python 3.11** — All backend code (`backend/Dockerfile:8` `python:3.11-slim` base for both builder and production stages)

**Secondary:**
- **JavaScript (ES2020)** — Build glue: `frontend/next.config.js`, `frontend/postcss.config.js`, `generate-category-images.cjs` (root)
- **Bash** — `kill.sh`, `run.sh`, `setup.sh`, `backend/test_flow.sh`

---

## Runtime

**Frontend:**
- **Node.js 20-alpine** — `frontend/Dockerfile:7` (deps stage), `frontend/Dockerfile:19` (builder), `frontend/Dockerfile:38` (production)
- Next.js standalone server: `node server.js` (`frontend/Dockerfile:74`), port 3000, `HOSTNAME=0.0.0.0`
- `libc6-compat` apk added for `sharp` native bindings (`frontend/Dockerfile:9, 43`)

**Backend:**
- **Python 3.11-slim** — Multi-stage build, runs as non-root `appuser` (`backend/Dockerfile:32`)
- ASGI server: **Uvicorn 0.38.0** with `[standard]` extras (httptools, uvloop, websockets, watchfiles) — `requirements.txt:5`
- Startup command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` (`backend/Dockerfile:64`)

**Package Manager:**
- Frontend: **npm** with `package-lock.json` committed (327 KB). `frontend/Dockerfile:16` uses `npm ci` for reproducible installs.
- Backend: **pip** with single root `requirements.txt` (109 lines, ~33 packages all version-pinned). **No lockfile** (no `requirements.lock`, no `pip-tools`, no `poetry.lock`).

---

## Frameworks

### Core

| Package | Version | File:Line | Purpose |
|---------|---------|-----------|---------|
| **Next.js** | ^14.2.35 | `frontend/package.json:24` | App Router, SSR/SSG, standalone Docker output |
| **React** | ^18.2.0 | `frontend/package.json:26` | UI framework |
| **React DOM** | ^18.2.0 | `frontend/package.json:28` | DOM bindings |
| **FastAPI** | 0.121.0 | `requirements.txt:4` | Async REST API + SSE streaming endpoints |
| **LangGraph** | 1.0.2 | `requirements.txt:11` | Multi-agent state machine (`backend/app/services/langgraph/workflow.py`) |
| **LangChain** | 1.0.4 | `requirements.txt:12` | LLM orchestration framework (+ `langchain-core==1.0.3`, `langchain-classic==1.0.0`, `langchain-community==0.4.1`, `langchain-text-splitters==1.0.0`) |
| **langchain-openai** | 1.0.2 | `requirements.txt:16` | OpenAI provider for LangChain (used in `backend/app/services/model_service.py`) |
| **MCP** | 1.21.1 | `requirements.txt:25` | Model Context Protocol server (`backend/mcp_server/main.py`, 23 tools) |
| **OpenAI SDK** | 2.7.1 | `requirements.txt:19` | Direct OpenAI client (also surfaced via litellm) |
| **Anthropic SDK** | 0.72.0 | `requirements.txt:20` | Claude client (secondary, ANTHROPIC_API_KEY optional in `backend/app/core/config.py:198`) |
| **litellm** | 1.79.1 | `requirements.txt:18` | LLM proxy for multi-provider routing |

### UI / Styling

| Package | Version | Purpose |
|---------|---------|---------|
| **Tailwind CSS** | ^3.3.6 | Utility-first CSS, configured in `frontend/tailwind.config.ts` |
| **@tailwindcss/typography** | ^0.5.19 | Markdown prose plugin (`frontend/tailwind.config.ts:85`) |
| **autoprefixer** | ^10.4.16 | PostCSS plugin |
| **postcss** | ^8.4.32 | CSS pipeline |
| **@mui/material** | ^7.3.5 | Admin panel components (used in `/admin` route only) |
| **@emotion/react** | ^11.14.0 | MUI peer dep |
| **@emotion/styled** | ^11.14.1 | MUI peer dep |
| **react-admin** | ^5.13.2 | Admin dashboard framework (`frontend/app/admin/`) |
| **ra-data-simple-rest** | ^5.13.2 | React-Admin REST adapter |
| **framer-motion** | ^12.26.2 | Animations across chat / browse |
| **lucide-react** | ^0.294.0 | Icon set (used in 40+ components) |
| **recharts** | ^3.5.1 | Admin analytics charts |
| **clsx** | ^2.1.1 | Class name composition |
| **tailwind-merge** | ^3.4.0 | Resolves conflicting Tailwind classes |

### Content Rendering

| Package | Version | Purpose |
|---------|---------|---------|
| **react-markdown** | ^9.0.1 | Renders LLM markdown output in `frontend/components/Message.tsx` |
| **dompurify** | ^3.3.1 | HTML sanitization (server- and client-safe) |
| **@types/dompurify** | ^3.0.5 | Types |
| **sharp** | ^0.33.5 | Next.js native image optimization (requires `libc6-compat` in Alpine) |

### Fonts

- **DM Sans** (body) and **Instrument Serif** (headings) loaded via `next/font/google` in `frontend/app/layout.tsx:3,6-7`. CSS variables `--font-dm-sans` and `--font-instrument` consumed in `frontend/tailwind.config.ts:12-14`.

### Testing

| Package | Version | File | Purpose |
|---------|---------|------|---------|
| **Vitest** | ^4.0.17 | `frontend/vitest.config.ts` | Frontend test runner, `jsdom` env |
| **@testing-library/react** | ^14.1.2 | — | React component testing |
| **@testing-library/jest-dom** | ^6.2.0 | — | DOM matchers |
| **@vitejs/plugin-react** | ^4.2.1 | `frontend/vitest.config.ts:3` | Vite React plugin |
| **jsdom** | ^23.2.0 | `frontend/vitest.config.ts:9` | Browser env simulation |
| **pytest** | 8.4.2 | `backend/pytest.ini` | Backend test runner, `asyncio_mode = auto` |
| **pytest-asyncio** | 1.2.0 | `requirements.txt:76` | Async test support |
| **httpx-sse** | 0.4.3 | `requirements.txt:77` | SSE testing for chat endpoint |

### Build / Dev Tools

| Tool | Version | Purpose |
|------|---------|---------|
| **TypeScript compiler** | 5.3.3 | `frontend/tsconfig.json` (no emit, strict mode) |
| **Next.js compiler** | 14.2.35 | `removeConsole: { exclude: ['error', 'warn'] }` in production (`frontend/next.config.js:14-18`) |
| **Alembic** | 1.17.1 | Database migrations — 19 migration files in `backend/alembic/versions/`, latest `20260222_0001_create_request_metrics.py` |

### Code Quality

| Tool | Version | Notes |
|------|---------|-------|
| **Ruff** | 0.14.4 | Python linting (`requirements.txt:82`) — no `ruff.toml` or `pyproject.toml` config; uses defaults |
| **Black** | 25.9.0 | Python formatter (`requirements.txt:83`) |
| **ESLint** | (via `next lint`) | No standalone `.eslintrc` — relies on Next.js defaults |

---

## Key Dependencies (with risk notes)

### Critical Path (failure breaks core flows)

| Package | Version | Risk / Notes |
|---------|---------|--------------|
| **OpenAI SDK 2.7.1** | `requirements.txt:19` | **CRITICAL** — every chat request needs `OPENAI_API_KEY`. Hard-coded as required in `backend/app/core/config.py:197` (`Field(...)`). |
| **LangGraph 1.0.2** | `requirements.txt:11` | Newly stable 1.0 release (Feb 2026). Major API surface. Workflow defined in `backend/app/services/langgraph/workflow.py`. |
| **LangChain 1.0.4** | `requirements.txt:12` | LangChain 1.0 split — `langchain-classic==1.0.0` is the legacy compatibility shim, `langchain==1.0.4` is the new orchestration core. Both pinned. |
| **SQLAlchemy 2.0.44** | `requirements.txt:30` | Async ORM via `asyncpg==0.30.0`. Used in `backend/app/core/database.py`. |
| **redis 7.0.1** (Python client) | `requirements.txt:39` | Used for cache, halt state, rate limiting. `hiredis==3.3.0` for C-accelerated parsing. |
| **pydantic 2.12.4** + **pydantic-settings 2.11.0** | `requirements.txt:67-68` | All config, request/response models. |
| **httpx 0.28.1** | `requirements.txt:52` | Default async HTTP client (used by Serper.dev, Amadeus, Booking, Skyscanner clients). |
| **Next.js 14.2.35** | `frontend/package.json:24` | **EOL warning:** Next.js 14 is on extended maintenance (Next 15 is LTS as of Q4 2025). Migration to 15 is a future tech-debt item. |
| **MCP 1.21.1** | `requirements.txt:25` | 23 tools registered. Defined in `backend/mcp_server/tools/`. |

### Infrastructure

| Package | Version | Purpose |
|---------|---------|---------|
| **amadeus 12.0.0** | `requirements.txt:98` | Official Amadeus SDK for hotels/flights (`backend/app/services/travel/providers/amadeus_provider.py`) |
| **google-search-results 2.4.2** | `requirements.txt:103` | SerpAPI Python client (legacy — current implementation in `backend/app/services/serpapi/client.py:7-9` is **Serper.dev**, swapped from SerpAPI while credits refill). The PyPI package name is misleading. |
| **aiohttp 3.13.2** | `requirements.txt:53` | Secondary async HTTP client used in some travel providers |
| **apscheduler 3.10.4** | `requirements.txt:93` | Background jobs (link health checker every 6h — `backend/app/services/link_health_checker.py`, started in `backend/app/services/scheduler.py`) |
| **langfuse 3.9.1** | `requirements.txt:58` | LLM observability (traces sent to `https://cloud.langfuse.com` by default, `backend/app/core/config.py:359`) |
| **opentelemetry-api/sdk/exporter-otlp 1.38.0** | `requirements.txt:60-62` | OTLP traces (Langfuse uses OTel under the hood) |
| **python-jose[cryptography] 3.5.0** | `requirements.txt:45` | JWT signing/verification (`backend/app/utils/auth.py:8`) |
| **passlib[bcrypt] 1.7.4** | `requirements.txt:46` | Listed but `backend/app/utils/auth.py:7,35-37` actually uses **`bcrypt` directly** (passlib wraps it). Risk: `passlib` is in maintenance-only mode since 2023; `bcrypt` is being used directly anyway. |
| **psycopg2-binary 2.9.11** | `requirements.txt:33` | Used by Alembic migrations (sync driver) |
| **greenlet 3.2.4** | `requirements.txt:34` | SQLAlchemy async dependency |
| **email-validator 2.2.0** | `requirements.txt:69` | Pydantic email field validation |
| **python-multipart 0.0.20** | `requirements.txt:6` | FastAPI form parsing |
| **python-dotenv 1.2.1** | `requirements.txt:47` | `.env` loading |
| **pyyaml 6.0.3** | `requirements.txt:70` | YAML config parsing |
| **colorama 0.4.6** | `requirements.txt:88` | Colored log output (`LOG_FORMAT=colored` mode) |

### Removed / Vendored

- **toon-python** — Removed from PyPI; vendored at `backend/app/lib/toon_python` (`requirements.txt:108` comment). Used for token-efficient LLM data format.

---

## Configuration

### Frontend Build Config

**`frontend/next.config.js`** (21 lines):
- `reactStrictMode: true`
- `output: 'standalone'` — required for Docker deployment (writes minimal `server.js` + node_modules subset)
- `env.NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000` (overridden by Vercel env)
- `compiler.removeConsole: { exclude: ['error', 'warn'] }` in production — **important:** retains `console.error/warn` for remote debugging (per MEMORY.md "Deployment Lessons")
- **Missing:** no `images.domains` / `images.remotePatterns` config — `next/image` external URLs will fail to optimize. Frontend uses `<img>` tags in many places to work around this.

**`frontend/tsconfig.json`** (28 lines):
- `target: ES2020`, `module: esnext`, `moduleResolution: bundler`
- `strict: true`, `isolatedModules: true`, `noEmit: true`
- Path alias: `@/*` → `./*` (root-relative)
- Includes `next-env.d.ts`, `**/*.ts`, `**/*.tsx`, `.next/types/**/*.ts`

**`frontend/tailwind.config.ts`** (88 lines):
- Content scan: `pages/`, `components/`, `app/`
- Custom font families wired to `--font-dm-sans` and `--font-instrument` CSS vars
- Custom colors all reference CSS variables (`var(--primary)`, `var(--accent)`, `var(--text)`, etc.) — defined in `frontend/app/globals.css:11-50`
- Custom shadows: `editorial`, `card`, `card-hover`, `float`, `premium`
- Custom animations: `fade-up`, `slide-in`, `card-enter` (RFC §2.6)
- Plugin: `@tailwindcss/typography`

**`frontend/vitest.config.ts`** (24 lines):
- `environment: 'jsdom'`, `globals: true`
- Setup file: `./tests/setup.ts`
- Coverage reporters: `text`, `json`, `html`
- Path alias `@` → repo root via `path.resolve(__dirname, './')`

### Backend Build Config

**`backend/alembic.ini`** (115 lines):
- Migration script location: `alembic/`
- File template: `%%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s` — date-prefixed for chronological ordering
- `sqlalchemy.url` left empty — actual URL read from `settings.DATABASE_URL` in `backend/alembic/env.py`
- Logging: SQLAlchemy at `WARN`, Alembic at `INFO`

**`backend/pytest.ini`** (13 lines):
- `testpaths = tests`
- `asyncio_mode = auto` — all async tests run automatically
- Filters all `DeprecationWarning` and `PendingDeprecationWarning` (potentially hides real upgrade warnings)
- Markers: `asyncio`, `slow`, `integration`

**`backend/app/core/config.py`** (462 lines, 197 `Field()` declarations):
- Single `Settings` class extends `pydantic_settings.BaseSettings`
- Loads from `.env` file (`Config.env_file = ".env"`, `case_sensitive = True`)
- 9 required-without-default fields: `SECRET_KEY` (min 32 chars), `ADMIN_PASSWORD` (min 8 chars), `DATABASE_URL`, `REDIS_URL`, `OPENAI_API_KEY` — others have defaults
- Custom validators: `parse_cors_origins`, `parse_trusted_proxy_cidrs`, `parse_domain_list`
- Override mechanism: `load_config_overrides_from_db()` (line 423) loads from Redis snapshot → DB `app_configs` table → `.env` (priority order)

---

## Build Pipeline & Deployment

### Frontend (Vercel)

- **Project ID:** `prj_lU4kjtXREUFL34njzOUg5haZEVJt` (`frontend/.vercel/project.json`)
- **Org ID:** `team_J9noddIEFWi23BtLs4yeYN63`
- **No `vercel.json` committed** — Vercel uses default Next.js detection
- Build command: `next build` (auto-detected from `frontend/package.json:7`)
- Install command: `npm install` (default)
- Output: standalone (`frontend/next.config.js:5`)
- **Build-time env var:** `NEXT_PUBLIC_API_URL` baked into bundle. Must rebuild Docker image / redeploy Vercel project to change.
- **Vercel preview URLs:** Each commit gets unique URL like `reviewguide-qs8pkjpk2-habibs-projects-2039317a.vercel.app`. Handled by backend `CORS_ORIGIN_REGEX=https://.*\.vercel\.app` (see Security section).

### Backend (Railway)

- Built from `backend/Dockerfile` (multi-stage: builder → production, both `python:3.11-slim`)
- Build context: project **root** (so `requirements.txt` and `backend/` are both accessible)
- App user: non-root `appuser` (uid created in Dockerfile, line 32)
- Healthcheck: `curl -f http://localhost:8000/health` every 30s (`backend/Dockerfile:57-58`)
- Startup: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` (`backend/Dockerfile:64`)
- **Builder gotcha:** Per MEMORY.md, Railway sometimes uses RAILPACK builder instead of DOCKERFILE on git-triggered deploys. Use `railway deploy` CLI as backup.

### docker-compose.yml (local dev)

| Service | Image / Build | Port | Healthcheck |
|---------|---------------|------|-------------|
| `postgres` | `postgres:15-alpine` | 5432 | `pg_isready` every 10s |
| `redis` | `redis:7-alpine` with `--appendonly yes` | 6379 | `redis-cli ping` every 10s |
| `backend` | Built from `backend/Dockerfile` | 8000 | `curl /health` every 30s |
| `frontend` | Built from `frontend/Dockerfile` (`NEXT_PUBLIC_API_URL=http://localhost:8000` arg) | 3000 | `wget` every 30s |
| `migrations` | Same as backend, runs `alembic upgrade head` once | — | One-shot, profile `setup` |

Volumes: `postgres_data`, `redis_data` (named volumes, persist across compose-down)
Network: `reviewguide-network` (bridge driver)

**CORS in docker-compose.yml:** Hardcoded at line 60 to `["http://localhost:3000","http://localhost:3001","http://localhost:3002","http://localhost:3003","http://127.0.0.1:3000","http://127.0.0.1:3001"]`. If you change `npm run dev` port, you must update this AND restart backend.

---

## Environment Variable Inventory

### Required (no default — startup fails if unset)

Source: `backend/app/core/config.py` `Field(..., ...)` declarations.

| Variable | Constraint | File:Line | Purpose |
|----------|-----------|-----------|---------|
| `SECRET_KEY` | min 32 chars | `config.py:18` | JWT signing, encryption |
| `ADMIN_PASSWORD` | min 8 chars | `config.py:51` | Admin panel login |
| `DATABASE_URL` | — | `config.py:54` | Postgres connection string (`postgresql+asyncpg://...`) |
| `REDIS_URL` | — | `config.py:61` | Redis connection (`redis://` or `rediss://` for TLS/MemoryDB) |
| `OPENAI_API_KEY` | — | `config.py:197` | OpenAI LLM access |

In `docker-compose.yml`, `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` use the `${VAR:?error}` syntax — compose refuses to start without them.

### Required for production (no startup fail, but feature disabled)

| Variable | File:Line | Affected Feature |
|----------|-----------|------------------|
| `CORS_ORIGINS` | `config.py:23` | Browser fetch will be silently blocked. Default covers localhost only. |
| `CORS_ORIGIN_REGEX` | `config.py:27` | **Required for Vercel previews.** Set to `https://.*\.vercel\.app` on Railway per MEMORY.md. |

### Optional / Feature-Flag Gated

#### LLM & Search
- `ANTHROPIC_API_KEY` (config.py:198) — Claude access, optional fallback
- `DEFAULT_MODEL` = `gpt-4o-mini` (config.py:199)
- `PLANNER_MODEL`, `INTENT_MODEL`, `CLARIFIER_MODEL`, `COMPOSER_MODEL`, `PRODUCT_SEARCH_MODEL` — per-agent model overrides
- `PLANNER_MAX_TOKENS=2000`, `INTENT_MAX_TOKENS=50`, `CLARIFIER_MAX_TOKENS=800`, `COMPOSER_MAX_TOKENS=80`, `PRODUCT_SEARCH_MAX_TOKENS=500`
- `SEARCH_PROVIDER` = `perplexity` (config.py default) or `openai` (docker-compose default)
- `PERPLEXITY_API_KEY` — only required if `SEARCH_PROVIDER=perplexity`
- `OPENAI_SEARCH_BASE_URL`, `OPENAI_SEARCH_TIMEOUT=30.0`
- Per-vertical domain filters: `OPENAI_PRODUCT_DOMAINS`, `OPENAI_SERVICE_DOMAINS`, `OPENAI_TRAVEL_DOMAINS`, `PERPLEXITY_PRODUCT_DOMAINS`, `PERPLEXITY_SERVICE_DOMAINS`, `PERPLEXITY_TRAVEL_DOMAINS`

#### Tiered Routing & Review Search
- `ENABLE_SERPAPI=false` (config.py:145) — gates Serper.dev review search (note: code under `backend/app/services/serpapi/` is named for SerpAPI but actually calls `https://google.serper.dev`)
- `SERPAPI_API_KEY` — Serper.dev API key (must be set or feature breaks silently)
- `SERPAPI_MAX_SOURCES=8`, `SERPAPI_CACHE_TTL=86400`, `SERPAPI_TIMEOUT=15.0`
- `ENABLE_REDDIT_API=false` (Tier 3, requires consent + commercial license)
- `ENABLE_YOUTUBE_TRANSCRIPTS=true` (Tier 2, default-on)
- `MAX_AUTO_TIER=2` — highest tier to escalate without user consent
- `PARALLEL_API_TIMEOUT_MS=5000`
- `LOG_API_COSTS=true` — logs to `api_usage_logs` table
- `CIRCUIT_BREAKER_FAILURE_THRESHOLD=3`, `CIRCUIT_BREAKER_RESET_TIMEOUT=300`

#### Affiliate
- `AMAZON_API_ENABLED=false` — `false` = mock mode w/ real ASINs (still produces working affiliate links)
- `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY` — PA-API credentials (only required when `AMAZON_API_ENABLED=true`)
- `AMAZON_ASSOCIATE_TAG=revguide-20` — **migrated from `mikejahshan-20` on 2026-03-25** per MEMORY.md
- `AMAZON_ASSOCIATE_TAGS=US:revguide-20,UK:...` — country-specific overrides
- `AMAZON_DEFAULT_COUNTRY=US`
- `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_CAMPAIGN_ID` — eBay Partner Network
- `EBAY_MKCID=1`, `EBAY_MKRID=711-53200-19255-0`, `EBAY_TOOLID=10001`, `EBAY_MKEVT=1` — eBay tracking constants
- `EBAY_AFFILIATE_CUSTOM_ID` — optional sub-ID
- `USE_MOCK_AFFILIATE=true` — uses mock provider for all affiliates
- `CJ_API_ENABLED=false`, `CJ_API_KEY`, `CJ_WEBSITE_ID`, `CJ_ADVERTISER_IDS=joined` — Commission Junction
- `CJ_API_TIMEOUT=10.0`, `CJ_CACHE_TTL=28800`, `CJ_MAX_RESULTS=20`
- **Placeholder (not yet implemented):** `WALMART_API_ENABLED`, `WALMART_API_KEY`, `WALMART_AFFILIATE_ID`, `BESTBUY_*`, `TARGET_*`
- `MAX_AFFILIATE_OFFERS_PER_PRODUCT=3`
- `SHOW_AFFILIATE_LINKS_PER_PRODUCT=false`

#### Travel
- `TRAVEL_HOTEL_PROVIDERS=mock` (or `booking,expedia`) — comma-separated provider list
- `TRAVEL_FLIGHT_PROVIDERS=mock` (or `skyscanner,amadeus`)
- `USE_MOCK_TRAVEL=true` (legacy flag)
- `BOOKING_API_KEY`, `BOOKING_AFFILIATE_ID` — Booking.com via RapidAPI
- `EXPEDIA_API_KEY`
- `SKYSCANNER_API_KEY` — via RapidAPI
- `AMADEUS_API_KEY`, `AMADEUS_API_SECRET`
- `VIATOR_AFFILIATE_ID` — activity search links only (no API)
- `ENABLE_TRAVEL_CACHE=true`, `TRAVEL_CACHE_TTL=3600`
- `ENABLE_AIRPORT_CACHE=true`, `AIRPORT_CACHE_EXPIRY_DAYS=180`
- Provider limits: `EBAY_MAX_RESULTS=50`, `AMADEUS_MAX_HOTEL_RESULTS=50`, `AMADEUS_MAX_HOTELS_PER_REQUEST=5`, `AMADEUS_MAX_HOTELS_TO_RETURN=10`, `AMADEUS_MAX_FLIGHT_RESULTS=10`, `BOOKING_MAX_RESULTS=10`, `SKYSCANNER_MAX_RESULTS=10`
- `SKYSCANNER_POLLING_DELAY=2`

#### Geolocation
- `IPINFO_TOKEN` — `https://ipinfo.io/{ip}/json?token=...` for country detection (`backend/app/services/geolocation.py:35`). **Optional** (works without token but rate-limited to 1k/day).

#### Database / Redis pool
- `DB_POOL_SIZE=50`, `DB_MAX_OVERFLOW=50`, `DB_POOL_RECYCLE=3600`, `DB_CONNECT_TIMEOUT=10`
- `REDIS_MAX_CONNECTIONS=50`, `REDIS_RETRY_MAX_ATTEMPTS=3`, `REDIS_SOCKET_CONNECT_TIMEOUT=5`, `REDIS_HEALTH_CHECK_INTERVAL=30`, `REDIS_RETRY_BACKOFF_BASE=0.1`
- `ENABLE_SEARCH_CACHE=true`
- `USE_REDIS_FOR_HISTORY=true` (false = direct Postgres reads, dev/debug only)
- `MAX_HISTORY_MESSAGES=30` (config default; docker-compose env shows older `10`)
- `MAX_USER_HISTORY_FOR_SLOT_EXTRACTION=5`
- `HALT_STATE_TTL=3600`, `CHAT_HISTORY_CACHE_TTL=3600`

#### Rate Limiting
- `RATE_LIMIT_ENABLED=true` (default)
- `RATE_LIMIT_GUEST_REQUESTS=20`, `RATE_LIMIT_GUEST_WINDOW=60` (per-minute for guests in code default; docker-compose env example uses 10/3600)
- `RATE_LIMIT_AUTH_REQUESTS=100`, `RATE_LIMIT_AUTH_WINDOW=60`
- `RATE_LIMIT_PER_IP=100`, `RATE_LIMIT_PER_SESSION=20` (legacy fields)
- `TRUSTED_PROXY_CIDRS=[]` — only trust `X-Forwarded-For` from these CIDRs

#### Observability
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST=https://cloud.langfuse.com`
- `LANGFUSE_OTLP_ENDPOINT=/api/public/otel`
- `ENABLE_TRACING=true`, `ENABLE_OPENTELEMETRY_EXPORT=true`
- OTel batch tuning: `OTEL_BATCH_SCHEDULE_DELAY_MILLIS=5000`, `OTEL_BATCH_MAX_QUEUE_SIZE=2048`, `OTEL_BATCH_MAX_EXPORT_BATCH_SIZE=512`, `OTEL_BATCH_EXPORT_TIMEOUT_MILLIS=30000`

#### MCP & Workflow
- `USE_MCP_PLANNER=false` — true = MCP-based dynamic planner; false = traditional LangGraph workflow

#### Logging
- `LOG_ENABLED=true`, `LOG_LEVEL=INFO`, `LOG_FORMAT=colored` (use `json` in production)
- `LITELLM_LOG_LEVEL=INFO`

#### Anonymous Users
- `ANONYMOUS_EMAIL_DOMAIN=@reviewguide.ai`, `ANONYMOUS_EMAIL_PREFIX=anonymous_`, `ANONYMOUS_EMAIL_RANDOM_LENGTH=16`

#### JWT
- `JWT_ALGORITHM=HS256`, `JWT_EXPIRATION_HOURS=24`
- `JWT_SECRET` — env var, falls back to `SECRET_KEY` (`backend/app/utils/auth.py:19`)

#### Encryption
- `CONFIG_ENCRYPTION_KEY` — Fernet key for encrypting sensitive values stored in `app_configs` DB table

#### Server
- `APP_HOST=0.0.0.0`, `APP_PORT=8000`
- `CHAT_EVENT_QUEUE_TIMEOUT=0.1`, `CHAT_STREAM_SLEEP_DELAY=0.01`

#### Link Health
- `ENABLE_LINK_HEALTH_CHECKER=true`
- `LINK_HEALTH_CHECK_INTERVAL_HOURS=6`, `LINK_HEALTH_CHECK_TIMEOUT=10`, `LINK_HEALTH_CHECK_MAX_CONCURRENT=10`

### Frontend Env Vars

- `NEXT_PUBLIC_API_URL` — backend base URL. **Build-time** (baked into bundle). Default `http://localhost:8000`. Set in:
  - `frontend/.env.local.example`
  - `frontend/.env.ecs.example` (set to `https://api.yourdomain.com`)
  - `docker-compose.yml:131,135` (set to `http://localhost:8000`)
  - Vercel project settings (production)
- `NODE_ENV`, `PORT=3000`, `HOSTNAME=0.0.0.0` — runtime, set in `frontend/Dockerfile:62-64`
- `NEXT_TELEMETRY_DISABLED=1` — disabled both at build (Dockerfile:32) and runtime (Dockerfile:62)

### Undocumented / Code-only

The following are read directly from environment but **not declared as `Field()` in `config.py`**:
- `JWT_SECRET` — `backend/app/utils/auth.py:19` (`os.getenv("JWT_SECRET", settings.SECRET_KEY)`)
- `DB_USER`, `DB_PASSWORD`, `DB_NAME` — only used by `docker-compose.yml` to construct `DATABASE_URL` for the `postgres` service container
- `ENV`, `DEBUG` — declared in config but read from env in docker-compose

---

## Third-Party API Dependencies

### Critical Path

| Service | SDK | Auth Var | Failure Mode |
|---------|-----|----------|--------------|
| **OpenAI** (LLM) | `openai==2.7.1` | `OPENAI_API_KEY` | **Hard fail** — every chat request invokes LLM. Required at startup (`config.py:197`). Marked CRITICAL in startup manifest (`startup_manifest.py:189-194`). |
| **Postgres** | `asyncpg==0.30.0` + `psycopg2-binary==2.9.11` | `DATABASE_URL` | Hard fail at startup — `init_db()` in lifespan handler exits process if connection fails (`backend/app/main.py:67-71`). |
| **Redis** | `redis==7.0.1` | `REDIS_URL` | Hard fail at startup (same lifespan handler). Used for halt state, rate limit, search cache, history cache. |

### Optional / Soft-Fail (degrades gracefully)

| Service | Endpoint / SDK | Auth Var | Failure Mode |
|---------|----------------|----------|--------------|
| **Anthropic Claude** | `anthropic==0.72.0` | `ANTHROPIC_API_KEY` | No-op if unset; falls back to OpenAI for all calls. |
| **Perplexity Search** | direct httpx → `https://api.perplexity.ai` | `PERPLEXITY_API_KEY` | If `SEARCH_PROVIDER=perplexity` and key missing → search returns empty, degraded response. |
| **Serper.dev** (review search) | direct httpx → `https://google.serper.dev/search` and `/shopping` | `SERPAPI_API_KEY` (env name is misleading — it's the Serper key) | Gated by `ENABLE_SERPAPI=true`. If disabled or key missing, `review_search` MCP tool returns empty bundle. **Known issue:** `ENABLE_SERPAPI` and `SERPAPI_API_KEY` were missing on Railway in the past, silently breaking review search (per MEMORY.md). |
| **Amazon PA-API** | Custom HMAC client in `amazon_provider.py` | `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY` | When `AMAZON_API_ENABLED=false` (current state), serves mock data with real ASINs from `backend/data/mock_amazon_products.json`. Affiliate links still work via `revguide-20` tag. |
| **Curated Amazon Links** | Static dict in `backend/app/services/affiliate/providers/curated_amazon_links.py` | none | 141 hardcoded `amzn.to/...` short links across 28+ keyword categories. Per MEMORY.md, this is the **preferred source** over PA-API. Resolved via `find_curated_links(query)` (line 219). |
| **eBay Partner Network** | direct httpx | `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_CAMPAIGN_ID` | If unset, `USE_MOCK_AFFILIATE=true` is used. |
| **Commission Junction (CJ)** | direct httpx | `CJ_API_KEY`, `CJ_WEBSITE_ID` | Gated by `CJ_API_ENABLED=false`. Off by default. |
| **Amadeus** (hotels + flights) | `amadeus==12.0.0` SDK | `AMADEUS_API_KEY`, `AMADEUS_API_SECRET` | Empty results returned if unset or `mock` provider selected. |
| **Booking.com** (RapidAPI) | direct httpx → `https://booking-com.p.rapidapi.com/v1` | `BOOKING_API_KEY` (RapidAPI key), `BOOKING_AFFILIATE_ID` | Empty results if unset. |
| **Skyscanner** (RapidAPI) | direct httpx | `SKYSCANNER_API_KEY` (RapidAPI key) | Empty results if unset. |
| **Expedia** (planned, RapidAPI) | placeholder provider only | `EXPEDIA_API_KEY` | Stub provider, not production-wired. |
| **Viator** (activities) | URL-only provider, no API | `VIATOR_AFFILIATE_ID` | Generates affiliate search URLs. No data fetch. |
| **TripAdvisor** | listed in tiered_router api_registry | none specific | Provider not yet implemented. |
| **YouTube transcripts** (Tier 2) | listed in tiered_router | none specific | Gated by `ENABLE_YOUTUBE_TRANSCRIPTS=true`. Implementation in `product_evidence` MCP tool. |
| **Reddit API** (Tier 3) | listed in tiered_router | requires `ENABLE_REDDIT_API=true` + user consent + commercial license | Off by default. |
| **IPInfo.io** (geolocation) | direct httpx → `https://ipinfo.io/{ip}/json` | `IPINFO_TOKEN` (optional) | Falls back to no-token mode (1k req/day limit). |
| **Langfuse** (observability) | `langfuse==3.9.1` | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | If unset, traces silently skipped. |

### Provider Status (from `backend/app/services/startup_manifest.py:178-296`)

The startup manifest reports the following enabled/disabled state per deploy:

1. **OpenAI** — required, marked critical
2. **Search provider** — perplexity OR openai_search (per `SEARCH_PROVIDER`)
3. **SerpAPI** — gated by `ENABLE_SERPAPI`
4. **Amazon** — gated by `AMAZON_API_ENABLED` (mock when false)
5. **eBay** — enabled if `EBAY_APP_ID` is set
6. **Booking.com** — enabled if `BOOKING_API_KEY` or `BOOKING_AFFILIATE_ID` is set
7. **Amadeus** — enabled if `AMADEUS_API_KEY` is set
8. **Viator** — enabled if `VIATOR_AFFILIATE_ID` is set

`all_critical_providers_ok` is determined solely by OpenAI status.

---

## Affiliate Provider Chain

### Amazon

- **Active tag:** `revguide-20` (US, primary)
- **Migration:** Switched from `mikejahshan-20` → `revguide-20` on 2026-03-25 across Railway env, code, static docs (per MEMORY.md)
- **Code references:**
  - `frontend/components/InlineProductCard.tsx:82` — `?tag=revguide-20`
  - `frontend/components/ResultsProductCard.tsx:92` — `?tag=revguide-20`
  - `backend/mcp_server/tools/product_compose.py:1193` — `?tag=revguide-20` in fallback Amazon search URL
- **Multi-region tags:** `AMAZON_ASSOCIATE_TAGS` env var format `US:revguide-20,UK:revguide-21,DE:revguide-21,CA:revguide-20`. Parsed by `parse_associate_tags()` in `backend/app/services/affiliate/providers/amazon_provider.py:224-244`.
- **Domain map:** `AMAZON_DOMAINS` dict at `amazon_provider.py:200-220` covers 21 country marketplaces (US, UK, DE, FR, JP, IT, ES, CA, AU, MX, BR, IN, NL, SG, AE, SA, SE, PL, BE, EG, TR).
- **Link generation:** `generate_amazon_affiliate_link(asin, country_code, associate_tag)` (`amazon_provider.py:247-286`) builds `https://www.{domain}/dp/{asin}?tag={tag}`.
- **Curated short links:** 141 hardcoded `amzn.to/...` links in `backend/app/services/affiliate/providers/curated_amazon_links.py` mapped to keyword patterns (`bluetooth speaker`, `noise cancelling headphone`, `laptop student`, `washing machine`, etc.). These are **preferred over PA-API** per MEMORY.md.

### eBay Partner Network

- Tracking IDs hardcoded in env defaults: `EBAY_MKCID=1`, `EBAY_MKRID=711-53200-19255-0` (US marketplace rotation), `EBAY_TOOLID=10001`, `EBAY_MKEVT=1`
- Custom sub-ID: `EBAY_AFFILIATE_CUSTOM_ID` (optional)
- Provider implementation: `backend/app/services/affiliate/providers/ebay_provider.py`
- Mock fallback when `USE_MOCK_AFFILIATE=true` (default `True` in `config.py:261`)

### Commission Junction (CJ)

- Provider: `backend/app/services/affiliate/providers/cj_provider.py`
- Off by default (`CJ_API_ENABLED=false`)
- Bearer token auth via `CJ_API_KEY`
- Targets multiple advertisers via `CJ_ADVERTISER_IDS=joined` (all joined advertisers)

### Booking.com

- Affiliate ID: `BOOKING_AFFILIATE_ID`
- API access via RapidAPI host `booking-com.p.rapidapi.com`

### Viator

- URL-only provider (`backend/app/services/travel/providers/viator_plp_provider.py`)
- Generates affiliate search URLs using `VIATOR_AFFILIATE_ID`
- No data fetch — links to Viator search pages

### Future / Placeholder

- **Walmart** (Impact Radius) — env vars defined (`WALMART_API_ENABLED`, `WALMART_API_KEY`, `WALMART_AFFILIATE_ID`) but **no provider file** in `backend/app/services/affiliate/providers/`
- **Best Buy** — same as above
- **Target** (Impact Radius) — same as above
- **Skimlinks** — **Not present** in codebase (no references in any `.py`, `.ts`, `.tsx`, or env example)

---

## Security Posture

### API Key Handling

- All secrets injected via env vars (no committed secrets in repo)
- `.env` file in `backend/` exists (referenced by pydantic-settings) but gitignored
- `frontend/.env`, `frontend/.env.*` are gitignored (`frontend/.dockerignore:18-19`)
- Secret encryption: `CONFIG_ENCRYPTION_KEY` (Fernet) used by `backend/app/services/config_encryption.py` to encrypt sensitive config values stored in the `app_configs` DB table. Encrypted keys list at `config_encryption.py:31` includes `IPINFO_TOKEN` and others.

### CORS Configuration

- Default origins (`backend/app/core/config.py:23-26`): `http://localhost:3000,3001,3002` and `127.0.0.1:3000,3001`
- Production: hardcoded list in `docker-compose.yml:60` for local dev; Railway env overrides for production
- **Vercel preview support:** `CORS_ORIGIN_REGEX=https://.*\.vercel\.app` set on Railway (per MEMORY.md "Deployment Lessons"). Without this, browser silently blocks preview deployments.
- Implementation: `backend/app/main.py:104-112` — combines explicit origins from `cors_origins_list` with regex from `CORS_ORIGIN_REGEX`
- `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]` — permissive once origin matches

### Rate Limiting

- Implementation: `backend/app/core/rate_limiter.py` — Redis-backed sliding window via sorted sets
- Default ON: `RATE_LIMIT_ENABLED=true` (config.py:96-99, docker-compose.yml:106)
- Two tiers:
  - **Guest:** 20 requests / 60 seconds (config.py defaults; .env.example shows older 10/3600)
  - **Authenticated:** 100 requests / 60 seconds
- Returns `429 TOO_MANY_REQUESTS` on limit (`rate_limiter.py:76-86`)
- Trusted proxy support: `TRUSTED_PROXY_CIDRS` allowlist for `X-Forwarded-For` parsing

### Authentication

- **Model:** JWT (HS256) for admin endpoints
- **Library:** `python-jose[cryptography]==3.5.0` (`backend/app/utils/auth.py:8`)
- **Password hashing:** `bcrypt` (used directly via `bcrypt.gensalt()` / `bcrypt.checkpw()` — `auth.py:7,35-37,57`). `passlib[bcrypt]` is in `requirements.txt:46` but largely bypassed.
- **Token lifetime:** 24 hours (`JWT_EXPIRATION_HOURS=24`, config.py:390)
- **Endpoints:** `backend/app/api/v1/admin_auth.py` — `HTTPBearer` dependency, login at `/v1/auth/login`, protected routes use `get_current_admin` dependency
- **Public chat endpoint:** Optional Bearer token (`chat.py:1011`). Most users are anonymous (auto-generated `anonymous_<random>@reviewguide.ai` per `ANONYMOUS_*` env vars).
- **Admin credentials:** `ADMIN_USERNAME` / `ADMIN_PASSWORD` env vars; required at startup with min 8 char password.

### Secret Rotation

- **No automated rotation** — all secrets are environment variables manually set on Railway / Vercel
- `JWT_SECRET` falls back to `SECRET_KEY` if not separately set (`auth.py:19`) — rotating `SECRET_KEY` invalidates all existing JWTs
- Database `app_configs` table values can be encrypted with `CONFIG_ENCRYPTION_KEY` for at-rest encryption

### Other

- Non-root containers: backend runs as `appuser` (Dockerfile:32, 49), frontend as `nextjs:nodejs` (Dockerfile:46-47)
- Healthcheck endpoints exposed: `GET /health` (backend), `GET /` (frontend)
- `removeConsole` in production preserves `console.error` and `console.warn` only — strips `console.log` from prod bundle but keeps error visibility for remote debugging (per MEMORY.md "Deployment Lessons")
- `ErrorBanner` component shows actual error string (not generic message) — critical for remote debugging

---

## Platform Requirements

### Development

- Docker + Docker Compose (primary supported dev environment)
- Node.js 20 (only if running frontend outside Docker via `npm run dev`)
- Python 3.11 (only if running backend outside Docker)
- PostgreSQL 15 on port 5432
- Redis 7 on port 6379
- Free ports: 3000, 8000, 5432, 6379

### Production

- **Backend:** Railway, deployed from `backend/Dockerfile`. Container exposes 8000.
- **Frontend:** Vercel, project `prj_lU4kjtXREUFL34njzOUg5haZEVJt`, builds via Next.js standalone output.
- **Database:** Postgres 15+ (Railway-hosted by default; AWS RDS configuration in `backend/.env.ecs.example`)
- **Cache:** Redis 7+ (Railway; AWS ElastiCache or MemoryDB optional — note `rediss://` for MemoryDB TLS)
- **CORS:** Must include `CORS_ORIGIN_REGEX=https://.*\.vercel\.app` for preview deployments
- **Build trigger:** Git push to `main` → both Railway (backend) and Vercel (frontend) rebuild

---

## Known Risks & Deprecation Watch

| Risk | Severity | Notes |
|------|----------|-------|
| **Next.js 14 on extended maintenance** | Medium | Next 15 is current LTS. No security patches imminent but should plan migration. |
| **`passlib` maintenance-only mode** | Low | Already bypassed in favor of direct `bcrypt`. Can drop `passlib[bcrypt]` from requirements. |
| **`google-search-results` package name misleading** | Medium | The PyPI package `google-search-results==2.4.2` is the SerpAPI client, but `backend/app/services/serpapi/client.py` actually calls Serper.dev directly via httpx. The SerpAPI package is currently unused — can be removed. |
| **`pytest.ini` filters all DeprecationWarnings** | Medium | `filterwarnings = ignore::DeprecationWarning` in `backend/pytest.ini:8` hides upgrade signals from pinned deps. |
| **Backend has no requirements lockfile** | Medium | Single `requirements.txt` with pinned versions but no transitive deps locked. Reproducible installs depend on PyPI not yanking versions. Consider `pip-compile` or `uv pip compile`. |
| **Hardcoded CORS in docker-compose.yml** | Low | Local dev only; production uses Railway env. But port 3000-3003 hardcoded means changing `npm run dev` port requires backend restart. |
| **`removeConsole` config note** | Low | Original deploy stripped ALL console methods, hiding errors. Now correctly excludes `error`/`warn`. Documented in MEMORY.md. |
| **No `next/image` remote pattern config** | Low | Frontend uses raw `<img>` tags for external product/hotel images. No optimization. Tradeoff for simplicity. |
| **Railway build can use RAILPACK instead of DOCKERFILE** | Medium | Per MEMORY.md, git-triggered deploys sometimes use wrong builder. Use `railway deploy` CLI as fallback. |
| **OpenTelemetry export deprecation in newer Python OTel SDKs** | Low | Pinned to 1.38.0 across api/sdk/exporter-otlp. Watch for breaking changes when bumping. |
| **Vendored `toon_python`** | Low | Removed from PyPI. Maintained internally at `backend/app/lib/toon_python`. Future maintenance burden. |

---

*Stack analysis: 2026-04-16 (v2-with-swipe branch — v2.0 + swipe carousel + curated-links integration era).*
