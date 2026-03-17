# Phase 15: Results Screen - Research

**Researched:** 2026-03-17
**Domain:** Next.js 14 dynamic routing, React component composition, localStorage data extraction, CSS Grid responsive layout
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Data source + URL scheme**
- Data sourced from localStorage — read the chat session's messages + ui_blocks using the session ID
- URL format: `/results/:sessionId` using the existing session UUID (e.g., `/results/a1b2c3d4-e5f6-...`)
- The expand icon (↗) in MobileHeader navigates to `/results/{currentSessionId}` — wire this in Phase 15 (was placeholder in Phase 14)
- If session not found in localStorage: redirect to `/` with a brief toast message "Session not found — start a new research"
- URL is "shareable" on the same browser only (localStorage limitation) — no backend persistence needed

**Product card grid**
- One `ResultsProductCard` component with responsive container
- Mobile: horizontal scroll container (flex-row, overflow-x-auto, snap-x), cards 170px wide, peek effect showing ~2.2 cards
- Desktop: CSS grid (grid-cols-3), cards ~200px wide, max-width 1200px content area
- Card design: 16px corner radius, 0.67px solid var(--border), white background, 12px internal padding
- Top section: 100px height, pastel background tints via new CSS variables (--card-accent-1 through --card-accent-4 with dark mode variants). Rank badge (24px black circle, white number). Centered product image (~64px, object-fit contain).
- Middle section: category badge (pill, colored bg — Top Pick = warm gold, Best Value = blue, Premium = purple), product name (SemiBold 14px, 2-line clamp), short description (Regular 11px, 2-line clamp), score bar (4px height, var(--primary) fill, score number right-aligned)
- Bottom section: price (Bold 18px) left, "Buy on Amazon" CTA button right (var(--primary) bg, white text, 8px radius, 36px height). If no affiliate link: muted "Check Amazon →" text link
- Score derivation: average review ratings if available, else position-based fallback (1st=95, 2nd=88, 3rd=82, 4th=76, 5th=70)
- Images: same curated Amazon lookup + category placeholder fallback as Phase 14 InlineProductCard

**Desktop layout + sidebar**
- Minimal left sidebar on desktop (320px): logo, current session title (active state), "Back to Chat" link. No conversation search, no history list.
- Sidebar hidden on mobile — back arrow in MobileHeader returns to chat
- Sidebar is part of the Results page component (not NavLayout) — implemented via CSS grid on desktop
- Sources section: inline below the header summary, above product grid. Collapsible on mobile (default expanded). Reuses SourceCitations component from Phase 14 with editorial "SOURCES ANALYZED" header styling.
- Results page renders inside NavLayout (gets MobileHeader + tab bar on mobile, UnifiedTopbar on desktop)

**Quick actions**
- Three actions: Compare side by side, Export to list, Share results
- Share: functional — copies current URL to clipboard via `navigator.clipboard.writeText()` with "Link copied!" toast
- Compare and Export: visual placeholders — show "Coming soon" toast on click
- No "Set price alert" button — requires accounts (out of v2.0 scope)
- "QUICK ACTIONS" editorial header (uppercase DM Sans Medium 11px, var(--text-muted), letter-spacing 1.5px)
- Each action: icon + label, 44px height, DM Sans Regular 14px

**Results header**
- Title: serif italic, 24px mobile / 28px desktop — derived from first user message (same as chat header title)
- Action buttons row below title: Share, Save (bookmark), Refresh — icon + label, spaced 24px
- Summary paragraph: 2-3 sentence synthesis mentioning number of sources in bold

