# Architecture Research

**Domain:** Mobile-first UX redesign — Discover → Chat → Results screens on existing Next.js 14 app
**Researched:** 2026-03-16
**Confidence:** HIGH (based on direct codebase analysis)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        NAVIGATION LAYER                          │
├───────────────────────┬─────────────────────────────────────────┤
│  Desktop (≥1024px)    │         Mobile (<768px)                  │
│  UnifiedTopbar        │         BottomTabBar (new)               │
│  (sticky, full width) │         (fixed bottom, 5 tabs + FAB)     │
└───────────┬───────────┴───────────────┬─────────────────────────┘
            │                           │
┌───────────▼───────────────────────────▼─────────────────────────┐
│                        ROUTE LAYER (Next.js App Router)          │
├────────────┬──────────────────┬────────────┬────────────────────┤
│  / → /browse│  /browse         │  /chat     │  /results/:id (new)│
│  (redirect) │  (Discover —     │  (Chat     │  (Results —        │
│             │   REPLACE with   │   screen — │   new route)       │
│             │   new DiscoverPg)│   MODIFY)  │                    │
└────────────┴──────────────────┴────────────┴────────────────────┘
            │                           │
┌───────────▼───────────────────────────▼─────────────────────────┐
│                       COMPONENT LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  REUSED (unchanged):          MODIFIED:          NEW:           │
│  - ChatContainer              - UnifiedTopbar    - BottomTabBar  │
│  - MessageList / Message      - BrowsePage       - DiscoverPage  │
│  - ChatInput                  - ChatPage         - ResultsPage   │
│  - BlockRegistry / UIBlocks   - CategorySidebar  - TrendingCard  │
│  - All block renderers        - ConvSidebar      - CompactCard   │
│  - ConversationSidebar        - ChatContainer    - ResultsHeader │
│  - chatApi.ts / SSE           (welcome screen)  - SourcePanel   │
│  - normalizeBlocks.ts                            - ResultsSidebar│
│  - useStreamReducer                              - NavLayout     │
└─────────────────────────────────────────────────────────────────┘
            │                           │
┌───────────▼───────────────────────────▼─────────────────────────┐
│                        DATA LAYER                                │
│  localStorage: session_id, messages, user_id, theme, accent     │
│  Backend API:  SSE /v1/chat/stream  GET /v1/chat/conversations   │
│  Redis:        halt-state (multi-turn)                           │
│  PostgreSQL:   conversation history                              │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `UnifiedTopbar` | Desktop top nav, theme/accent controls | Modify: add route-awareness for new screens |
| `BottomTabBar` (new) | Mobile 5-tab nav + central FAB | Create new |
| `NavLayout` (new) | Wrapper that injects correct nav for breakpoint | Create new |
| `BrowsePage` | Discover screen: hero, chips, trending, categories | Heavily modify (becomes Discover) |
| `ChatPage` | Chat screen: session mgmt, layout wiring | Modify: new header, remove left sidebar on mobile |
| `ChatContainer` | SSE streaming, message state, welcome screen | Modify welcome screen only; stream logic untouched |
| `ResultsPage` (new) | Full results view: split panel desktop, full-width mobile | Create new (reads from session/localStorage) |
| `CategorySidebar` | Left category nav (desktop) | Keep for desktop chat; hide on mobile in favor of bottom nav |
| `ConversationSidebar` | Right slide-out history drawer | Reuse unchanged; also becomes left panel on Results desktop |
| `Message` | Renders user/assistant bubbles with blocks | Modify bubble styling; do not touch block logic |
| `BlockRegistry / UIBlocks` | Dispatches NormalizedBlock to sub-renderers | Reuse unchanged |
| All block renderers | ProductCarousel, HotelCards, FlightCards, etc. | Reuse unchanged |
| `ChatInput` | Composer input + send | Minor style tweak for new pill shape |
| `chatApi.ts` | SSE streaming client, reconnect logic | Reuse unchanged |
| `normalizeBlocks.ts` | Converts raw ui_blocks to NormalizedBlock | Reuse unchanged |
| `useStreamReducer` | FSM for stream state | Reuse unchanged |

