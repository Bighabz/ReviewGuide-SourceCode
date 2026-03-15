# Codebase Concerns

**Analysis Date:** 2026-03-15

---

## Security Considerations

**Unauthenticated conversation endpoints:**
- Risk: Any caller who knows a `session_id` (a UUID) can read or delete any conversation's history with no authentication required.
- Files: `backend/app/api/v1/chat.py` lines 924–986 (`DELETE /conversations/{session_id}`, `GET /history/{session_id}`)
- Current mitigation: None. Both handlers accept `session_id` as a path parameter with no `Depends(get_current_user)` guard.
- Recommendations: Add `current_user` dependency and verify the caller owns the session before returning or deleting data. The `/stream` endpoint already performs this ownership check as a pattern to follow.

**Most admin config endpoints lack per-endpoint auth dependency:**
- Risk: `GET /v1/admin/config`, `POST /v1/admin/config`, `PUT /v1/admin/config/{id}`, `DELETE /v1/admin/config/{id}` have no `Depends(get_current_admin_user)` guard. Only one endpoint at line 511 (`/internal/model-cache/invalidate`) has the dependency.
- Files: `backend/app/api/v1/admin.py` lines 73–167
- Current mitigation: `AdminAuthMiddleware` exists in `backend/app/middleware/admin_auth_middleware.py` but is **not registered** in `backend/app/main.py`. The middleware is dead code.
- Recommendations: Either add `AdminAuthMiddleware` to `app.add_middleware(...)` in `backend/app/main.py`, or add `Depends(get_current_admin_user)` to every admin endpoint that modifies data.

**Raw exception messages exposed to API clients:**
- Risk: Internal database/service error strings leak implementation details (table names, query structure, stack traces) to HTTP responses.
- Files: `backend/app/api/v1/admin.py` lines 86, 105, 118–165, 391, 440, 503; `backend/app/api/v1/chat.py` lines 904, 947, 985
- Pattern: `raise HTTPException(status_code=500, detail=f"Failed to ...: {str(e)}")`
- Recommendations: Return a static user-facing message in `detail` and log `str(e)` server-side only.

**DEBUG mode enabled by default:**
- Risk: `DEBUG: bool = Field(default=True, ...)` means debug mode is active unless explicitly overridden in the deployment environment.
- Files: `backend/app/core/config.py` line 17
- Recommendations: Change default to `False` and require explicit opt-in for development environments.

---

## Tech Debt

**Module-level `langfuse_handler` singleton shared across concurrent requests:**
- Issue: `langfuse_handler = CallbackHandler()` is initialized once at module load time (lines 85–106 of `backend/app/api/v1/chat.py`). All concurrent requests share this single handler instance. Trace data from different requests will be mixed.
- Files: `backend/app/api/v1/chat.py` lines 85, 106, 381, 516, 534, 780
- Impact: Langfuse traces become unreliable for attribution; multi-user concurrent sessions will corrupt each other's trace context.
- Fix approach: Instantiate `CallbackHandler()` inside `generate_chat_stream()` so each request gets an isolated handler.

**`plan_executor_instance` singleton in `AGENT_NAME_TO_INSTANCE` map:**
- Issue: `plan_executor_instance = PlanExecutor()` is created at module level and placed in `AGENT_NAME_TO_INSTANCE` for status message lookup. The executor has mutable per-request state (`self.context`, `self.state`, `self.tool_citations`). The actual execution path correctly creates a new instance per request (`executor = PlanExecutor()` at line 412), but the stale module-level singleton remains in memory, confusing the codebase about which pattern is canonical.
- Files: `backend/app/services/langgraph/workflow.py` lines 36, 45, 412
- Impact: Low risk currently (execution path is isolated), but the dead module-level instance signals the previous bug (cross-session state leak) and will confuse future developers.
- Fix approach: Remove `plan_executor_instance` from `AGENT_NAME_TO_INSTANCE`. Keep only the per-request instantiation pattern.

**`USE_MCP_PLANNER` feature flag does nothing:**
- Issue: `USE_MCP_PLANNER: bool` is defined in `backend/app/core/config.py` but no production code path reads this setting or branches on it.
- Files: `backend/app/core/config.py` line 70
- Impact: Dead config clutters the settings object and misleads developers.
- Fix approach: Either implement the branching logic or remove the flag.

**Deprecated global callback functions in `plan_executor.py`:**
- Issue: `register_tool_citation_callback()`, `clear_tool_citation_callbacks()`, and `get_tool_citation_callbacks()` are marked `DEPRECATED` but remain in production code. The module-level `_tool_citation_callbacks: List` list is separate from the per-instance `self._citation_callbacks` list.
- Files: `backend/app/services/plan_executor.py` lines 74–92
- Impact: Two parallel callback registries can diverge. Code calling the deprecated global functions will not trigger per-instance callbacks and vice versa.
- Fix approach: Audit all call sites that use the global functions and migrate them to the instance methods, then remove the deprecated functions and the module-level list.