### Claude's Discretion
- Exact pastel tint CSS variable values for dark mode
- Score bar animation/transition treatment
- Toast notification implementation (native vs component)
- How to extract product + source data from session messages/ui_blocks
- Results header summary text generation (from first AI response content)
- Horizontal scroll snap behavior details on mobile
- Whether to add follow-up chips at the bottom of Results (spec mentions them, but they may be deferred)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RES-01 | User can navigate to `/results/:id` to see full results for a completed research session | Next.js dynamic route `app/results/[id]/page.tsx`; localStorage read using CHAT_CONFIG.MESSAGES_STORAGE_KEY and CHAT_CONFIG.SESSION_STORAGE_KEY |
| RES-02 | Product cards display in 3-column grid on desktop, horizontal scroll on mobile | CSS grid-cols-3 on desktop; flex-row overflow-x-auto snap-x on mobile; single ResultsProductCard component |
| RES-03 | Product cards show real Amazon images, prices, and affiliate links from curated static data | lookupCuratedProduct() pattern from InlineProductCard.tsx; curatedLinks.ts with 120+ products via ASIN image URLs |
| RES-04 | Each product card shows rank badge, score bar, and CTA button | Rank badges extend InlineProductCard RANK_LABELS; score = position-based fallback or avg rating; score bar = 4px div width % |
| RES-05 | Quick actions panel shows: Compare side by side, Export to list, Share results | navigator.clipboard.writeText() for Share; "Coming soon" toast for Compare/Export |
| RES-06 | Sources section shows colored dots, source names, and clickable article links | SourceCitations component from Phase 14 — reuse directly with title="SOURCES ANALYZED" |
| RESP-01 | All screens render mobile-first single-column layout below 768px | NavLayout already provides MobileHeader + tab bar at <768px; Results page uses block layout below md: breakpoint |
| RESP-02 | Desktop layout (>=1024px) shows 3-column product grids, persistent sidebar, top nav, max 1200px content | CSS grid layout on lg: breakpoint; 320px sidebar + main content; max-w-[1200px] constraint |
</phase_requirements>

---

## Summary

Phase 15 builds a dedicated `/results/:sessionId` page that renders the "final output" of a research session. All data lives in localStorage — specifically the `chat_messages` key storing the array of Message objects, each of which can carry `ui_blocks` containing product and source data. The page reads this data client-side and renders an editorial-style results view.

The implementation is entirely frontend-only: one new dynamic route (`app/results/[id]/page.tsx`), two new components (`ResultsProductCard`, `ResultsQuickActions`), one new `ResultsHeader` component, and wiring edits to `MobileHeader.tsx`. The reuse story is strong: `SourceCitations` and the `lookupCuratedProduct()` / ASIN image pattern from `InlineProductCard` both transfer directly.

The key architectural challenge is data extraction: pulling product items and source citations from the heterogeneous `ui_blocks` array in stored messages. The existing `ui_blocks` typing in `Message` uses `any[]`, so a dedicated extractor utility is needed to walk the blocks and find `type: 'product_recommendations'` and `type: 'review_sources'` blocks.

**Primary recommendation:** Build a `extractResultsData(messages)` utility as the data layer, keep `ResultsProductCard` as a pure presentational component, and wire the route with a client-side `useEffect` that reads localStorage on mount.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 14.2.x | Dynamic routing (`app/results/[id]/page.tsx`) | Already in use; App Router dynamic segments |
| React | 18.2.x | Component model | Already in use |
| TypeScript | 5.3.x | Type safety | Already in use |
| Tailwind CSS | 3.3.x | Utility classes | Already in use; project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| framer-motion | 12.26.x | Score bar entrance animation, card fade-in | Optional micro-interaction polish |
| lucide-react | 0.294.x | Action icons (Share, Bookmark, RefreshCw, GitCompare, Download) | All icon needs |
| next/navigation | 14.2.x | `useRouter`, `useParams`, `usePathname` | Route navigation and params |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| localStorage data source | Backend API fetch | Backend requires no new endpoints; localStorage is the locked decision |
| Inline toast state | react-hot-toast library | Library adds bundle size; a simple 3-second state-driven toast is sufficient and aligns with project pattern |

**Installation:** No new packages required. All dependencies are already in `package.json`.

---

## Architecture Patterns

### Recommended Project Structure

```
frontend/
├── app/
│   └── results/
│       └── [id]/
│           └── page.tsx          # Dynamic route — 'use client', reads params + localStorage
├── components/
│   ├── ResultsProductCard.tsx    # New: large product card with rank badge + score bar
│   ├── ResultsQuickActions.tsx   # New: Compare / Export / Share actions panel
│   └── MobileHeader.tsx          # Edit: wire Maximize2 icon → /results/:sessionId
├── lib/
│   └── extractResultsData.ts     # New: utility to pull products+sources from messages
└── tests/
    └── resultsScreen.test.tsx    # New: RED tests for RES-01 through RES-06
```

### Pattern 1: Next.js App Router Dynamic Segment

