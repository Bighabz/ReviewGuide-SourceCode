# 2. Environment and Configuration

## Environment Files Overview

| File | Purpose | Location |
|------|---------|----------|
| `backend/.env` | Backend local development | Gitignored |
| `backend/.env.example` | Backend template | Version controlled |
| `backend/.env.ecs.example` | ECS production template | Version controlled |
| `frontend/.env.local` | Frontend local development | Gitignored |
| `frontend/.env.local.example` | Frontend template | Version controlled |
| `frontend/.env.ecs.example` | ECS production template | Version controlled |
| `docs/backend.env` | Production env reference | Contains actual values |
| `docs/frontend.env` | Production env reference | Contains actual values |

---

## Backend Environment Variables

### Application Core
```bash
APP_NAME=ReviewGuide.ai
ENV=production                    # development | production
DEBUG=false                       # true | false
API_V1_PREFIX=/v1
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=<64-char-random-key>   # [SECRET] Generate with: openssl rand -hex 32
```

### CORS Configuration
```bash
CORS_ORIGINS=["http://localhost:3000","https://your-frontend-domain.com"]
```

### Admin Credentials
```bash
ADMIN_USERNAME=admin              # [SECRET]
ADMIN_PASSWORD=<strong-password>  # [SECRET]
```

### Database (PostgreSQL RDS)
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname  # [SECRET]
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
DB_CONNECT_TIMEOUT=10
```

**Current Production:**
- Host: `review-guide-postgres.c72wquegyskv.ca-central-1.rds.amazonaws.com`
- Database: `postgres`
- Port: `5432`

### Redis (MemoryDB/ElastiCache)
```bash
REDIS_URL=redis://host:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_RETRY_MAX_ATTEMPTS=3
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_HEALTH_CHECK_INTERVAL=30
REDIS_RETRY_BACKOFF_BASE=0.1
ENABLE_SEARCH_CACHE=true
USE_REDIS_FOR_HISTORY=true
```

**Current Production:**
- Host: `clustercfg.review-guide-redis.a7w3fb.memorydb.ca-central-1.amazonaws.com`
- Port: `6379`

### Conversation Settings
```bash
MAX_HISTORY_MESSAGES=10
MAX_USER_HISTORY_FOR_SLOT_EXTRACTION=5
```

### Rate Limiting
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GUEST_REQUESTS=10
RATE_LIMIT_GUEST_WINDOW=3600
RATE_LIMIT_AUTH_REQUESTS=100
RATE_LIMIT_AUTH_WINDOW=3600
RATE_LIMIT_PER_IP=100
RATE_LIMIT_PER_SESSION=20
```

### LLM Providers
```bash
OPENAI_API_KEY=sk-...             # [SECRET]
ANTHROPIC_API_KEY=sk-ant-...      # [SECRET] (if using)
DEFAULT_MODEL=gpt-4o-mini
LITELLM_LOG_LEVEL=WARNING

# Agent-specific Models
PLANNER_MODEL=o3-mini
INTENT_MODEL=gpt-4o-mini
CLARIFIER_MODEL=gpt-4o-mini
COMPOSER_MODEL=gpt-4o-mini
```

### Search Configuration
```bash
SEARCH_PROVIDER=openai
OPENAI_SEARCH_BASE_URL=https://api.openai.com/v1
OPENAI_SEARCH_TIMEOUT=30.0
OPENAI_PRODUCT_DOMAINS=amazon.com,ebay.com,walmart.com
OPENAI_SERVICE_DOMAINS=g2.com,capterra.com,trustpilot.com
OPENAI_TRAVEL_DOMAINS=tripadvisor.com,lonelyplanet.com,booking.com

PERPLEXITY_API_KEY=pplx-...       # [SECRET]
PERPLEXITY_BASE_URL=https://api.perplexity.ai
PERPLEXITY_MODEL=sonar
PERPLEXITY_TIMEOUT=30.0
PERPLEXITY_PRODUCT_DOMAINS=ebay.com
PERPLEXITY_SERVICE_DOMAINS=g2.com,capterra.com,trustpilot.com
PERPLEXITY_TRAVEL_DOMAINS=tripadvisor.com,lonelyplanet.com

ENABLE_LLM_SEARCH_QUERY=false
```

