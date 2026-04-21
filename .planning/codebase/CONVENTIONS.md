# Coding Conventions

**Analysis Date:** 2026-04-16
**Branch:** v2-with-swipe (deployed as production main)
**Scope:** Frontend (113 TS/TSX files, 8,323 LOC in `components/`) + Backend (130 Python files)

## Naming Patterns

**Files:**
- Frontend components: `PascalCase.tsx` — e.g., `ChatContainer.tsx`, `ProductCarousel.tsx`, `ProductReviewCarousel.tsx`
- Frontend hooks: `camelCase.ts` with `use` prefix — `frontend/hooks/useStreamReducer.ts` (only one hook in repo)
- Frontend lib utilities: `camelCase.ts` — `frontend/lib/chatApi.ts`, `extractResultsData.ts`, `trackAffiliate.ts`
- Frontend admin pages: mix of `Dashboard.tsx` + `page.tsx` (Next.js App Router convention)
- Backend modules: `snake_case.py` — `backend/app/services/chat_history_manager.py`, `backend/mcp_server/tools/product_search.py`
- Backend tests: `test_<module>.py` — `backend/tests/test_chat_api.py`, `backend/tests/test_tiered_router/test_orchestrator.py`
- Subdirectory layout: `frontend/components/{blocks,browse,discover,ui}/` — feature subfolders, lowercase

**Style mismatch in admin folder:** `frontend/app/admin/Dashboard.tsx` and `ConfigManagement.tsx` use semicolons and PascalCase filenames despite being inside an `app/` route directory; rest of codebase has no trailing semicolons. This is dead-code from React-Admin scaffold (see Concerns).

**Functions/Methods:**
- TypeScript: `camelCase` — `streamChat`, `formatTimestamp`, `sortSuggestions`, `lookupCuratedProduct`, `trackSuggestionClick`
- Python: `snake_case` — `get_history`, `check_rate_limit`, `log_and_raise_agent_error`, `_execute_safety_checks`
- Python private helpers: single underscore prefix — `_sse_event`, `_load_session_context`, `_run_safety`, `_detect_and_redact_pii`
- Type guards (TypeScript): `isXxx` returning typed boolean — `isPLPLink` in `HotelCards.tsx:40` and `FlightCards.tsx:44`

**Variables:**
- TypeScript: `camelCase` — `sessionId`, `uiBlocks`, `streamState`, `pendingSkeleton`, `currentMessageIdRef`
- Python: `snake_case` — `session_id`, `ui_blocks`, `mock_redis`, `tool_contracts`
- React refs: `<name>Ref` suffix — `colorPickerRef`, `containerRef`, `originalQueryRef`, `currentMessageIdRef`
- Constants (both): `UPPER_SNAKE_CASE` — `MAX_RETRIES`, `INITIAL_BACKOFF_MS`, `SUGGESTION_CLICK_PREFIX`, `CATEGORY_SORT_ORDER`, `CYCLING_VERBS`, `RANK_LABELS`, `PII_PATTERNS`, `FALLBACK_KEYWORDS`, `POSITION_SCORES`

**Types/Classes/Interfaces:**
- TypeScript interfaces: `PascalCase` with descriptive names — `NextSuggestion`, `StreamAction`, `ResponseMetadata`, `ProductCarouselProps`, `HotelCard`, `FlightPLPLink`
- TypeScript type aliases: `PascalCase` — `StreamState`, `SuggestionCategory`, `Hotel = HotelCard | HotelPLPLink`
- Python classes: `PascalCase` — `BaseAgent`, `SafetyAgent`, `ConversationRepository`, `TieredAPIOrchestrator`
- Pydantic models: `PascalCase` ending in `Request`/`Response`/`Model` — `ClickRequest`, `ClickResponse`, `LivenessResponse`
- Python TypedDict: `PascalCase` — `GraphState`

**CSS Classes (Tailwind utilities + custom):**
- Tailwind utilities: kebab-case — `flex-col`, `bg-[var(--surface)]`, `text-[var(--text-muted)]`
- Custom semantic classes: kebab-case — `product-card-hover`, `shadow-card`, `shadow-card-hover`, `font-serif`, `stream-status-text`, `scrollbar-hide`, `comparison-html-container`
- Custom Tailwind extensions: kebab-case — `transitionDuration: { stream: '150ms', skeleton: '200ms', card: '200ms' }` (`tailwind.config.ts:73-76`)

**Backend Settings:**
- All settings on `Settings(BaseSettings)` use `UPPER_SNAKE_CASE` — `OPENAI_API_KEY`, `CORS_ORIGINS`, `MAX_PRODUCTS_RETURN`, `DEFAULT_MODEL`
- Located at `backend/app/core/config.py`, accessed globally as `settings`

## TypeScript Strictness & Type Coverage

**Compiler config (`frontend/tsconfig.json`):**
- `"strict": true` (enables strictNullChecks, noImplicitAny, strictFunctionTypes, etc.)
- `"target": "ES2020"`, `"module": "esnext"`, `"moduleResolution": "bundler"`
- `"jsx": "preserve"` (Next.js handles transformation)
- `"isolatedModules": true`
- Path alias `@/*` → project root
- No `"noUnusedLocals"` or `"noUnusedParameters"` enabled — unused imports slip through

**`any` usage — 90 occurrences across 17 files** (out of 113 TS/TSX files = ~15% of files have `any`):

