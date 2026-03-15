# External Integrations

**Analysis Date:** 2026-03-15

## APIs & External Services

**LLM Providers:**
- OpenAI (GPT-4o, GPT-4o-mini) - Primary LLM for all agents and composers
  - SDK/Client: `langchain-openai` via `ModelService` in `backend/app/services/model_service.py`
  - Auth: `OPENAI_API_KEY`
  - Per-agent model config: `PLANNER_MODEL`, `INTENT_MODEL`, `CLARIFIER_MODEL`, `COMPOSER_MODEL`, `PRODUCT_SEARCH_MODEL`

- Anthropic (Claude) - Secondary LLM provider, available but not primary
  - SDK/Client: `anthropic` 0.72 in `requirements.txt`
  - Auth: `ANTHROPIC_API_KEY`

- LiteLLM - Multi-provider LLM proxy
  - SDK/Client: `litellm` 1.79 in `requirements.txt`
  - Purpose: Provider abstraction layer alongside LangChain

**Search Providers (pluggable, set via `SEARCH_PROVIDER`):**
- Perplexity AI - Default search provider (`SEARCH_PROVIDER=perplexity`)
  - SDK/Client: Direct `httpx` calls in `backend/app/services/search/providers/perplexity_provider.py`
  - Auth: `PERPLEXITY_API_KEY`
  - Endpoint: `https://api.perplexity.ai`, model `sonar`

- OpenAI Web Search - Alternative search provider (`SEARCH_PROVIDER=openai`)
  - SDK/Client: `backend/app/services/search/providers/openai_provider.py`
  - Auth: `OPENAI_API_KEY` (shared)
  - Endpoint: `https://api.openai.com/v1`

**Review Search:**
- Serper.dev (currently active) / SerpAPI (fallback) - Product review aggregation
  - SDK/Client: `google-search-results` 2.4 + direct `httpx` in `backend/app/services/serpapi/client.py`
  - Auth: `SERPAPI_API_KEY` (env var name kept for compatibility)
  - Feature flag: `ENABLE_SERPAPI` (default: false)
  - Caching: Redis with 24h TTL (`SERPAPI_CACHE_TTL`)

## Affiliate Networks

**eBay Partner Network:**
- Purpose: Product search and affiliate link generation
- SDK/Client: Direct `httpx` calls to eBay Browse API in `backend/app/services/affiliate/providers/ebay_provider.py`
- Auth: `EBAY_APP_ID`, `EBAY_CERT_ID`
- Affiliate tracking: `EBAY_CAMPAIGN_ID`, `EBAY_MKCID`, `EBAY_MKRID`
- Supports mock mode when `USE_MOCK_AFFILIATE=true`

**Amazon Associates / Product Advertising API:**
- Purpose: Product listings and affiliate links
- SDK/Client: Direct HMAC-signed `httpx` requests in `backend/app/services/affiliate/providers/amazon_provider.py`
- Auth: `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_ASSOCIATE_TAG`
- Feature flag: `AMAZON_API_ENABLED` (default: false — runs mock data by default)
- Multi-region: `AMAZON_ASSOCIATE_TAGS` (country:tag pairs), `AMAZON_DEFAULT_COUNTRY`

**Commission Junction (CJ):**
- Purpose: Product search and affiliate links via CJ Product Search API
- SDK/Client: Direct `httpx` XML requests in `backend/app/services/affiliate/providers/cj_provider.py`
- Auth: `CJ_API_KEY` (Bearer token), `CJ_WEBSITE_ID`
- Endpoint: `https://product-search.api.cj.com/v2/product-search`
- Feature flag: `CJ_API_ENABLED` (default: false)
- Caching: Redis with 8h TTL (`CJ_CACHE_TTL`)
- Config: `CJ_ADVERTISER_IDS` (default: `"joined"` = all joined advertisers)

**Affiliate Providers — Placeholder (not yet implemented):**
- Walmart: `WALMART_API_KEY`, `WALMART_AFFILIATE_ID` — config in `backend/app/core/config.py`
- Best Buy: `BESTBUY_API_KEY`, `BESTBUY_AFFILIATE_ID` — config only
- Target: `TARGET_API_KEY`, `TARGET_AFFILIATE_ID` — config only

## Data Storage