### eBay Partner Network
```bash
EBAY_APP_ID=<ebay-app-id>         # [SECRET]
EBAY_CERT_ID=<ebay-cert-id>       # [SECRET]
EBAY_CAMPAIGN_ID=<campaign-id>    # [SECRET]
EBAY_AFFILIATE_CUSTOM_ID=ai_review
EBAY_MKCID=1
EBAY_MKRID=711-53200-19255-0
EBAY_TOOLID=10001
EBAY_MKEVT=1
EBAY_MAX_RESULTS=50
USE_MOCK_AFFILIATE=false
```

### Amazon Associates
```bash
AMAZON_API_ENABLED=false          # Not currently active
AMAZON_ACCESS_KEY=<access-key>    # [SECRET]
AMAZON_SECRET_KEY=<secret-key>    # [SECRET]
AMAZON_ASSOCIATE_TAG=reviewguideai-20
AMAZON_ASSOCIATE_TAGS=US:reviewguideai-20,UK:reviewguideai-20
AMAZON_DEFAULT_COUNTRY=US
```

### IP Geolocation
```bash
IPINFO_TOKEN=<ipinfo-token>       # [SECRET]
```

### Travel APIs
```bash
# Hotels
BOOKING_API_KEY=<rapidapi-key>    # [SECRET]
BOOKING_AFFILIATE_ID=<affiliate-id>
BOOKING_MAX_RESULTS=10

# Flights
SKYSCANNER_API_KEY=<rapidapi-key> # [SECRET]
SKYSCANNER_MAX_RESULTS=10
SKYSCANNER_POLLING_DELAY=2

# Amadeus (Active)
AMADEUS_API_KEY=<api-key>         # [SECRET]
AMADEUS_API_SECRET=<api-secret>   # [SECRET]
AMADEUS_MAX_HOTEL_RESULTS=50
AMADEUS_MAX_HOTELS_PER_REQUEST=5
AMADEUS_MAX_HOTELS_TO_RETURN=10
AMADEUS_MAX_FLIGHT_RESULTS=10

# Provider Selection
TRAVEL_HOTEL_PROVIDERS=amadeus
TRAVEL_FLIGHT_PROVIDERS=amadeus
USE_MOCK_TRAVEL=false
```

### Travel Cache
```bash
ENABLE_TRAVEL_CACHE=true
TRAVEL_CACHE_TTL=3600
ENABLE_AIRPORT_CACHE=true
AIRPORT_CACHE_EXPIRY_DAYS=180
```

### Link Health Monitoring
```bash
ENABLE_LINK_HEALTH_CHECKER=true
LINK_HEALTH_CHECK_INTERVAL_HOURS=6
LINK_HEALTH_CHECK_TIMEOUT=10
LINK_HEALTH_CHECK_MAX_CONCURRENT=10
```

### Logging
```bash
LOG_ENABLED=true
LOG_LEVEL=WARNING                  # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json                    # json | text
```

### Observability (Langfuse)
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...     # [SECRET]
LANGFUSE_SECRET_KEY=sk-lf-...     # [SECRET]
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_OTLP_ENDPOINT=/api/public/otel
ENABLE_TRACING=true
ENABLE_OPENTELEMETRY_EXPORT=true

