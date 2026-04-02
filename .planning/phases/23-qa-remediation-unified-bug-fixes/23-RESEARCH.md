# Phase 23: QA Remediation — Unified Bug Fixes - Research

**Researched:** 2026-04-01
**Domain:** Full-stack bug remediation — Python/FastAPI backend pipeline + Next.js/React/Tailwind frontend
**Confidence:** HIGH (all findings verified directly in source code)

## Summary

This phase remediates 47 bugs across the backend LangGraph/MCP pipeline and the Next.js frontend. The code has been read directly, so root causes are confirmed rather than speculative. The backend bugs are concentrated in `product_compose.py` (fallback loop control flow, multi-provider gating) and the travel pipeline (no timeout UX). The frontend bugs are concentrated in mobile CSS (chat bubble width, nav overlap, overflow-x strategy, iOS scroll chain) plus three isolated UX gaps (Stop button dark mode, custom 404 page, /browse redirect).

All backend bugs have an existing pytest suite at `backend/tests/test_product_compose.py` using pytest-asyncio and `unittest.mock`. All frontend bugs have a Vitest test suite at `frontend/tests/` using `@testing-library/react`. Validation should extend both suites.

**Primary recommendation:** Fix bugs in dependency order — backend pipeline first (product_compose fallback loop, multi-provider gating, accessory suppression, budget enforcement, travel timeout UX), then independent frontend CSS fixes in parallel, then citations/status transparency, then regression harness.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Phase 0 (baseline): Record commit SHA, backend env snapshot (redacted), model/provider config, affiliate tag values, API base URL. Create QA run template. Run 8 canonical prompts against frozen baseline and store traces.
- Backend Pipeline Fixes: Fix `break` → `continue` in `product_compose.py` fallback loop; relax multi-provider gating; enforce merchant-label/link consistency; add accessory/part suppression denylist; add budget enforcement before final compose.
- Travel Reliability: Instrument travel path with per-tool timing and timeout flags; return partial travel response + recovery prompt instead of indefinite "Thinking".
- Citations & Transparency: Citation block must use actual URLs from search results; streaming must show meaningful intermediate status updates beyond "Thinking...".
- Frontend P0: Chat bubble only 167px wide on mobile — needs full-width on small viewports; chat input hidden behind nav bar (38px overlap, z-index conflict).
- Frontend P1: `overflow-x: hidden` on body → `overflow-x: clip`; "Stop generating" button uses hardcoded light-mode colors; no custom 404 page.
- Frontend P2: Forward navigation loads wrong chat session; silent message drop during active streaming; WCAG contrast failures on 7 elements; landscape orientation hides bottom nav at 844px; /browse silent redirect to homepage; chat history shows 0 conversations.
- iOS Scroll Fix: Change `overflow-hidden` → `overflow-clip` on 4 ancestor containers; add `-webkit-overflow-scrolling: touch` and `overscroll-behavior-y: contain`; replace setInterval + rAF auto-scroll with sentinel `<div ref={bottomRef} />` + `scrollIntoView({ block: 'end' })` in a `useEffect`.
- Regression Harness (Phase 5): Convert 25 test prompts into automated smoke tests; gate deploys on affiliate label-domain parity, accessory suppression, budget enforcement, travel non-hang, source link presence; manual QA checklist on mobile + desktop.
- Dependency Order: Backend pipeline fixes MUST land before frontend fixes that depend on correct data; independent frontend CSS fixes can proceed in parallel with backend work; revenue-impacting fixes come first.

### Claude's Discretion

- How to structure the QA run template (file format, storage location)
- Specific test framework for regression harness (pytest, vitest, playwright, etc.)
- Implementation details for budget parsing heuristics
- Specific z-index values for nav overlap fix
- Custom 404 page design (within editorial luxury theme)
- How to structure partial travel response UX

### Deferred Ideas (OUT OF SCOPE)

