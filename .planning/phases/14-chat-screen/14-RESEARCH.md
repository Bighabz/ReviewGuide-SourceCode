# Phase 14: Chat Screen - Research

**Researched:** 2026-03-17
**Domain:** React/Next.js chat UI — message bubbles, streaming status, inline product cards, source citations, suggestion chips; Python/FastAPI backend — review_sources bug fix in product_compose.py
**Confidence:** HIGH (all findings verified against actual codebase)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Message bubble styling**
- User bubbles: right-aligned, bg var(--primary) (#1B4DFF), white text, DM Sans Regular 15px
- User bubble corners: asymmetric — 20px top-left, 20px top-right, 4px bottom-right, 20px bottom-left (iMessage-style tail)
- User bubble max-width: 80% of chat area, padding 12px 16px
- AI bubbles: left-aligned, bg var(--surface-elevated) (#FFFFFF), border 1px solid var(--border), text var(--text)
- AI bubble corners: asymmetric — 4px top-left, 20px top-right, 20px bottom-right, 20px bottom-left
- AI bubble max-width: 85% of chat area, padding 16px
- "✦ ReviewGuide" label on EVERY AI message — DM Sans SemiBold 12px, var(--primary). Consistent, no message-type detection needed.
- All ui_blocks (product cards, source citations, itineraries) render INSIDE the white AI bubble — content is visually grouped within the bubble container

**Compact inline product cards**
- New `inline_product_card` block type added to BlockRegistry — existing `product_cards` and `product_carousel` remain for backward compat
- Card height: 64px, horizontal layout, full width of bubble
- Left: product image (64x64, square, 8px radius) — use curated Amazon image if match found, generic category placeholder if not
- Center: rank number + product name (SemiBold 14px) + one-line "why" (Regular 12px, var(--text-secondary))
- Right: price (SemiBold 16px) + "Buy on Amazon" link in var(--primary)
- Rank badges by position: #1 = "Top Pick", #2 = "Best Value", #3 = "Premium"
- Rank data derived from product position in response (position 1→Top Pick, 2→Best Value, 3→Premium)
- Cards separated by thin 1px var(--border) divider
- Affiliate links: curated data first, Amazon search URL fallback (`https://amazon.com/s?k=<product+name>&tag=<affiliate-id>`)
- Products without curated images get a generic category-themed placeholder — never show broken image icons

**Chat header status line**
- MobileHeader enhanced: dynamic title + status line below
- Title: first user message in session, truncated to ~30 chars. "New Research" for fresh sessions with no messages yet.
- Status line: DM Sans Regular 12px, var(--text-secondary). Shows "Researching • 4 sources analyzed" during streaming, disappears when done.
- Expand icon (↗) on the right side of header — placeholder for Phase 15. Non-functional (navigates to # or shows tooltip).
- Status data flow: Claude's discretion (React context, custom event, or prop drilling)

**Source citations**
- Fix the review_sources backend bug (broken after product_compose refactor at bd4b5c3) — trace and restore source URL threading so real review URLs reach the frontend
- Source citations section: "Sources" header in DM Sans SemiBold 12px, var(--text-secondary)
- Colored dots by position: source 1 = red, source 2 = blue, source 3 = green, source 4 = orange. Dynamic assignment, no per-source mapping table.
- Each citation: colored dot + source name + article title (truncated) + external link icon
- Clickable — opens original review URL in new tab
- 3-4 sources visible, "+X more" expander if additional sources exist

**Follow-up suggestion chips**
- Restyle existing `next_suggestions` chips to match spec
- Pill shape: var(--primary) border, var(--primary) text, transparent background
- 20px corner radius, 8px 16px padding, DM Sans Medium 13px
- Horizontal scrollable row below AI message (outside the bubble)
- Existing `sendSuggestion` custom event click behavior stays unchanged

### Claude's Discretion
- Status data flow mechanism (context vs custom event vs prop drilling)
- Exact review_sources bug fix approach (trace the broken threading)
- Loading/typing state animation style (shimmer vs pulse)
- Compact card image placeholder design
- Source citation "+X more" expander interaction
- Whether to add a new `inline_product_card` ui_block type to backend or handle frontend-only via normalizeBlocks

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CHAT-01 | AI responses follow structured format: summary → ranked inline product cards → source citations → follow-up chips | Message.tsx already renders in this order; need bubble wrapper and new inline_product_card block type |
| CHAT-02 | Inline product cards are compact (64px height) with image, rank, name, price, and affiliate link | New InlineProductCard component + BlockRegistry registration; curatedLinks.ts provides image/price data |
| CHAT-03 | Chat header shows real-time status ("Researching • 4 sources analyzed") during streaming | MobileHeader needs dynamic title + status; statusText already flows through ChatContainer → Message |
| CHAT-04 | Source citations are clickable links to actual review article URLs from search results | review_sources bug in product_compose.py confirmed: block was removed in bd4b5c3 refactor; must be restored |
| CHAT-05 | User message bubbles are right-aligned blue, AI bubbles are left-aligned white with "✦ ReviewGuide" label | Message.tsx bubble wrapper needs redesign — current partial implementation exists, needs full iMessage-style treatment |
| CHAT-06 | Follow-up suggestion chips appear below AI responses and auto-submit on tap | Chips work functionally; need restyle to pill shape with var(--primary) border, outside the bubble |
</phase_requirements>

---

## Summary

Phase 14 is a UI polish and backend bug-fix phase. The frontend work is contained to four files: `Message.tsx` (bubble wrapper + chip restyle), `MobileHeader.tsx` (dynamic title + status line), `BlockRegistry.tsx` (new `inline_product_card` renderer), and a new `InlineProductCard.tsx` component. The backend work is a single targeted fix in `product_compose.py` to restore the `review_sources` UI block that was deleted in commit bd4b5c3.

The current code already has the structural plumbing in place: `statusText` flows from `ChatContainer` through `Message` for the thinking indicator; `normalizeBlocks` canonicalizes block types; `sendSuggestion` CustomEvent handles chip dispatch. Phase 14 layers polish on top of this infrastructure rather than replacing it.

The most technically novel piece is the status data flow from `ChatContainer` (which owns `isStreaming` and `statusText`) to `MobileHeader` (which is rendered by `NavLayout`, a sibling of the chat page's `<main>`). These components share no direct parent-child relationship — they are siblings under `NavLayout`. The recommended solution is a React Context (`ChatStatusContext`) created in `NavLayout` and consumed by both the chat page and `MobileHeader`.

**Primary recommendation:** Fix review_sources backend first (Wave 0), then build InlineProductCard and bubble wrappers (Wave 1), then wire status to MobileHeader (Wave 2), then restyle chips (Wave 3).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 18 | Component tree | Project standard |
| Next.js | 14 | App router, SSR | Project standard |
| TypeScript | 5 | Type safety | Project standard |
| Tailwind CSS | 3 | Utility classes | Project standard — use via CSS vars only |
| Framer Motion | 11 | Animations (existing) | Already in use for message entry |
| lucide-react | Latest | Icons (ExternalLink, ChevronDown) | Already in use throughout |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `curatedLinks.ts` | Static | Amazon product images/prices/URLs | Lookup by product name for inline cards |
| React Context API | Built-in | Cross-tree state sharing | Status propagation from ChatContainer to MobileHeader |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| React Context for status | Custom event `chatStatus` | Events are simpler but fire-and-forget — Context lets MobileHeader re-render reactively |
| React Context for status | Prop drilling through NavLayout | Would require NavLayout to manage chat state — violates separation of concerns |
| React Context for status | Zustand/Redux | Overkill for two consumers sharing one string value |

**Installation:** No new packages required. All libraries already installed.

---

## Architecture Patterns

### Recommended Project Structure

No new directories needed. New files fit into existing structure:

```
frontend/
├── components/
│   ├── InlineProductCard.tsx        # NEW: 64px compact product row
│   ├── SourceCitations.tsx          # NEW: colored-dot citation list
│   ├── Message.tsx                  # MODIFY: add bubble wrappers, chip restyle
│   ├── MobileHeader.tsx             # MODIFY: dynamic title + status line
│   └── blocks/
│       └── BlockRegistry.tsx        # MODIFY: register inline_product_card
├── lib/
│   ├── normalizeBlocks.ts           # MODIFY: map inline_product_card type
│   └── chatStatusContext.tsx        # NEW: React Context for streaming status
└── app/
    └── chat/
        └── page.tsx                 # MODIFY: wrap in ChatStatusProvider
backend/
└── mcp_server/tools/
    └── product_compose.py           # MODIFY: restore review_sources block
```

### Pattern 1: Bubble Wrapper in Message.tsx

**What:** Wrap AI message content in a white rounded container with "✦ ReviewGuide" byline. Wrap user message in right-aligned blue bubble with iMessage-tail corners.

**When to use:** Every message render in `Message.tsx`.

**Key insight from current code:** The current Message.tsx at line 151-164 has a partial bubble for user messages (`rounded-2xl rounded-tr-md bg-[var(--primary)]`). The AI side has no bubble — content renders directly. Phase 14 adds the full bubble treatment to both.

**Critical constraint:** `ui_blocks` rendering (`<UIBlocks>`) and `next_suggestions` chips MUST remain in their current order (lines 201-281 of Message.tsx). The bubble wrapper goes AROUND the content — do not restructure the rendering order.

```typescript
// Source: Message.tsx current structure (lines 172-311)
// AI message bubble — wrap existing content, do not reorder internals
<div
  className="rounded-tl-[4px] rounded-tr-[20px] rounded-br-[20px] rounded-bl-[20px] border border-[var(--border)] p-4"
  style={{ background: 'var(--surface-elevated)', maxWidth: '85%' }}
>
  {/* "✦ ReviewGuide" byline — top of every AI bubble */}
  <div className="text-[12px] font-semibold text-[var(--primary)] mb-2 font-sans">
    ✦ ReviewGuide
  </div>
  {/* ...existing content (statusText, message.content, UIBlocks)... */}
</div>
{/* Chips OUTSIDE the bubble — horizontal scroll row */}
{message.next_suggestions && ...}
```

### Pattern 2: InlineProductCard Component

**What:** A 64px horizontal row showing rank badge, image, name, price, affiliate link. Registered in `BlockRegistry` under `inline_product_card` type.

**When to use:** When `product_compose.py` emits a `product_cards` block — normalizeBlocks will map this to `inline_product_card` OR the backend emits it directly.

**Decision (Claude's discretion):** Handle frontend-only via `normalizeBlocks.ts`. Map `product_cards` type to `inline_product_card` in the `BLOCK_TYPE_MAP`. This avoids any backend changes for the card format. The existing `product_cards` and `carousel` types remain for backward compat (old sessions in localStorage).

```typescript
// Source: normalizeBlocks.ts pattern
const BLOCK_TYPE_MAP: Record<string, string> = {
  // ...existing mappings...
  product_cards: 'inline_product_card',  // Remap to compact format
}
// Keep 'carousel' and 'products' types as-is for backward compat
```

**Curated lookup:** `curatedLinks.ts` exports `CuratedCategory` keyed by category → topics → products (ASIN + URL). For inline cards, match by product name against curated topic titles using fuzzy substring match. Fall back to Amazon search URL `https://www.amazon.com/s?k=${encodeURIComponent(name)}` if no match.

### Pattern 3: ChatStatusContext for MobileHeader Status

**What:** React Context that carries `{ isStreaming: boolean, statusText: string, sessionTitle: string }` from `ChatContainer` to `MobileHeader` across the NavLayout component tree.

**Why this pattern:** `ChatContainer` is rendered inside `<main>` in `chat/page.tsx`. `MobileHeader` is rendered in `NavLayout` as a sibling of `<main>`. They share no props. A context provider wrapping the whole layout at `layout.tsx` or at `NavLayout` level allows both to read/write the same state.

**Implementation approach:**
1. Create `lib/chatStatusContext.tsx` with `ChatStatusContext` and `ChatStatusProvider`
2. Wrap `NavLayout`'s root `<div>` with `<ChatStatusProvider>` (or add the provider in `app/layout.tsx`)
3. `ChatContainer` calls `useChatStatus().setStatus(...)` during streaming
4. `MobileHeader` calls `useChatStatus()` to read `isStreaming`, `statusText`, `sessionTitle`

```typescript
// Source: React Context API pattern (standard, no library needed)
// frontend/lib/chatStatusContext.tsx
'use client'
import { createContext, useContext, useState } from 'react'

interface ChatStatus {
  isStreaming: boolean
  statusText: string
  sessionTitle: string
  setIsStreaming: (v: boolean) => void
  setStatusText: (v: string) => void
  setSessionTitle: (v: string) => void
}

const ChatStatusContext = createContext<ChatStatus>({...defaults})
export function ChatStatusProvider({ children }) { ... }
export const useChatStatus = () => useContext(ChatStatusContext)
```

**Alternative (simpler, less elegant):** Use a module-level custom event:
```typescript
// ChatContainer fires:
window.dispatchEvent(new CustomEvent('chatStatus', { detail: { isStreaming, statusText } }))
// MobileHeader listens:
window.addEventListener('chatStatus', handler)
```
This works but requires useEffect cleanup and is fire-and-forget — the header won't pick up current state on mount. Context is preferred.

### Pattern 4: review_sources Bug Fix in product_compose.py

**Root cause confirmed:** Commit `bd4b5c3` ("refactor: rewrite product_compose Phase 4 for blog-style output") explicitly deleted the `review_sources` UI block construction. The git diff shows the removed code built a `review_sources` block from `review_bundles` with source URLs including `site_name`, `url`, `title`, `snippet`, `rating`, `favicon_url`, `date`.

**The data exists:** `review_data` (product_name → ReviewBundle) and `review_bundles` are still populated in the current code (lines 285, 460 of product_compose.py). The sources list with URLs is at `bundle.get("sources", [])` — each source has `site_name`, `url`, `title`, `snippet`.

**Fix strategy:** Restore the `review_sources` block construction AFTER the blog article is built (not replacing it). The block runs alongside `assistant_text`, not instead of it.

```python
# Source: product_compose.py — restore after line ~960 (after citations are built)
# This is the code deleted in bd4b5c3, adapted to current variable names:
if review_data and review_bundles:
    review_products = []
    for product_name, bundle in review_bundles.items():
        consensus = _get_result(f'consensus:{product_name}', '')
        review_products.append({
            "name": product_name,
            "avg_rating": bundle.get("avg_rating", 0),
            "total_reviews": bundle.get("total_reviews", 0),
            "consensus": consensus,
            "editorial_label": editorial_labels.get(product_name),
            "sources": [
                {
                    "site_name": s.get("site_name", ""),
                    "url": s.get("url", ""),
                    "title": s.get("title", ""),
                    "snippet": s.get("snippet", ""),
                    "rating": s.get("rating"),
                    "favicon_url": s.get("favicon_url", ""),
                    "date": s.get("date"),
                }
                for s in bundle.get("sources", [])[:6]
            ],
        })
    if review_products:
        ui_blocks.append({
            "type": "review_sources",
            "title": "Sources",
            "data": {"products": review_products}
        })
```

**New frontend SourceCitations component:** The existing `ReviewSources.tsx` renders product-centric cards with star ratings and consensus text — this is too heavy for the Phase 14 spec. Phase 14 needs a lighter `SourceCitations.tsx` that renders a flat list of colored-dot citations from all sources across all products, not nested by product. Register both in BlockRegistry — `review_sources` maps to the new `SourceCitations` component.

### Anti-Patterns to Avoid

- **Modifying streaming logic in ChatContainer.tsx**: The `streamChat` callback chain is fragile — do not add status-setting logic inside `onToken` directly. Use the existing `isThinking`/`statusText` fields on the message, or emit a side-channel context update from outside the callback.
- **Reordering ui_blocks rendering in Message.tsx**: The `UIBlocks` component must stay in its current position (after `message.content`, before chips). Only add the bubble wrapper around it — never reorder.
- **Using `Math.random()` in SSR**: Rank badge text is deterministic (derived from array index), so this is not a risk here.
- **Modifying the `sendSuggestion` CustomEvent dispatch**: The existing chip click handler is a project invariant. Restyle only — never change the onClick logic.
- **Adding `dark:` Tailwind utilities**: This project uses `data-theme` attribute strategy. All colors must use `var(--*)` CSS variables.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Product name → image matching | Custom fuzzy search | Substring match on curatedLinks.ts topic titles | Static data is already keyed by topic; fuzzy match is sufficient for 120+ products |
| State sharing across component tree | Event bus or global var | React Context API | React's built-in solution, proper re-render lifecycle, SSR safe |
| Colored dot generation | Manual color array with per-source mapping | Positional index mod 4 | Spec says "dynamic assignment" — `['red','blue','green','orange'][index % 4]` is the entire implementation |
| Source URL extraction | Re-scraping or re-fetching | review_data already has sources with URLs from SerpAPI | Data exists in GraphState, just needs to be passed through to ui_blocks |

---

## Common Pitfalls

### Pitfall 1: Breaking Backward-Compat for Existing Messages

**What goes wrong:** If `normalizeBlocks.ts` remaps `product_cards` → `inline_product_card` globally, any messages loaded from localStorage or the database that were saved with the old `ProductCards` component's expected data shape may render incorrectly.

**Why it happens:** `normalizeBlocks` runs on every message load, including history. Old `product_cards` blocks have a `products: []` data shape; new `inline_product_card` must handle the same shape.

**How to avoid:** Make `InlineProductCard` read from `(b.data as any)?.products ?? []` — the same data shape that `ProductCards` already uses. The shapes are compatible.

**Warning signs:** Product cards appear empty or throw TypeErrors when loading old chat sessions.

### Pitfall 2: MobileHeader Status State on Mount

**What goes wrong:** When the user navigates back to `/chat` mid-session, `MobileHeader` mounts fresh but `ChatContainer` is already done streaming. The header shows "New Research" instead of the session title.

**Why it happens:** If status is propagated via CustomEvents (fire-and-forget), a component that mounts after events were fired gets no catch-up state.

**How to avoid:** Use React Context (stored state) rather than events. On `ChatContainer` mount, read session title from the first user message in `messages` and update context immediately.

**Warning signs:** Header shows "New Research" even for sessions with existing messages.

### Pitfall 3: review_sources Block Breaking Existing blog-style assistant_text

**What goes wrong:** The restored `review_sources` block appears alongside the blog-style markdown `assistant_text`. This may cause duplication — product names and sources appear in both the markdown text and the citation block.

**Why it happens:** The bd4b5c3 refactor intentionally removed the block to avoid redundancy with the blog article. Restoring it risks that.

**How to avoid:** The new `SourceCitations` component should render a FLAT citation list (just source names + URLs) rather than full product-centric cards with consensus text. This is complementary to the blog text, not redundant. The `ReviewSources` component rendered product cards — `SourceCitations` renders only the source links.

**Warning signs:** Source names and snippets appear twice (once in the markdown, once in the block).

### Pitfall 4: 64px Card Height Not Respected

**What goes wrong:** The InlineProductCard exceeds 64px when product names are long or when the "why" text wraps.

**Why it happens:** `h-16` in Tailwind is 64px, but only constrains the container — internal text can overflow if not clipped.

**How to avoid:** Use `h-16 overflow-hidden` on the card container and `truncate` (text-overflow: ellipsis, no-wrap) on both the product name and "why" lines. Use `flex-shrink-0` on the image div.

**Warning signs:** Cards appear taller than others when product names are long.

### Pitfall 5: Image Load Errors Showing Broken Icon

**What goes wrong:** Amazon images 404 or are blocked by CORS, showing the browser's broken image icon.

**Why it happens:** Amazon image URLs can expire or have referrer restrictions.

**How to avoid:** Add `onError={(e) => { e.currentTarget.style.display='none'; /* show placeholder div */ }}` on the `<img>` tag, or use a fallback `<div>` with a category-themed background color/icon.

**Warning signs:** Broken image icons in product cards during review.

---

## Code Examples

Verified patterns from codebase:

### Existing statusText flow (ChatContainer.tsx lines 411-414)
```typescript
// Source: ChatContainer.tsx onToken callback
msg.id === currentMessageIdRef.current
  ? isPlaceholder
    ? { ...msg, isThinking: true, statusText: token }  // status text stored on message
    : { ...msg, content: msg.content + token, isThinking: false, statusText: undefined }
  : msg
```

### Existing chip dispatch (Message.tsx lines 253-257)
```typescript
// Source: Message.tsx — DO NOT CHANGE THIS PATTERN
onClick={() => {
  trackSuggestionClick(suggestion, message.id, idx)
  const event = new CustomEvent('sendSuggestion', {
    detail: { question: suggestion.question }
  })
  window.dispatchEvent(event)
}}
```

### Existing block registration pattern (BlockRegistry.tsx)
```typescript
// Source: BlockRegistry.tsx lines 31-117
const BLOCK_RENDERERS: Record<string, BlockRenderer> = {
  // ...
  review_sources: (b) => (
    <ReviewSources data={(b.data as any) ?? { products: [] }} title={b.title} />
  ),
  // Add new type:
  inline_product_card: (b) => (
    <InlineProductCard products={(b.data as any)?.products ?? []} />
  ),
}
```

### Curated product lookup pattern
```typescript
// Source: curatedLinks.ts structure — lookup by iterating topics
import { curatedLinks } from '@/lib/curatedLinks'

function findCuratedProduct(productName: string): { imageUrl?: string; affiliateUrl?: string } {
  const lowerName = productName.toLowerCase()
  for (const category of Object.values(curatedLinks)) {
    for (const topic of category) {
      if (topic.title.toLowerCase().includes(lowerName) ||
          lowerName.includes(topic.title.toLowerCase().split(' ').slice(1).join(' '))) {
        const first = topic.products[0]
        return {
          imageUrl: `https://images-na.ssl-images-amazon.com/images/I/${first.asin}._SL300_.jpg`,
          affiliateUrl: first.url,
        }
      }
    }
  }
  return {}
}
```

### Existing MobileHeader structure (MobileHeader.tsx lines 19-83)
```typescript
// Source: MobileHeader.tsx — current chat route section (lines 27-48)
// Phase 14 replaces the static "Research Session" span with dynamic title + status
{isChatRoute ? (
  <>
    <button onClick={() => router.push('/browse')} ...><ArrowLeft /></button>
    <span className="flex-1 text-center text-sm font-medium truncate px-2">
      Research Session  {/* Replace with dynamic title from context */}
    </span>
    <div className="w-8" />  {/* Replace with ↗ expand placeholder */}
  </>
) : ...}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `review_sources` UI block + short assistant_text | Blog-style markdown `assistant_text` only | bd4b5c3 (2026-03-10) | Source URLs no longer reach frontend — Phase 14 fixes this |
| Flat message rendering (no bubbles) | Partial bubble on user messages only | Current state | Phase 14 adds full iMessage-style treatment |
| Vertical chip list with category labels | Horizontal pill-style chip row | Phase 14 change | More mobile-friendly, consistent with spec |

