# ReviewGuide.ai — Deep Dive Audit, Codebase Analysis & Strategic Roadmap

## For: Claude Opus 4.7 (or latest frontier model)
## Date: 2026-04-16
## Estimated Duration: 2-3 hours (automated)
## Branch: `v2-with-swipe` (deployed to production as `main`)

---

## Mission Brief

You are a principal engineer hired to perform a complete audit of **ReviewGuide.ai** — a live AI-powered shopping and travel assistant. This is not a surface-level QA pass. You will:

1. **Map the entire codebase** — architecture, dependencies, conventions, integration points, technical debt
2. **Test every user-facing surface** in the browser — on desktop and mobile, during streaming and after, in light and dark mode
3. **Analyze the backend pipeline** — LLM orchestration, affiliate provider chain, data flow, failure modes
4. **Produce a strategic roadmap** — what to fix, what to build, what to rearchitect, in what order, with effort estimates

Your output will be used by the founding team to prioritize the next 3 months of engineering work. Be thorough. Be honest. Think like someone who's going to own this codebase.

---

## What You're Looking At

ReviewGuide.ai is a full-stack AI product:

| Layer | Stack | Purpose |
|-------|-------|---------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS | User interface — chat, browse, results pages |
| Backend | FastAPI, Python, LangGraph state machine | AI orchestration — safety → intent → clarifier → executor pipeline |
| MCP Server | 17 tools via Model Context Protocol | Product search, travel search, compose, affiliate linking |
| Database | PostgreSQL 15, SQLAlchemy async | Sessions, conversations, user data |
| Cache | Redis 7 | Sessions, search results, halt state for multi-turn |
| AI | GPT-4o-mini (all agents), Serper.dev (web search) | LLM calls + live review search |
| Affiliates | Amazon, eBay, Serper Shopping, Skimlinks, CJ, Impact, Booking, Expedia, Viator | Revenue — commission on purchases |
| Deploy | Railway (backend) + Vercel (frontend) | Production hosting |
| Observability | Langfuse + OpenTelemetry | Tracing and monitoring |

**The current production build is v2.0** ("Editorial Luxury" redesign) with cherry-picked improvements from a later v3.0 branch. The stakeholder explicitly chose v2.0's warmer, cleaner aesthetic over v3.0's bolder, more aggressive visual direction. Your job includes giving your professional opinion on this decision.

---

## Part 1: Codebase Deep Dive (use GSD map-codebase)

Run `/gsd:map-codebase` to produce fresh analysis documents. This dispatches 4 parallel mapper agents that explore the repo and write structured documents to `.planning/codebase/`.

**If `/gsd:map-codebase` is available as a skill, invoke it.** If not, manually spawn 4 `gsd-codebase-mapper` agents in parallel with these focus areas:

### Agent 1 — Technology & Stack Analysis
**Focus:** `tech`
**Output:** `.planning/codebase/STACK.md`

Analyze:
- All dependencies (package.json, requirements.txt, Dockerfile) — versions, purpose, risks
- Framework configuration (next.config.js, tsconfig, tailwind.config, vitest.config)
- Build pipeline and deployment config (Vercel settings, Railway Dockerfile, docker-compose)
- Environment variable inventory — what's required, what's optional, what's undocumented
- Third-party API dependencies — which are critical path, which are optional, failure modes
- Security posture — API key handling, CORS config, rate limiting, auth model

### Agent 2 — Architecture & Data Flow
**Focus:** `arch`
**Output:** `.planning/codebase/ARCHITECTURE.md`

Analyze:
- Frontend component tree — which components own state, which are presentational
- Backend LangGraph state machine — node graph, edge conditions, state schema (GraphState TypedDict)
- MCP tool inventory — all 17 tools, their inputs/outputs, dependencies between them
- SSE streaming pipeline — from `graph.astream_events()` through SSE to frontend reducer
- Data flow for a product query: user input → safety → intent → clarifier → planner → executor → compose → stream → render
- Data flow for a travel query: same but with hotel/flight/activity tool fan-out
- Redis usage — session state, halt state, search cache, affiliate cache
- Database schema — tables, relationships, migration state

### Agent 3 — Code Quality & Conventions
**Focus:** `quality`
**Output:** `.planning/codebase/CONVENTIONS.md`

Analyze:
- TypeScript strictness and type coverage — any `any` abuse?
- Component patterns — are they consistent? (CSS vars vs Tailwind classes, server vs client components)
- Error handling patterns — try/catch consistency, error boundaries, fallback UI
- Test coverage — what's tested, what's not, test quality assessment
- Code duplication — any copy-paste patterns across components?
- Naming conventions — files, functions, variables, CSS classes
- Dead code — unused imports, unreachable branches, commented-out blocks
- Accessibility — ARIA attributes, keyboard navigation, screen reader support
- Performance patterns — unnecessary re-renders, missing memoization, bundle size concerns