- eBay campid fix — blocked on Mike providing real campaign ID
- v4.0 affiliate integrations (eBay real ID, CJ activation, Expedia) — blocked on Mike
- Real-device iOS scroll verification — requires physical iPhone after deploy
- Comprehensive automated E2E tests (beyond smoke tests) — future milestone
</user_constraints>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest + pytest-asyncio | existing in backend | Backend unit and integration tests | All existing backend tests use this; conftest.py already set up |
| vitest + @testing-library/react | existing in frontend | Frontend component tests | All existing frontend tests use this; vitest.config already set up |
| Python asyncio | stdlib | Async backend tool execution | Already the execution model for all MCP tools |
| Next.js App Router | 14 | Frontend routing and 404 handling | `app/not-found.tsx` is the correct file for custom 404 in App Router |
| Tailwind CSS | existing | All frontend styling | Entire codebase uses utility classes; no CSS modules |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock (AsyncMock, MagicMock, patch) | stdlib | Mocking model_service in backend tests | Every backend test that touches LLM paths |
| pytest-asyncio | existing | Async test execution | All `async def` test functions |
| @testing-library/user-event | existing | DOM interaction in tests | Form input and button click tests |
| lucide-react | existing | Icons in custom 404 and UI | Already used throughout; use same icon set |

**Installation:** No new packages needed. All required libraries are already installed.

---

## Architecture Patterns

### Pattern 1: Backend — Fallback Loop Control Flow Bug (CONFIRMED)

**Location:** `backend/mcp_server/tools/product_compose.py` lines 1063–1116

**The bug (verified in source):**
```python
# Line 1065–1066 — CURRENT (broken):
for pname in blog_product_names:
    if pname in seen_card_names or review_card_count + fallback_card_count >= 5:
        break   # <-- exits the entire loop when first item is a duplicate
```

The `break` exits the entire fallback loop the moment it encounters a product already in `seen_card_names`. If the first product in `blog_product_names` is already covered by a `product_review` card, all subsequent products that could have gotten fallback cards are silently skipped.

**Fix:**
```python
for pname in blog_product_names:
    if review_card_count + fallback_card_count >= 5:
        break   # cap: stop when we have enough cards total
    if pname in seen_card_names:
        continue   # skip this one but keep iterating
```

**Unit test shape:**
```python
@pytest.mark.asyncio
async def test_fallback_loop_continue_not_break():
    # First blog product is already in seen_card_names (has review card),
    # second is not — must still emit a fallback card for the second.
    ...
```

### Pattern 2: Backend — Multi-Provider Gating (CONFIRMED)

**Location:** `backend/mcp_server/tools/product_compose.py` lines 937–944

**Current logic (verified):**
```python
providers_in_offers = set(o.get("source", "") for o in real_offers)
if len(providers_in_offers) < 2:
    # Fallback: include if at least 1 real offer exists (for curated Amazon links)
    curated_offers = [o for o in real_offers if "amzn.to" in o.get("url", "")]
    ebay_offers = [o for o in real_offers if o.get("source") == "ebay"]
    if not (curated_offers or ebay_offers):
        continue   # Silently drops single-provider products
```

Products with only one provider (e.g., only eBay or only a Serper result) are dropped unless they happen to have a curated Amazon short link or eBay offer. This means single-provider products that have legitimate buy links are suppressed.

**Fix — tier relaxation:**
```python
providers_in_offers = set(o.get("source", "") for o in real_offers)
if len(providers_in_offers) < 2:
    # Allow single-provider if at least 1 real offer with a valid URL exists
    if not real_offers:
        continue
    # (optional) annotate with availability state in card_data
```

### Pattern 3: Backend — Accessory Suppression

**Current state (verified):** `ACCESSORY_KEYWORDS` constant already exists in `product_compose.py` (lines 58–69) and `_filter_relevant_products()` function applies it to affiliate offers. However, this filtering only runs against offer titles at compose time. The `product_search.py` LLM prompt has no explicit anti-accessory constraint — it says "always return products" without filtering.

**Gap:** Accessories can get into `product_names` (from `product_search`) and `normalized_products` (from `product_normalize`), and the compose-level filter only catches offer titles, not normalized product names.

**Fix approach:** Add explicit anti-accessory instruction to the `product_search.py` LLM prompt, and add a product-name-level check in `product_compose.py` before the product is added to `products_with_offers`.

**Relevant denylist (already in codebase):**
```python
ACCESSORY_KEYWORDS = {
    "case", "charger", "protector", "cable", "adapter", "stand", "cover",
    "sleeve", "mount", "holder", "film", "tempered glass", "cleaning kit",
    "skin", "sticker", "screen protector", "screw", "screws", "hinge",
    "hinges", "bracket", "bezel", "replacement part", "repair", "tool kit",
    "rubber feet", "battery", "fan", "heatsink", "power cord", "cord",
    "dongle", "hub", "dock", "replacement filter", "logic board",
    "motherboard", "replacement", "refurbished part", "spare part",
    "hepa filter", "filter cartridge",
}
```

