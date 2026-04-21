# ReviewGuide.ai — Stabilization Sprint Plan

**Start:** 2026-04-21 (Monday)
**End:** 2026-05-08 (Friday) — 15 working days / 3 weeks
**Team:** 2 engineers (1 frontend, 1 backend)
**Strategy:** Cherry-pick from `v3-full-implementation` into `v2-with-swipe`
**Source:** `docs/audits/opus-4.7-audit-report-2026-04-16.md` + `.planning/codebase/CONCERNS.md`

---

## Goal

Close the 96-commit gap between v2-with-swipe (production) and v3-full-implementation, plus fix revenue leaks and stand up missing infrastructure — **without losing v2's visual direction** (warm ivory/charcoal palette, Instrument Serif accents, spare homepage).

## Success Criteria

By end of sprint:

- [ ] Every product query returns working `ui_blocks` with affiliate links containing `tag=revguide-20` (verified via regression test)
- [ ] Desktop at 1440×900 shows the chat welcome screen + input without footer overlap
- [ ] `.github/workflows/ci.yml` blocks merge on test/lint/build failure
- [ ] Sentry captures one test exception from frontend AND backend in the dashboard
- [ ] Custom 404 page renders on `/browse/headphones` (invalid slug) with editorial styling
- [ ] Travel queries ("Plan a 5-day trip to Tokyo") complete within 30s OR show a retry UI
- [ ] "Best espresso machines under $500" returns zero products over $500
- [ ] "Best laptops for students" returns zero replacement parts or logic boards
- [ ] `DELETE /conversations/{id}` returns 401 without auth; 403 for non-owner
- [ ] DB pool reduced to safe per-worker values; 2-worker test deploy doesn't exhaust Postgres
- [ ] All 19 Phase 23 QAR-01 → QAR-19 bugs from the original test document are regression-tested

## Non-Goals

Out of scope for this sprint (tracked in backlog for next cycle):

- `next/image` migration (cosmetic, not blocking)
- Refactor of `product_compose.py` (1,400 LOC) into smaller units (XL effort, defer)
- Saved & Compare feature implementations (XL each, post-stabilization)
- Profile page build-out (just hide the broken link for now)
- Next.js 15 migration
- A/B testing infrastructure
- Multi-region deployment

---

## Team Split

| Lane | Owner | Focus |
|---|---|---|
| **FE** | Frontend engineer | Cherry-picks that touch `frontend/`, CI frontend job, Sentry frontend, kishan cleanup, Profile nav, ChatContainer test, dark-mode logo polish |
| **BE** | Backend engineer | Cherry-picks that touch `backend/`, Amazon tag fix, compose bugs, CI backend job, Sentry backend, CSRF, admin auth, DB pool, langfuse singleton, tiered router activation |
| **Both** | Pair | CI setup (day 6), final regression pass (day 15) |

Daily 15-min standup. Friday 30-min retro. No mid-sprint scope additions.

## Sprint-Level Risks

| Risk | Mitigation |
|---|---|
| Cherry-pick conflicts cascade (one PR breaks the next) | Land each commit in its own PR; rebase next PR on main after each merge; don't stack more than 2 PRs in review at once |
| Fixing compose breaks travel (shared code paths) | Full regression sweep before each compose-related deploy. Add travel smoke test to CI |
| CI gate blocks already-in-flight PRs | Stand CI up on day 6, warn team day 5. Existing PRs squash-merged before day 6 |
| Railway auto-deploy lands a half-fixed state | Use feature branch → staging env → prod promotion pattern for days 1-5 while compose is unstable |
| Sentry quota blown by noisy errors | Set `tracesSampleRate: 0.1`, add `beforeSend` filter for known-benign errors |

---

# Week 1: Stop the Bleeding (Days 1-5)

**Theme:** Restore revenue and fix the desktop experience.

## Day 1 (Mon 2026-04-21) — Amazon tag + compose tokens

### BE-1.1: Verify + fix Amazon affiliate tag [XS, P0]
- **Task:** Check Railway env for `AMAZON_ASSOCIATE_TAG` and `AMAZON_ASSOCIATE_TAGS`. If empty or placeholder (`"US:,UK:,DE:,FR:,JP:,CA:,AU:"`), populate with real tags. Per MEMORY.md the migration was supposed to land `revguide-20` — verify it actually did.
- **Files:** Railway env vars only (no code).
- **Acceptance:**
  - `curl -sS https://backend-production-0ae7.up.railway.app/health` → 200
  - A product query's first Amazon link in the response contains `tag=revguide-20`