**`sys.path.insert` sprayed across production modules:**
- Issue: Fourteen production files (agents, MCP tools, mcp_server/main.py) call `sys.path.insert(0, mcp_server_path)` to make cross-package imports work. This is a packaging workaround.
- Files: `backend/app/agents/clarifier_agent.py`, `backend/app/agents/planner_agent.py`, `backend/app/services/plan_executor.py`, `backend/mcp_server/tools/*.py` (11 files)
- Impact: Fragile in containerized deployments if working directory changes; makes package imports non-deterministic.
- Fix approach: Add `mcp_server` as a proper package (add `__init__.py` if missing, install via `pip install -e .` or update `PYTHONPATH` in `docker-compose.yml`).

**In-process intent cache won't survive multi-worker deployment:**
- Issue: `_intent_cache: Dict[str, Tuple[Dict, float]] = {}` is a process-local dict in `backend/app/agents/intent_agent.py`. Under Gunicorn/Uvicorn with multiple workers, each process has its own cache — cache misses are multiplied.
- Files: `backend/app/agents/intent_agent.py` lines 18–164
- Impact: Cache provides no benefit when scaled horizontally; each worker independently calls the LLM for the same query.
- Fix approach: Migrate to Redis-backed cache using the existing Redis client infrastructure.

**Circuit breaker state is in-process and not shared across workers:**
- Issue: `_circuit_breaker` in `backend/app/services/tiered_router/circuit_breaker.py` is a module-level singleton with in-memory state. The file header notes this explicitly with `TODO: If scaling beyond 3 workers, consider Redis-backed state`.
- Files: `backend/app/services/tiered_router/circuit_breaker.py` line 5
- Impact: API failures on one worker do not propagate the circuit-open state to other workers.
- Fix approach: Back state with a Redis hash as noted in the TODO.

**DB pool size set to 100 total connections by default:**
- Issue: `DB_POOL_SIZE=50` and `DB_MAX_OVERFLOW=50` gives 100 possible connections per worker. A standard PostgreSQL instance allows 100 connections total. With two backend workers, the pool will exhaust the database.
- Files: `backend/app/core/config.py` lines 55–56
- Impact: `too many connections` errors under multi-worker deployment.
- Fix approach: Reduce defaults to `DB_POOL_SIZE=10, DB_MAX_OVERFLOW=5` per worker, or introduce PgBouncer.

---

## Known Issues / Bugs

**`MockRequest` inline class in production chat endpoint:**
- Symptoms: A bare `class MockRequest` is defined inline inside a conditional block within `generate_chat_stream()` to satisfy `is_consent_confirmation()`.
- Files: `backend/app/api/v1/chat.py` lines 239–244
- Trigger: Any request that resumes a halted session with `halt_reason == "consent_required"`.
- Workaround: Functional but fragile; `is_consent_confirmation` should accept `message: str` and `action: Optional[str]` directly instead of duck-typing a request object.

**Debug log statements left in production request path:**
- Symptoms: Eight `logger.info(f"🔍 DEBUG: ...")` lines fire on every single chat request, polluting production logs.
- Files: `backend/app/api/v1/chat.py` lines 522, 523, 586, 606, 612, 718, 719; `backend/app/services/langgraph/workflow.py` lines 337, 401; `backend/app/services/plan_executor.py` lines 187–189
- Impact: Log volume, search noise, minor performance overhead.
- Fix approach: Downgrade to `logger.debug()` or remove.

**`print()` calls in `mcp_client.py`:**
- Symptoms: `print(f"Tool {name} returned empty string")` and `print(f"Tool {name} returned invalid JSON")` write to stdout in the production request path.
- Files: `backend/app/services/mcp_client.py` lines 138, 152
- Impact: Output goes to container stdout outside the structured logging system; invisible in log aggregators.
- Fix approach: Replace with `logger.error(...)` (a call already exists on the next line for both cases — remove the `print` duplicates).

**Empty Amazon affiliate tags in default config silently generate untracked links:**
- Issue: `AMAZON_ASSOCIATE_TAGS` defaults to `"US:,UK:,DE:,FR:,JP:,CA:,AU:"` — all tags are empty strings. `parse_associate_tags()` skips entries where `tag` is empty, so no country-specific tag is found, and the code falls back to `settings.AMAZON_ASSOCIATE_TAG` which also defaults to `""`. Links are generated without any affiliate tag.
- Files: `backend/app/core/config.py` line 269; `backend/app/services/affiliate/providers/amazon_provider.py` lines 224–244
- Impact: Revenue loss — affiliate links with no tag earn nothing.
- Fix approach: Add startup validation to warn (or fail) if `AMAZON_API_ENABLED=True` and associate tags are empty.

---

## Fragile Areas

**`backend/app/api/v1/chat.py` (1089 lines) — monolithic stream handler:**
- Files: `backend/app/api/v1/chat.py`
- Why fragile: `generate_chat_stream()` spans ~800 lines handling halt state detection, session loading, state initialization, SSE event forwarding, post-stream persistence, QoS logging, and Langfuse flushing in a single generator function. Any change to one concern risks side-effecting others.
- Safe modification: Understand the flow via the inline comments referencing RFC sections (§1.1, §4.1, §4.2). Do not reorder `yield` calls — SSE event ordering is load-bearing for the frontend parser.
- Test coverage: `backend/tests/test_chat_api.py` and `backend/tests/test_sse_events.py` exist but do not cover the full execution path.