# OpenTelemetry Batch Processing
OTEL_BATCH_SCHEDULE_DELAY_MILLIS=5000
OTEL_BATCH_MAX_QUEUE_SIZE=2048
OTEL_BATCH_MAX_EXPORT_BATCH_SIZE=512
OTEL_BATCH_EXPORT_TIMEOUT_MILLIS=30000
```

### Anonymous Users
```bash
ANONYMOUS_EMAIL_DOMAIN=@reviewguide.ai
ANONYMOUS_EMAIL_PREFIX=anonymous_
ANONYMOUS_EMAIL_RANDOM_LENGTH=16
```

### Chat Settings
```bash
CHAT_EVENT_QUEUE_TIMEOUT=0.1
CHAT_STREAM_SLEEP_DELAY=0.01
```

### Cache TTLs
```bash
HALT_STATE_TTL=3600
CHAT_HISTORY_CACHE_TTL=3600
```

---

## Frontend Environment Variables

```bash
# API URL - Backend endpoint
NEXT_PUBLIC_API_URL=https://your-backend-url.com

# Node Environment
NODE_ENV=production
PORT=3000

# Disable telemetry
NEXT_TELEMETRY_DISABLED=1
```

**Current Production:**
```bash
NEXT_PUBLIC_API_URL=https://review-guide-backend-173284151.ca-central-1.elb.amazonaws.com
```

**Important**: `NEXT_PUBLIC_*` variables are embedded at **build time**. You must rebuild the Docker image when changing these values.

---

## AWS Secrets Manager Configuration

For ECS deployments, sensitive values should be stored in AWS Secrets Manager.

### Secret Structure
Create a secret named `reviewguide/production` with this JSON structure:

```json
{
  "SECRET_KEY": "your-64-char-random-key",
  "ADMIN_PASSWORD": "your-strong-admin-password",
  "DATABASE_URL": "postgresql+asyncpg://user:pass@rds-endpoint:5432/dbname",
  "OPENAI_API_KEY": "sk-...",
  "ANTHROPIC_API_KEY": "sk-ant-...",
  "PERPLEXITY_API_KEY": "pplx-...",
  "EBAY_APP_ID": "...",
  "EBAY_CERT_ID": "...",
  "EBAY_CAMPAIGN_ID": "...",
  "AMAZON_ACCESS_KEY": "...",
  "AMAZON_SECRET_KEY": "...",
  "BOOKING_API_KEY": "...",
  "SKYSCANNER_API_KEY": "...",
  "AMADEUS_API_KEY": "...",
  "AMADEUS_API_SECRET": "...",
  "IPINFO_TOKEN": "...",
  "LANGFUSE_PUBLIC_KEY": "pk-lf-...",
  "LANGFUSE_SECRET_KEY": "sk-lf-..."
}
```

### Create Secret via CLI
```bash
aws secretsmanager create-secret \
  --name reviewguide/production \
  --description "ReviewGuide production secrets" \
  --secret-string file://secrets.json \
  --region ca-central-1
```

See `docs/aws-secrets-setup.md` for complete ECS task definition examples.

---

## Configuration Priority

The backend configuration system loads in this priority (highest first):

1. **Environment variables** (runtime)
2. **Database `core_config` table** (dynamic config)
3. **Default values** in code

This allows dynamic configuration updates without redeployment via the admin dashboard.

---

## Sensitive Values Summary

Variables marked as `[SECRET]` should NEVER be committed to version control:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | JWT signing key |
| `ADMIN_PASSWORD` | Admin login password |
| `DATABASE_URL` | Database connection with credentials |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `PERPLEXITY_API_KEY` | Perplexity API key |
| `EBAY_APP_ID` | eBay application ID |
| `EBAY_CERT_ID` | eBay certificate ID |
| `EBAY_CAMPAIGN_ID` | eBay affiliate campaign |
| `AMAZON_ACCESS_KEY` | Amazon PA-API key |
| `AMAZON_SECRET_KEY` | Amazon PA-API secret |
| `AMADEUS_API_KEY` | Amadeus API key |
| `AMADEUS_API_SECRET` | Amadeus API secret |
| `IPINFO_TOKEN` | IPInfo geolocation token |
| `LANGFUSE_PUBLIC_KEY` | Langfuse tracing key |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key |