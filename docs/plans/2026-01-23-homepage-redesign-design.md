# Homepage Redesign Design

**Date:** 2026-01-23
**Status:** Approved
**Branch:** frontend-redesign

## Overview

Redesign the homepage (`/browse`) to be clean and minimal with a centered logo animation, search bar, and hybrid product display. The topbar is hidden on the homepage to create a focused, app-like experience.

## Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              ┌──────────────────────┐                       │
│              │   Animated Logo      │                       │
│              │   (video, once/session)                      │
│              └──────────────────────┘                       │
│                                                             │
│         ┌────────────────────────────────┐                  │
│         │   What are you looking for?    │                  │
│         └────────────────────────────────┘                  │
│                                                             │
│  Top Picks ──────────────────────────────────────────────   │
│  ◄ [Card] [Card] [Card] [Card] [Card] ►      (carousel)     │
│                                                             │
│  Browse All ─────────────────────────────────────────────   │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                           │
│  │     │ │     │ │     │ │     │             (grid)         │
│  └─────┘ └─────┘ └─────┘ └─────┘                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Animated Logo

**File:** `public/images/animated_logo.mp4`

**Behavior:**
- Plays automatically on page load
- Plays **once per session** (tracked via `sessionStorage`)
- After playback completes, displays the **final frame as a static image**
- No looping
- Optional: Include sound (muted by default, respect user preference)

**Implementation:**
- Use HTML5 `<video>` element with `playsInline`, `autoPlay`, `muted`
- On `ended` event: hide video, show static fallback image
- Check `sessionStorage.getItem('logoPlayed')` on mount
- If already played this session, show static image immediately

### 2. Search Bar

**Design:**
- Centered below logo
- Clean, minimal styling (subtle border or borderless)
- No decorative icons inside
- Generous padding and whitespace
- Placeholder: "What are you looking for?"

**Behavior on submit:**
1. Filter products below in real-time
2. Show subtle "Ask AI instead →" link below the search bar
3. Clicking "Ask AI instead" navigates to `/chat?q={query}&new=1`

### 3. Product Display (Hybrid Layout)

**Featured Carousel:**
- Horizontal scrolling row
- Section title: "Top Picks" or similar
- Shows 5-8 cards, scrollable left/right

**Product Grid:**
- Responsive grid below carousel
- Section title: "Browse All" or similar
- 2 columns (mobile) → 3 columns (tablet) → 4 columns (desktop)

### 4. Product Cards

**Elements (all visible):**
```
┌─────────────────────────┐
│      [Product Image]    │
├─────────────────────────┤
│ Product Name            │
│ ⭐ 4.5 (2,341)  · $299  │
│                         │
│ "AI-generated summary   │
│ based on user context"  │
│                         │
│      [View Deal]        │
└─────────────────────────┘
```

**AI Summary:**
- Generated on-demand using chat context
- Personalized based on user's search query
- If no query/context, show generic product highlight

**No source badges** (Reddit, Amazon, YouTube badges removed)

### 5. Topbar Visibility

| Page | Topbar |
|------|--------|
| `/browse` (homepage) | **Hidden** |
| `/chat` | Visible (full) |
| `/product/*` | Visible (full) |
| All other pages | Visible (full) |

## What to Remove

The following elements from the current design should be removed:

- [ ] Gradient hero background
- [ ] Welcome text and taglines
- [ ] Stats bars ("X products", "avg rating", "reviews analyzed")
- [ ] Decorative blur elements
- [ ] Filter pills (unless user has actively filtered)
- [ ] Source badges on cards (Reddit, Amazon, YouTube)
- [ ] "Ask AI for Recommendations" button in hero (replaced by search bar behavior)

## Technical Notes

### Session Storage Key
```javascript
// Check if logo has played this session
const hasPlayed = sessionStorage.getItem('logoAnimationPlayed') === 'true'

// After video ends
sessionStorage.setItem('logoAnimationPlayed', 'true')
```

### Video Element
```jsx
<video
  ref={videoRef}
  src="/images/animated_logo.mp4"
  autoPlay
  muted
  playsInline
  onEnded={() => {
    setShowStaticLogo(true)
    sessionStorage.setItem('logoAnimationPlayed', 'true')
  }}
  className="..."
/>
```

### Conditional Topbar
```jsx
// In layout or topbar component
const pathname = usePathname()
const isHomepage = pathname === '/browse' || pathname === '/'

if (isHomepage) return null // Hide topbar on homepage
```

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/app/browse/page.tsx` | Replace hero with logo + search, restructure product layout |
| `frontend/components/UnifiedTopbar.tsx` | Add conditional rendering based on route |
| `frontend/app/layout.tsx` | May need to pass route info for topbar visibility |
| `frontend/components/browse/ProductCard.tsx` | Add AI summary field, remove source badges |
| `frontend/components/browse/ContentRow.tsx` | Keep as featured carousel |
| `frontend/components/browse/ProductGrid.tsx` | Ensure clean grid layout |

## New Components Needed

| Component | Purpose |
|-----------|---------|
| `AnimatedLogo.tsx` | Video player with session-aware playback |
| `HomeSearchBar.tsx` | Centered search with "Ask AI" link behavior |

## Design Principles

1. **Minimal** - Remove everything that doesn't serve a direct purpose
2. **Clean** - White/neutral backgrounds, accent colors only on interactive elements
3. **Focused** - Logo and search bar are the hero, products support discovery
4. **Fast** - Video plays once, no repeated animations, efficient rendering