---

## Recommended Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root — add NavLayout wrapper here
│   ├── page.tsx                # Redirect / → /browse (keep)
│   ├── browse/
│   │   ├── layout.tsx          # Becomes NavLayout (wraps BrowseLayout)
│   │   └── page.tsx            # REPLACE with new DiscoverPage content
│   ├── chat/
│   │   └── page.tsx            # MODIFY: new ChatPage layout
│   └── results/
│       └── [sessionId]/
│           └── page.tsx        # NEW: ResultsPage
├── components/
│   ├── nav/                    # NEW folder — navigation components
│   │   ├── BottomTabBar.tsx    # Mobile 5-tab + FAB
│   │   ├── NavLayout.tsx       # Breakpoint-aware nav wrapper
│   │   └── ChatHeader.tsx      # NEW: Chat screen header (back, title, expand)
│   ├── discover/               # NEW folder — Discover screen
│   │   ├── TrendingCard.tsx    # Individual trending research card
│   │   └── CategoryChips.tsx   # Horizontal scroll chip row
│   ├── results/                # NEW folder — Results screen
│   │   ├── ResultsHeader.tsx   # Title, action buttons, summary
│   │   ├── SourcesPanel.tsx    # Collapsible sources list
│   │   ├── ResultsSidebar.tsx  # Desktop left conversation panel
│   │   └── CompactProductCard.tsx  # 170/200px inline product card
│   ├── ChatContainer.tsx       # Modify welcome screen section only
│   ├── Message.tsx             # Modify bubble CSS only
│   ├── UnifiedTopbar.tsx       # Modify: hide on mobile when BottomTabBar active
│   └── [all existing]          # Keep unchanged
└── lib/
    ├── sessionRouter.ts        # NEW: utility to navigate /results/:sessionId
    └── [all existing]          # Keep unchanged
```

### Structure Rationale

- **`components/nav/`:** All navigation components isolated so BottomTabBar and UnifiedTopbar never know about each other's existence — NavLayout mediates.
- **`components/discover/`:** New Discover-specific components separated from the now-generic browse components that may still serve category pages.
- **`components/results/`:** Results screen is new enough to warrant its own folder; reuses existing block renderers via imports.
- **`app/results/[sessionId]/`:** Dynamic route allows direct linking to a completed research session. `sessionId` matches the existing UUID-based session IDs already in localStorage.

---

## Architectural Patterns

### Pattern 1: Responsive Nav Injection via NavLayout

**What:** A single wrapper component (`NavLayout`) renders either `UnifiedTopbar` (desktop) or `BottomTabBar + ChatHeader` (mobile) based on Tailwind breakpoints. Pages do not decide which nav to render.

**When to use:** All app routes except `/admin/*`, `/login`, `/privacy`, `/terms`.

**Trade-offs:** Centralizes nav logic; pages stay nav-agnostic. Slight prop-drilling required for page-specific callbacks (onNewChat, onHistoryClick). Accept this rather than using global state for nav events.

**Example:**
```typescript
// NavLayout.tsx
export default function NavLayout({ children, chatProps }: NavLayoutProps) {
  return (
    <>
      {/* Desktop top nav — hidden below lg */}
      <div className="hidden lg:block">
        <UnifiedTopbar {...chatProps} />
      </div>
      {/* Content */}
      <main>{children}</main>
      {/* Mobile bottom nav — hidden at lg and above */}
      <div className="lg:hidden">
        <BottomTabBar />
      </div>
    </>
  )
}
```

### Pattern 2: Results Route as Session Reader

**What:** `/results/[sessionId]` reads the session from localStorage (primary) or the backend conversations API (fallback) and renders the last AI response's `ui_blocks` and `next_suggestions` in the full Results layout. It does NOT run a new stream — it displays a completed session.

**When to use:** User taps expand icon from Chat header, or navigates back to a prior session.

**Trade-offs:** No new API needed. Reuses `fetchConversationHistory` from `chatApi.ts`. The Results page becomes a "view" over existing data. Risk: localStorage may be cleared between chat and results — always fall back to backend API.

**Example:**
```typescript
// results/[sessionId]/page.tsx
const session = await fetchConversationHistory(sessionId)
const lastAssistantMessage = session.messages.findLast(m => m.role === 'assistant')
const blocks = normalizeBlocks(lastAssistantMessage?.ui_blocks ?? [])
// Render ResultsHeader + SourcesPanel + CompactProductCard list
```

### Pattern 3: Suggestion Chips Stay on CustomEvent Bus

**What:** Follow-up suggestion chips in Results and Chat continue to use `window.dispatchEvent(new CustomEvent('sendSuggestion', { detail: { question } }))`. ChatContainer already has the listener registered.

**When to use:** Any new component that renders suggestion chips (ResultsPage, TrendingCard click from Discover).

**Trade-offs:** Keeps the established contract. No refactor of ChatContainer's event listener. Navigating from Results to Chat with a chip tap requires routing to `/chat` first and then firing the event after mount — use `?q=` URL param pattern that already exists.

---

## Data Flow

### Discover → Chat Flow (existing, keep as-is)

```
User types in hero search input (BrowsePage)
    ↓