**Type-system holes (lib + hooks):**
- `frontend/lib/chatApi.ts:77, 80, 91, 486, 509` — `ui_blocks?: any[]`, `itinerary?: any[]`, `blocks?: any[]`, `Promise<any>` returns from `fetchConversationHistory` and `checkHealth`
- `frontend/lib/extractResultsData.ts:41-128` — 10 `any` casts inside `resolveProducts`/`resolveReviewSources` because `Message.ui_blocks` is `any[]`
- `frontend/hooks/useStreamReducer.ts:15, 23-28` — `UIBlock { [key: string]: any }`, `DoneChunk { itinerary?: any[]; next_suggestions?: any[]; [key: string]: any }`
- `frontend/lib/normalizeBlocks.ts:28` — `normalizeBlocks(rawBlocks: any[])` (unavoidable boundary type)

**Block dispatcher hot-path:**
- `frontend/components/blocks/BlockRegistry.tsx:36, 40, 43, 59, 62, 65, 69-78, 80-110` — 26 `any` casts because each `b.data` is untyped. The renderer table maps tag → component but loses every type guarantee at the call site.

**Component prop leak:**
- `frontend/components/ChatContainer.tsx:38-41` — `ui_blocks?: any[]`, `itinerary?: any[]`, structured-vs-array union for `followups` typed loosely
- `frontend/components/ProductCards.tsx:52` — `(product.best_offer as any)?.image_url` (best_offer interface lacks image_url field, hacky widening)
- `frontend/components/CategorySidebar.tsx:23` — `const ICON_MAP: Record<string, any>` (should be `Record<string, LucideIcon>`)

**Admin pages (worst offenders):**
- `frontend/app/admin/Dashboard.tsx:32, 37, 47, 66` — `chart_data: any[]`, `top_errors: any[]`, `expensive: any[]`, `icon: any` in MetricCard prop
- `frontend/app/admin/users/page.tsx:155` — `const updateData: any = {}` (mutable accumulator pattern)
- `frontend/app/login/page.tsx:52` — `} catch (err: any)`

**Test files** (acceptable):
- `frontend/tests/chatScreen.test.tsx:21-38` — `({ children, ...props }: any) =>` framer-motion stubs, normal in mocks
- `frontend/tests/resultsScreen.test.tsx` — 14 `any` for fixture data and mock components

**Score:** TypeScript strict mode is technically enabled but strictness is undermined by `any` escape hatches concentrated in (a) the SSE/streaming boundary, (b) the BlockRegistry dispatcher, and (c) the entire admin surface. The block schema should be replaced with a discriminated union (`{type: 'carousel'; data: CarouselData} | {type: 'hotels'; data: HotelCard[]} | ...`) to eliminate the 26 `any` casts in BlockRegistry alone.

## Code Style

**Formatting:**
- No `.prettierrc`, `.eslintrc.*`, or `biome.json` in `frontend/` — relies on Next.js default ESLint
- No `pyproject.toml`, `.flake8`, or `setup.cfg` in `backend/` — Python formatting not enforced
- Trailing semicolons: codebase mostly **omits** them (TS); admin folder (`Dashboard.tsx`, `ConfigManagement.tsx`, `AdminProtectedRoute.tsx`) inconsistently uses semicolons
- Quote style: single quotes in TS (`'use client'`, `'./MessageList'`); Python uses double quotes
- Indentation: 2 spaces (TS), 4 spaces (Python)

**Linting:**
- Frontend: Next.js built-in ESLint (`npm run lint` → `next lint`)
- One `// eslint-disable-next-line @next/next/no-img-element` in `frontend/components/HotelCards.tsx:139` — only place where `<img>` is acknowledged as a lint suppression (yet 14 other files use raw `<img>` without disabling, see Performance section)
- Backend: `# noqa: E402` used for sys.path import ordering, `# type: ignore[no-any-return]` used once in `backend/app/lib/toon_python/normalizer.py`

## Import Organization

**TypeScript order observed (`frontend/components/ChatContainer.tsx:1-16`):**
1. `'use client'` directive (one blank line after)
2. React hooks (`import { useState, useEffect, useRef } from 'react'`)
3. Internal component imports (`import MessageList from './MessageList'`)
4. Internal lib imports via `@/*` alias (`import { streamChat } from '@/lib/chatApi'`)
5. Type-only imports last (`import type { SkeletonBlockType } from '@/components/BlockSkeleton'`)

**Python order observed (`backend/app/agents/safety_agent.py:1-15`):**
1. Module docstring
2. Standard library (`import re`, `from typing import ...`)
3. Internal absolute imports (`from app.core.centralized_logger import get_logger`)
4. Third-party (`from openai import AsyncOpenAI`)
5. Internal relative (`from ..schemas.graph_state import GraphState`)

Note: backend ordering is *not* strictly stdlib → third-party → internal; `app.core.centralized_logger` is sometimes imported before `openai`. Not enforced by tooling.

**Path Aliases:**
- Frontend: `@/*` → project root (`frontend/tsconfig.json:22`)
- Relative imports used for siblings (`./MessageList`) and `../hooks/...` for one-level-up

## Component Patterns: CSS Vars vs Tailwind

**Documented Editorial Luxury foundation** (`frontend/app/globals.css:5-100`):
- Light/dark themes defined via CSS variables on `:root` and `[data-theme="dark"]`
- Semantic vars: `--text`, `--text-secondary`, `--text-muted`, `--background`, `--surface`, `--surface-hover`, `--surface-elevated`, `--border`, `--border-strong`, `--primary`, `--accent`
- Legacy `--gpt-*` vars are aliased to semantic vars at `globals.css:57-76` for backward compatibility

**Semantic var usage:** 638 hits across **62 files** of `var(--text|--bg|--surface|--border|--primary)` — the dominant pattern.