### Agent 4 — Technical Debt & Concerns
**Focus:** `concerns`
**Output:** `.planning/codebase/CONCERNS.md`

Analyze:
- Known bugs (check git log for "fix:" commits — what keeps breaking?)
- Fragile code — what would break if you changed one thing? (tight coupling, implicit dependencies)
- Scalability concerns — what happens at 10x traffic? 100x?
- Missing infrastructure — no CI/CD pipeline? No automated tests in deploy gate? No error monitoring?
- Security vulnerabilities — exposed API keys, XSS vectors, SQL injection risks
- Dependency risks — outdated packages, deprecated APIs, vendor lock-in
- Configuration drift — differences between local dev, docker-compose, and production env vars
- The "overflow-hidden vs overflow-clip" saga — trace the full history of scroll bugs and assess whether the current fix is durable

---

## Part 2: Live Browser Audit (use Chrome MCP tools)

### Your Chrome MCP Toolbox

You have 19 browser automation tools. Use ALL of them.

**Tab & Navigation:**
- `tabs_context_mcp` — get tab IDs (call FIRST)
- `tabs_create_mcp` — create new tabs
- `navigate` — go to URLs, back/forward
- `resize_window` — set viewport size for responsive testing

**Visual Inspection:**
- `computer` action:`screenshot` — full-viewport capture
- `computer` action:`zoom` — pixel-level region inspection `[x0, y0, x1, y1]`
- `computer` action:`scroll` — scroll in any direction at coordinates
- `computer` action:`hover` — check hover states, tooltips, dropdowns

**Interaction:**
- `computer` action:`left_click` — click elements
- `computer` action:`type` — type into inputs
- `computer` action:`key` — press keys (Enter, Tab, Escape)
- `computer` action:`left_click_drag` — drag gestures (swipe simulation)
- `find` — find elements by description ("search bar", "add to cart")
- `form_input` — set form values by ref ID
- `read_page` — accessibility tree with ref IDs (filter: "interactive" or "all")

**Data & Debugging:**
- `javascript_tool` — execute JS in page context (DOM measurements, computed styles, state inspection)
- `read_console_messages` — browser console (ALWAYS use `pattern` filter)
- `read_network_requests` — HTTP monitoring (use `urlPattern` for filtering)
- `get_page_text` — extract all page text

**Recording:**
- `gif_creator` — record interactions as animated GIF (start → actions → stop → export)

### Test Execution Plan

#### Setup
1. `tabs_context_mcp` → get state
2. Create 3 tabs: desktop (1440×900), tablet (768×1024), mobile (390×844)
3. Navigate all to `https://www.reviewguide.ai`
4. `read_console_messages` pattern: `error|Error|ERR` on all 3 — baseline errors

#### Surface 1: Homepage (all 3 viewports)
- Screenshot each viewport
- Verify mosaic hero images load: `javascript_tool` → `[...document.querySelectorAll('img[src*="mosaic"]')].map(i => ({src: i.src.split('/').pop(), loaded: i.naturalWidth > 0}))`
- Verify carousel renders 5 distinct slides (not duplicates)
- Test carousel interaction: arrows, dots, swipe (mobile), auto-rotation
- Verify carousel content: badges, scores, prices (roundups should NOT have prices)
- Verify "Research →" is `<a>` tag with `href`
- Test category chip clicks → navigate to `/chat?q=...`
- Test trending card clicks → same
- Check all images for 404s: `read_network_requests` urlPattern: "images" → filter status 404
- Test navigation: topbar links (desktop), tab bar (mobile)
- `read_console_messages` pattern: `error|warn`

#### Surface 2: Product Chat Query
- Navigate to `/chat`, send: "best wireless earbuds under $100"
- **During streaming:** screenshot, check for thinking indicator, test scroll-up ability
- **After completion:**
  - Screenshot full response (all 3 viewports)
  - **Swipe carousel (CRITICAL — new feature):**
    - `gif_creator` start recording
    - On mobile: `left_click_drag` from right to left across carousel — record swipe
    - On desktop: click arrow buttons
    - `gif_creator` stop, export as `swipe-carousel-test.gif`
    - Verify: counter badge ("1 of N"), dot indicators, snap scroll
    - `javascript_tool`: measure carousel container `scrollWidth` vs `clientWidth` — confirm overflow exists
  - **Product cards:** image present (real or fallback)? rating visible? affiliate link works?
  - **Top Pick block:** image? CTA? affiliate URL has correct tag?
  - **Blog narrative:** citation links clickable? Open in new tab?
  - **Source citations:** colored dots visible? Links work?
  - **Follow-up chips:** visible? Click one → sends message?