**What:** `app/results/[id]/page.tsx` captures the session ID from the URL path.
**When to use:** Any shareable URL with a variable path segment.
**Example:**
```typescript
// app/results/[id]/page.tsx
'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { CHAT_CONFIG } from '@/lib/constants'

export default function ResultsPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  useEffect(() => {
    // localStorage only accessible after mount (client-side)
    const stored = localStorage.getItem(CHAT_CONFIG.MESSAGES_STORAGE_KEY)
    if (!stored) {
      // Session not found — redirect with toast state
      router.replace('/?toast=session-not-found')
      return
    }
    // parse and use...
  }, [sessionId, router])
}
```

### Pattern 2: localStorage Data Extraction

**What:** Walk the stored `Message[]` array to extract product and source blocks from `ui_blocks`.
**When to use:** Any component that needs to reconstitute research results from chat history.

The `ui_blocks` array in stored messages uses a `type` discriminant. Based on the existing block registry and Message type, product data lives in blocks with `type: 'product_recommendations'` and sources live in `type: 'review_sources'`.

```typescript
// lib/extractResultsData.ts
import type { Message } from '@/components/ChatContainer'

export interface ResultsData {
  sessionTitle: string       // First user message content
  summaryText: string        // First assistant message text content
  products: ProductItem[]    // Aggregated from all product_recommendations blocks
  sources: ReviewSourceItem[] // Aggregated + deduplicated from all review_sources blocks
}

export function extractResultsData(messages: Message[]): ResultsData {
  const userMessages = messages.filter(m => m.role === 'user')
  const aiMessages = messages.filter(m => m.role === 'assistant')

  const sessionTitle = userMessages[0]?.content ?? 'Research Results'
  const summaryText = aiMessages[0]?.content ?? ''

  const products: ProductItem[] = []
  const sources: ReviewSourceItem[] = []
  const seenSourceUrls = new Set<string>()

  for (const msg of aiMessages) {
    for (const block of (msg.ui_blocks ?? [])) {
      if (block.type === 'product_recommendations' && block.products) {
        products.push(...block.products)
      }
      if (block.type === 'review_sources' && block.products) {
        for (const p of block.products) {
          for (const s of (p.sources ?? [])) {
            if (!seenSourceUrls.has(s.url)) {
              seenSourceUrls.add(s.url)
              sources.push(s)
            }
          }
        }
      }
    }
  }

  return { sessionTitle, summaryText, products, sources }
}
```

### Pattern 3: Desktop Split-Panel via CSS Grid

**What:** The Results page wraps in a CSS grid that places a 320px sidebar on the left and content on the right, only on desktop.
**When to use:** Any page needing a persistent sidebar without NavLayout modification.

```tsx
{/* Results page root — inside NavLayout */}
<div className="min-h-dvh" style={{ background: 'var(--background)' }}>
  <div className="hidden lg:grid max-w-[1200px] mx-auto"
       style={{ gridTemplateColumns: '320px 1fr', gap: '0' }}>
    {/* Left sidebar */}
    <aside className="border-r h-full" style={{ borderColor: 'var(--border)' }}>
      {/* logo, session title, back to chat link */}
    </aside>
    {/* Main content */}
    <main className="min-w-0">
      {/* header, sources, product grid, quick actions */}
    </main>
  </div>
  {/* Mobile: single column, no sidebar */}
  <div className="lg:hidden">
    {/* same content, full width */}
  </div>
</div>
```

### Pattern 4: Score Bar

**What:** A 4px-height progress bar showing product quality score (0-100).
**When to use:** Each ResultsProductCard middle section.

```tsx
function ScoreBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 rounded-full overflow-hidden"
           style={{ background: 'var(--surface-hover)' }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${score}%`, background: 'var(--primary)' }}
        />
      </div>
      <span className="text-xs font-medium flex-shrink-0"
            style={{ color: 'var(--text-secondary)' }}>
        {score}
      </span>
    </div>
  )
}
```

### Pattern 5: Simple Toast Notification

**What:** A short-lived notification that fades out after 2-3 seconds. No external library.
**When to use:** Share "Link copied!", Compare/Export "Coming soon", session-not-found.

```tsx
function useToast() {
  const [toast, setToast] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }

  return { toast, showToast }
}

