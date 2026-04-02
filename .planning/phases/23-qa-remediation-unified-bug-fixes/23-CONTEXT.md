# Phase 23: QA Remediation — Unified Bug Fixes - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning
**Source:** PRD Express Path (C:\Users\habib\Favorites\Claude_Code_Prompt.md)

<domain>
## Phase Boundary

This phase delivers a unified remediation of 47 bugs found across 25 automated test prompts run by a browser agent in Chrome DevTools with iPhone 14 Pro viewport emulation. The work spans both backend pipeline fixes (product_compose, product_search, travel pipeline, citations) and frontend CSS/UX fixes (chat bubble width, nav overlap, dark mode, scroll, 404 page, WCAG contrast). The phase begins with a reproducible baseline (Phase 0), proceeds through dependency-ordered fixes, and ends with a regression harness gating future deploys.

**Source documents:**
1. Browser QA Report (25 test cases, 47 bugs) — executive report with prioritized findings and root cause analysis
2. Raw agent test results (full prompt-by-prompt output) — DOM measurements, pixel evidence, pass/fail verdicts
3. Code-grounded audit critique — identifies backend pipeline bugs explaining some frontend symptoms, proposes phased remediation

</domain>

<decisions>
## Implementation Decisions

### Phase 0: Reproducible Baseline (must do first)
- Record current commit SHA, backend environment snapshot (redacted secrets), model/provider config, affiliate tag values, API base URL
- Create QA run template capturing: prompt, session_id, request_id, tools invoked, time to first token, time to done
- Run 8 canonical test prompts against frozen baseline and store traces
- This is the "before" snapshot — all fixes measured against it

### Backend Pipeline Fixes (Phase 1-2 from Document 3)
- Fix `break` → `continue` in `product_compose.py` fallback loop (suppresses later fallback cards after first duplicate)
- Relax multi-provider gating (currently requires ≥2 providers, suppresses single-provider products entirely)
- Enforce merchant-label/link consistency (Amazon label must resolve to Amazon domain)
- Add accessory/part suppression in search/normalize pipeline (denylist: "replacement", "filter", "logic board", "case", "charger")
- Add budget enforcement before final compose (parse numeric bounds, filter/penalize out-of-budget offers)

### Travel Reliability (Phase 3 from Document 3)
- Instrument travel path with per-tool timing and timeout flags
- Return partial travel response + recovery prompt instead of indefinite "Thinking"

### Citations & Transparency (Phase 4 from Document 3)
- Citation block must use actual URLs from search results, not generated ones
- Streaming must show meaningful intermediate status updates beyond "Thinking..."

### Frontend P0 Fixes (from Document 1)
- Chat bubble only 167px wide on mobile — needs full-width on small viewports
- Chat input hidden behind nav bar (38px overlap, z-index conflict)

### Frontend P1 Fixes (from Document 1)
- `overflow-x: hidden` on body blocks horizontal pan when zoomed — change to `overflow-x: clip`
- "Stop Claude" button hardcoded to light-mode colors in dark mode
- No custom 404 page (raw Next.js default on all invalid URLs)

### Frontend P2 Fixes (from Document 1)
- Forward navigation loads wrong chat session (no session ID in URL)
- Silent message drop when sending during active streaming
- WCAG contrast failures on 7 elements (specific values in Prompt 10 evidence)
- Landscape orientation hides bottom nav at 844px
- /browse silent redirect to homepage
- Chat history shows 0 conversations (backend session/conversation table sync)

### iOS Scroll Fix (from original audit)
- Change `overflow-hidden` to `overflow-clip` on 4 ancestor containers in chat scroll chain
- Add `-webkit-overflow-scrolling: touch` and `overscroll-behavior-y: contain` to messages scroll container
- Replace `setInterval` + `requestAnimationFrame` auto-scroll with sentinel `<div ref={bottomRef} />` pattern using `scrollIntoView({ block: 'end' })` in a `useEffect`

### Regression Harness (Phase 5 from Document 3)
- Convert 25 test prompts into automated smoke tests (API-level + minimal UI E2E)
- Gate deploys on: affiliate label-domain parity, accessory suppression, budget enforcement, travel non-hang, source link presence
- Manual QA checklist on mobile + desktop after automated gate passes

### Dependency Order
- Backend pipeline fixes MUST land before frontend fixes that depend on correct data
- Independent frontend CSS fixes (chat bubble, nav overlap, overflow-x, dark mode) can proceed in parallel with backend work
- Revenue-impacting fixes come first (eBay campid, Google Shopping leaks, broken images, fallback loop bug)

### Claude's Discretion
- How to structure the QA run template (file format, storage location)
- Specific test framework for regression harness (pytest, vitest, playwright, etc.)
- Implementation details for budget parsing heuristics
- Specific z-index values for nav overlap fix
- Custom 404 page design (within editorial luxury theme)
- How to structure partial travel response UX

</decisions>

<specifics>
## Specific Ideas

### Files to modify (from Document 3)
- `backend/mcp_server/tools/product_compose.py` — fallback loop `break` → `continue`, multi-provider gating
- `backend/mcp_server/tools/product_search.py` — accessory/part suppression denylist
- Travel pipeline tools — per-tool timing instrumentation
- `frontend/components/ChatContainer.tsx` — scroll chain overflow fixes
- `frontend/components/Message.tsx` — chat bubble width
- `frontend/components/ChatInput.tsx` — nav overlap z-index
- `frontend/app/not-found.tsx` — custom 404 page

### Blocked items (need external input)
- eBay campid fix: blocked on Mike providing real eBay Partner Network campaign ID
- v4.0 affiliate integrations (eBay real ID, CJ activation, Expedia): blocked on Mike's input
- Real-device iOS scroll verification: requires physical iPhone testing after CSS fixes deploy

### Exit criteria (from Document 3)
- Phase 1: Product query always returns at least one Amazon path when available; no label/domain mismatches
- Phase 2: "best laptops for students" excludes parts/accessories; "under $500" respects budget
- Phase 3: No travel query remains in undifferentiated loading state beyond threshold
- Phase 4: Product responses include clickable source links; streaming shows meaningful status updates
- Phase 5: All P0/P1 tests green in CI before release candidate

</specifics>

<deferred>
## Deferred Ideas

- eBay campid fix — blocked on Mike providing real campaign ID
- v4.0 affiliate integrations (eBay real ID, CJ activation, Expedia) — blocked on Mike
- Real-device iOS scroll verification — requires physical iPhone after deploy
- Comprehensive automated E2E tests (beyond smoke tests) — future milestone

</deferred>

---

*Phase: 23-qa-remediation-unified-bug-fixes*
*Context gathered: 2026-04-01 via PRD Express Path*