- **Rollback:** Revert env var; no code change.

### BE-1.2: Add Amazon-tag startup validator [XS, P0]
- **Task:** In `backend/app/services/affiliate/providers/amazon_provider.py`, add a module-level assertion that raises `RuntimeError` at import time if `AMAZON_API_ENABLED=True` and `settings.AMAZON_ASSOCIATE_TAG == ""` AND `parse_associate_tags()` returns `{}`.
- **Acceptance:** Unit test in `backend/tests/test_amazon_provider.py` that patches env to empty and confirms import raises.
- **Rollback:** Remove the assert block.

### BE-1.3: Bump `COMPOSER_MAX_TOKENS` [XS, P0]
- **Task:** `backend/app/core/config.py:284` — change default from 80 to **1500**. Also update Railway env override if one exists.
- **Rationale:** 80 tokens ≈ 60 words. Composer emits structured JSON with product cards, comparison tables, follow-up suggestions — 80 tokens truncates mid-JSON, Pydantic parse throws, compose catch-all returns the fallback string. This one change may fix P0-4 entirely.
- **Acceptance:** After deploy, run `"best wireless earbuds under $100"` in prod. Response must include ≥3 product cards, not the fallback string.
- **Rollback:** Revert config value.

### BE-1.4: Add compose error SSE event [S, P0]
- **Task:** In `backend/mcp_server/tools/product_compose.py:1418-1429`, inside the `except Exception as e:` block, add structured logging of each step that completed (so we can tell WHERE it threw) AND include the exception class name + stack hash in the returned dict. Frontend reads `error` field and shows a retry UI.
- **Files:** `backend/mcp_server/tools/product_compose.py`, `frontend/components/Message.tsx` (or wherever the assistant message renders)
- **Acceptance:** If compose fails, user sees "Something went wrong composing the response. [Retry]" button instead of the silent fallback string.
- **Rollback:** Revert the error-event code; fallback to the string still works.

### Deploy gate (end of day):
- Staging deploy first. Run canonical product query + travel query. Verify Amazon tag present AND no compose error. THEN promote to prod.

### FE-1.1: Delete `kishan_frontend/` [XS, P2]
- **Task:** `git rm -r kishan_frontend/` + commit + PR.
- **Why today:** quick win, unblocks search/lint tooling that currently scans both trees.
- **Rollback:** `git revert`. Recoverable from history.

### FE-1.2: Fix Profile nav link [XS, P1]
- **Task:** In the navigation config (find via grep for `href: '/browse'` alongside label `Profile`), either change href to `/profile` AND add a placeholder `frontend/app/profile/page.tsx` that says "Profile coming soon", OR hide the link entirely on desktop + mobile tab bar.
- **Decision:** Hide for now (less scope). Defer profile feature to backlog.
- **Acceptance:** `read_page` accessibility tree for desktop topbar and mobile tab bar does NOT include "Profile" link.
- **Rollback:** Restore link visibility.

## Day 2 (Tue 2026-04-22) — Desktop scroll chain cherry-pick

### FE-2.1: Cherry-pick v3 commits `74b1b3d` + `f6735ab` [M, P0]
- **Task:** Cherry-pick both commits together — they're the `h-dvh` double-viewport fix + the `min-h-0` flex chain fix for all flex-1 children in the chat scroll chain. This pair fixes the desktop layout overflow.
- **Commits:**
  - `74b1b3d` — h-dvh double-viewport + min-h-0 fix
  - `f6735ab` — add min-h-0 to all flex-1 children in chat scroll chain
- **Files touched:** `frontend/components/NavLayout.tsx`, `frontend/components/ChatContainer.tsx`, `frontend/components/MessageList.tsx`, `frontend/app/chat/page.tsx`, probably `frontend/app/template.tsx`
- **Conflict risk:** Medium — v2-with-swipe has swipe carousel work that may touch some of these files. Resolve conflicts preserving both changes (swipe + min-h-0).
- **Acceptance (manual):**
  - `/` at 1440×900: trending cards fully visible above footer, no overlap
  - `/chat?new=1` at 1440×900: welcome screen visible, chat input clickable, input at y<viewport-height
  - `/chat?new=1` at 1024×768: same
  - `/browse/electronics` at 1440×900: hero + ask input visible without footer overlap