// Render: fixed bottom-center or top-center, fades with opacity transition
{toast && (
  <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[500] px-4 py-2 rounded-full text-sm font-medium text-white"
       style={{ background: 'var(--text)', boxShadow: 'var(--shadow-lg)' }}>
    {toast}
  </div>
)}
```

### Anti-Patterns to Avoid

- **Server-side data access from localStorage:** `localStorage` is undefined during SSR. The entire Results page must be `'use client'` and all localStorage reads must be inside `useEffect`. Do not attempt to read localStorage in the component body or during render.
- **Hydration errors from Math.random():** The pastel card background tint index assignment must be deterministic (e.g., `index % 4`) not random. CLAUDE.md explicitly warns against `Math.random()` in SSR.
- **Modifying NavLayout for Results sidebar:** The context decision is that the sidebar is part of the Results page component, not NavLayout. Adding sidebar logic to NavLayout would break all other routes.
- **Importing NavLayout-internal components (MobileHeader, UnifiedTopbar) directly in Results page:** The page renders inside NavLayout which already supplies these. Adding them again creates double navigation bars — a known CLAUDE.md pitfall.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Curated product image lookup | Custom image fetching or CDN logic | `lookupCuratedProduct()` pattern from `InlineProductCard.tsx` + `curatedLinks.ts` | Already handles ASIN → Amazon image URL + affiliate link fallback; 120+ products |
| Source citations rendering | Custom source list component | `SourceCitations` component (Phase 14) | Already handles colored dots, deduplication, +N more toggle, external links |
| ASIN image URL format | Custom URL builder | `https://images-na.ssl-images-amazon.com/images/I/${asin}._SL300_.jpg` | Exact pattern already in InlineProductCard; proven working |
| Session title extraction | Parse first message manually | `useChatStatus()` context — `sessionTitle` already derived from first user message | ChatContainer already sets this; just read from context or localStorage messages[0].content |

**Key insight:** InlineProductCard.tsx is the direct ancestor of ResultsProductCard. The image lookup, affiliate URL fallback, rank label logic, and buy-on-amazon link pattern are all reusable verbatim — just wrapped in a taller card layout.

---

## Common Pitfalls

### Pitfall 1: localStorage is Undefined on Server
**What goes wrong:** `localStorage.getItem(...)` throws `ReferenceError: localStorage is not defined` during Next.js SSR/static generation.
**Why it happens:** Next.js App Router server-renders pages by default. localStorage is a browser-only API.
**How to avoid:** Mark page and all components that touch localStorage as `'use client'`. Place all localStorage reads inside `useEffect(() => { ... }, [])`.
**Warning signs:** Build error "ReferenceError: localStorage is not defined" or hydration mismatch.

### Pitfall 2: useParams() vs params prop in App Router
**What goes wrong:** Trying to access route params via props (`function ResultsPage({ params })`) works in some RSC patterns but may not behave correctly with `'use client'` pages.
**Why it happens:** App Router distinguishes server components (params as props) from client components (use useParams() hook).
**How to avoid:** In `'use client'` pages, use `useParams()` from `next/navigation`. The id is accessed as `params.id as string`.
**Warning signs:** `params` is always empty object in a client component.

### Pitfall 3: MobileTabBar Active State for /results Route
**What goes wrong:** The `getIsActive()` function in MobileTabBar doesn't handle `/results` routes, so no tab appears active when on `/results/:id`.
**Why it happens:** The current `getIsActive` checks for `/chat` for the "ask" tab. `/results` is an unaccounted route.
**How to avoid:** Update `getIsActive` so the "ask" tab also treats `/results` as active (results are produced from the chat/ask flow). Add: `pathname?.startsWith('/results')` to the `ask` condition.
**Warning signs:** No bottom tab highlighted while on the Results page.

### Pitfall 4: Empty Products When ui_blocks Structure Doesn't Match
**What goes wrong:** `extractResultsData` returns empty products array even when the session has data.
**Why it happens:** The block `type` field might differ from what the extractor expects. The backend sends `review_product_cards`, not `product_recommendations`, as the type.
**How to avoid:** Log the actual `ui_blocks` structure from a real session to confirm type strings. Check `normalizeBlocks.ts` for any type normalization. Accept multiple possible type strings as fallbacks in the extractor.
**Warning signs:** Results page renders with 0 products despite the chat having results.

### Pitfall 5: navigator.clipboard Requires HTTPS or Localhost
**What goes wrong:** `navigator.clipboard.writeText()` silently fails or throws in HTTP environments.
**Why it happens:** The Clipboard API requires a secure context (HTTPS). In production (Vercel/Railway) this is fine, but local HTTP dev may fail.
**How to avoid:** Wrap in try/catch. Show the toast on success, gracefully swallow errors. Provide `document.execCommand('copy')` as fallback for insecure contexts.
**Warning signs:** Share button appears to work but URL is never copied; no toast appears.

