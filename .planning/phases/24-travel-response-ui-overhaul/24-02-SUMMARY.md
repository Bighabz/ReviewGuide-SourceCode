---
phase: 24-travel-response-ui-overhaul
plan: "02"
subsystem: frontend/travel-ui
tags: [travel, ui, hotel-cards, flight-cards, typography, conclusion-block]
dependency_graph:
  requires: [24-01]
  provides: [hotel-plp-hero-image, flight-plp-hero-image, travel-typography-cleanup, conclusion-tinted-bg]
  affects: [HotelCards, FlightCards, DestinationInfo, ItineraryView, ListBlock, BlockRegistry]
tech_stack:
  added: []
  patterns: [color-mix-tinted-background, overflow-clip-card-layout, hero-image-band]
key_files:
  created: []
  modified:
    - frontend/components/HotelCards.tsx
    - frontend/components/FlightCards.tsx
    - frontend/components/DestinationInfo.tsx
    - frontend/components/ItineraryView.tsx
    - frontend/components/ListBlock.tsx
    - frontend/components/blocks/BlockRegistry.tsx
decisions:
  - "overflow-clip used on card wrapper (not overflow-hidden) per Phase 23 decision — prevents scroll containment BFC issues"
  - "p-0 outer card + p-5 inner content div pattern for image-top card layout"
  - "tracking-wider retained in TraditionalFlightCard airport code labels — only removed from PLPLinkCard destination spans"
metrics:
  duration: 331s
  completed: "2026-04-01"
  tasks_completed: 2
  files_modified: 6
---

# Phase 24 Plan 02: Travel Response UI Overhaul — PLPLinkCard & Typography Summary

Hotel and flight PLPLinkCards upgraded from empty icon boxes to visual cards with destination hero images; all travel section headers migrated from decorative serif to clean sans-serif; Caribbean text-wrapping bug eliminated; conclusion block given a color-mix tinted background.

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Hotel and Flight PLPLinkCard overhaul | 3daf06a | HotelCards.tsx, FlightCards.tsx |
| 2 | Typography cleanup, conclusion block, spacing polish | 317076d | DestinationInfo.tsx, ItineraryView.tsx, ListBlock.tsx, BlockRegistry.tsx |

## What Was Built

### Task 1 — Hotel and Flight PLPLinkCard Overhaul

**HotelCards.tsx PLPLinkCard:**
- Replaced centered search-icon layout with image-top + content-below structure
- Added `relative h-[120px] sm:h-[140px] overflow-clip` hero image band using `fallback-hotel.webp`
- Gradient overlay `from-black/30 to-transparent` on hero image
- Outer card: `p-0 overflow-clip` (was `p-8`); inner content: `p-5`
- CTA changed from "Search Properties" to "Search on Expedia"
- Provider badge: `text-[10px] px-2 py-1 opacity-60` (was `text-xs px-3 py-1.5`)
- Title h4: `font-sans font-bold text-lg sm:text-xl` (was `font-serif font-semibold text-xl`)
- TraditionalHotelCard h4: `font-sans font-bold text-lg` (was `font-serif font-semibold text-xl`)
- Section h3: `font-sans font-bold text-xl` (was `font-serif text-2xl font-semibold`)
- Removed unused `Search` lucide import

**FlightCards.tsx PLPLinkCard:**
- Same image-top restructuring using `fallback-flight.webp`
- Fixed Caribbean text wrapping: destination spans changed from `text-xl font-bold tracking-wider` to `text-base sm:text-lg font-bold whitespace-nowrap`
- CTA changed from "Search Flights" to "Search on Expedia"
- Provider badge shrunken to match hotel treatment
- Title h4: `font-sans font-bold text-lg sm:text-xl`
- Section h3: `font-sans font-bold text-xl`
- Removed unused `Search` lucide import

### Task 2 — Typography Cleanup and Conclusion Block

**DestinationInfo.tsx:**
- All 4 h4 headers (Weather & Climate, Best Time to Visit, Travel Tips, Local Customs & Etiquette): `font-serif` -> `font-sans`, `text-base` -> `text-[15px]`
- Travel Tips h4 preserves `mb-3` (others use `mb-1`)

**ItineraryView.tsx:**
- Main h3 "Your Itinerary": `font-serif text-xl` -> `font-sans font-bold text-xl`
- Day title h4: `font-serif text-lg` -> `font-sans font-bold text-lg`

**ListBlock.tsx:**
- Section h3: `font-serif font-bold text-lg` -> `font-sans font-bold text-lg`

**BlockRegistry.tsx — conclusion renderer:**
- `mt-4` -> `mt-2` (reduce dead space above)
- `px-3 sm:px-4 py-3 rounded-2xl rounded-tl-md` -> `p-4 rounded-xl`
- `bg-[var(--surface-elevated)]` -> `style={{ background: 'color-mix(in srgb, var(--primary) 6%, var(--surface))' }}`
- `text-[var(--text)]` -> `text-[var(--text-secondary)]`

## Test Results

All 11 travelUI tests pass:
- TRVL-01: ResortCards renders cards not bullet list items — PASS
- TRVL-02: ResortCards uses deterministic image fallback — PASS
- TRVL-03: HotelCards PLPLinkCard renders hero image — PASS
- TRVL-04: HotelCards PLPLinkCard CTA reads "Search on Expedia" — PASS
- TRVL-05: FlightCards PLPLinkCard CTA reads "Search on Expedia" — PASS
- TRVL-06: FlightCards PLPLinkCard destination no tracking-wider — PASS
- TRVL-07: BlockRegistry conclusion block has color-mix style — PASS

Build: clean (no TypeScript errors)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] ResortCards.tsx already existed from partial Plan 01 execution**
- **Found during:** Task 1 — travelUI test suite failed to run due to missing ResortCards import
- **Issue:** Test file references `@/components/ResortCards` which appeared missing. Glob search initially returned no results.
- **Fix:** Read the file — ResortCards.tsx and the BlockRegistry wiring were already present (Plan 01 partial execution). No action needed. Tests ran correctly once the HotelCards/FlightCards changes were made.
- **Files modified:** None (investigation only)

## Decisions Made

1. `overflow-clip` used on card wrapper (not `overflow-hidden`) — consistent with Phase 23 decision to prevent scroll containment BFC issues
2. `p-0` outer card + `p-5` inner content div pattern enables hero image flush to card edges
3. `tracking-wider` retained in TraditionalFlightCard airport code labels (`text-xs`) — plan only required removing it from PLPLinkCard destination spans (Caribbean wrapping issue specific to the large `text-xl` spans)

## Self-Check

### Files Verified

- HotelCards.tsx: fallback-hotel.webp hero image present, "Search on Expedia" CTA, no font-serif
- FlightCards.tsx: fallback-flight.webp hero image present, "Search on Expedia" CTA, no font-serif, no tracking-wider on destination span
- DestinationInfo.tsx: all 4 h4 headers use font-sans
- ItineraryView.tsx: h3 and h4 use font-sans font-bold
- ListBlock.tsx: h3 uses font-sans font-bold
- BlockRegistry.tsx: conclusion renderer has color-mix inline style

### Commits Verified

- 3daf06a — Task 1 (HotelCards, FlightCards)
- 317076d — Task 2 (DestinationInfo, ItineraryView, ListBlock, BlockRegistry)

## Self-Check: PASSED