**Legacy `--gpt-*` var usage:** 169 hits across **8 files** (admin code only):
- `frontend/components/AdminProtectedRoute.tsx:31, 34` — 2 hits
- `frontend/components/ErrorBoundary.tsx:40, 57, 60, 68, 78, 87, 90, 79` — 8 hits (the user-visible fallback UI itself uses legacy vars)
- `frontend/app/admin/Dashboard.tsx` — 37 hits
- `frontend/app/admin/ConfigManagement.tsx` — 36 hits
- `frontend/app/admin/users/page.tsx` — 58 hits
- `frontend/app/admin/page.tsx` — 2 hits
- `frontend/app/admin/layout.tsx` — 25 hits
- `frontend/tailwind.config.ts:42` — `'premium': 'var(--gpt-shadow-premium)'` (the only non-admin reference, kept for legacy mapping)

**Editorial Luxury exceptions (components NOT yet migrated):** All 8 files above. The admin surface uses MUI (`@mui/material`) with `sx={{ background: 'var(--gpt-background)' }}` style props, never converted. ErrorBoundary's fallback UI also still on legacy vars — when an actual error fires, the user sees a non-Editorial-styled screen.

**Three styling approaches coexist:**
1. **Tailwind utility with CSS-var bracket** (`bg-[var(--surface-elevated)] text-[var(--text)]`) — used by all newer Editorial components (`ProductCarousel.tsx`, `HotelCards.tsx`, `Message.tsx`, `ChatInput.tsx`)
2. **Inline `style={{ ... }}` with CSS vars** (`style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}`) — used by `TrendingCards.tsx:23-31`, `MobileTabBar.tsx:158-160`, `ResultsProductCard.tsx:97-101`, `ProductReviewCarousel.tsx:120-124`
3. **MUI `sx={{ ... }}` with legacy vars** (`sx={{ background: 'var(--gpt-background)' }}`) — admin pages only

The mixing of patterns 1 and 2 within the same component (e.g., `MobileTabBar.tsx` uses className for layout AND inline styles for color) is inconsistent. Pattern 1 (Tailwind brackets) is preferred per `CLAUDE.md` editorial guidance.

**Hard-coded colors despite tokens:**
- `frontend/components/ProductCarousel.tsx:38, 42, 44, 49` — `fill="#E5A100"`, `stroke="#D6D3CD"` for Star rating (these are token values inlined, not vars)
- `frontend/components/MobileTabBar.tsx:138, 158, 168, 198, 286-291` — `borderTop: '1px solid #E8E6E1'`, `color: '#9B9B9B'`, `'#1B4DFF'` repeated 12+ times (should use `var(--border)` and `var(--primary)`)
- `frontend/components/ResultsProductCard.tsx:45-51` — `color: '#B8860B'`, `'#7C3AED'` for badges (one-off rank colors)
- `frontend/components/HotelCards.tsx:152` — `style={{ backgroundColor: '#E5A100' }}` for rating overlay

## Server vs Client Components

**'use client' directive prevalence:** 67 of 67 `.tsx` files audited declare `'use client'`. **There are zero true Server Components.**

Even pages that could be statically rendered (`frontend/app/privacy/page.tsx`, `frontend/app/terms/page.tsx`, `frontend/app/affiliate-disclosure/page.tsx`) are not currently server components — though they don't explicitly mark `'use client'` either; they're plain components in the App Router with no client hooks. The `Footer.tsx` is one of the rare components without `'use client'` directive (server-renderable).

**Implication:** Bundle size impact is meaningful — Next.js App Router's RSC benefit is being left on the table.

**Quote style for the directive:** All occurrences use single-quoted `'use client'` (zero double-quoted `"use client"`) — consistent.

## Error Handling

**Backend Patterns:**

Three error-handling layers:

**1. Agents — `BaseAgent.generate()` wraps model calls** (`backend/app/agents/base_agent.py:70-93`):
```python
try:
    return await model_service.generate(...)
except Exception as e:
    log_and_raise_agent_error(
        logger=self.logger,
        source=self.agent_name,
        message=f"Model generation failed: {str(e)}",
        original_error=e,
        session_id=session_id,
        extra_context={"operation": "generate", "model": model}
    )
```

**2. Tools — `@tool_error_handler` decorator** (`backend/app/core/error_manager.py:119-151`):
```python
@tool_error_handler(tool_name="product_search", error_message="Failed to search products")
async def product_search(state: Dict[str, Any]) -> Dict[str, Any]:
    ...
```
Used on **21 of 22 MCP tools** in `backend/mcp_server/tools/` — 100% adoption. Only `base_tool.py` (helper module) and `__init__.py` lack the decorator.

**3. FastAPI endpoints — raise `HTTPException` directly** (`backend/app/api/v1/health.py`, `backend/app/api/v1/chat.py`):
```python
raise HTTPException(status_code=503, detail=health_status)
```

**Error class hierarchy** (`backend/app/core/error_manager.py:10-42`):
- `BaseError(Exception)` — carries `source`, `message`, `original_error`, `context`
- `AgentError(BaseError)` — raised by agents
- `ToolError(BaseError)` — raised by tools
- Both implement `to_dict()` for API serialization

**Inconsistency: SafetyAgent's bespoke pattern.** `backend/app/agents/safety_agent.py:43-56` uses a **try/except that returns dict on error** instead of using `BaseAgent.handle_error()` or `log_and_raise_agent_error`:
```python
except Exception as e:
    logger.error(f"Safety Agent error: {str(e)}", exc_info=True)
    return {
        "policy_status": "allow",  # Fail-open!
        "sanitized_text": state["user_message"],
        ...
    }
```
This silently swallows safety-check failures and treats them as "allow." It's intentional (fail-open for moderation API), but bypasses the standardized error pipeline. SafetyAgent also doesn't extend `BaseAgent` — it's a parallel implementation.

**Bare-except prevalence:** 189 `except Exception` clauses across 57 backend files. Many are recovery paths, but some are too broad — `backend/app/api/v1/admin.py` has 11 such clauses; `backend/app/repositories/conversation_repository.py` has 10.