### Pitfall 6: Score Bar Values Without Any Rating Data
**What goes wrong:** All score bars show 0 if the score derivation logic finds no rating field.
**Why it happens:** Product data from the API may not include numeric ratings. The position-based fallback must be the default, not a secondary path.
**How to avoid:** In `ResultsProductCard`, derive score as: `product.rating ? Math.round(product.rating * 20) : POSITION_SCORES[index] ?? 60`. Define `POSITION_SCORES = [95, 88, 82, 76, 70]`.
**Warning signs:** All score bars identical width or showing 0.

---

## Code Examples

### Existing lookupCuratedProduct pattern (reuse verbatim)
```typescript
// Source: frontend/components/InlineProductCard.tsx (lines 30-46)
function lookupCuratedProduct(name: string): { imageUrl: string | null; affiliateUrl: string | null } {
  const nameLower = name.toLowerCase()
  for (const category of Object.values(curatedLinks)) {
    for (const topic of category) {
      if (topic.title.toLowerCase().includes(nameLower) || nameLower.includes(topic.title.toLowerCase().split(' ').slice(1).join(' ').toLowerCase())) {
        const firstProduct = topic.products[0]
        if (firstProduct) {
          return {
            imageUrl: `https://images-na.ssl-images-amazon.com/images/I/${firstProduct.asin}._SL300_.jpg`,
            affiliateUrl: firstProduct.url,
          }
        }
      }
    }
  }
  return { imageUrl: null, affiliateUrl: null }
}
```

### CHAT_CONFIG localStorage keys
```typescript
// Source: frontend/lib/constants.ts (lines 80-86)
export const CHAT_CONFIG = {
  MAX_MESSAGE_LENGTH: 2000,
  SESSION_STORAGE_KEY: 'chat_session_id',       // stores current session UUID
  ALL_SESSIONS_KEY: 'chat_all_session_ids',
  USER_ID_STORAGE_KEY: 'chat_user_id',
  MESSAGES_STORAGE_KEY: 'chat_messages',         // stores Message[] JSON array
} as const
```

### SourceCitations reuse (pass title prop)
```tsx
// Source: frontend/components/SourceCitations.tsx
// SourceCitations accepts optional title prop (default: 'Sources')
// For Results page, pass: title="SOURCES ANALYZED"
<SourceCitations
  data={{ products: sourcesAsProducts }}
  title="SOURCES ANALYZED"
/>
```

### MobileHeader expand icon wiring
```tsx
// Source: frontend/components/MobileHeader.tsx (lines 59-68)
// Currently: onClick={() => {}}
// Phase 15 fix: read sessionId from CHAT_CONFIG key and navigate
import { CHAT_CONFIG } from '@/lib/constants'

const handleExpandClick = () => {
  const sessionId = localStorage.getItem(CHAT_CONFIG.SESSION_STORAGE_KEY)
  if (sessionId) {
    router.push(`/results/${sessionId}`)
  }
}
// Replace onClick={() => {}} with onClick={handleExpandClick}
```

### CSS variables to add for card accent tints
```css
/* Add to globals.css :root — light mode */
--card-accent-1: #FFF8F0;   /* warm peach */
--card-accent-2: #F0F4FF;   /* soft blue */
--card-accent-3: #F0FFF4;   /* pale mint */
--card-accent-4: #FDF0FF;   /* lavender blush */

/* Add to [data-theme="dark"] — dark mode */
--card-accent-1: #2A2218;
--card-accent-2: #181E2A;
--card-accent-3: #182218;
--card-accent-4: #22182A;
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pages Router (`pages/results/[id].tsx`) | App Router (`app/results/[id]/page.tsx`) | Next.js 13+ | `useParams()` instead of router.query; no getServerSideProps needed |
| `getServerSideProps` for data | `useEffect` + localStorage client-side read | Phase 15 decision | No server round-trip; instant page load for same-browser shareable links |

---

## Open Questions