router.push('/chat?q=QUERY&new=1')
    ↓
ChatPage reads searchParams, generates new sessionId
    ↓
ChatContainer receives initialQuery + externalSessionId props
    ↓
handleStream() called → SSE to /v1/chat/stream
    ↓
Messages accumulate in useState(messages)
    ↓
Persisted to localStorage (MESSAGES_STORAGE_KEY)
```

### Chat → Results Flow (new)

```
User taps expand icon in ChatHeader (new component)
    ↓
router.push('/results/' + currentSessionId)
    ↓
ResultsPage reads sessionId from route params
    ↓
fetchConversationHistory(sessionId) → backend or localStorage
    ↓
Find last assistant message with ui_blocks
    ↓
normalizeBlocks(ui_blocks) → NormalizedBlock[]
    ↓
Render: ResultsHeader + SourcesPanel + CompactProductCard carousel + UIBlocks
```

### Bottom Nav → New Chat Flow (new)

```
User taps central FAB on BottomTabBar
    ↓
router.push('/chat?new=1')
    ↓
ChatPage generates new sessionId, clears localStorage messages
    ↓
ChatContainer shows welcome screen (messages.length === 0)
```

### State Management

```
localStorage (client-only)
    ↓ (read on mount)
ChatContainer.sessionId / messages
    ↓ (write on change)
localStorage (session_id, chat_messages, user_id, theme, accent)
    ↑
External session switches via externalSessionId prop (from ChatPage)
    ↑
ConversationSidebar.onSelectConversation callback
```

**Key constraint:** The `window.dispatchEvent('sendSuggestion')` custom event is the only inter-component communication channel for suggestion clicks. Do not replace with context or props — ChatContainer already relies on this.

### Key Data Flows

1. **Block rendering:** Backend `ui_blocks` → `onComplete` callback in `chatApi.ts` → `setMessages()` in `ChatContainer` → `Message.tsx` → `normalizeBlocks()` → `UIBlocks` → individual block renderers. This pipeline is complete and must not be modified.

2. **Session identity:** `session_id` is a UUID generated client-side in `ChatPage`. It flows into `ChatContainer` as `externalSessionId`, then into `streamChat()` as the session identifier. The same ID is the key for `/results/:sessionId` lookup.

3. **Theme/accent:** Set on `document.documentElement` by `UnifiedTopbar`. The inline `<script>` in `layout.tsx` hydrates theme before first paint. `BottomTabBar` must NOT re-implement this — read from DOM attribute only.

---

## Component Boundaries — What Talks to What

```
ChatPage (page-level state: sessionId, sidebarOpen)
  ├── NavLayout (provides nav for breakpoint)
  │   ├── UnifiedTopbar [desktop] — callbacks: onNewChat, onHistoryClick, onSearch
  │   ├── ChatHeader [mobile, new] — callbacks: onBack, onExpand
  │   └── BottomTabBar [mobile, new] — no callbacks needed (uses router directly)
  ├── CategorySidebar [desktop only, fixed left] — navigates via router
  ├── ChatContainer [main content] — props: externalSessionId, initialQuery, onSessionChange
  │   ├── MessageList → Message[] → UIBlocks → block renderers
  │   ├── ChatInput — props: value, onChange, onSend, disabled
  │   ├── BlockSkeleton — shown during tool execution
  │   └── ErrorBanner / MessageRecoveryUI
  └── ConversationSidebar [right overlay] — props: isOpen, onSelectConversation