- **Acceptance (automated):** Playwright test `tests/e2e/desktop-layout.spec.ts` that asserts `document.querySelector('textarea').getBoundingClientRect().bottom < window.innerHeight` on `/chat?new=1` at 1440×900
- **Rollback:** `git revert` both commits in one revert-commit. 5 minutes.

### BE-2.1: Land compose structured logging from day 1 [S, P0]
- **Finish BE-1.4.** Push to staging. Watch Railway logs during test product query. Identify which compose step is throwing. **Document root cause in this plan doc.**
- **Output:** One-line addendum to this plan identifying the actual root cause, e.g. "compose fails at line X because Y".

## Day 3 (Wed 2026-04-23) — Custom 404 + WCAG pass

### FE-3.1: Cherry-pick v3 commit `cef2f33` [M, P1]
- **Task:** Mobile bubble width + nav overlap + overflow-x + **custom 404**. Biggest win: `frontend/app/not-found.tsx` lands as part of this commit.
- **Conflict risk:** Medium — `Message.tsx`, `ChatContainer.tsx`, `chat/page.tsx`, `globals.css` may conflict with v2 swipe work. Keep both.
- **Acceptance:**
  - `/browse/nonexistent-slug` shows editorial-styled 404 with "Back to home" CTA, not the default Next.js 404
  - Mobile chat bubbles respect viewport width (no horizontal scroll)
  - No horizontal scroll on any page at 390×844
- **Rollback:** Revert; previous unstyled 404 returns.

### FE-3.2: Cherry-pick v3 commit `3e5f0a3` [M, P1]
- **Task:** WCAG contrast + landscape nav + queued message + browse redirect.
- **Why bundled:** these are smaller polish items bundled in one v3 commit.
- **Acceptance:**
  - Sending a message while the prior response is streaming is queued, not dropped
  - Landscape orientation on mobile: bottom tab bar remains visible
  - Text contrast on category chips in light mode passes WCAG AA (4.5:1)
  - `/browse` redirect behavior matches documented intent
- **Rollback:** Revert.

### BE-3.1: Move `langfuse_handler` out of module scope [S, P1]
- **Task:** Instantiate `CallbackHandler()` inside `generate_chat_stream()` in `backend/app/api/v1/chat.py:85-106`. Each request gets its own handler. Trace context no longer bleeds between users.
- **Acceptance:** Unit test that spawns 10 concurrent `generate_chat_stream` calls and asserts each gets a distinct `CallbackHandler` instance (via id()).
- **Rollback:** Revert.

## Day 4 (Thu 2026-04-24) — Compose cascade fixes

### BE-4.1: Cherry-pick v3 commit `f66a32a` [M, P0]
- **Task:** Accessory suppression + budget enforcement. Adds `_parse_budget()` and `_extract_price()` helpers in `product_compose.py`. Adds anti-accessory LLM instruction + post-filter suppression.
- **Acceptance:**
  - "Best espresso machines under $500" → zero products over $500 (regression test)
  - "Best laptops for students" → zero items with names containing "logic board", "replacement", "cable", "charger", "case", "sleeve"
  - "Best air purifier" → zero items containing "filter", "replacement HEPA", "pre-filter"
- **Rollback:** Revert. The bugs return but composer still works.

### BE-4.2: Cherry-pick v3 commit `1a9ec4c` [M, P0]
- **Task:** 4 product card bugs — fallback continue, single-provider cards, label-domain parity, citation URL validation.
- **Acceptance:**
  - If PA-API returns empty, curated-links fallback still produces cards (not an empty array)
  - Label on buy button ("View on Amazon") matches the href domain (not "Amazon" → ebay.com)
  - Only valid URLs make it into citations (no malformed)
- **Rollback:** Revert.

### FE-4.1: Re-enable `ChatContainer.test.tsx.skip` [S, P1]
- **Task:** Rename `.skip` → `.tsx`. Run, see what fails, fix. If the fix is bigger than a day, scope a follow-up; for now fix the quick wins and note the rest.
- **Acceptance:** `npm run test` includes ChatContainer test file (not skipped).
- **Rollback:** Rename back to `.skip` if time-boxed fix fails — but document the failure.