1. **Exact ui_blocks type string for product data**
   - What we know: `Message.ui_blocks` is typed as `any[]`; InlineProductCard is rendered from blocks via BlockRegistry
   - What's unclear: The exact `type` value — is it `'product_recommendations'`, `'review_product_cards'`, `'products'`, or something else?
   - Recommendation: Before implementing extractor, add a `console.log(msg.ui_blocks)` to a real session's messages in the browser and note the type field. Alternatively, check `frontend/lib/skeletonMap.ts` and `frontend/components/blocks/BlockRegistry.tsx` for the canonical type strings.

2. **SourceCitations data shape vs extracted source shape**
   - What we know: SourceCitations expects `{ products: [{ name, sources: [...] }] }` — a nested structure grouped by product
   - What's unclear: Whether the raw `review_sources` block in ui_blocks matches this shape or needs transformation
   - Recommendation: The extractor utility should output sources in the SourceCitations-expected format directly, or wrap flat sources in a single pseudo-product: `{ products: [{ name: 'Sources', sources: flatSources }] }`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.0.x |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test:run -- tests/resultsScreen.test.tsx` |
| Full suite command | `cd frontend && npm run test:run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RES-01 | `/results/:id` route renders; redirects to `/` when localStorage missing | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ Wave 0 |
| RES-02 | Desktop grid-cols-3 on lg:; mobile flex-row overflow-x-auto on <md: | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ Wave 0 |
| RES-03 | ResultsProductCard shows Amazon image, price, affiliate link | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ Wave 0 |
| RES-04 | Rank badge "#1 Top Pick", score bar rendered per card | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ Wave 0 |
| RES-05 | Share copies URL to clipboard; Compare/Export show "Coming soon" | unit | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ Wave 0 |
| RES-06 | Sources section renders colored dots, source names, clickable links | unit | `npm run test:run -- tests/resultsScreen.test.tsx` (imports SourceCitations) | ❌ Wave 0 |
| RESP-01 | Mobile single-column layout below 768px | unit (class inspection) | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ Wave 0 |
| RESP-02 | Desktop 3-col grid + sidebar + max-w-[1200px] container | unit (class inspection) | `npm run test:run -- tests/resultsScreen.test.tsx` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run test:run -- tests/resultsScreen.test.tsx`
- **Per wave merge:** `cd frontend && npm run test:run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/tests/resultsScreen.test.tsx` — covers RES-01 through RES-06, RESP-01, RESP-02
- [ ] `frontend/lib/extractResultsData.ts` — new utility file (no test file needed separately; tested via resultsScreen.test.tsx)
- [ ] `frontend/app/results/[id]/page.tsx` — dynamic route (no pre-existing file)

---

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection — `frontend/components/InlineProductCard.tsx`: lookupCuratedProduct pattern, RANK_LABELS, image URL format
- Codebase direct inspection — `frontend/components/SourceCitations.tsx`: exact props interface, DOT_COLORS array, expand/collapse behavior
- Codebase direct inspection — `frontend/components/MobileHeader.tsx`: expand icon placeholder at line 59-68, useRouter pattern
- Codebase direct inspection — `frontend/components/NavLayout.tsx`: rendering context, ChatStatusProvider scope
- Codebase direct inspection — `frontend/components/MobileTabBar.tsx`: getIsActive logic, `/chat` active detection (must be extended to `/results`)
- Codebase direct inspection — `frontend/lib/constants.ts`: CHAT_CONFIG storage keys
- Codebase direct inspection — `frontend/app/globals.css`: existing CSS variable naming conventions for new --card-accent-* vars
- Codebase direct inspection — `frontend/vitest.config.ts`: test setup, include pattern, path aliases
- Codebase direct inspection — `frontend/tests/setup.ts`: localStorage mock, router mock patterns for new tests
- Next.js 14 App Router docs — `useParams()` hook for client components with dynamic segments

### Secondary (MEDIUM confidence)
- Codebase inspection of Phase 13/14 test files — established RED-first test pattern using vitest + @testing-library/react
- `frontend/app/chat/page.tsx` — Suspense wrapping pattern for client-side data loading pages

### Tertiary (LOW confidence)
- Clipboard API fallback via `document.execCommand('copy')` — older pattern, browser support varies; verify if needed for production

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All libraries already in use; no new dependencies
- Architecture: HIGH — Based on direct codebase inspection of NavLayout, MobileHeader, InlineProductCard, SourceCitations
- Pitfalls: HIGH — localStorage SSR pitfall and MobileTabBar active state gap both verified from code inspection; clipboard HTTPS pitfall is standard web knowledge

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable stack — no fast-moving dependencies)
