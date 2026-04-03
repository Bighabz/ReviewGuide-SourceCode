# Phase 23 — Pre-Fix Baseline

**Captured:** 2026-04-03T05:49:23Z
**Commit SHA:** 46c3b9984f79329e3580e45771d931efac1ed25d

---

## Environment Snapshot

Captured from `docker-compose.yml` (which reads from `backend/.env` via shell variable substitution).

| Variable | Value / Status |
|---|---|
| `ENV` | `development` (default) |
| `DEBUG` | `true` (default) |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:3001","http://localhost:3002","http://localhost:3003","http://127.0.0.1:3000","http://127.0.0.1:3001"]` |
| `CORS_ORIGIN_REGEX` | Not set in docker-compose (Railway: `https://.*\.vercel\.app`) |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:[REDACTED]@postgres:5432/reviewguide_db` |
| `REDIS_URL` | `redis://redis:6379` |
| `RATE_LIMIT_ENABLED` | `false` (overridden in `.env`) |
| `SEARCH_PROVIDER` | `openai` (set in `.env`) |
| `ENABLE_SERPAPI` | Not set in `.env` — defaults to `false` |
| `USE_CURATED_LINKS` | `true` (set in `.env`) |
| `USE_FAST_ROUTER` | Not set — defaults to `false` |
| `USE_SPECULATIVE_SEARCH` | Not set — defaults to `false` |
| `USE_MOCK_AFFILIATE` | Not set in `.env` — defaults to `True` |
| `AMAZON_API_ENABLED` | `false` (default) |
| `CJ_API_ENABLED` | `false` (default in docker-compose) |
| `SECRET_KEY` | Set (value redacted) |
| `OPENAI_API_KEY` | Set (value redacted) |
| `PERPLEXITY_API_KEY` | Set (value redacted — provider not active) |

---

## Model / Provider Config

Sourced from `backend/app/core/config.py` defaults and `backend/.env` overrides:

| Agent | Model | Max Tokens |
|---|---|---|
| `DEFAULT_MODEL` | `gpt-4o-mini` | — |
| `PLANNER_MODEL` | `gpt-4o-mini` (docker-compose default; `.env.example` shows `o3-mini`) |`2000` |
| `INTENT_MODEL` | `gpt-4o-mini` | `50` |
| `CLARIFIER_MODEL` | `gpt-4o-mini` | `800` |
| `COMPOSER_MODEL` | `gpt-4o-mini` | `80` |
| `PRODUCT_SEARCH_MODEL` | `gpt-4o-mini` | `500` |
| `FAST_ROUTER_MODEL` | `claude-haiku-4-5-20251001` (not active — USE_FAST_ROUTER=false) | — |

**Search provider:** `openai` (WebSearch via OpenAI API)
**Temperature:** Not explicitly configured — LiteLLM/OpenAI defaults apply
**LiteLLM log level:** `INFO`

---

## Affiliate Tags

| Network | Tag / ID | Status |
|---|---|---|
| Amazon Associate Tag (primary) | `mikejahshan-20` (set in `.env` — NOTE: code fallback uses `revguide-20`) | Active in `.env`; code hardcodes `revguide-20` as fallback |
| Amazon Associate Tag (code fallback) | `revguide-20` (hardcoded in `product_affiliate.py` lines 176, 302; `product_compose.py` line 1069) | Active as fallback |
| eBay Campaign ID | Not set (`EBAY_CAMPAIGN_ID=` placeholder in `.env.example`) | Blocked — pending real campaign ID from eBay Partner Network |
| eBay MKRID (US rotation ID) | `711-53200-19255-0` | Default |
| eBay MKCID | `1` (EPN channel) | Default |
| CJ (Commission Junction) | Not configured (keys empty) | Disabled |
| Skimlinks / Impact.com | Not configured | Disabled |

**Note:** `.env` still references old `mikejahshan-20` tag — memory file records migration to `revguide-20` happened on 2026-03-25, but `.env` was not updated. Both tags may appear in production traffic depending on code path taken.

---

## API Base URL