**Frontend Patterns:**

**Callbacks-based error propagation** in streaming — callers pass `onError` callback to `streamChat` (`frontend/lib/chatApi.ts`).

**ErrorBoundary** (`frontend/components/ErrorBoundary.tsx`):
- Class component, 104 lines, used in only **1 location**: `frontend/app/chat/page.tsx`
- Pages like `/results`, `/browse`, `/saved`, `/admin` have no boundary above them
- Falls back to generic "Something went wrong" UI styled with **legacy `--gpt-*` vars** (lines 40, 57, 68, 78) — when this UI actually fires, it visually clashes with the rest of the app

**try/catch counts:** 31 `try {` blocks with 37 `catch (` clauses across 17 frontend files. Imbalance suggests some `try` blocks have `catch` + `finally` (`Message.tsx:99-102` clipboard fallback uses nested try/finally).

**Silent failures:** `frontend/lib/recentSearches.ts:13-27, 32-47, 51-55` uses three empty `catch {}` blocks for localStorage SSR safety — appropriate but undocumented.

**ChatContainer state machine:** `frontend/hooks/useStreamReducer.ts` properly handles `errored` and `interrupted` terminal states with documented FSM transitions in lines 47-58.

## Logging

**Backend:**
- `get_logger(__name__)` from `backend/app/core/centralized_logger.py` used in every module
- `get_colored_logger(__name__)` from `backend/app/core/colored_logging.py` used in agent debug paths
- Both loggers respect `LOG_ENABLED` env flag (disabled in test environment via `conftest.py:18`)
- F-string interpolation throughout: `logger.error(f"Database health check failed: {e}")`
- Log levels: `logger.info`, `logger.warning`, `logger.error`, `logger.debug`
- Structured JSON logging optional via `LOG_FORMAT=json`
- `extra={"session_id": session_id, ...}` passed to `logger.error` for structured context (`backend/app/core/error_manager.py:64-71`)

**Frontend:**
- `console.error` and `console.warn` preserved in production (`frontend/next.config.js:14-17` excludes them from `removeConsole`)
- All other `console.*` stripped from production builds
- No frontend logging framework — plain `console.*`
- Tests mock console with `vi.spyOn(console, 'error').mockImplementation(() => {})` to suppress noise

## Comments

**When to Comment:**
- Python: docstrings required on all classes, public methods, and module headers
- TypeScript: JSDoc blocks on exported functions and key types
- RFC section markers used as living documentation: `// RFC §2.4 — Category sort priority` (10+ occurrences in `Message.tsx`, `chatApi.ts`, `useStreamReducer.ts`, `tailwind.config.ts:53, 65, 71, 77`)

**Inline Style:**
- Python: `# Comment text` — space after `#`
- TypeScript: `//` for single-line, `/* */` for multi-line
- Box-drawing comment headers in TS (`// ─── Reducer ───────────`) — `useStreamReducer.ts:1, 45, 88`

**TODO/FIXME presence:**
- Frontend: 1 TODO — `frontend/lib/chatApi.ts:409` (legacy event handler removal)
- Backend: 11 TODO/FIXME across 4 files — concentrated in `backend/app/services/travel/providers/expedia_provider.py` (5) and `backend/app/services/travel/providers/mock_provider.py` (4) — these are placeholder providers awaiting real implementation

## Function Design

**Python async functions:**
- All agent and tool entry points are `async def`
- State dict (`Dict[str, Any]`) is the standard tool interface: read from `state.get(...)`, return dict of partial state updates
- Inner coroutines nested inside workflow nodes for budget/cancellation wrapping

**TypeScript functions:**
- Arrow functions for callbacks, event handlers, and inline closures
- Named `function` declarations for exported utilities, type guards, and reducers
- Component-internal helpers as nested functions (`StarRatingInline`, `ProductImage` inside `ProductCarousel.tsx:30-84`)

**Component file size — large file outliers:**
- `frontend/components/ChatContainer.tsx` — **884 lines** (the god-component)
- `frontend/app/admin/users/page.tsx` — **625 lines**
- `frontend/components/UnifiedTopbar.tsx` — **352 lines**
- `frontend/components/Message.tsx` — **305 lines**
- `frontend/components/MobileTabBar.tsx` — **304 lines**
- `frontend/components/HotelCards.tsx` — **260 lines**
- `frontend/components/ProductCarousel.tsx` — **251 lines**
- `frontend/components/ProductReview.tsx` — **199 lines**
- `frontend/components/ResultsProductCard.tsx` — **191 lines**

ChatContainer at 884 LOC absorbs streaming logic, message reducer interaction, halt-state handling, error banner, recovery UI, status context, and SSE reconnection — it's a refactor candidate (split into hooks).

**Parameters:**
- Python: keyword args with `Optional` type hints and defaults
- TypeScript: destructured object params for component props with explicit `interface` definitions inline above the function

**Return Values:**
- Python tools: `Dict[str, Any]` — partial state updates merged into `GraphState`
- Python agents: `async def run(self, state: Any) -> Any` — returns updated state dict
- TypeScript hooks: named object with state and dispatch (`{ streamState, isStreaming, dispatch }`)

## Code Duplication

**Card components have substantial copy-paste:**

**1. PLPLink card pattern duplicated** between `HotelCards.tsx:45-115` (`PLPLinkCard`) and `FlightCards.tsx:49-160+` (`PLPLinkCard`) and `CarRentalCard.tsx:49-110` — three near-identical components for "Search Properties / Search Flights / Search Cars" CTAs. Same structure: search icon → title → date range → guests/passengers → provider badge → CTA button. Should extract a shared `<SearchPLPCard>` component.

