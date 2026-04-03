# Phase 24: Travel Response UI Overhaul - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning
**Source:** PRD Express Path (C:\Users\habib\Downloads\travel-ui-overhaul-dev-prompt22.md)

<domain>
## Phase Boundary

This phase transforms travel chat responses from a text wall with pin icons into a visual, card-based experience matching or exceeding the product card quality. Three priorities: (1) resort cards with hero images replacing the flat bullet list, (2) hotel/flight widget cards with destination imagery replacing empty placeholder boxes, (3) spacing and typography cleanup for cohesive response layout. Mobile-first throughout.

</domain>

<decisions>
## Implementation Decisions

### Priority 1: Resort Cards (Must-See Attractions)
- Replace flat bullet list (pin icon + resort name) with card-based layout
- Single-column full-width stack on mobile, 2-column grid on desktop (768px+ breakpoint)
- Each card: hero image (~60% card height mobile, 16:9 or 3:2 aspect), bold resort name, lighter location text, star rating if available, price indicator ("From $XXX/night") if available, CTA ("View Details" / "Check Availability") linking to booking partner
- Image sourcing priority: (1) hotel/travel API real photos, (2) AI-generated fallbacks based on resort name + location, (3) generic destination placeholder
- Lazy load images — don't load all upfront
- Touch targets minimum 44px tall on CTAs
- Card gap 12-16px between stacked cards

### Priority 2: Hotel & Flight Widget Cards
- Add destination hero image (beach/ocean for hotels, sky/aerial for flights)
- Stack vertically on mobile (no side-by-side — that's causing "Caribb ean" text wrapping bug)
- Side-by-side only at tablet+ (768px+)
- Hero image ~120-150px height on mobile (shorter than resort cards — these are functional CTAs)
- Shrink "Powered by Expedia" badge — too much visual weight currently
- Fix "Caribbean" text wrapping bug
- Update CTA labels: "Search Properties" → "Search on Expedia" (sets expectation of external link)
- CTA button full card width on mobile

### Priority 3: Spacing, Typography & Visual Hierarchy
- Reduce dead space between user message bubble and bot reply
- Wrap entire travel response in consistent container with uniform padding (16px mobile, 24px desktop)
- Switch section headers to same sans-serif font family as body text (just bolder/larger) — current decorative serif clashes
- Add subtle dividers or consistent spacing rhythm between sections
- Style "Want better results?" prompt as distinct secondary CTA with background tint or border
- Section spacing: 24px between major sections on mobile
- Font sizes: body 14-16px, section headers 18-20px, card titles 16-18px, minimum 14px anywhere

### Image Generation
- 10 specific resort AI prompts provided in PRD for Caribbean query
- Generate destination hero images per region (Caribbean, Europe, etc.) reusable across queries
- Generic beach/resort placeholder as last fallback
- All images WebP, under 200KB

### Claude's Discretion
- Whether to use horizontal swipe carousel vs vertical scroll for resort cards on mobile
- Specific implementation of image sourcing from travel APIs (Google Places, Amadeus, etc.)
- How to structure the fallback image generation pipeline
- Exact CSS for card hover/touch states
- Whether hotel/flight widget images are background overlays or top sections

</decisions>

<specifics>
## Specific Ideas

### Frontend components to create/modify
- New `ResortCard.tsx` component (card layout with hero image, name, location, rating, price, CTA)
- Modify `HotelCards.tsx` — add destination hero image, fix text wrapping, stack vertically on mobile
- Modify `FlightCards.tsx` — add destination hero image, fix text wrapping, stack vertically on mobile  
- Modify `DestinationInfo.tsx` — may need restructuring for card-based attractions layout
- Modify `Message.tsx` travel response container — spacing, padding, typography consistency

### AI image prompts (from PRD)
- 10 specific resort prompts for Caribbean query
- Generic destination hero images (Caribbean beach, European city, Asian temple, etc.)

### Design reference
- Target UX: Airbnb search results, Google Travel — visual-first, scannable cards, clear actions
- NOT a ChatGPT text dump

</specifics>

<deferred>
## Deferred Ideas

- Google Places API integration for real resort photos (requires API key + billing)
- Open Graph image scraping from resort websites
- Dynamic AI image generation per resort at runtime (expensive, slow)
- Horizontal swipe carousel for mobile resort cards (test vertical first)

</deferred>

---

*Phase: 24-travel-response-ui-overhaul*
*Context gathered: 2026-04-03 via PRD Express Path*
