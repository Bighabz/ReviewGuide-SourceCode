# Product Experience — Phase 3 Design

**Date:** 2026-02-13
**Status:** Approved
**Scope:** 5 issues across backend pipeline, frontend UX, and browse page

---

## Table of Contents

1. [Issue 2: Context Loss Across Follow-up Queries](#issue-2-context-loss-across-follow-up-queries)
2. [Issue 1: Scroll Lock During Chat Replies](#issue-1-scroll-lock-during-chat-replies)
3. [Issue 4+5: Browse Page Overhaul](#issue-45-browse-page-overhaul)
4. [Issue 3: Chatty Engagement Responses](#issue-3-chatty-engagement-responses)
5. [Issue 6: Affiliate Provider Expansion](#issue-6-affiliate-provider-expansion)

---

## Issue 2: Context Loss Across Follow-up Queries

### Problem

When a user asks a follow-up like "what's the cheapest one?", the system loses context about what was previously discussed (e.g., vacuums). Context is lost at 6 points in the pipeline: `product_search.py`, `product_affiliate.py`, Intent Agent, Clarifier Agent, `product_compose.py`, and slot inheritance.

### Design Decisions

- **Session memory model:** Full session — context persists for the entire chat session
- **Conflict resolution:** Latest-wins with history — `last_search_context` holds the most recent search, `search_history` array keeps up to 5 previous contexts
- **Context richness:** Rich object (~12 fields) — enough for natural follow-ups without re-querying

### Data Model

**New GraphState fields:**

```python
# In GraphState TypedDict
last_search_context: Dict[str, Any]    # Current/latest search context
search_history: List[Dict[str, Any]]   # Previous search contexts (max 5)
```

**Initial state in `chat.py`:**

```python
"last_search_context": {},
"search_history": [],
```

**Search context object shape:**

```python
{
    "category": "vacuum",
    "product_type": "robot vacuums",
    "product_names": ["Dyson V15", "Shark Navigator", "Bissell Pet Pro"],
    "budget": "$200-400",
    "brand": "any",
    "features": ["cordless", "pet hair"],
    "use_case": "home cleaning",
    "top_prices": {"Dyson V15": 449.99, "Shark Navigator": 199.99},
    "avg_rating": {"Dyson V15": 4.7, "Shark Navigator": 4.3},
    "query": "best robot vacuums for pet hair",
    "timestamp": "2026-02-13T...",
    "turn_index": 3
}
```

### Producer — Writing Context

**Where:** End of `product_compose.py`, after all UI blocks are built.

```python
new_context = {
    "category": slots.get("category", ""),
    "product_type": slots.get("product_type", ""),
    "product_names": product_names,
    "budget": slots.get("budget"),
    "brand": slots.get("brand"),
    "features": slots.get("features"),
    "use_case": slots.get("use_case"),
    "top_prices": {
        p["name"]: p["best_offer"]["price"]
        for p in products_with_offers
        if p.get("best_offer", {}).get("price")
    },
    "avg_rating": {
        name: rd.get("avg_rating", 0)
        for name, rd in review_data.items()
    } if review_data else {},
    "query": user_message,
    "timestamp": datetime.utcnow().isoformat(),
    "turn_index": len(state.get("conversation_history", [])),
}

# Push previous context to history, set new as current
prev = state.get("last_search_context", {})
history = list(state.get("search_history", []))
if prev:
    history.append(prev)
    history = history[-5:]  # Cap at 5

return {
    ...existing_return,
    "last_search_context": new_context,
    "search_history": history,
}
```

Only `product_compose` writes context — it's the only tool with the full picture.

### Consumers — Reading Context

Six points consume `last_search_context` as fallback:

**1. `product_search.py`** — Category and product type fallback:

```python
category = slots.get("category") or state.get("last_search_context", {}).get("category")
product_type = slots.get("product_type") or state.get("last_search_context", {}).get("product_type")
```

Also inject previous product names into the search prompt so the LLM knows what was already shown.

**2. `product_affiliate.py`** — Category detection fallback:

```python
category = _detect_category(query, product_type) or state.get("last_search_context", {}).get("category")
```

**3. Intent Agent (`workflow.py`)** — Pass `last_search_context` summary to the intent classifier so "cheapest one" is recognized as a product follow-up, not a vague general query.

**4. Clarifier Agent** — If `last_search_context` exists and the new query is a follow-up (short, contains pronouns/superlatives), skip clarification.

**5. `product_compose.py`** — Accessory filtering uses context category:

```python
category = slots.get("category") or state.get("last_search_context", {}).get("category")
```

**6. Slot inheritance** — When intent stays `product` and current slots are sparse:

```python
for key in ["budget", "brand", "features", "use_case"]:
    if not slots.get(key) and state.get("last_search_context", {}).get(key):
        slots[key] = state["last_search_context"][key]
```

### Follow-up Detection

```python
def _is_follow_up_query(query: str, last_context: dict) -> bool:
    """Detect if query references previous search results."""
    if not last_context:
        return False

    q = query.lower().strip()

    reference_signals = [
        "that one", "the first", "the second", "the third",
        "cheapest", "most expensive", "best rated", "any of",
        "compare them", "which one", "between those",
        "more about", "tell me more", "go back to",
        "the one with", "how about the",
    ]
    if any(signal in q for signal in reference_signals):
        return True

    # Very short query with no product category noun
    if len(q.split()) <= 4:
        return True

    return False
```

### History Scanning

For explicit callbacks like "go back to the vacuums":

```python
def _find_in_history(query: str, history: list) -> dict | None:
    """Scan search_history for a matching previous context."""
    q = query.lower()
    for ctx in reversed(history):
        cat = ctx.get("category", "").lower()
        ptype = ctx.get("product_type", "").lower()
        if cat and cat in q:
            return ctx
        if ptype and ptype in q:
            return ctx
    return None
```

If matched, that context temporarily overrides `last_search_context` for the current turn without mutating state.

### Files Changed

| Component | File | Change |
|-----------|------|--------|
| State fields | `chat.py`, GraphState TypedDict | Add `last_search_context`, `search_history` with defaults |
| Producer | `product_compose.py` | Build and write context after pipeline completes |
| Consumer 1 | `product_search.py` | Category/product_type fallback from context |
| Consumer 2 | `product_affiliate.py` | Category detection fallback |
| Consumer 3 | `workflow.py` (Intent Agent) | Pass context summary to intent classifier |
| Consumer 4 | Clarifier Agent | Skip clarification when context covers follow-ups |
| Consumer 5 | `product_compose.py` | Accessory filtering uses context category |
| Consumer 6 | Slot inheritance (workflow) | Unfilled slots inherit from context |
| Detection | New helper module or inline | `_is_follow_up_query()` + `_find_in_history()` |

### Risk

Stale context — user asks about vacuums, browses for 10 minutes, comes back referencing something external. The 5-entry history cap and session-only persistence mitigate this.

---

## Issue 1: Scroll Lock During Chat Replies

### Problem

`MessageList.tsx:14-16` has an unconditional `scrollIntoView()` that fires on every `[messages]` state change. During streaming, each token update triggers this, constantly locking scroll to bottom and preventing the user from scrolling up to read.

### Design Decision

Smart scroll with user intent detection. Auto-scroll during streaming unless the user has scrolled up. Snap to bottom when streaming completes.

### Implementation

**File: `MessageList.tsx`**

```tsx
interface MessageListProps {
  messages: MessageType[]
  isStreaming?: boolean
}

const [userScrolledUp, setUserScrolledUp] = useState(false)
const containerRef = useRef<HTMLDivElement>(null)
const bottomRef = useRef<HTMLDivElement>(null)

// Detect user scroll intent
useEffect(() => {
  const container = containerRef.current
  if (!container) return

  const handleScroll = () => {
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
    setUserScrolledUp(!isNearBottom)
  }

  container.addEventListener('scroll', handleScroll)
  return () => container.removeEventListener('scroll', handleScroll)
}, [])

// Auto-scroll only when user hasn't scrolled up
useEffect(() => {
  if (!userScrolledUp) {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
}, [messages, userScrolledUp])

// Snap to bottom + reset flag when streaming completes
useEffect(() => {
  if (!isStreaming) {
    setUserScrolledUp(false)
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
}, [isStreaming])
```

**File: `ChatContainer.tsx`** — Pass prop:

```tsx
<MessageList messages={messages} isStreaming={isStreaming} />
```

### Files Changed

| Component | File | Change |
|-----------|------|--------|
| MessageList | `MessageList.tsx` | Add `isStreaming` prop, scroll detection, conditional auto-scroll |
| ChatContainer | `ChatContainer.tsx` | Pass `isStreaming` to MessageList |

---

## Issue 4+5: Browse Page Overhaul

### Problem

- `browseData.ts` contains 100% static mock data with fake reviews generated via seed hashing (legal risk)
- 12 categories are too many — most are low-research categories that don't fit "AI review guide" positioning

### Design Decisions

- **Page type:** Discovery hub — editorial category cards with trending query chips, no product data
- **Categories:** 5 high-research categories (Travel, Electronics, Home Appliances, Health & Wellness, Outdoor & Fitness)
- **Hero images:** Curated Unsplash/Pexels photos committed to repo
- **Trending queries:** Manually curated seed list, structured for future swap to analytics API
- **Query pattern:** 2 discovery + 1 comparison + 1 budget per category
- **Sidebar:** CategorySidebar with anchor-based scrolling + IntersectionObserver active state
- **Future path:** Option to swap to real analytics-driven trending data when available

### Category Config

**Delete:** `browseData.ts`

**New file:** `categoryConfig.ts`

```typescript
export interface BrowseCategory {
  slug: string
  name: string
  tagline: string
  image: string            // /images/browse/[slug].jpg
  queries: string[]         // Curated seed, swap to API later
}

export const categories: BrowseCategory[] = [
  {
    slug: "travel",
    name: "Travel",
    tagline: "Flights, hotels & destinations worth the trip",
    image: "/images/browse/travel.jpg",
    queries: [
      "Top all-inclusive resorts in the Caribbean",
      "When to book flights to Japan for cheap",
      "Airbnb vs hotels for family vacations",
      "Great travel backpacks under $100",
    ],
  },
  {
    slug: "electronics",
    name: "Electronics",
    tagline: "Researched, rated & ready to buy",
    image: "/images/browse/electronics.jpg",
    queries: [
      "Most popular noise cancelling headphones",
      "Top-rated laptops for students 2026",
      "Samsung vs iPhone comparison",
      "Solid budget smartphones under $400",
    ],
  },
  {
    slug: "home-appliances",
    name: "Home Appliances",
    tagline: "The machines that make your home work",
    image: "/images/browse/home-appliances.jpg",
    queries: [
      "Top robot vacuums for pet hair",
      "Highly rated washing machines for large families",
      "Dyson vs Shark cordless vacuums",
      "Great espresso machines under $500",
    ],
  },
  {
    slug: "health-wellness",
    name: "Health & Wellness",
    tagline: "Gear and supplements backed by research",
    image: "/images/browse/health-wellness.jpg",
    queries: [
      "Top-rated standing desks for back pain",
      "Most effective supplements for energy and focus",
      "Theragun vs Hypervolt massage gun",
      "Affordable fitness trackers under $100",
    ],
  },
  {
    slug: "outdoor-fitness",
    name: "Outdoor & Fitness",
    tagline: "Built for the trail, the road & the gym",
    image: "/images/browse/outdoor-fitness.jpg",
    queries: [
      "Top hiking boots for beginners",
      "Highly rated running shoes for flat feet",
      "Garmin vs Apple Watch for fitness",
      "Great home treadmills under $1000",
    ],
  },
]
```

### Recently Researched (Client-Side History)

Populated from localStorage after each product chat. Renders above category cards only when the user has history.

**localStorage schema:**

```typescript
// Key: "reviewguide_recent_searches"
interface RecentSearch {
  query: string
  productNames: string[]    // Top 3 product names from results
  category: string          // "electronics", "travel", etc.
  timestamp: number         // Date.now()
}
// Value: RecentSearch[] (max MAX_RECENT_SEARCHES, newest first)
```

**Config constant:** `MAX_RECENT_SEARCHES = 8`

**Writing (in `ChatContainer.tsx`):** After streaming completes, extract from rendered UI blocks:

```typescript
// After setIsStreaming(false)
const productBlock = uiBlocks.find(b =>
  b.type === 'product_cards' || b.type === 'product_carousel'
)
if (productBlock) {
  const recentSearch: RecentSearch = {
    query: currentQuery,
    productNames: productBlock.items?.slice(0, 3).map(i => i.title) || [],
    category: productBlock.category || '',
    timestamp: Date.now(),
  }
  saveRecentSearch(recentSearch) // Dedupes by query, enforces cap
}
```

**Reading (on browse page):** Renders above category cards only when populated:

```tsx
const recentSearches = getRecentSearches()

{recentSearches.length > 0 && (
  <section className="mb-10">
    <h2 className="font-serif text-xl text-[var(--text)] mb-4">
      Recently Researched
    </h2>
    <div className="flex gap-3 overflow-x-auto pb-2">
      {recentSearches.map((search, idx) => (
        <a
          key={idx}
          href={`/chat?q=${encodeURIComponent(search.query)}&new=1`}
          className="flex-shrink-0 rounded-xl border border-[var(--border)]
                     bg-[var(--surface-elevated)] p-4 w-[220px]
                     product-card-hover group"
        >
          <p className="text-sm font-semibold text-[var(--text)]
                        line-clamp-2 group-hover:text-[var(--primary)]">
            {search.query}
          </p>
          <div className="mt-2 space-y-0.5">
            {search.productNames.map((name, i) => (
              <p key={i} className="text-[11px] text-[var(--text-muted)] truncate">
                {name}
              </p>
            ))}
          </div>
        </a>
      ))}
    </div>
  </section>
)}
```

**Utility functions (new file `lib/recentSearches.ts`):**
- `saveRecentSearch(search)` — Dedupes by query, prepends, caps at `MAX_RECENT_SEARCHES`
- `getRecentSearches()` — Returns array, handles missing/corrupt localStorage gracefully
- `clearRecentSearches()` — For a future "clear history" button

### Page Layout

**Route:** `/browse` (single page, category sub-routes removed)

**Structure — top to bottom:**

1. **Header area** — Search bar (existing `SearchInput`) with editorial tagline: "What are you researching today?" in Instrument Serif
2. **Recently Researched** — Horizontal scroll of recent search cards (only if populated)
3. **Category grid** — 5 cards, responsive:
   - Desktop: 3 columns top + 2 columns bottom (centered)
   - Tablet: 2 columns, last card full-width
   - Mobile: single column stack
3. **Each category card:**
   - Hero image with dark gradient overlay (bottom 50%)
   - Category name (Instrument Serif) + tagline (DM Sans, muted white) over image
   - 4 query chips below image on card body
   - Chip click → `/chat?q={query}&new=1` (existing sticky bar flow)
   - Card click → `/chat` with category context

### CategorySidebar (Revised)

- 5 category links, each scrolls to `#category-{slug}` anchor
- Active state via IntersectionObserver (highlights when section is in viewport)
- Desktop: Fixed sidebar, always visible
- Tablet: Collapsed, hamburger toggle
- Mobile: Hidden (cards visible in single-column stack)

```tsx
// Click handler
onClick={() => {
  document.getElementById(`category-${slug}`)?.scrollIntoView({
    behavior: 'smooth',
    block: 'start'
  })
}}

// Each category card anchor
<div id={`category-${category.slug}`} className="scroll-mt-24">
  {/* Card content */}
</div>
```

### Files Changed

| Component | Action |
|-----------|--------|
| `browseData.ts` | Delete entirely |
| `categoryConfig.ts` | New — 5 categories with curated queries, `MAX_RECENT_SEARCHES` constant |
| `lib/recentSearches.ts` | New — `saveRecentSearch`, `getRecentSearches`, `clearRecentSearches` |
| `ChatContainer.tsx` | Write recent search to localStorage after streaming completes |
| `/browse` page | Redesign — search bar + recently researched + category cards with query chips |
| `/browse/[category]` routes | Delete |
| `CategorySidebar` | Revise — 5 anchor links with IntersectionObserver active state |
| `CategoryHero`, `ContentRow`, `ProductGrid`, `FilterSidebar` | Delete (browse-only components) |
| `/images/browse/` | Add 5 curated Unsplash/Pexels images |

---

## Issue 3: Chatty Engagement Responses

### Problem

After showing product results, the assistant ends abruptly. Users don't feel invited to continue the conversation.

### Design Decision

- **Where:** LLM-generated closing line in `product_compose.py`
- **Style:** Brief, warm, context-aware — references specific user details (names, preferences, use cases)
- **Constraint:** "End with a brief, warm follow-up that shows you remember the user's context. Keep it to one sentence."

### Implementation

**File: `product_compose.py`** — Add to the compose LLM prompt:

```python
"""
End with a brief, warm follow-up that shows you remember the user's context.
Keep it to one sentence. Reference specific details they mentioned — names,
preferences, use cases — to show you're paying attention.
"""
```

No other files change. The closing line is part of `assistant_text`, which already streams to the frontend and renders as markdown.

### Files Changed

| Component | File | Change |
|-----------|------|--------|
| Compose prompt | `product_compose.py` | Add closing-line instruction to compose prompt |

---

## Issue 6: Affiliate Provider Expansion

### Problem

Only eBay and Amazon affiliate providers exist. Google Shopping is not a viable affiliate network.

### Design Decision

- **Registration:** Explicit — add new providers to `AffiliateManager._initialize_providers()`
- **Priority:** Walmart first, Best Buy second, Target third
- **Pattern:** Existing `BaseAffiliateProvider` abstract class already provides the contract

### Existing Architecture (No Changes Needed)

```
backend/app/services/affiliate/
├── base.py          # BaseAffiliateProvider (abstract), AffiliateProduct (dataclass)
├── manager.py       # AffiliateManager (registry, parallel search, fallback)
└── providers/
    ├── ebay_provider.py      # EbayAffiliateProvider
    └── amazon_provider.py    # AmazonAffiliateProvider
```

`product_affiliate.py` already discovers providers via `affiliate_manager.get_available_providers()` and searches all in parallel with `asyncio.gather`. Zero changes needed in the MCP tool layer.

### Adding a New Provider (Checklist)

**1. Create provider file:** `providers/walmart_provider.py`

```python
class WalmartAffiliateProvider(BaseAffiliateProvider):
    def __init__(self, api_key=None, affiliate_id=None):
        self.api_key = api_key or settings.WALMART_API_KEY
        self.affiliate_id = affiliate_id or settings.WALMART_AFFILIATE_ID
        self.api_enabled = bool(self.api_key)

    async def search_products(self, query, category=None,
                              brand=None, min_price=None,
                              max_price=None, limit=5) -> List[AffiliateProduct]: ...
    async def generate_affiliate_link(self, product_id, campaign_id=None, tracking_id=None) -> str: ...
    async def check_link_health(self, affiliate_link) -> bool: ...
    def get_provider_name(self) -> str: return "walmart"
```

**2. Register in manager:** Add to `_initialize_providers()`

**3. Add settings:** `WALMART_API_KEY`, `WALMART_AFFILIATE_ID`, `WALMART_API_ENABLED`

**4. Export:** Add to `providers/__init__.py`

### Provider Priority

| # | Provider | Why | API Type |
|---|----------|-----|----------|
| 1 | **Walmart** | Largest US catalog after Amazon, direct affiliate API | REST (Walmart Affiliate API) |
| 2 | **Best Buy** | Strong for electronics (top category), well-documented | REST (Best Buy Products API) |
| 3 | **Target** | US retail coverage, fills gaps in home/wellness | REST (via Impact Radius) |

**Not recommended:** Google Shopping (not an affiliate network), CJ/ShareASale/Rakuten (per-merchant setup, no unified product API).

### Mock Mode Pricing Strategy

| Provider | Price Strategy | Example ($100 Amazon baseline) |
|----------|---------------|-------------------------------|
| Amazon | Baseline | $99.99 |
| eBay | 5-15% below (used/auction factor) | $85-95 |
| Walmart | 3-8% below (everyday low price) | $92-97 |
| Best Buy | Match or 2% above (premium electronics) | $99-102 |
| Target | Match Amazon +/-3% | $97-103 |

### Environment Variables per Provider

```python
# Walmart
WALMART_API_KEY: str = ""
WALMART_AFFILIATE_ID: str = ""
WALMART_API_ENABLED: bool = False  # Mock by default

# Best Buy
BESTBUY_API_KEY: str = ""
BESTBUY_AFFILIATE_ID: str = ""
BESTBUY_API_ENABLED: bool = False

# Target
TARGET_API_KEY: str = ""
TARGET_AFFILIATE_ID: str = ""
TARGET_API_ENABLED: bool = False
```

---

## Implementation Order

| # | Issue | Priority | Effort | Files |
|---|-------|----------|--------|-------|
| 1 | Context Loss (Issue 2) | Critical | High | `chat.py`, GraphState, `product_compose.py`, `product_search.py`, `product_affiliate.py`, `workflow.py` |
| 2 | Scroll Lock (Issue 1) | High | Low | `MessageList.tsx`, `ChatContainer.tsx` |
| 3 | Browse Overhaul (Issue 4+5) | High | Medium | `browseData.ts` (delete), `categoryConfig.ts` (new), `lib/recentSearches.ts` (new), `ChatContainer.tsx`, browse page, `CategorySidebar`, delete unused components |
| 4 | Chatty Responses (Issue 3) | Medium | Low | `product_compose.py` |
| 5 | Affiliate Expansion (Issue 6) | Low | High per provider | `providers/`, `manager.py`, `config.py` |

## Verification

1. **Context Loss:** "Best headphones" → "cheapest one" → should return the cheapest headphone, not random products
2. **Scroll Lock:** During streaming, scroll up mid-response — should stay where user scrolled. On stream end, should snap to bottom.
3. **Browse Page:** No mock data anywhere. All query chips navigate to `/chat?q=...&new=1`. Sidebar anchors scroll correctly. Recently Researched section appears after at least one product chat, shows query + top 3 product names, clicking navigates to new chat.
4. **Chatty Responses:** Product responses end with a personalized follow-up sentence referencing user context.
5. **Affiliate Expansion:** New providers appear in product carousels alongside eBay/Amazon. Mock pricing follows the positioning strategy.