---

## Open Questions

1. **Where to provision the ChatStatusProvider**
   - What we know: `NavLayout` renders both `MobileHeader` and `<main>` (which contains the chat page). Provider can live in `NavLayout` or `app/layout.tsx`.
   - What's unclear: Putting it in `NavLayout` means every page gets the provider (minor overhead). Putting it in `app/layout.tsx` is slightly broader but cleaner.
   - Recommendation: Put `ChatStatusProvider` inside `NavLayout` — it only makes sense for nav-wrapped pages and keeps the chat concern co-located with the nav components that consume it.

2. **Backend inline_product_card vs frontend normalizeBlocks mapping**
   - What we know: CONTEXT.md marks this as Claude's discretion. The `product_cards` block already exists in backend output.
   - What's unclear: Whether future phases will need distinct backend `inline_product_card` semantics.
   - Recommendation: Frontend-only mapping in `normalizeBlocks.ts` for Phase 14. Add `product_cards: 'inline_product_card'` to `BLOCK_TYPE_MAP`. This avoids any backend deployment risk and can be promoted to a backend type later if needed.

3. **review_sources and ChatContainer's `saveRecentSearch` logic**
   - What we know: ChatContainer.tsx line 503 saves to recent searches when `product_cards`, `ebay_products`, or `amazon_products` blocks are found. `review_sources` is not in this check.
   - What's unclear: Should `review_sources` also trigger `saveRecentSearch`?
   - Recommendation: No change needed. `review_sources` is supplementary metadata; the product carousel blocks already trigger the save.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 2.x with jsdom |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test:run -- tests/chatScreen.test.tsx` |
| Full suite command | `cd frontend && npm run test:run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CHAT-01 | AI response renders in order: summary text first, then ui_blocks, then chips | unit | `npm run test:run -- tests/chatScreen.test.tsx` | Wave 0 |
| CHAT-02 | InlineProductCard renders at 64px height with image, rank, name, price, link | unit | `npm run test:run -- tests/inlineProductCard.test.tsx` | Wave 0 |
| CHAT-03 | MobileHeader shows status text during streaming, clears when done | unit | `npm run test:run -- tests/chatScreen.test.tsx` | Wave 0 |
| CHAT-04 | SourceCitations renders source URLs as clickable links with target="_blank" | unit | `npm run test:run -- tests/sourceCitations.test.tsx` | Wave 0 |
| CHAT-05 | User bubble is right-aligned; AI bubble is left-aligned with "✦ ReviewGuide" label | unit | `npm run test:run -- tests/chatScreen.test.tsx` | Wave 0 |
| CHAT-06 | Chip renders with pill styling; click fires sendSuggestion CustomEvent | unit | Existing: `npm run test:run -- tests/suggestions.test.tsx` (restyle only — no logic change) | Exists (partial) |