## Day 5 (Fri 2026-04-25) — Travel timeout + Week 1 close-out

### BE-5.1: Cherry-pick v3 commit `0bd88eb` [M, P0]
- **Task:** Travel tool instrumentation + recovery path (silent travel hang fix). Adds `tool_timing` module + timeout handlers in `travel_compose.py` and `travel_itinerary.py`.
- **Acceptance:**
  - "Plan a 5-day trip to Tokyo" either completes within 30s OR surfaces a timeout error to the user (not a silent hang)
  - Per-tool execution time logged in Langfuse
- **Rollback:** Revert.

### BE-5.2: Cherry-pick v3 commit `2b1c653` [S, P1]
- **Task:** Sentinel scroll + chat history session tracking + session in URL.
- **Acceptance:**
  - Deep-linking to `/chat?session_id=X` resumes that conversation
  - Scroll-to-bottom uses sentinel ref pattern (no null-check race)
- **Rollback:** Revert.

### Both-5.1: Regression + deploy to prod [S]
- Full manual sweep on staging:
  - 5 product queries across categories
  - 3 travel queries (including Tokyo trip that used to hang)
  - Multi-turn clarifier flow
  - Dark mode toggle
  - 1440×900, 1366×768, 390×844 viewports
- Promote to prod by end of day.
- **End-of-week deliverable:** prod shows real product responses with working affiliate links, desktop layout fixed, custom 404, no travel hangs.

### Week 1 retro (Fri PM, 30 min):
- What shipped?
- What carried over to Week 2?
- Any unexpected conflicts or regressions?

---

# Week 2: Infrastructure + Observability (Days 6-10)

**Theme:** Make it impossible for this to regress silently again.

## Day 6 (Mon 2026-04-28) — CI/CD setup

### Both-6.1: Create `.github/workflows/ci.yml` [M, P0]
- **Task:** Single workflow with two jobs (backend, frontend) running on every PR targeting main:
  ```yaml
  name: CI
  on:
    pull_request:
      branches: [main, v2-with-swipe]
  jobs:
    backend:
      runs-on: ubuntu-latest
      services:
        postgres: {image: postgres:15}
        redis: {image: redis:7}
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: {python-version: '3.11'}
        - run: pip install -r requirements.txt
        - run: cd backend && alembic upgrade head
        - run: cd backend && pytest -x --ignore=tests/integration
        - run: ruff check backend/
        - run: black --check backend/
    frontend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-node@v4
          with: {node-version: '20', cache: 'npm', cache-dependency-path: frontend/package-lock.json}
        - run: cd frontend && npm ci
        - run: cd frontend && npm run lint
        - run: cd frontend && npm run test:run
        - run: cd frontend && npm run build
  ```
- **Task:** Also configure branch protection on main requiring CI to pass.
- **Task:** Add "Ignored Build Step" on Vercel project settings: `if ! npm run test:run; then exit 1; fi` — blocks Vercel deploy on test failure.
- **Acceptance:**
  - Open a throwaway PR that adds `expect(true).toBe(false)` somewhere
  - CI reports failure
  - Merge button is disabled
  - Vercel skips deploy for that commit
- **Rollback:** Delete the workflow file; disable branch protection.