**2. `formatDate` helper duplicated** in `HotelCards.tsx:46-57`, `FlightCards.tsx:50-61`, and `CarRentalCard.tsx:20-31` — identical implementation, ~12 lines each.

**3. `lookupCuratedProduct` duplicated verbatim** in `frontend/components/InlineProductCard.tsx:30-46` and `frontend/components/ResultsProductCard.tsx:13-39` — identical 16-line function. Should live in `frontend/lib/curatedLinks.ts`.

**4. `ProductImage` inner component duplicated** in `ProductCarousel.tsx:55-84`, `InlineProductCard.tsx:48-71`, and `ResultsProductCard.tsx:56-79` — all implement "render image with fallback to placeholder on error/missing src." `frontend/components/ui/ImageWithFallback.tsx` exists for exactly this purpose but is not used by any of the three.

**5. Star rating implementations** — `frontend/components/StarRating.tsx` (52 lines) is the canonical version, but `ProductCarousel.tsx:30-53` reimplements `StarRatingInline` with hard-coded colors instead of importing the shared component.

**6. `trackAffiliateClick` `onClick` handler duplicated** with `e.preventDefault()` + tracking call across 5+ card components (`ProductCarousel.tsx:162-169`, `HotelCards.tsx:65-74`, `FlightCards.tsx:71-79`, `PriceComparison.tsx:78`, `CarRentalCard.tsx:56-66`) — could be a single `useTrackedAffiliateLink` hook.

**7. "Disclosure: We may earn commissions" footer** appears in 5 components (`ProductCarousel.tsx:246-248`, `ProductCards.tsx:152-154`, `AffiliateLinks.tsx:78-80`, `BlockRegistry.tsx:113-115`, `PriceComparison.tsx`) — should be a shared `<AffiliateDisclosure>` component.

**8. ACCENT_COLORS constant duplicated** at `frontend/components/UnifiedTopbar.tsx:9-15` and `frontend/components/MobileTabBar.tsx:8-14` — identical 5-element array. Should live in `frontend/lib/constants.ts`.

## Dead Code & Unused Imports

**Unused lucide-react imports detected:**
- `frontend/components/HotelCards.tsx:3` imports `Star` (never used in file body)
- `frontend/components/Message.tsx:3` imports `Copy` and `Check` (never rendered — only `User` and `ArrowRight` are used)