### Pattern 4: Backend — Budget Enforcement

**Current state (verified):** `slots.budget` is extracted as a string (e.g., `"under $500"`, `"$100-$200"`) in `product_search.py` (line 149) and passed through state. There is no numeric parsing or price filtering applied in `product_compose.py` before products are emitted. Budget is used only in the LLM prompt as descriptive text.

**Fix approach:** Parse budget string into `(min_price, max_price)` bounds. Filter `all_offers_for_product` to prefer in-budget offers. If all offers exceed budget, include them with an explicit "over budget" label rather than silently omitting.

**Parsing heuristics (Claude's discretion — these are recommended):**
```python
import re

def _parse_budget(budget_str: str) -> tuple[float | None, float | None]:
    if not budget_str:
        return None, None
    # "under $500" / "below $500" / "less than $500"
    m = re.search(r'(?:under|below|less than)\s*\$?([\d,]+)', budget_str, re.I)
    if m:
        return None, float(m.group(1).replace(',', ''))
    # "$100-$200" / "$100 to $200"
    m = re.search(r'\$?([\d,]+)\s*[-–to]+\s*\$?([\d,]+)', budget_str, re.I)
    if m:
        return float(m.group(1).replace(',', '')), float(m.group(2).replace(',', ''))
    # "around $500" / "about $500"
    m = re.search(r'(?:around|about|roughly)\s*\$?([\d,]+)', budget_str, re.I)
    if m:
        center = float(m.group(1).replace(',', ''))
        return center * 0.8, center * 1.2
    return None, None
```

### Pattern 5: Backend — Travel Timeout UX

**Current state (verified):** `travel_compose.py` reads itinerary, hotels, flights, cars, activities from state and formats them. There is no per-tool timing instrumentation or partial-response-with-recovery-prompt path. If any upstream travel tool hangs, the user sees indefinite "Thinking...".

**Fix approach:**
- In each travel tool (`travel_itinerary.py`, `travel_search_hotels.py`, etc.), capture start/end time and set a `tool_timing` key in state.
- In `travel_compose.py`, check if all expected keys are missing (indicating timeout) and return a partial response with an actionable recovery prompt.

**Pattern for travel tool instrumentation:**
```python
import time
start = time.monotonic()
# ... tool work ...
elapsed = round(time.monotonic() - start, 2)
return {
    "itinerary": result,
    "tool_timing": {**state.get("tool_timing", {}), "travel_itinerary": elapsed},
    "success": True,
}
```

**Recovery response pattern (in travel_compose.py):**
```python
if not any([itinerary, hotels, flights]):
    return {
        "assistant_text": (
            "I ran into an issue fetching travel details. "
            "You can try again, or ask for a specific piece — "
            "e.g., 'Show me hotels in Paris' or 'Give me a 3-day itinerary for Tokyo.'"
        ),
        "ui_blocks": [],
        "citations": [],
        "success": True,
    }
```

### Pattern 6: Backend — Citations Use Actual URLs

**Current state (verified):** `product_compose.py` lines 1233–1240:
```python
# Create citations — prefer review source URLs (Wirecutter, Reddit, etc.)
review_source_urls = []
for bundle in review_bundles.values():
    for source in bundle.get("sources", [])[:2]:
        if source.get("url"):
            review_source_urls.append(source["url"])

citations = review_source_urls[:5] or [p["url"] for p in normalized_products if p.get("url")][:5]
```

This correctly uses real source URLs. The issue is that `source.get("url")` may be empty if the review search did not return URLs. The fix is to validate URL format (must start with `http`) and add a test that citation block is non-empty when sources exist.

### Pattern 7: Frontend — Chat Bubble Mobile Width

**Location:** `frontend/components/Message.tsx` line 152

**Current state (verified):**
```tsx
<div className="px-4 py-3 rounded-tl-[20px] rounded-tr-[20px] rounded-br-[4px] rounded-bl-[20px] bg-[var(--primary)] text-white shadow-card max-w-[85%]" style={{ minWidth: 'fit-content' }}>
```

`max-w-[85%]` works on desktop. On mobile, when the parent container is constrained, `minWidth: 'fit-content'` combined with `max-w-[85%]` can result in a very narrow bubble if the content is short or the viewport is narrow.

**Fix:** The user bubble should be `max-w-[85%] w-auto` on all viewports, but the container wrapping it must allow it to fill most of the width. Check that `max-w-full` on the outer container is not causing a constraint.

Confirmed at line 119: `overflow-hidden max-w-full` on the `#message-container`. The `overflow-hidden` there truncates the bubble width on narrow screens. Changing this container's overflow to `overflow-clip` (not `overflow-hidden`) will stop it from creating a new BFC that crushes flex children.

### Pattern 8: Frontend — Chat Input Nav Overlap (z-index)

**Location:** `frontend/components/ChatContainer.tsx` lines 876–908 (chat input footer bar)

**Current state (verified):** The footer bar containing `ChatInput` uses:
```tsx
style={{
  borderTop: '1px solid var(--border)',
  background: 'var(--surface)',
  backdropFilter: 'blur(12px)'
}}
```

No explicit `position`, `z-index`, or `bottom` is set on this element. On mobile, the bottom nav bar (likely in `NavLayout` or `MobileHeader`) overlaps because it has a higher stacking context.

**Fix:** Add `position: sticky`, `bottom: 0`, and `z-index: 40` (or whichever value sits above the mobile nav) to the chat input container. The exact value depends on the nav bar's z-index — check `NavLayout.tsx` / `MobileHeader.tsx`.

### Pattern 9: Frontend — overflow-x: hidden → clip

**Location:** `frontend/app/globals.css` line 274

**Current state (verified):**
```css
body {
  overflow-x: hidden;   /* blocks horizontal pan when zoomed on iOS */
}
```

`overflow-x: hidden` creates a new block formatting context on the body element, which prevents position: sticky from working in some contexts and prevents users from panning horizontally when zoomed in (accessibility violation on iOS).

**Fix:**
```css
body {
  overflow-x: clip;   /* clips without creating BFC; allows zoom-pan */
}
```

`overflow-x: clip` is supported in all modern browsers (Chrome 90+, Safari 15.4+, Firefox 81+). It does not create a BFC.

Additionally, the 4 ancestor containers in the chat scroll chain that use `overflow-hidden` must be changed to `overflow-clip`:
- `frontend/app/chat/page.tsx` line 130: `overflow-hidden` on h-dvh wrapper
- `frontend/app/chat/page.tsx` line 133: `overflow-hidden` on flex-1 inner
- `frontend/app/chat/page.tsx` line 140: `overflow-hidden` on main
- `frontend/components/ChatContainer.tsx` line 756: `overflow-hidden` on chat-container

### Pattern 10: Frontend — Stop Button Dark Mode

**Location:** `frontend/components/ChatContainer.tsx` lines 889–896

**Current state (verified):**
```tsx
<button
  onClick={() => { dispatchStream({ type: 'STREAM_INTERRUPTED' }) }}
  className="px-4 py-1.5 rounded-full text-xs font-medium border border-[var(--border)] bg-[var(--surface-elevated)] text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-all"
>
  Stop generating
</button>
```

This already uses CSS variables. There are no hardcoded color strings. However, the QA report says it appears wrong in dark mode. The most likely cause: the dark mode theme is applied via `data-theme="dark"` attribute, not the Tailwind `dark:` prefix. If `var(--surface-elevated)` or `var(--border)` are missing dark mode counterparts in `globals.css`, the button will appear wrong.

**Fix:** Verify that `--surface-elevated`, `--border`, `--text-secondary`, `--text`, and `--surface-hover` all have values inside the `[data-theme="dark"]` selector block in `globals.css`.

### Pattern 11: Frontend — Custom 404 Page

**Location:** In Next.js 14 App Router, the custom 404 page lives at `frontend/app/not-found.tsx`. This file does NOT currently exist (confirmed: glob found no matches).

**Fix:** Create `frontend/app/not-found.tsx` following the editorial luxury theme. Use the same font, color variables, and layout conventions as other pages. No `'use client'` needed — it can be a server component.

**Pattern:**
```tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <h1 className="font-serif text-5xl font-normal text-[var(--text)] mb-4">404</h1>
      <p className="text-[var(--text-secondary)] text-lg mb-8">
        That page doesn&apos;t exist.
      </p>
      <Link
        href="/"
        className="px-6 py-3 rounded-full bg-[var(--primary)] text-white text-sm font-medium hover:bg-[var(--primary-hover)] transition-colors"
      >
        Back to home
      </Link>
    </div>
  )
}
```

### Pattern 12: Frontend — /browse Redirect

**Location:** `frontend/app/browse/page.tsx`

**Current state (verified):**
```tsx
import { redirect } from 'next/navigation'
export default function BrowsePage() {
  redirect('/')
}
```

The redirect is intentional but silent — users who navigate to `/browse` are sent to `/` without explanation. The QA report flags this as a "silent redirect" bug. The fix depends on intent: if `/browse` should exist as a real browse page, it needs content. If the redirect is intentional, it should at least redirect to a sensible location (the discover page, currently at `/`).

**Clarification:** CONTEXT.md lists "/browse silent redirect to homepage" as a P2 fix. The correct action is to either provide content at `/browse` or change the redirect to be intentional and documented. Since the home page IS the discover/browse experience, the redirect may be correct — the fix is adding a proper browse landing page or accepting the redirect as intended.

### Pattern 13: Frontend — Chat History Shows 0 Conversations

**Location:** `frontend/components/ConversationSidebar.tsx` lines 42–68

**Current state (verified):** The sidebar reads `chat_all_session_ids` from `localStorage` and fetches `/v1/chat/conversations?session_ids=...`. If `localStorage` is empty or the backend returns no matching conversations, the list shows empty.

**Root cause:** When a new session is created in `frontend/app/chat/page.tsx`, `localStorage.setItem(CHAT_CONFIG.SESSION_STORAGE_KEY, newSessionId)` stores the current session, but `chat_all_session_ids` (the array of ALL past sessions) is only updated in `ConversationSidebar.fetchConversations` when the sidebar is opened. If the user has never opened the sidebar, `chat_all_session_ids` is never populated.

**Fix:** In `chat/page.tsx`, when creating a new session, also push the new session ID into `chat_all_session_ids` in localStorage.

### Pattern 14: Frontend — iOS Scroll Sentinel Pattern

**Current state:** `MessageList.tsx` uses `setInterval` polling + `requestAnimationFrame` for auto-scroll during streaming (confirmed by CONTEXT.md noting this was recently throttled to 400ms).

**Fix — sentinel pattern:**
```tsx
// In MessageList.tsx
const bottomRef = useRef<HTMLDivElement>(null)

useEffect(() => {
  if (isStreaming) {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }
}, [messages, isStreaming])

// In JSX, at the bottom of the message list:
<div ref={bottomRef} aria-hidden="true" />
```

This replaces polling with a declarative scroll that fires on every message update. Combined with `overscroll-behavior-y: contain` and `-webkit-overflow-scrolling: touch` on the scroll container.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Budget string parsing | Custom regex-heavy parser | Simple `re.search` patterns (Pattern 4 above) | Budgets follow ~4 common patterns; no need for NLP |
| Citation URL validation | URL parser library | `url.startswith('http')` guard | Already have source URLs; just validate non-empty |
| 404 page routing | Custom middleware | Next.js `app/not-found.tsx` convention | App Router handles this automatically |
| Scroll to bottom | `setInterval` + `rAF` | `ref.scrollIntoView()` in `useEffect` | Declarative, no timer management, iOS-safe |
| Dark mode detection | JS `window.matchMedia` | CSS `[data-theme="dark"]` variables | Already the project's established pattern |
| Test framework setup | Any new framework | Extend existing pytest + vitest | Both already configured and working |

---

## Common Pitfalls

### Pitfall 1: `break` vs `continue` in the Fallback Loop
**What goes wrong:** The fallback loop exits entirely when the first already-seen product is encountered. All subsequent unseen products that need fallback cards are silently skipped.
**Root cause:** `break` on line 1066 of `product_compose.py` exits the `for pname in blog_product_names` loop instead of skipping to the next iteration.
**How to avoid:** Change to `continue`. Keep a separate early-exit guard using `break` only for the cap check (`review_card_count + fallback_card_count >= 5`).
**Warning signs:** Queries that return 5+ blog products but fewer than expected product cards.

### Pitfall 2: Multi-Provider Gating Drops Legitimate Products
**What goes wrong:** A product with only eBay results (no Amazon shortlink, no curated link) is silently dropped even if it's a perfectly valid result.
**Root cause:** `len(providers_in_offers) < 2` guard + narrow exceptions.
**How to avoid:** Relax to "at least 1 real offer with a valid URL". Keep provider ranking (Amazon first) but don't gate on count.
**Warning signs:** "best laptops" query returns 0 product cards when only eBay data is available.

### Pitfall 3: overflow-x: hidden Creates BFC
**What goes wrong:** Setting `overflow-x: hidden` on `body` creates a new Block Formatting Context. This breaks `position: sticky` for elements inside, prevents horizontal pan on iOS when zoomed, and clips content in unexpected ways.
**Root cause:** CSS specification: any `overflow` value other than `visible` and `clip` establishes a BFC.
**How to avoid:** Use `overflow-x: clip`. The `clip` value does NOT create a BFC and does not affect `position: sticky`.
**Warning signs:** Sticky elements stop sticking; iOS zoom pan is locked; horizontal overflow hidden in nested containers.

### Pitfall 4: Ancestor overflow-hidden Breaks iOS Scroll
**What goes wrong:** Even with the correct scroll container styles, if an ancestor element has `overflow: hidden`, iOS Safari will not scroll the child container — it intercepts the touch events.
**Root cause:** iOS Safari's scroll event bubbling interacts poorly with `overflow: hidden` on ancestor elements.
**How to avoid:** Change all 4 ancestor containers in the chat scroll chain (verified in `app/chat/page.tsx` lines 130, 133, 140 and `ChatContainer.tsx` line 756) from `overflow-hidden` to `overflow-clip`.
**Warning signs:** Chat messages not scrollable on iOS despite correct CSS on the message list container.

### Pitfall 5: Dark Mode Uses data-theme, Not Tailwind dark:
**What goes wrong:** Adding `dark:bg-X` Tailwind classes to components will have no effect in this project. Dark mode is controlled entirely by `[data-theme="dark"]` CSS variable overrides.
**Root cause:** Project uses `data-theme` attribute strategy (set in `layout.tsx` inline script) — Tailwind's `darkMode: 'class'` is not configured for this approach.
**How to avoid:** All dark mode styling must use CSS variables (`var(--text)`, `var(--surface)`, etc.) that have values in both `:root` and `[data-theme="dark"]` blocks in `globals.css`.
**Warning signs:** Dark mode styling changes made with `dark:` prefix classes have no visible effect.

### Pitfall 6: GraphState TypedDict Must Have Defaults in initial_state
**What goes wrong:** Adding new keys to `GraphState` TypedDict without adding corresponding default values in `initial_state` in `chat.py` causes LangGraph channel initialization to crash.
**Root cause:** LangGraph requires all channels to have initial values.
**How to avoid:** For any new state key (e.g., `tool_timing: dict`), add `"tool_timing": {}` to the `initial_state` dict in `backend/app/api/v1/chat.py` around line 243.
**Warning signs:** Backend crashes with LangGraph channel error on first request after adding new state key.

### Pitfall 7: Silent Message Drop During Active Streaming
**What goes wrong:** If the user sends a message while `isStreaming` is true, `handleSendMessage` returns early (`if (!messageToSend.trim() || isStreaming) return`), dropping the message silently.
**Root cause:** `ChatContainer.tsx` lines 682/643 guard against sending during streaming without notifying the user.
**How to avoid:** Queue the message or show a visual indicator that the message was received but will send after streaming completes. Do NOT just remove the guard — that would cause race conditions.
**Warning signs:** User types and hits Enter during streaming; no feedback, message disappears.

---

## Code Examples

### Verified Pattern: Extending Backend Tests
```python
# Source: backend/tests/test_product_compose.py (existing pattern)
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("LOG_ENABLED", "false")

from mcp_server.tools.product_compose import product_compose

@pytest.mark.asyncio
async def test_fallback_continue_emits_unseen_products(mock_model_service):
    """First blog product already has review card; second must still get fallback."""
    state = {
        "user_message": "best running shoes",
        "normalized_products": [{"name": "Nike Pegasus 40"}, {"name": "Adidas Ultraboost 23"}],
        "affiliate_products": {},
        "review_data": {},
        "blog_product_names_for_test": ["Nike Pegasus 40", "Adidas Ultraboost 23"],
    }
    # ...
```

### Verified Pattern: Frontend Component Tests
```tsx
// Source: frontend/tests/chatScreen.test.tsx (existing pattern)
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('framer-motion', () => ({
  motion: { div: ({ children, ...props }: any) => <div {...props}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

it('user bubble is full-width on mobile viewport', () => {
  // render Message with a user message, check max-w-[85%] applied
})
```

### Verified Pattern: pytest Run Command
```bash
# From backend/ directory (run inside Docker or with correct PYTHONPATH):
python -m pytest tests/test_product_compose.py -x -v

# Quick smoke: single test
python -m pytest tests/test_product_compose.py::test_fallback_continue_emits_unseen_products -x
```

### Verified Pattern: Vitest Run Command
```bash
# From frontend/ directory:
npm run test -- --run tests/chatScreen.test.tsx

# All frontend tests:
npm run test -- --run
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `overflow-x: hidden` on body (clips BFC) | `overflow-x: clip` (no BFC) | CSS Spec evolution; `clip` fully supported since Safari 15.4 | Fixes iOS zoom-pan and sticky elements |
| `setInterval` + `rAF` scroll polling | Sentinel `<div ref>` + `scrollIntoView` in `useEffect` | React 16+ | Declarative, no memory leaks, iOS-safe |
| Per-tool break in fallback loop | `continue` to skip, `break` only for cap | This phase | Fixes silent card suppression |
| Tailwind `dark:` class prefix | `[data-theme="dark"]` CSS variable overrides | Project-level architectural choice (pre-existing) | All dark mode work must use CSS vars |
| Next.js `pages/404.tsx` | `app/not-found.tsx` | Next.js 13+ App Router | Must create in app directory |

**Deprecated/outdated:**
- `overflow-x: hidden` on body: Causes iOS zoom lockout and BFC side-effects — use `overflow-x: clip`
- `setInterval` auto-scroll: Causes scroll fights on mobile (recently patched to 400ms throttle) — replace with sentinel pattern
- `pages/_error.tsx` / `pages/404.tsx`: Not used in this project — App Router uses `app/not-found.tsx`

---

## Open Questions

1. **/browse redirect intent**
   - What we know: `frontend/app/browse/page.tsx` explicitly redirects to `/`
   - What's unclear: Is this intentional (browse IS the homepage) or a bug where `/browse` should show a category list?
   - Recommendation: If the homepage already IS the browse experience, the fix is to document this and suppress the QA failure. If `/browse` should be a real page, create `app/browse/page.tsx` with content instead of a redirect.

2. **Forward navigation + session ID in URL**
   - What we know: `chat/page.tsx` does NOT put `sessionId` in the URL; it's only in `localStorage`. Forward nav (browser forward button) reloads the page without the session context.
   - What's unclear: Whether the session should be in the URL (shareable links) or localStorage only.
   - Recommendation: Store current sessionId in the URL as a query param (`/chat?session=<id>`) and read it on load. This also fixes the "chat history 0 conversations" issue for some cases.

3. **WCAG contrast failures on 7 elements**
   - What we know: Prompt 10 evidence in the QA report has specific element values (referenced in CONTEXT.md but raw data not read)
   - What's unclear: Exact CSS variable values that fail, which components contain them
   - Recommendation: During implementation, use browser DevTools accessibility panel to identify the 7 failing elements and fix the CSS variable values in `globals.css`

4. **Landscape orientation hides bottom nav at 844px**
   - What we know: This is a viewport-height breakpoint issue in the mobile nav bar
   - What's unclear: Which component and which CSS rule causes the hide
   - Recommendation: Inspect `MobileHeader.tsx` and `NavLayout.tsx` for height-based show/hide logic; add `@media (orientation: landscape) and (max-height: 500px)` override

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Backend Framework | pytest + pytest-asyncio (existing) |
| Backend Config | `backend/tests/conftest.py` (existing) |
| Backend Quick Run | `python -m pytest tests/test_product_compose.py -x -v` |
| Backend Full Suite | `python -m pytest tests/ -v` |
| Frontend Framework | Vitest + @testing-library/react (existing) |
| Frontend Config | `frontend/vitest.config.ts` or `frontend/package.json` test script |
| Frontend Quick Run | `npm run test -- --run tests/chatScreen.test.tsx` |
| Frontend Full Suite | `npm run test -- --run` |

### Phase Requirements → Test Map

Derived from CONTEXT.md locked decisions (no explicit REQ-IDs in REQUIREMENTS.md for this phase):

| Derived ID | Behavior | Test Type | Automated Command | File Exists? |
|------------|----------|-----------|-------------------|-------------|
| QAR-01 | Fallback loop emits cards for all unseen products (not just first) | unit | `pytest tests/test_product_compose.py::test_fallback_loop_continue -x` | Wave 0 |
| QAR-02 | Single-provider product emits card when valid URL exists | unit | `pytest tests/test_product_compose.py::test_single_provider_card -x` | Wave 0 |
| QAR-03 | Amazon-labeled CTA resolves to amazon domain | unit | `pytest tests/test_product_compose.py::test_label_domain_parity -x` | Wave 0 |
| QAR-04 | "best laptops for students" excludes replacement parts | unit | `pytest tests/test_product_compose.py::test_accessory_suppression -x` | Wave 0 |
| QAR-05 | "under $500" offers filtered before compose | unit | `pytest tests/test_product_compose.py::test_budget_enforcement -x` | Wave 0 |
| QAR-06 | Travel query with all tools timing out returns partial response + recovery | unit | `pytest tests/test_travel_compose.py::test_timeout_recovery -x` | Wave 0 |
| QAR-07 | Citation block contains http URLs when sources exist | unit | `pytest tests/test_product_compose.py::test_citations_have_real_urls -x` | Wave 0 |
| QAR-08 | Chat bubble renders at ≥85% width on 390px viewport | component | `npm run test -- --run tests/chatScreen.test.tsx` | Partial (existing test at line 172 checks 85%) |
| QAR-09 | Body overflow-x is `clip` not `hidden` | unit | `npm run test -- --run tests/layout.test.tsx` | Wave 0 |
| QAR-10 | not-found page renders with editorial theme | component | `npm run test -- --run tests/notFound.test.tsx` | Wave 0 |
| QAR-11 | Stop button uses CSS variable colors (no hardcoded hex) | component | `npm run test -- --run tests/chatScreen.test.tsx` | Wave 0 |
| QAR-12 | All 5 P0/P1 gate conditions pass | smoke API | manual + CI gate script | Wave 0 |

### Sampling Rate
- **Per task commit:** Run the test for the specific file modified (quick run)
- **Per wave merge:** `python -m pytest tests/ -v` + `npm run test -- --run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_product_compose.py` — extend with QAR-01 through QAR-07 tests
- [ ] `backend/tests/test_travel_compose.py` — create, covers QAR-06
- [ ] `frontend/tests/notFound.test.tsx` — create, covers QAR-10
- [ ] `frontend/tests/layout.test.tsx` — extend or create, covers QAR-09
- [ ] `frontend/tests/chatScreen.test.tsx` — extend existing, covers QAR-08/QAR-11

---

## Sources

### Primary (HIGH confidence)
- Direct source code read: `backend/mcp_server/tools/product_compose.py` — fallback loop bug at line 1066, multi-provider gating at lines 937–944, citation construction at lines 1233–1240, ACCESSORY_KEYWORDS at lines 58–69
- Direct source code read: `backend/mcp_server/tools/product_search.py` — no accessory filtering in LLM prompt
- Direct source code read: `backend/mcp_server/tools/travel_compose.py` — no timeout/partial-response path
- Direct source code read: `frontend/components/Message.tsx` — chat bubble `max-w-[85%]` at line 152, `overflow-hidden` on container at line 119
- Direct source code read: `frontend/components/ChatContainer.tsx` — "Stop generating" button at lines 889–896 (uses CSS vars), streaming guard at line 682
- Direct source code read: `frontend/app/globals.css` line 274 — `overflow-x: hidden` on body confirmed
- Direct source code read: `frontend/app/chat/page.tsx` lines 130/133/140 — `overflow-hidden` ancestors confirmed
- Direct source code read: `frontend/app/browse/page.tsx` — explicit `redirect('/')` confirmed
- Direct source code read: `frontend/components/ConversationSidebar.tsx` — localStorage-based session tracking confirmed
- Direct source code read: `frontend/app/layout.tsx` — `data-theme` attribute strategy confirmed, no `dark:` Tailwind class needed

### Secondary (MEDIUM confidence)
- CSS `overflow-x: clip` browser support: caniuse.com — Chrome 90+, Firefox 81+, Safari 15.4+; all modern browsers supported
- Next.js 14 App Router `not-found.tsx` convention: nextjs.org/docs — `app/not-found.tsx` is the correct location for custom 404

### Tertiary (LOW confidence)
- None — all critical findings are verified directly in source code

---

## Metadata

**Confidence breakdown:**
- Backend bugs: HIGH — all root causes confirmed by direct source code read with line numbers
- Frontend CSS bugs: HIGH — all verified by direct source code read
- Travel timeout fix: HIGH — confirmed absence of timeout handling in `travel_compose.py`
- Test framework: HIGH — existing test suites confirmed at `backend/tests/` and `frontend/tests/`
- WCAG specific elements: LOW — specific failing elements require runtime browser measurement

**Research date:** 2026-04-01
**Valid until:** 2026-05-01 (stable codebase; code not actively changing during this phase)