**Databases:**
- PostgreSQL 15
  - Connection: `DATABASE_URL` (format: `postgresql+asyncpg://...`)
  - Client: SQLAlchemy 2.0 async ORM + asyncpg driver (`backend/app/core/database.py`)
  - Pool: 50 connections + 50 overflow (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`)
  - Migrations: Alembic, versioned in `backend/alembic/versions/`
  - Models: `backend/app/models/` (user, session, conversation_message, affiliate_link, affiliate_click, affiliate_merchant, product_index, airport_cache, api_usage_log, request_metric)

**File Storage:**
- Local filesystem only — no S3 or cloud file storage detected
- Static assets served from `frontend/public/` and `static/` at project root

**Caching:**
- Redis 7 (Alpine)
  - Connection: `REDIS_URL`
  - Client: `redis[asyncio]` 7.0 + hiredis 3.3 (`backend/app/core/redis_client.py`)
  - Pool: 50 max connections, exponential backoff retry
  - Used for: halt state persistence, chat history cache, search result cache, CJ/SerpAPI caches, config snapshot (Magento 2-style single-key snapshot)

## Authentication & Identity

**Auth Provider:**
- Custom JWT-based auth (no third-party auth provider)
  - Implementation: `python-jose` + `passlib[bcrypt]` in `backend/app/api/v1/admin_auth.py`
  - Algorithm: HS256 (`JWT_ALGORITHM`)
  - Expiry: 24 hours (`JWT_EXPIRATION_HOURS`)
  - Signing key: `SECRET_KEY` (min 32 chars, required)

**Anonymous Users:**
- Auto-created with generated email `anonymous_{16_random_chars}@reviewguide.ai`
- Config: `ANONYMOUS_EMAIL_DOMAIN`, `ANONYMOUS_EMAIL_PREFIX` in `backend/app/core/config.py`

**Admin:**
- Separate admin credentials: `ADMIN_USERNAME`, `ADMIN_PASSWORD` (required, no defaults)
- Admin panel uses React Admin 5.13 + ra-data-simple-rest at `/admin` route

## Travel APIs

**Amadeus Self-Service API:**
- Purpose: Hotel search and flight search
- SDK/Client: Official `amadeus` 12.0 SDK in `backend/app/services/travel/providers/amadeus_provider.py`
- Auth: `AMADEUS_API_KEY`, `AMADEUS_API_SECRET` (OAuth2)
- Configured via: `TRAVEL_HOTEL_PROVIDERS`, `TRAVEL_FLIGHT_PROVIDERS`

**Booking.com API:**
- Purpose: Hotel search
- SDK/Client: Direct `httpx` in `backend/app/services/travel/providers/booking_provider.py` and `booking_plp_provider.py`
- Auth: `BOOKING_API_KEY`, `BOOKING_AFFILIATE_ID`

**Skyscanner API:**
- Purpose: Flight search
- SDK/Client: Direct `httpx` with polling in `backend/app/services/travel/providers/skyscanner_provider.py`
- Auth: `SKYSCANNER_API_KEY`

**Expedia API:**
- Purpose: Hotel search
- SDK/Client: Direct `httpx` in `backend/app/services/travel/providers/expedia_provider.py` and `expedia_plp_provider.py`
- Auth: `EXPEDIA_API_KEY`

**Viator:**
- Purpose: Activity/experience affiliate links (placeholder)
- Config: `VIATOR_AFFILIATE_ID`
- SDK/Client: `backend/app/services/travel/providers/viator_plp_provider.py`

**Travel Defaults:**
- All travel providers default to mock mode: `USE_MOCK_TRAVEL=true`, `TRAVEL_HOTEL_PROVIDERS=mock`, `TRAVEL_FLIGHT_PROVIDERS=mock`
- Redis caching enabled: `ENABLE_TRAVEL_CACHE=true`, TTL 1 hour

## Monitoring & Observability

**LLM Tracing:**
- Langfuse 3.9 — LLM call tracing and monitoring
  - Auth: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
  - Host: `https://cloud.langfuse.com` (`LANGFUSE_HOST`)
  - Feature flag: `ENABLE_TRACING=true`, `ENABLE_OPENTELEMETRY_EXPORT=true`
  - OTLP path: `/api/public/otel`

**OpenTelemetry:**
- opentelemetry-api/sdk/exporter-otlp 1.38 — spans exported to Langfuse
- Batch processor config: `OTEL_BATCH_SCHEDULE_DELAY_MILLIS=5000`, queue size 2048

**IP Geolocation:**
- ipinfo.io - Country detection from client IP for regional affiliate link routing
  - SDK/Client: Direct `httpx` call in `backend/app/services/geolocation.py`
  - Auth: `IPINFO_TOKEN` (optional; without token limited to 1,000 req/day)

**Logging:**
- Structured logging with colorama 0.4, configurable format (`LOG_FORMAT=colored|json`)
- Centralized logger at `backend/app/core/centralized_logger.py`
- Log level: `LOG_LEVEL`, enable/disable: `LOG_ENABLED`

## CI/CD & Deployment

**Hosting:**
- Backend: Railway (Docker container, git-triggered or `railway deploy` CLI)
- Frontend: Vercel (automatic preview deployments per commit)

**CI Pipeline:**
- Not detected in repository (no `.github/workflows/` or similar)

## Webhooks & Callbacks

**Incoming:**
- SSE streaming endpoint: `POST /v1/chat/stream` — long-lived connection for chat responses
- Affiliate click tracking: `GET /v1/affiliate/click/{link_id}` — redirect with tracking

**Outgoing:**
- No outgoing webhooks detected

## Environment Configuration

**Required env vars (will crash without):**
- `SECRET_KEY` — JWT signing (min 32 chars)
- `ADMIN_USERNAME`, `ADMIN_PASSWORD` — admin panel access
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `OPENAI_API_KEY` — LLM calls

**Secrets location:**
- `backend/.env` file (not committed)
- Production: Railway environment variables panel (backend), Vercel environment panel (frontend)

---

*Integration audit: 2026-03-15*