### Both-6.2: Add secret scanning [S, P1]
- **Task:** Add `gitleaks` step to CI (or use GitHub's built-in secret scanning if team has GitHub Advanced Security).
- **Acceptance:** Deliberately committing a fake AWS key triggers CI failure.

## Day 7 (Tue 2026-04-29) — Sentry integration

### FE-7.1: Add `@sentry/nextjs` [M, P0]
- **Task:**
  - `npm install @sentry/nextjs` in `frontend/`
  - `npx @sentry/wizard@latest -i nextjs` to generate config
  - Configure `sentry.client.config.ts` with `tracesSampleRate: 0.1`, `replaysSessionSampleRate: 0`, `replaysOnErrorSampleRate: 0.1`
  - Add `SENTRY_DSN` to Vercel env vars
  - Test: throw a synthetic error, confirm it appears in Sentry dashboard
- **Acceptance:** One test exception visible in Sentry's issues panel, with breadcrumbs and stack trace.
- **Rollback:** Uninstall `@sentry/nextjs`, remove the config files, revert `next.config.js`.

### BE-7.1: Add `sentry-sdk[fastapi]` [M, P0]
- **Task:**
  - `pip install sentry-sdk[fastapi]` (add to requirements.txt)
  - In `backend/app/main.py` lifespan setup:
    ```python
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration(), StarletteIntegration()],
        traces_sample_rate=0.1,
        environment=settings.ENV,
    )
    ```
  - Add `SENTRY_DSN` field to `config.py` (optional, defaults to empty)
  - Add `SENTRY_DSN` to Railway env
  - Test: throw a synthetic exception in a new `/v1/_sentry-test` endpoint, confirm in dashboard
- **Acceptance:** One test exception visible in Sentry backend project with request path/method tags.
- **Rollback:** Remove init call + env var.

### Both-7.1: Route Sentry alerts to Slack [XS, P1]
- **Task:** Sentry project settings → Alerts → New alert → "When error count > 10 in 5 min" → Slack webhook. One alert for each project (FE + BE).

## Day 8 (Wed 2026-04-30) — Security hardening

### BE-8.1: Auth on `DELETE /conversations/{session_id}` + `GET /history/{session_id}` [S, P0]
- **Files:** `backend/app/api/v1/chat.py:924-986`
- **Task:**
  - Add `user: User = Depends(get_current_user)` (or optional variant) to both endpoints
  - Fetch session from DB by `session_id`, verify `session.user_id == user.id` OR session is anonymous and the current request has the matching anonymous cookie
  - Return 401 if unauthenticated AND session is not anonymous
  - Return 403 if session belongs to a different user
- **Acceptance:**
  - `curl -X DELETE .../conversations/{any_uuid}` without auth → 401
  - Same with another user's token → 403
  - Owner's token → 204
- **Test:** Add `test_delete_conversation_auth` + `test_get_history_auth` to `tests/test_chat_api.py`.
- **Rollback:** Revert the auth check. Document known vulnerability until next sprint.

### BE-8.2: Enable `AdminAuthMiddleware` [S, P0]
- **Task:** `backend/app/middleware/admin_auth_middleware.py` exists as dead code. Either register it in `app/main.py` via `app.add_middleware()` OR add `Depends(get_current_admin_user)` to each endpoint in `backend/app/api/v1/admin.py:73-167`.
- **Decision:** Use `Depends` approach — more explicit, easier to audit, doesn't affect non-admin routes.
- **Acceptance:** `curl -X POST .../v1/admin/config ...` without admin JWT → 401. With valid admin JWT → 200.
- **Rollback:** Remove the Depends. Dead middleware stays dead.

### BE-8.3: Add CSRF protection [M, P1]
- **Task:**
  - `pip install starlette-csrf`
  - Register middleware in `main.py` AFTER CORS middleware
  - Configure to require CSRF token on state-changing methods (`POST`, `PUT`, `PATCH`, `DELETE`)
  - Exempt `/v1/chat/stream` if needed (SSE can't easily carry CSRF header; revisit)
  - Frontend: read token from cookie, attach to fetch as `X-CSRF-Token` header
- **Files:** `backend/app/main.py`, `frontend/lib/chatApi.ts`, possibly `frontend/lib/apiClient.ts`
- **Acceptance:**
  - `POST /v1/admin/config` without CSRF token → 403
  - Frontend normal flow works (token auto-attached)
- **Rollback:** Remove middleware. Document remaining exposure.

## Day 9 (Thu 2026-05-01) — DB pool + compose logging polish

### BE-9.1: Reduce DB pool defaults [XS, P0]
- **Files:** `backend/app/core/config.py:55-56`
- **Task:** Change `DB_POOL_SIZE` default from 50 → 10. Change `DB_MAX_OVERFLOW` default from 50 → 5. Update Railway env if overridden.
- **Acceptance:** Deploy 2 workers (staging). Run a load test (100 concurrent requests). No `"too many connections"` errors in Postgres logs.
- **Rollback:** Revert defaults to 50/50.

### BE-9.2: Replace compose catch-all with granular per-section handling [L, P1]
- **Files:** `backend/mcp_server/tools/product_compose.py`
- **Task:** Refactor the 1,400 LOC compose into sections, each wrapped in its own try/except:
  - `_compose_skeleton()` — card skeletons
  - `_compose_narrative()` — prose text
  - `_compose_comparison()` — comparison table
  - `_compose_citations()` — citation links
  - `_compose_followups()` — suggestion chips
  - `_compose_context_update()` — `last_search_context` + `search_history`
- Each returns a result dict; failure = empty block for that section only, not global failure. Global result is `{**skeleton, **narrative, **comparison, ...}`.
- **Why this size:** this is the "L" effort from the audit backlog, scoped down to be tractable in one day by keeping the existing functions and just wrapping them. Full refactor (splitting into separate files) deferred to post-sprint.
- **Acceptance:**
  - Add a test that forces the comparison section to throw; assert narrative + cards still return
  - All 5 test product queries from Week 1 still return ≥3 product cards
- **Rollback:** Revert to the old single try/except.

### FE-9.1: Dark-mode logo polish [XS, P3]
- **Task:** Replace the white-blue gradient pill in `UnifiedTopbar` with a single-color SVG that respects `--text` / `--surface` CSS vars in both modes.
- **Acceptance:** Logo contrast passes WCAG AA in both light and dark modes.

## Day 10 (Fri 2026-05-02) — Scroll polish + Week 2 close-out

### FE-10.1: Cherry-pick v3 commits `5d0b595`, `022f7eb`, `dbdd910`, `083132b` [M, P1]
- **Task:** Remaining scroll architecture polish — allow scrolling up during streaming, scroll to bottom after sending, throttle auto-scroll to 400ms, touch state tracking.
- **Conflict risk:** Low (MessageList.tsx changes, most likely non-overlapping with swipe work).
- **Acceptance:**
  - During streaming, user can scroll up and content doesn't fight them
  - After sending a message, view scrolls to bottom (new message visible)
  - Rapid streaming doesn't cause scroll thrashing (throttled)
- **Rollback:** Revert each commit independently if any fails.

### Both-10.1: Regression sweep + deploy [S]
- Full manual sweep + all Week 1 regression tests.
- Verify Sentry captures a test error from prod.
- Promote to prod.
- **End-of-week deliverable:** CI blocking deploys on failure, Sentry visible for both FE + BE, CSRF protection on state-changing endpoints, DB pool safe for multi-worker, scroll fully polished.

### Week 2 retro.

---

# Week 3: Reliability + Activation + Close-out (Days 11-15)

**Theme:** Activate dormant infrastructure, finish the long tail, document the sprint.

## Day 11 (Mon 2026-05-05) — Tiered router activation

### BE-11.1: Wire `routing_gate` emission in clarifier [M, P1]
- **Task:** Modify clarifier to emit `next_agent="routing_gate"` for product/travel/comparison/price_check/review_deep_dive intents (instead of always `"plan_executor"`). Keep LLM-planner path as fallback.
- **Files:** `backend/app/agents/clarifier_agent.py` (or wherever clarifier's return dict is constructed), `backend/app/services/langgraph/workflow.py` edge conditions
- **Decision gate:** The routing_gate exists in code and has tests. This should be activated BEHIND a feature flag (`ENABLE_TIERED_ROUTING=false` default) so we can A/B test.
- **Acceptance:**
  - With flag off: existing flow works (regression)
  - With flag on: one product query's Langfuse trace shows `routing_gate_node → tiered_executor_node → product_compose_node` path instead of `plan_executor_node`
  - LLM token count drops for tiered queries (measured via Langfuse)
- **Rollback:** Feature flag off. No code revert needed.

### BE-11.2: Activate tiered router in staging, measure [S]
- **Task:** Enable flag in staging env. Run 20 product queries + 20 travel queries. Compare Langfuse LLM token totals vs same queries on flag-off.
- **Target:** ≥30% reduction in LLM tokens per product query.
- **Output:** One-paragraph memo in this doc.

## Day 12 (Tue 2026-05-06) — Restore deleted providers

### BE-12.1: Restore Skimlinks provider [M, P1]
- **Task:** Per CONCERNS.md, Skimlinks provider was DELETED from v2 (only `.pyc` remains). Restore from v3 branch: `git checkout v3-full-implementation -- backend/app/services/affiliate/providers/skimlinks_provider.py` (path may differ).
- **Why:** Skimlinks is the universal-merchant fallback — catches affiliate revenue on text-mention products without a curated card.
- **Acceptance:**
  - Provider file present, imports cleanly
  - Unit test for Skimlinks link generation passes
  - A product query whose text mentions a non-Amazon, non-eBay merchant gets a Skimlinks-wrapped link
- **Rollback:** `git rm` the file.

### BE-12.2: Restore Serper Shopping provider [M, P1]
- **Task:** Same approach, for the Serper Shopping provider deleted from v2.
- **Acceptance:** Shopping search results populate for product queries; Langfuse shows the provider being invoked.
- **Rollback:** Same.

### FE-12.1: Consolidate carousel components [S, P2]
- **Task:** Remove `ProductCarousel.tsx` (251 LOC button-only). Update `BlockRegistry.tsx` dispatch to use `ProductReviewCarousel.tsx` (137 LOC) for all product-list blocks. Handle the `total <= 1` case in the swipe carousel if it doesn't already.
- **Files:** `frontend/components/ProductCarousel.tsx` (delete), `frontend/components/blocks/BlockRegistry.tsx` (update dispatch)
- **Acceptance:** All product-list rendering goes through `ProductReviewCarousel`. Snapshot tests still pass.
- **Rollback:** Restore `ProductCarousel.tsx` and the BlockRegistry dispatch.

## Day 13 (Wed 2026-05-07) — Dedup + code quality

### FE-13.1: Dedupe `lookupCuratedProduct` + `formatDate` [S, P2]
- **Task:**
  - Extract `lookupCuratedProduct` from `InlineProductCard.tsx:30` and `ResultsProductCard.tsx:13` into `frontend/lib/curatedProducts.ts`. Update both callsites.
  - Extract `formatDate` from `HotelCards.tsx:46`, `FlightCards.tsx:50`, `CarRentalCard.tsx:20` into `frontend/lib/dates.ts`. Update all three callsites.
- **Acceptance:** grep shows only one definition of each function. Snapshot tests unchanged.
- **Rollback:** Inline back. Low-risk change.

### FE-13.2: Add `React.memo` to streaming hot path [S, P2]
- **Task:** Wrap in `React.memo`:
  - `ProductCard`, `ResultsProductCard`, `InlineProductCard`
  - `HotelCard`, `FlightCard`, `CarRentalCard`
  - `ProductReviewCarousel`
  - Top-level message renderer in `MessageList.tsx`
- **Acceptance:** Profile a streaming response with React DevTools; memoized components show "Did not render" on most SSE events.
- **Rollback:** Remove `memo()` wrappers.

### BE-13.1: Raise `pytest.ini` warning filter [XS, P2]
- **Files:** `backend/pytest.ini:8`
- **Task:** Remove `filterwarnings = ignore::DeprecationWarning`. Let deprecation warnings surface. Fix or downgrade any that are noisy.
- **Acceptance:** `pytest -W error::DeprecationWarning` passes (or list documented exceptions).
- **Rollback:** Re-add the filter.

### BE-13.2: Drop unused deps [XS, P3]
- **Files:** `backend/requirements.txt`
- **Task:** Remove `passlib[bcrypt]==1.7.4` (bypassed for direct bcrypt). Remove `google-search-results==2.4.2` (unused; Serper called via httpx). Confirm nothing imports them (`grep -r "from passlib"`, `grep -r "serpapi"`).
- **Acceptance:** `pip install -r requirements.txt` + `pytest` still passes.
- **Rollback:** Re-add.

## Day 14 (Thu 2026-05-08) — Documentation + final polish

### Both-14.1: Update CLAUDE.md + MEMORY.md [S]
- **Task:** Document:
  - Cherry-picked commits (link to each PR)
  - New env vars (SENTRY_DSN, ENABLE_TIERED_ROUTING)
  - CI workflow invocation
  - Amazon tag validator behavior
  - Compose error event contract (frontend can now show retry UI)
- **Files:** `CLAUDE.md`, the `memory/` directory
- **Output:** PR updating both.

### FE-14.1: Add Playwright smoke test suite [M, P1]
- **Task:** Create `frontend/tests/e2e/smoke.spec.ts` with 5 tests:
  1. Homepage loads, trending cards visible at 1440×900
  2. `/chat?new=1` renders welcome screen + input at 1440×900
  3. Send "best wireless earbuds under $100" → receive response with ≥3 product cards within 15s
  4. Send "plan a 5-day trip to Tokyo" → receive clarifier OR response within 20s (no hang)
  5. `/browse/nonexistent` shows custom 404 (not default Next.js)
- **Task:** Add to CI as `npm run test:e2e` — blocks merge if any fails.
- **Acceptance:** All 5 pass on staging; added to CI.
- **Rollback:** Delete the suite, remove CI step.

### BE-14.1: Post-deploy smoke check script [XS, P1]
- **Files:** new `scripts/post-deploy-smoke.sh`
- **Task:** 5-line bash script that curls `/health`, sends one product query to `/v1/chat/stream` (parses SSE for non-empty `ui_blocks`), sends one travel query. Exits non-zero on failure.
- **Task:** Wire into Railway's deploy hook (if available) or GitHub Action post-deploy.
- **Acceptance:** Running the script against prod returns 0 for healthy state.

## Day 15 (Fri 2026-05-09) — Full regression + sprint close

### Both-15.1: End-to-end regression sweep [L]
- Run the original 19 Phase 23 QAR bugs against prod:
  - QAR-01 through QAR-19 (from `# ReviewGuide.ai — Comprehensive Te.txt`)
  - Each should be verified fixed OR explicitly deferred with a ticket
- Run all 5 Playwright smoke tests
- Manually verify desktop layout at 4 viewport sizes
- Verify Sentry captures a synthetic error from prod
- Check Langfuse for clean per-user trace attribution (singleton fix)
- Confirm DB pool stats under 2-worker load don't exceed safe margins

### Both-15.2: Sprint retrospective (60 min) [S]
- What shipped vs planned
- What didn't and why
- Outstanding backlog items (candidates for next sprint)
- Lessons learned (CI lag time, cherry-pick friction, any surprises)
- Update `CLAUDE.md` with any discovered quirks

### Both-15.3: Hand-off / announcement
- Short Slack / email to stakeholders:
  - "Sprint closed. Desktop fixed, product flow fixed, CI live, Sentry live."
  - Link to this plan doc with check marks
  - Link to the audit report for context
  - Pointer to next sprint's top-three items (from the deferred backlog)

---

## Deferred Backlog (for next sprint)

From the audit's Short-term + Medium-term sections that didn't fit this sprint:

| Item | Effort | Impact | Reason deferred |
|---|---|---|---|
| `next/image` migration | M | 6 | Cosmetic; doesn't block revenue |
| Full `product_compose.py` refactor (split into files) | XL | 7 | Day 9 did minimal wrapper; full split is next-sprint |
| Walmart / Best Buy / Target providers | L | 8 | Out of scope; diversification work |
| Saved & Compare features | XL (each) | 8 | Separate product work |
| Profile page build-out | M | 4 | Hidden for now |
| History & conversation continuation | M | 6 | Foundation work for Saved |
| Image-based search | XL | 7 | Differentiator work |
| Anthropic fallback path tested | M | 8 | Vendor-risk mitigation |
| Next.js 15 migration | L | 5 | Schedule during a slow week |
| Requirements lockfile (`uv pip compile`) | M | 4 | Reproducibility hardening |
| Full observability dashboard | L | 9 | Beyond Sentry MVP |

---

## Sprint-level KPIs to track

Daily in standup, show:

1. **Cherry-picks merged today / total.** Target: 11 cherry-pick PRs total by day 10.
2. **CI pass rate on main.** Target: 100% after day 6.
3. **Sentry error count on staging.** Target: <5/day after day 7 (excluding synthetic tests).
4. **Product-query success rate.** Target: 0% → >95% by day 5.
5. **Amazon link tag-present rate.** Target: 100% by end of day 1.
6. **LLM cost per product query.** Target: baseline day 1, ≥30% reduction by day 11 (tiered router).

---

## Decision log

| Decision | Who | When | Why |
|---|---|---|---|
| Cherry-pick over promote-v3 | Stakeholder | 2026-04-21 | Lower risk; v2 visual choices preserved |
| 3-week sprint, 2 engineers | Planning | 2026-04-21 | Matches the critical-fix backlog depth |
| Hide Profile link vs build Profile page | Planning | 2026-04-21 | Scope control; page build deferred |
| Tiered router behind feature flag | Planning | 2026-04-21 | Safe rollout; A/B-able |
| Compose refactor minimal scope | Planning | 2026-04-21 | Full split is L+ effort; defer to next sprint |

---

*End of sprint plan. Owner: engineering lead. Update daily with status + decision additions.*