BrowsePage (Discover — page-level state: heroInput, recentSearches, activeChip)
  ├── NavLayout
  ├── CategoryChips [new] — horizontal scroll, navigates via router
  ├── TrendingCard list [new] — each navigates to /chat?q=QUERY&new=1
  └── Category grid (existing markup, keep)

ResultsPage (new — reads session, no streaming)
  ├── NavLayout
  ├── ResultsHeader [new] — title, share/save/refresh buttons, summary
  ├── ResultsSidebar [desktop only, new] — wraps ConversationSidebar content
  ├── SourcesPanel [new] — collapsible sources from review_sources block
  ├── CompactProductCard carousel [new] — 170px mobile / 200px desktop
  └── UIBlocks (existing) — renders full block output below compact cards
```

---

## New vs Modified vs Reused

### New (create from scratch)

| Component | Location | Purpose |
|-----------|----------|---------|
| `BottomTabBar` | `components/nav/` | 5-tab mobile nav with central FAB |
| `NavLayout` | `components/nav/` | Breakpoint-aware nav wrapper |
| `ChatHeader` | `components/nav/` | Chat screen header: back, title, expand |
| `TrendingCard` | `components/discover/` | Trending research card with icon, title, subtitle |
| `CategoryChips` | `components/discover/` | Horizontal scrollable chip row |
| `ResultsPage` | `app/results/[sessionId]/` | Full results screen route |
| `ResultsHeader` | `components/results/` | Title + action buttons + summary |
| `SourcesPanel` | `components/results/` | Collapsible sources list |
| `ResultsSidebar` | `components/results/` | Desktop left panel (conversation list) |
| `CompactProductCard` | `components/results/` | 170/200px product card for results grid |
| `sessionRouter.ts` | `lib/` | Navigate to /results/:sessionId from ChatHeader |

### Modified (change existing)

| Component | Change Needed | Risk |
|-----------|--------------|------|
| `BrowsePage` | Replace hero + add CategoryChips + TrendingCard sections | Low — pure UI |
| `ChatPage` | Add ChatHeader (mobile), pass sessionId to expand handler | Low |
| `ChatContainer` | Modify welcome screen JSX only; do NOT touch streaming logic | Low |
| `Message.tsx` | Update bubble CSS to match spec (radius, border, colors) | Low |
| `UnifiedTopbar` | Add `hidden lg:block` wrapper so mobile hides it | Low |
| `BrowseLayout` | Pass through NavLayout instead of owning nav itself | Medium — layout shift risk |
| `app/layout.tsx` | Add `pb-16 lg:pb-0` to `<body>` for bottom tab clearance | Low |
| `globals.css` | Add `.hide-scrollbar` utility for CategoryChips horizontal scroll | Low |

### Reused (zero change)

| Component | Reason |
|-----------|--------|
| `ChatContainer` stream logic | Verified working, RFC-compliant FSM |
| `chatApi.ts` | SSE client with reconnect — do not touch |
| `normalizeBlocks.ts` | Correct block normalizer |
| `BlockRegistry / UIBlocks` | All 14+ block types working |
| All block renderers | ProductCarousel, HotelCards, FlightCards, etc. |
| `useStreamReducer` | 120s watchdog, interruption handling |
| `ConversationSidebar` | Reused in Results desktop split-panel |
| `CategorySidebar` | Stays on desktop chat view |
| `ErrorBanner`, `MessageRecoveryUI` | Working error recovery |
| `BlockSkeleton` | Tool-execution skeleton loading |
| `lib/constants.ts` | CHAT_CONFIG keys, TRENDING_PRODUCTS |
| `lib/recentSearches.ts` | Recent searches on Discover |

---

## Build Order (Phase Dependencies)

Build in this order to minimize re-work:

**Phase 1 — Navigation Foundation**
Build `BottomTabBar`, `NavLayout`, `ChatHeader` first. These have no dependencies on other new components and unblock all subsequent work. Modify `UnifiedTopbar` to self-hide on mobile.

**Phase 2 — Discover Screen**
Build `CategoryChips` and `TrendingCard`, then wire them into `BrowsePage`. Depends on NavLayout (Phase 1) for correct layout context. The existing category grid and recent searches carry over.

**Phase 3 — Chat Screen Modifications**
Add `ChatHeader` to `ChatPage` layout. Modify `Message.tsx` bubble styles and `ChatContainer` welcome screen. Depends on NavLayout (Phase 1). The streaming pipeline is untouched.

**Phase 4 — Results Route**
Build `ResultsPage`, `ResultsHeader`, `SourcesPanel`, `CompactProductCard`, `ResultsSidebar`. Depends on Phase 3 (needs Chat → Results expand navigation working). Reuses `UIBlocks` and `ConversationSidebar`.

**Phase 5 — Placeholder Routes**
Add `/saved`, `/compare`, `/profile` as static pages with bottom tab support. These are layout-only stubs.

**Dependency graph:**
```
BottomTabBar + NavLayout + ChatHeader  (Phase 1, no deps)
         ↓
  BrowsePage Discover  (Phase 2, needs Phase 1)
         ↓
  ChatPage modifications  (Phase 3, needs Phase 1)
         ↓
  ResultsPage  (Phase 4, needs Phase 3 for expand nav)
         ↓
  Placeholder routes  (Phase 5, needs Phase 1)