### Sampling Rate

- **Per task commit:** `cd frontend && npm run test:run -- tests/chatScreen.test.tsx tests/inlineProductCard.test.tsx tests/sourceCitations.test.tsx`
- **Per wave merge:** `cd frontend && npm run test:run`
- **Phase gate:** Full suite green (172+ passing) before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/tests/chatScreen.test.tsx` — covers CHAT-01, CHAT-03, CHAT-05 (bubble alignment, bubble label, render order, status display)
- [ ] `frontend/tests/inlineProductCard.test.tsx` — covers CHAT-02 (card height constraint, rank badges, image fallback, affiliate link)
- [ ] `frontend/tests/sourceCitations.test.tsx` — covers CHAT-04 (citation links have href and target="_blank", colored dots by position, "+X more" toggle)

*(CHAT-06 is already partially covered by `tests/suggestions.test.tsx` — chip click dispatch is tested; the restyle is visual and only needs manual verification)*

---

## Sources

### Primary (HIGH confidence)

- `frontend/components/Message.tsx` — full source read; current bubble structure, statusText/isThinking flow, UIBlocks integration, chip dispatch
- `frontend/components/ChatContainer.tsx` — full source read; SSE streaming, statusText propagation, message state management
- `frontend/components/blocks/BlockRegistry.tsx` — full source read; all registered block types and renderers
- `frontend/lib/normalizeBlocks.ts` — full source read; BLOCK_TYPE_MAP and normalization logic
- `frontend/components/MobileHeader.tsx` — full source read; current static "Research Session" title, isChatRoute check
- `frontend/components/NavLayout.tsx` — full source read; component tree structure, MobileHeader placement
- `frontend/components/ReviewSources.tsx` — full source read; existing source display component (too heavy for Phase 14 spec)
- `backend/mcp_server/tools/product_compose.py` — partial read (lines 450-1024); review_sources deletion confirmed
- `backend/app/schemas/graph_state.py` — full source read; review_data, review_bundles, ui_blocks fields confirmed present
- `frontend/lib/curatedLinks.ts` — structure read; ASIN + URL keyed by category/topic
- `frontend/app/chat/page.tsx` — full source read; ChatContainer props, session management
- `git show bd4b5c3` — diff confirmed exact lines deleted (review_sources block construction)
- `frontend/vitest.config.ts` — full source read; test framework confirmed as Vitest 2.x with jsdom

### Secondary (MEDIUM confidence)

- `.planning/phases/14-chat-screen/14-CONTEXT.md` — user decisions document; all design specs
- `.planning/REQUIREMENTS.md` — requirement definitions CHAT-01 through CHAT-06

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against package.json and existing codebase
- Architecture: HIGH — all patterns verified against actual component code
- Bug fix (review_sources): HIGH — root cause confirmed via git diff of bd4b5c3
- Pitfalls: HIGH — derived from direct code reading
- Test infrastructure: HIGH — vitest.config.ts and existing tests confirmed working

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable stack; no fast-moving dependencies)