| Service | URL |
|---|---|
| Backend API (local Docker) | `http://localhost:8000` |
| Frontend (local Docker) | `http://localhost:3000` |
| Backend health check | `http://localhost:8000/health` |
| Chat stream endpoint | `http://localhost:8000/v1/chat/stream` |
| Frontend env var `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |

---

## Canonical Test Prompts

Eight prompts covering the primary QAR behaviors under test. To be run against commit SHA `46c3b9984f79329e3580e45771d931efac1ed25d` before any Phase 23 fixes are applied.

| # | Prompt | Expected Tools Invoked | QAR Coverage |
|---|---|---|---|
| 1 | "best laptops for students" | `product_search`, `product_affiliate`, `product_normalize`, `product_ranking`, `product_compose` | QAR-01 (product cards rendered), QAR-04 (accessory suppression — no chargers/cases in results) |
| 2 | "best laptops under $500" | `product_search`, `product_affiliate`, `product_normalize`, `product_ranking`, `product_compose` | QAR-05 (budget enforcement — all returned products ≤ $500) |
| 3 | "best wireless headphones" | `product_search`, `product_affiliate`, `product_normalize`, `product_ranking`, `product_compose` | QAR-01 (product cards appear), QAR-02 (fallback loop completes — no silent suppression after first duplicate via `break` bug) |
| 4 | "compare AirPods Pro vs Sony WH-1000XM5" | `product_search`, `product_evidence`, `product_comparison`, `product_compose` | QAR-03 (citation block uses real URLs), QAR-07 (merchant label matches link domain — Amazon label resolves to amazon.com) |
| 5 | "plan a 3-day trip to Paris" | `travel_itinerary`, `travel_destination_facts`, `travel_search_hotels`, `travel_search_flights`, `travel_compose` | QAR-06 (travel timeout recovery — partial response + recovery prompt instead of infinite "Thinking…") |
| 6 | "best running shoes" | `product_search`, `product_affiliate`, `product_normalize`, `product_ranking`, `product_compose` | QAR-01 (product cards general flow — end-to-end pipeline smoke test) |
| 7 | "hotels in Tokyo for next week" | `travel_search_hotels`, `travel_destination_facts`, `travel_compose` | QAR-06 (travel partial response — if hotels slow, shows partial card set not blank screen) |
| 8 | "best coffee makers under $200" | `product_search`, `product_affiliate`, `product_normalize`, `product_ranking`, `product_compose` | QAR-05 (budget enforcement), QAR-01 (product pipeline end-to-end), QAR-04 (accessory suppression — no paper filters/pods) |

### QAR Key

| ID | Bug Description |
|---|---|
| QAR-01 | Product cards missing or not rendered |
| QAR-02 | Fallback loop has `break` instead of `continue` — suppresses later fallback cards after first duplicate |
| QAR-03 | Citation block uses generated URLs instead of real search result URLs |
| QAR-04 | Accessory/part results (chargers, cases, filters) appear in product listings |
| QAR-05 | Budget constraint not enforced — products over stated budget appear in results |
| QAR-06 | Travel pipeline hangs indefinitely — no timeout/partial response recovery |
| QAR-07 | Merchant label/link mismatch — "Amazon" label links to non-Amazon domain |

### QA Run Template

For each test run against these prompts, record:

```
Prompt:         [exact prompt text]
Session ID:     [session_id from response headers]
Request ID:     [request_id from response headers]
Tools Invoked:  [comma-separated list from SSE events]
Time to First Token: [ms from request to first SSE chunk]
Time to Done:   [ms from request to done event]
Product Cards:  [count of cards rendered]
Pass/Fail:      [per QAR criteria above]
Notes:          [any anomalies observed]
```

---

## Files to Watch (Phase 23 Fix Targets)

| File | Bug | QAR |
|---|---|---|
| `backend/mcp_server/tools/product_compose.py` | `break` → `continue` in fallback loop; multi-provider gating too strict | QAR-02 |
| `backend/mcp_server/tools/product_search.py` | Missing accessory/part suppression denylist | QAR-04 |
| `backend/mcp_server/tools/product_affiliate.py` | Merchant label/domain parity not enforced | QAR-07 |
| Travel pipeline tools | No per-tool timing or partial response on timeout | QAR-06 |
| `frontend/components/Message.tsx` | Chat bubble 167px wide on mobile (should be full-width) | P0 |
| `frontend/components/ChatInput.tsx` | Input hidden behind nav bar (38px overlap, z-index conflict) | P0 |
| `frontend/app/not-found.tsx` | No custom 404 page | P1 |
| `frontend/components/ChatContainer.tsx` | `overflow-hidden` blocks iOS scroll; sentinel auto-scroll needed | iOS |