(Without ESLint's `no-unused-vars` enforced, these accumulate.)

**Skipped test file:** `frontend/tests/ChatContainer.test.tsx.skip` (385 lines) — explicitly disabled. Likely broken due to ChatContainer's complexity; never deleted.

**Empty `frontend/app/browse/page.tsx`** — only 5 lines, redirects logic to nested route. Acceptable but noted.

**Admin route scaffolding largely orphaned** — `frontend/app/admin/{Dashboard.tsx, ConfigManagement.tsx}` use MUI (`@mui/material`, `@emotion/react`, `react-admin`, `recharts`) which adds ~200KB to the bundle. The pages may not be actively used in production.

## Accessibility

**ARIA attributes — 49 occurrences across 18 files** (mostly `aria-label`):

**Strong examples:**
- `frontend/components/ProductCarousel.tsx:133, 140, 240` — `aria-label="Previous"`, `aria-label="Next"`, `aria-label={\`Page ${idx + 1}\`}` on nav buttons
- `frontend/components/ProductReviewCarousel.tsx:79, 88, 125` — `aria-label="Previous product"`, `aria-label="Next product"`, `aria-label={\`Go to product ${i + 1}\`}`
- `frontend/components/MobileTabBar.tsx:152, 187, 261, 279, 280` — `aria-label`, `aria-current="page"` on active tab
- `frontend/components/MobileHeader.tsx:46, 74, 112` — `aria-label` on back button, expand button, user menu
- `frontend/components/discover/TrendingCards.tsx:62, 78, 116` — `aria-hidden="true"` on decorative icons
- `frontend/components/ResultsProductCard.tsx:156-159` — proper `role="progressbar"` + `aria-valuenow/valuemin/valuemax` on score bar
- `frontend/components/InlineProductCard.tsx:104` — `aria-hidden="true"` on emoji decoration

**Gaps:**
- `frontend/components/ChatInput.tsx:78-91` — Send button has no `aria-label` (relies on `<ArrowUp>` icon alone for screen readers)
- `frontend/components/ChatInput.tsx:56-76` — `<textarea>` lacks `aria-label` and `id` for label association
- `frontend/components/Message.tsx:152-156` — User message bubble has no role; copy button removed (Copy icon imported but unused — see Dead Code)
- `frontend/components/ProductReview.tsx:88-94` — Product image `alt` is just `product_name` (acceptable, but no descriptive context)
- `frontend/app/admin/Dashboard.tsx`, `ConfigManagement.tsx`, `users/page.tsx` — MUI components rely on Material's defaults; no explicit ARIA enhancement
- `frontend/components/ErrorBoundary.tsx` — error fallback UI has no `role="alert"` to announce the error

**Keyboard navigation:**
- `frontend/components/ChatInput.tsx:25-30` — properly handles Enter to send, Shift+Enter for newline
- `frontend/components/ProductReviewCarousel.tsx:33-45` — touch swipe handlers but **no keyboard arrow-key navigation** despite being a carousel (only desktop arrow buttons work via click)
- `frontend/components/ProductCarousel.tsx:103-109` — pagination buttons clickable but **no keyboard focus management** when slides change

**Semantic HTML:**
- Footer uses `<footer>` (`Footer.tsx:5`); good
- MobileTabBar uses `<nav>` (`MobileTabBar.tsx:130`); good
- MobileHeader uses `<header>` (`MobileHeader.tsx:32`); good
- Chat container is all `<div>` — could use `<main>` for the message area
- Message bubbles are `<div>` — should use `<article>` per message for screen-reader navigation

**Image alt text — 18 `<img>` occurrences, all with `alt=`:**
- `Message.tsx:127` — `alt="AI"` (terse but acceptable)
- `AnimatedLogo.tsx:59, 72` — `alt="ReviewGuide.ai"` (good)
- `MobileHeader.tsx:96` — `alt="ReviewGuide.Ai"` (note inconsistent capitalization vs AnimatedLogo)
- `ResultsProductCard.tsx:74`, `InlineProductCard.tsx:66`, `ProductCarousel.tsx:76`, `HotelCards.tsx:142`, `ProductCards.tsx:69` — all use `alt={productName}` or `alt={hotel.name}` (acceptable)
- `app/browse/[category]/page.tsx:40, 126` — `alt={category.name}` (acceptable)
- `ImageWithFallback.tsx:50, 37` — properly forwards `alt` prop and uses it as fallback caption

## Performance Patterns

**`useMemo` / `useCallback` / `React.memo` — 28 occurrences across 9 files:**
- `frontend/components/Message.tsx:71-74` — `useMemo` for `sortedSuggestions` (good, prevents resort on streaming re-renders)
- `frontend/components/MessageList.tsx` — uses `useCallback` for scroll handlers (4 occurrences)
- `frontend/components/MobileTabBar.tsx:38, 84, 90` — `useCallback` for `navRefCallback`, `startLongPress`, `cancelLongPress`
- `frontend/components/ProductReviewCarousel.tsx:16, 25, 29` — `useCallback` for `scrollToIndex`, `next`, `prev`
- `frontend/components/HomeSearchBar.tsx` — 4 occurrences
- `frontend/hooks/useStreamReducer.ts` — 2 occurrences for stable handlers
- `frontend/lib/chatStatusContext.tsx` — 4 (memoized context value)
- `frontend/app/chat/page.tsx` — 4
- `frontend/app/browse/[category]/page.tsx` — 2

**`React.memo` — zero occurrences.** No component is memoized despite high re-render frequency in chat (Message components re-render on every token). For ChatContainer's tight streaming loop, message-level memoization could help.

**Image optimization:**
- `next/image` is imported in **only 2 files**: `frontend/next-env.d.ts` (auto-generated type) and `frontend/app/login/page.tsx` (likely unused import)
- **All 14 image-rendering components use raw `<img>` tags.** Misses Next.js auto-optimization (WebP conversion, responsive sizes, lazy loading via Intersection Observer, blur placeholders)
- Manual `loading="lazy"` added in `ProductCards.tsx:71`, `ProductCarousel.tsx:77`, `ProductReview.tsx:92`, `ImageWithFallback.tsx:57`
- `onError` fallbacks implemented manually in many components — `next/image`'s `onError` would handle this

**Bundle splits:**
- `frontend/next.config.js:5` — `output: 'standalone'` for Docker
- No explicit dynamic imports (`next/dynamic`) found in components
- Admin pages bundled with main app despite using heavy MUI (`@mui/material 7.3.5`, `react-admin 5.13.2`, `recharts 3.5.1`) — should be `next/dynamic` route-split

**Window event listeners properly cleaned up:**
- `frontend/components/ProductCarousel.tsx:99-101` — `removeEventListener` on cleanup
- `frontend/components/ProductReviewCarousel.tsx:57-58` — proper cleanup of `scrollend` listener
- `frontend/components/UnifiedTopbar.tsx:73, 79` — proper cleanup
- `frontend/components/MobileTabBar.tsx:62-63, 79-80` — proper cleanup of `visualViewport` and click-outside

## Test Coverage Assessment

**Frontend tests** (`frontend/tests/`): 19 test files, **4,205 LOC of test code**, vitest + @testing-library/react

**What's covered:**
- `useStreamReducer.test.ts` (358 LOC) — exhaustive state-transition coverage of all 7 FSM states (lines 8-64)
- `chatApi.test.ts` (285 LOC) — SSE parsing, retry logic, telemetry
- `chatScreen.test.tsx` (383 LOC) — top-level chat integration with full mock harness
- `resultsScreen.test.tsx` (489 LOC) — Phase-15 results page including extraction logic
- `suggestions.test.tsx` (398 LOC) — RFC §2.4 suggestion sorting and category labels
- `discoverScreen.test.tsx` (219 LOC) — Discover page with router mocks
- `messageRecovery.test.tsx` (145 LOC) — RFC §2.3 partial/degraded message recovery
- `mobileTabBar.test.tsx` (206 LOC) — keyboard detection, profile popover, accent picker
- `inlineProductCard.test.tsx` (258 LOC), `sourceCitations.test.tsx` (267 LOC), `explainabilityPanel.test.tsx` (312 LOC) — block-level component coverage
- `designTokens.test.ts` (70 LOC) — verifies CSS variables exist
- `ErrorBoundary.test.tsx` (103 LOC), `blockSkeleton.test.tsx` (90 LOC), `layout.test.tsx` (38 LOC), `pageTransition.test.tsx` (50 LOC), `navLayout.test.tsx` (114 LOC)

**What's NOT covered (gaps):**
- **No tests for the new ProductReviewCarousel** (`frontend/components/ProductReviewCarousel.tsx`, 137 LOC) — the swipe carousel that gives this branch its name has zero test coverage
- **No tests for HotelCards, FlightCards, CarRentalCard, PriceComparison, ComparisonTable, ItineraryView, DestinationInfo, AffiliateLinks** — major card components untested
- **No tests for ChatContainer** — `ChatContainer.test.tsx.skip` is disabled (385 LOC, never re-enabled)
- **No tests for the BlockRegistry dispatcher** — the central rendering switch is untested
- **No tests for admin pages** (Dashboard, ConfigManagement, users) — this is acceptable if treated as scaffolding
- **No accessibility tests** (no jest-axe usage)
- **No visual regression / snapshot tests**
- **No E2E tests** — no Playwright, Cypress, or Puppeteer config detected

**Backend tests** (`backend/tests/`): 30 test files, **5,249 LOC of test code**, pytest + asyncio_mode = auto (`pytest.ini:6`)

**What's covered:**
- `test_chat_api.py` (335), `test_chat_streaming.py` (126), `test_chat_history_efficiency.py` (130) — chat endpoint integration
- `test_qos.py` (395) — quality-of-service / QoS budgeting
- `test_review_search.py` (454) — SerpAPI review fetching
- `test_model_service.py` (345), `test_tool_validator.py` (323), `test_startup_manifest.py` (351) — service layer
- `test_product_compose.py` (275), `test_product_affiliate.py` (110) — MCP tool tests
- `test_sse_events.py` (277), `test_telemetry.py` (219), `test_stage_telemetry.py` (261) — observability
- `test_state_serializer.py` (130), `test_degradation_policy.py` (142), `test_query_complexity.py` (76) — supporting services
- `test_cj_provider.py` (242) — affiliate provider
- Tiered router subdirectory: 11 test files including `test_circuit_breaker.py`, `test_orchestrator.py`, `test_parallel_fetcher.py`, `test_router.py`, `test_workflow_integration.py` — comprehensive coverage of the tiered API system

**What's NOT covered (gaps):**
- **No agent tests** for SafetyAgent, IntentAgent, ClarifierAgent, PlannerAgent — only indirectly via chat integration
- **No tests for MCP tools individually** (other than product_compose, product_affiliate, review_search) — `travel_search_hotels`, `travel_search_flights`, `travel_itinerary`, `intro_compose`, `general_compose` are untested
- **No tests for the LangGraph workflow** — `backend/app/services/langgraph/workflow.py` has no dedicated unit tests
- **No tests for ConversationRepository or HaltStateManager** despite their critical role
- **No tests for travel providers** (Booking, Skyscanner, Amadeus, Expedia) — placeholder tests would catch HTTP signature drift

**Test patterns:**
- Mocking: `unittest.mock.AsyncMock`/`MagicMock` for backend, `vi.mock()` for frontend
- `frontend/tests/setup.ts` mocks Next.js navigation, localStorage, fetch, scrollIntoView
- Backend `conftest.py:21-76` patches all lifespan startup/shutdown I/O — comprehensive mock harness
- No fixtures directory — fixtures inlined in test files
- Coverage command: `npm run test:coverage` (frontend), no coverage gate

## Module Design

**Barrel files:** Not used. Direct imports from specific paths.

**Exports:**
- Python: no `__all__` defined; all public symbols importable
- TypeScript: named exports for types/utilities, default export for React components
- Re-export pattern documented: `export type { SuggestionCategory, NextSuggestion } from '@/lib/chatApi'` in `ChatContainer.tsx:31` keeps type canonical in `chatApi.ts`

**Singleton Pattern (Python):**
- Module-level instances for services — `chat_history_manager` in `backend/app/services/chat_history_manager.py`, `model_service` in `backend/app/services/model_service.py`
- Settings loaded once: `settings = Settings()` at module level in `backend/app/core/config.py`

## Editorial Luxury Foundation Audit

**Documented expectations** (per `CLAUDE.md` and existing CONVENTIONS.md):
- DM Sans (body) + Instrument Serif (headings) loaded in `layout.tsx`
- Warm ivory (#FAFAF7) light / warm charcoal (#1A1816) dark
- Primary blue (#1B4DFF), terracotta accent (#E85D3A)
- Legacy `--gpt-*` vars mapped to new semantic vars in `globals.css` for backward compat
- All components should use semantic vars (`--text`, `--bg`, `--surface`)

**Compliance audit (62 of 67 client components use semantic vars):**

**Compliant Editorial components** (use `var(--text|--surface|--border|--primary)` exclusively):
- `Message.tsx`, `ChatContainer.tsx`, `ChatInput.tsx`, `MessageList.tsx`
- `ProductCarousel.tsx`, `ProductCards.tsx`, `ProductReview.tsx`, `ProductReviewCarousel.tsx`
- `HotelCards.tsx`, `FlightCards.tsx`, `CarRentalCard.tsx`
- `ComparisonTable.tsx`, `ListBlock.tsx`, `DestinationInfo.tsx`, `AffiliateLinks.tsx`, `ItineraryView.tsx`
- `UnifiedTopbar.tsx`, `MobileTabBar.tsx`, `MobileHeader.tsx`, `NavLayout.tsx`, `Footer.tsx`
- `ConversationSidebar.tsx`, `CategorySidebar.tsx`
- All `browse/*` components (`CategoryHero`, `CategoryNav`, `FilterSidebar`, `QuickQuestion`, `SearchInput`, `SentimentBar`, `SourceStack`, `SourcesModal`)
- All `discover/*` components (`CategoryChipRow`, `DiscoverSearchBar`, `TrendingCards`)
- `StarRating.tsx`, `BlockSkeleton.tsx`, `ResultsHeader.tsx`, `ResultsProductCard.tsx`, `ResultsQuickActions.tsx`
- All app pages: `app/page.tsx`, `app/chat/page.tsx`, `app/results/[id]/page.tsx`, `app/saved/page.tsx`, `app/compare/page.tsx`, `app/privacy/page.tsx`, `app/terms/page.tsx`, `app/affiliate-disclosure/page.tsx`

**Non-compliant exceptions (8 files using legacy `--gpt-*` vars exclusively):**
1. `frontend/components/AdminProtectedRoute.tsx` — admin gate (2 vars)
2. `frontend/components/ErrorBoundary.tsx` — fallback UI (8 vars) — **highest priority to fix** because users see this when things break
3. `frontend/app/admin/Dashboard.tsx` — 37 vars (MUI scaffolding)
4. `frontend/app/admin/ConfigManagement.tsx` — 36 vars
5. `frontend/app/admin/users/page.tsx` — 58 vars
6. `frontend/app/admin/page.tsx` — 2 vars
7. `frontend/app/admin/layout.tsx` — 25 vars
8. `frontend/tailwind.config.ts:42` — single legacy mapping kept intentionally as a Tailwind boxShadow alias (`'premium': 'var(--gpt-shadow-premium)'`)

**SourceBadge.tsx exception:** Uses brand-specific hardcoded colors (intentional per memory note).

**Hardcoded color leaks** (use of literal hex/rgb instead of vars) found in 4 Editorial-compliant components:
- `MobileTabBar.tsx` — `#E8E6E1`, `#9B9B9B`, `#1B4DFF` repeated in inline styles instead of `var(--border)`, `var(--text-muted)`, `var(--primary)`
- `ProductCarousel.tsx:38, 42, 44, 49` — Star colors `#E5A100`, `#D6D3CD` (rating amber + empty stone)
- `ResultsProductCard.tsx:45, 51, 109` — `#B8860B`, `#7C3AED`, `bg-black` for badge variants
- `HotelCards.tsx:152` — `#E5A100` for rating overlay

These should be promoted to CSS variables (`--rating-fill`, `--rating-empty`, `--badge-gold`, `--badge-violet`).

## Swipe Product Carousel Quality Audit

**File:** `frontend/components/ProductReviewCarousel.tsx` (137 LOC, new in v2-with-swipe branch)

**Pattern adherence — strong:**
- `'use client'` directive ✓
- TypeScript interface for props (line 6-8) ✓
- Refs typed properly (`useRef<HTMLDivElement>(null)`) ✓
- `useCallback` for scrollToIndex/next/prev ✓
- Cleanup on unmount: `removeEventListener('scrollend', handleScroll)` (line 58) ✓
- Lucide icons via named import ✓
- Edge case: returns `<div>{children}</div>` if `total <= 1` (line 61-63) ✓
- ARIA: `aria-label="Previous product"`, `aria-label="Next product"`, `aria-label={\`Go to product ${i + 1}\`}` ✓

**Pattern divergences from `ProductCarousel.tsx`:**

| Aspect | `ProductCarousel.tsx` (existing) | `ProductReviewCarousel.tsx` (new) |
|--------|----------------------------------|-----------------------------------|
| Styling approach | Tailwind utility brackets `bg-[var(--surface-elevated)]` | Mix of Tailwind + inline `style={{ background: 'var(--surface)', ... }}` |
| Pagination dot active color | `bg-[var(--primary)]` (utility) | `background: 'var(--primary)'` (inline) |
| Animation library | `framer-motion` | None — uses CSS scroll-snap |
| Swipe input | Mouse arrows + pagination dots only | Touch swipe + arrows + dots + scroll-snap |
| Scroll mechanism | State-driven `currentIndex` slice | Native browser scroll with `scroll-snap` |
| Image loading | `<img>` with manual loading state | Receives children — no image concern |
| Items API | `items: Product[]` typed array | `children: React.ReactNode[]` (less typed) |
| Item width control | Calculates `itemsPerPage` based on `window.innerWidth` (1/2/3) | `w-full` + scroll-snap (1 visible at a time) |

The new carousel uses **scroll-snap CSS** (`snap-x snap-mandatory`, `snap-start`) which is more performant and gives native momentum on mobile. It's a different (and arguably better) approach but creates **two coexisting carousel implementations** with different APIs.

**Quality issues:**
1. **Touch swipe threshold hardcoded** at `Math.abs(diff) > 50` (line 41) — should be a constant
2. **Type `children: React.ReactNode[]`** (line 7) is permissive — allows non-renderable children; could use `ReactElement[]`
3. **`scrollend` event has limited browser support** (`ProductReviewCarousel.tsx:57`) — Safari support landed only in 17.4 (2024); fallback to `scroll` debounced would be safer
4. **No keyboard arrow-key support** — only touch and click, leaving keyboard users stuck on first card
5. **Hardcoded color fallback** `'var(--border-strong, #D4D1CC)'` at line 123 — uses `--border-strong` which is defined in globals; the literal fallback shouldn't be needed
6. **"Swipe to browse products" hint text** (line 132) — always shown on mobile, no dismissal/first-visit gating despite the comment claim
7. **No memoization of children** — re-creates inner divs on every parent re-render
8. **Counter shows "X of Y products"** (line 70) — assumes children are products; not generalizable
9. **No tests** — new feature ships without unit tests (see Test Coverage gaps)

**BlockRegistry integration** (`frontend/components/blocks/BlockRegistry.tsx:174-189`):
- Properly groups multiple `product_review` blocks into a single `<ProductReviewCarousel>` (good consolidation)
- Uses `productReviewCarouselRendered` flag to prevent duplicate rendering across iterations (similar to existing `travelGridRendered` pattern at line 138)
- Correctly handles the single-review case via the carousel's internal short-circuit at line 61

**Verdict:** Implementation is functional and follows established conventions for ARIA, refs, and cleanup, but introduces a *second* carousel pattern instead of unifying with `ProductCarousel.tsx`. Long-term, the two should converge — `ProductCarousel` could adopt scroll-snap and accept either typed `items` or `children`.

---

*Convention analysis: 2026-04-16*