**`backend/app/services/plan_executor.py` — shared `self.context` dict:**
- Files: `backend/app/services/plan_executor.py`
- Why fragile: Tools write results to `self.context` using keys like `"step_id.key"`. If two parallel tools write to overlapping context keys, one silently overwrites the other. There is no key-collision detection.
- Safe modification: Always pass unique step IDs to tools and verify the tool contract `output_key` is not reused across parallel steps.
- Test coverage: No dedicated test file for `PlanExecutor` directly.

**`backend/app/agents/clarifier_agent.py` (966 lines) — complex multi-turn logic:**
- Files: `backend/app/agents/clarifier_agent.py`
- Why fragile: Halt state detection, slot extraction from LLM responses (regex + JSON parsing), and resume logic are interleaved. The agent reads Redis halt state AND workflow-passed state, which can diverge.
- Safe modification: Do not add new slot types without updating `tool_contracts.py` and re-testing multi-turn flows end-to-end.
- Test coverage: No `test_clarifier_agent.py` exists.

---

## Stub / Unimplemented Features

**Expedia hotel provider is a stub returning empty results:**
- Files: `backend/app/services/travel/providers/expedia_provider.py`
- Status: Entire `search_hotels()` method returns `[]`. All parsing and deeplink methods are commented-out TODOs.
- Impact: Expedia is usable as a provider name in config but contributes zero hotel results.

**Walmart, Best Buy, Target affiliate providers are not implemented:**
- Files: `backend/app/core/config.py` lines 274–288 (config vars with `placeholder — not yet implemented` comment)
- Impact: These providers appear in config but no provider classes exist for them; enabling their flags has no effect.

**`ParallelFetcher._execute_mcp_tool()` raises `NotImplementedError`:**
- Files: `backend/app/services/tiered_router/parallel_fetcher.py` line 180
- Impact: Any tiered-router code path that reaches `_execute_mcp_tool` raises at runtime.
- TODO comment: `# TODO: Wire up to actual MCP tools during workflow integration`

---

## Test Coverage Gaps

**Core agents have no direct unit tests:**
- What's not tested: `ClarifierAgent`, `PlannerAgent`, `SafetyAgent`, `IntentAgent` class logic, slot extraction, PII redaction, jailbreak detection, plan validation.
- Files: `backend/app/agents/clarifier_agent.py`, `backend/app/agents/planner_agent.py`, `backend/app/agents/safety_agent.py`, `backend/app/agents/intent_agent.py`
- Risk: Regressions in multi-turn conversation handling, safety filtering, or plan generation are not caught before deployment.
- Priority: High

**`PlanExecutor` has no direct unit tests:**
- What's not tested: Topological sort, parallel step execution, context key resolution, `args_from` dependency injection, timeout handling.
- Files: `backend/app/services/plan_executor.py`
- Risk: Silent failures in step execution fall through to graceful degradation without indication of the root cause.
- Priority: High

**LangGraph workflow has no integration tests for the full agent chain:**
- What's not tested: End-to-end message → Safety → Intent → Planner → Clarifier → Executor → SSE output path.
- Files: `backend/app/services/langgraph/workflow.py`
- Risk: Changes to agent routing logic or halt/resume flow can break chat silently.
- Priority: High

**Delete conversation and get history endpoints have no tests:**
- What's not tested: `DELETE /v1/chat/conversations/{session_id}`, `GET /v1/chat/history/{session_id}`, including the security gaps noted above.
- Files: `backend/app/api/v1/chat.py` lines 924–986
- Risk: Authorization bypass regression introduced undetected.
- Priority: High (security-adjacent)

---

## Performance Bottlenecks

**`COMPOSER_MAX_TOKENS` default of 80 is extremely low:**
- Problem: `COMPOSER_MAX_TOKENS: int = Field(default=80, ...)` gives composer agents only 80 tokens for output generation. This is likely insufficient for any meaningful composed response, forcing truncation or empty responses.
- Files: `backend/app/core/config.py` line 213
- Cause: Appears to be a misconfigured default — 80 tokens is appropriate for a short label, not a composed article or product summary.
- Improvement path: Audit actual composer output lengths in Langfuse traces; set the default to at least 1000–2000 tokens.

**Conversation history loads up to 100 messages per request to pass to LLM:**
- Problem: `MAX_HISTORY_LIMIT = 100` in `ConversationRepository` retrieves 100 messages, but `MAX_HISTORY_MESSAGES = 30` in config limits what is sent to the LLM. The 100-message DB fetch happens on every request even when only 30 will be used.
- Files: `backend/app/repositories/conversation_repository.py` line 35; `backend/app/core/config.py` line 87
- Cause: Limit mismatch between the repository constant and the config setting.
- Improvement path: Pass `settings.MAX_HISTORY_MESSAGES` as the `limit` argument to `get_history()` at the call site to avoid over-fetching.

---

*Concerns audit: 2026-03-15*