- **Scroll behavior:**
  - Scroll to very top — first message fully visible above header?
  - `javascript_tool`: `const ml = document.querySelector('.overflow-y-auto'); ({scrollH: ml.scrollHeight, clientH: ml.clientHeight, canScroll: ml.scrollHeight > ml.clientHeight})`
- **Affiliate link audit:**
  - `read_page` filter: "interactive" → find all `<a>` with `href` containing "amazon" or "ebay"
  - Verify affiliate tags present (`revguide-20` for Amazon)
  - Check label-domain parity

#### Surface 3: Travel Chat Query
- Send: "Top all-inclusive resorts in the Caribbean"
- After completion:
  - Hotel/flight widget cards: hero images? "Search on Expedia" CTA? "Caribbean" text wrapping?
  - Resort cards: card-based layout (not bullet list)? Images?
  - Typography: sans-serif headers? Consistent spacing?
  - Conclusion block: tinted background?
  - Mobile: hotel/flight stacked vertically?

#### Surface 4: Follow-up & Multi-turn
- After product response, type: "how do the top 3 compare?"
- Does it return a comparison table?
- Is conversation context maintained?

#### Surface 5: Browse Pages
- Navigate to `/browse/headphones` — hero image? Editor's Picks? Affiliate links?
- Navigate to `/browse/electronics` — different category, same quality?
- Navigate to `/nonexistent` — styled 404 page?
- Navigate to `/browse` — redirects to `/` (documented intentional redirect)?

#### Surface 6: Edge Cases
- `/chat?new=1` — welcome screen with suggestions?
- Send message during streaming — queued or dropped?
- Dark mode toggle — all surfaces render correctly?
- Landscape orientation (mobile) — bottom nav visible?
- `/saved` and `/compare` — placeholder pages render?

#### Surface 7: Performance & Accessibility
- `javascript_tool`: `performance.getEntriesByType('navigation')[0].loadEventEnd` — page load time
- `javascript_tool`: check for images without alt text
- `read_page` depth: 3 — scan for missing ARIA labels on interactive elements
- `read_network_requests` — count total requests, total bytes, any slow requests (>3s)
- `read_console_messages` pattern: `deprecat|warn` — framework warnings

#### Surface 8: Dark Mode Comprehensive
- Toggle dark mode
- Screenshot: homepage, chat (with response), browse category, 404 page
- `javascript_tool`: check for any element with computed `color` close to computed `backgroundColor` (invisible text)
- Check all CSS variable overrides: `getComputedStyle(document.documentElement).getPropertyValue('--text')` in both modes

---

## Part 3: Strategic Analysis

After completing Parts 1 and 2, synthesize everything into strategic recommendations.

### Questions to Answer

1. **Architecture:** Is the LangGraph pipeline the right abstraction? Does the MCP server add value or complexity? Should any tools be consolidated?

2. **Frontend:** Is the component architecture sustainable at 2x the current page count? What needs refactoring before adding more features?

3. **Backend:** Where are the bottlenecks? What fails silently? What would break at scale?

4. **Affiliate Revenue:** Which providers are actually returning data vs. returning empty? Where is money being left on the table?

5. **UX Quality:** How does this compare to Perplexity, Google Shopping, Wirecutter, Airbnb? Where is it competitive? Where is it embarrassing?

6. **v2.0 vs v3.0:** The stakeholder chose v2.0's cleaner look over v3.0's bolder visual language. Having seen both codebases (v3.0 is on `v3-backup` branch), what's your professional assessment? Would you recommend a v2.5 that cherry-picks the best visual improvements from v3.0 without the parts that felt overdone?

7. **Swipe Carousel:** The new product review swipe carousel — does it feel native? Is the implementation robust? What would you change?

8. **What's Missing:** What features would a user expect from a product like this that don't exist yet? What would make this a daily-use tool vs. a novelty?

---

## Deliverable Format

Produce a single comprehensive document:

```markdown
# ReviewGuide.ai — Principal Engineer Audit Report
**Date:** [date]
**Auditor:** Claude Opus 4.7
**Branch:** v2-with-swipe (deployed as main)
**Duration:** [time spent]

---

## Executive Summary
[500 words. What is this product, what's its current state, what are the 3 biggest
opportunities and 3 biggest risks. Written for a CEO/CTO audience.]

---

## Part A: Codebase Health

### Stack Assessment
[From STACK.md analysis — dependency health, config quality, security posture]

### Architecture Assessment
[From ARCHITECTURE.md — data flow quality, coupling analysis, scalability]
[Include a mermaid or ASCII diagram of the actual data flow you traced]

### Code Quality Score
[Rate 1-10 on: type safety, test coverage, error handling, consistency, accessibility]
| Dimension | Score | Evidence |
|-----------|-------|----------|
| Type Safety | X/10 | [specific findings] |
| Test Coverage | X/10 | [what's covered, what's not] |
| Error Handling | X/10 | [patterns found] |
| Consistency | X/10 | [conventions followed/violated] |
| Accessibility | X/10 | [WCAG compliance] |
| Performance | X/10 | [load times, bundle size, render perf] |

### Technical Debt Inventory
[From CONCERNS.md — prioritized list of debt items with effort estimates]
| # | Debt Item | Severity | Effort | Impact if Ignored |
|---|-----------|----------|--------|-------------------|

---

## Part B: Live Site Audit

### Critical Issues (P0)
[Table: issue, page, viewport, evidence (screenshot ID), root cause hypothesis]

### Major Issues (P1)
[Same format]

### Minor Issues (P2)
[Same format]

### Polish Items (P3)
[Same format]

### What Works Well
[Bullet list — things that should NOT be changed. Acknowledge good work.]

---

## Part C: Feature-Specific Deep Dives

### Swipe Carousel Assessment
[Detailed UX review: feel, performance, edge cases, comparison to best-in-class
(Airbnb photo carousel, Amazon product image swipe, Tinder card swipe).
What works, what's jank, what to change. Include GIF evidence.]

### Affiliate Link Health
[Which providers are actually returning data? Which affiliate tags are present?
Revenue leakage points. Specific broken links found.]

### Travel Response Quality
[Before/after assessment. What improved with the Phase 24 overhaul?
What still needs work? Comparison to Google Travel, Kayak, TripAdvisor.]

### Streaming & Real-time UX
[How does the streaming experience feel? Status updates? Loading states?
Error recovery? Comparison to ChatGPT, Perplexity, Google AI Overview.]

---

## Part D: v2.0 vs v3.0 Assessment

[You have access to both codebases. v2.0 is live (main branch), v3.0 is on v3-backup.

Give your honest professional opinion:
- What does v2.0 do better? (warmth, readability, trust, simplicity)
- What does v3.0 do better? (visual impact, modern feel, brand differentiation)
- If you were designing v2.5, which specific elements would you pull from v3.0?
- Which v3.0 elements were the stakeholder right to reject?

Be specific — reference actual components, colors, typography choices, animations.]

---

## Part E: Strategic Roadmap

### Immediate (Week 1-2): Stabilize
[Critical fixes that must land before any feature work]

### Short-term (Week 3-6): Strengthen
[Feature improvements, UX polish, revenue optimization]

### Medium-term (Month 2-3): Expand
[New capabilities, new verticals, architectural improvements]

### Long-term (Quarter 2+): Scale
[What needs to change for 10x growth? Infrastructure, team, product strategy]

### Effort Estimates
| Initiative | Effort | Impact | Priority |
|-----------|--------|--------|----------|
| [name] | [S/M/L/XL] | [1-10] | [P0-P3] |

---

## Appendix

### A: All Screenshots Taken
[Table: screenshot ID, page, viewport, description]

### B: Console Errors Found
[Full list with file/line if available]

### C: Network Issues Detected
[404s, slow requests, failed API calls]

### D: Accessibility Violations
[Missing alt text, ARIA issues, contrast failures]

### E: GIF Recordings
[List of recorded GIFs with descriptions]
```

---

## Execution Rules

1. **Do NOT summarize what you would do. Actually do it.** Open the browser, take screenshots, measure pixels, click buttons, read console errors.

2. **Use `javascript_tool` for every measurement.** Don't guess element sizes from screenshots — measure `getBoundingClientRect()`, `getComputedStyle()`, `scrollHeight vs clientHeight`.

3. **Record GIFs** of the swipe carousel on mobile and desktop. Record any bug you find in action.

4. **Read the codebase.** Don't just test the UI — trace bugs to their source files with line numbers. When you find a visual issue, grep for the responsible component and explain exactly what CSS/JS causes it.

5. **Compare to competitors.** For every major surface, note how Perplexity, Google Shopping, Wirecutter, or Airbnb handles the same UX pattern. Specific comparisons, not vague "should be more like Airbnb."

6. **Quantify everything.** Page load time in ms. Image sizes in KB. Bundle size. Number of API calls per query. Time to first token. Time to complete response. Don't say "slow" — say "2.3 seconds to first visible product card, vs Perplexity's 0.8 seconds."

7. **Think in systems.** Don't just list bugs — identify patterns. If 3 components have the same type of issue, that's a convention problem, not 3 separate bugs.

8. **Be opinionated.** You're a principal engineer, not a QA intern. When something is wrong, say what the right approach is and why. When the architecture has a problem, propose the fix with tradeoffs.

9. **Respect what works.** The team shipped a working AI product with real affiliate revenue. Acknowledge the good decisions and solid engineering before diving into what needs improvement.

10. **This report determines the next quarter of work.** Write it like your reputation depends on it.