```

---

## Anti-Patterns

### Anti-Pattern 1: Duplicating the SSE/Stream Logic

**What people do:** Create a new streaming hook or copy `handleStream` into `ResultsPage` to "refresh" results.

**Why it's wrong:** `ChatContainer` owns all stream state including `useStreamReducer`, recovery UI, skeleton, and error handling. Duplicating this creates two sources of truth. Results are a read view over completed sessions — they never stream.

**Do this instead:** `ResultsPage` calls `fetchConversationHistory()` (read-only) and renders `UIBlocks` directly. No streaming in Results.

### Anti-Pattern 2: Putting BottomTabBar in RootLayout

**What people do:** Add BottomTabBar to `app/layout.tsx` so it's global.

**Why it's wrong:** The `/admin/*`, `/login`, `/privacy`, `/terms`, and `/affiliate-disclosure` routes must not show the bottom tab bar. Putting it in root layout forces complex route exclusion logic.

**Do this instead:** Put BottomTabBar inside `NavLayout`, and only use `NavLayout` in the routes that need it (browse, chat, results, saved, compare, profile).

### Anti-Pattern 3: Replacing CategorySidebar on Desktop

**What people do:** Remove the desktop `CategorySidebar` (left 56px-wide panel) because the mobile design has no sidebar.

**Why it's wrong:** The desktop chat layout explicitly uses the sidebar as the left navigation. The spec says "No bottom tab bar on desktop — use top navigation instead". The sidebar provides quick-search and category access that bottom tabs do not.

**Do this instead:** Keep `CategorySidebar` for desktop. `BottomTabBar` only renders below the `lg` breakpoint. The sidebar renders only at `lg` and above.

### Anti-Pattern 4: Modifying Message.tsx Block Logic

**What people do:** "Simplify" the block rendering in `Message.tsx` while restyling bubbles.

**Why it's wrong:** The MEMORY.md explicitly flags this: "All render functions in Message.tsx are protected — never modify ui_blocks logic." Block rendering is the core product output.

**Do this instead:** Touch only the bubble container CSS (background, border-radius, padding). The `<UIBlocks blocks={normalizedBlocks} />` call and everything inside it stays untouched.

### Anti-Pattern 5: Generating Session IDs with Math.random() in SSR

**What people do:** Add session ID generation or random-based content to new server components.

**Why it's wrong:** CLAUDE.md explicitly warns: "Don't use Math.random() in components rendered on server (causes hydration errors)."

**Do this instead:** Mark all components that use session IDs or random-based content as `'use client'`. The existing pattern in `ChatPage` uses Math.random() only inside a `useEffect`, which is correct.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Backend API (`/v1/chat/stream`) | SSE via `chatApi.ts` — do not change | All auth headers, reconnect logic is in this file |
| Backend API (`/v1/chat/conversations`) | `fetchConversationHistory()` in `chatApi.ts` | Used by ResultsPage for session read |
| Vercel deployment | Static export of Next.js 14 App Router | CORS regex `CORS_ORIGIN_REGEX` set on Railway covers preview URLs |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| ChatPage ↔ ChatContainer | Props: `externalSessionId`, `initialQuery`, `onSessionChange` | Props are the contract; do not add more |
| Message ↔ ChatContainer | None (Message is pure display; ChatContainer passes `messages` array via MessageList) | No callbacks up |
| Suggestion chips → ChatContainer | `window.dispatchEvent(CustomEvent('sendSuggestion'))` | This is the established pattern — keep it for ResultsPage chips too |
| BottomTabBar → Routes | `useRouter().push()` directly | No callbacks needed; BottomTabBar is navigation-only |
| ResultsPage → ConversationSidebar | Props: `isOpen`, `onSelectConversation`, `currentSessionId` | Same interface as ChatPage — no changes to ConversationSidebar |
| NavLayout → BottomTabBar / UnifiedTopbar | Renders each conditionally via Tailwind `lg:hidden` / `hidden lg:block` | CSS-only breakpoint switch, no JS resize listener needed |

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current (100s of users) | Current architecture is correct. localStorage + PostgreSQL handles this comfortably. |
| 1k-10k users | No frontend changes needed. Backend rate limiting (already implemented) is the bottleneck. |
| 10k+ users | Consider moving conversation history to a dedicated endpoint with pagination. `fetchConversationHistory` currently returns all messages — add `?limit=` param. |

### Scaling Priorities

1. **First bottleneck:** `ConversationSidebar` fetches ALL session IDs from localStorage on open. At 100+ conversations, this list can be large. Add a limit in `fetchConversations()` early.
2. **Second bottleneck:** `ResultsPage` loads full conversation history to find the last assistant message. A dedicated `/v1/chat/sessions/{id}/last-result` endpoint would be faster than deserializing the full history.

---

## Sources

- Direct codebase analysis: `frontend/app/chat/page.tsx`, `frontend/app/browse/page.tsx`, `frontend/components/ChatContainer.tsx`, `frontend/components/UnifiedTopbar.tsx`, `frontend/components/blocks/BlockRegistry.tsx`
- Design spec: `# ReviewGuide.ai — frontendredesign.txt` (in project root)
- Project context: `.planning/PROJECT.md`
- CLAUDE.md development notes (hydration warnings, component protection notes)
- MEMORY.md (Message.tsx block logic protection, editorial theme patterns)

---

*Architecture research for: ReviewGuide.ai v2.0 Frontend UX Redesign — Discover / Chat / Results*
*Researched: 2026-03-16*
