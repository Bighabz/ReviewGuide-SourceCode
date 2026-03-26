# ReviewGuide.ai v3 Frontend Redesign Brief

**Date:** 2026-03-26
**Status:** Approved by user
**Source:** Direct user feedback after competitive review (Amazon, Best Buy, RTINGS)

## User Feedback Summary

- Homepage is "essentially a slightly themed Google search page" — needs visual product catalog
- Streaming still shows "Thinking..." for ~10s (Phase A-C just deployed, retest needed)
- Product images inconsistent — some show, many blank placeholders
- Dark mode is just an inversion, no richness/depth
- Category pills on homepage are redundant with sidebar

## Requirements

### 1. STREAMING RESPONSES (already partially addressed in Phase A-C)
- Text begins appearing within 200ms of first token
- Auto-scroll follows streaming text
- Typing/shimmer animation during initial wait
- Product cards render progressively

### 2. PRODUCT IMAGES EVERYWHERE
- Nano Banana MCP (Gemini Flash Image) for generated hero/category art
- Real product photos from: Amazon CDN (ASIN), Serper Shopping, eBay API
- Fallback chain: affiliate provider image > ASIN CDN > Serper Image Search > Nano Banana generated > branded category placeholder
- NO blank/placeholder images ever
- Cache fetched images for performance

### 3. DARK-FIRST THEME OVERHAUL
- Default dark: deep charcoal (#0D0F12), surface cards (#161921), border (#1E2330)
- Accent: electric blue (#3B82F6) or vibrant orange-gold for CTAs
- Text: off-white (#E8EAED) primary, muted gray (#9CA3AF) secondary
- Subtle gradient overlays, layered surfaces, glow/shadow on hover
- Rating stars: vivid gold/amber
- Price badges: green for deals, orange for regular
- Light mode: warm off-white (#F8F7F4), soft shadows, visual texture
- Vibe: premium tech review + modern e-commerce (RTINGS + Best Buy)

### 4. HOMEPAGE REDESIGN — VISUAL PRODUCT CATALOG
- A: Full-width hero with animated gradient or product collage, bold heading, prominent search bar
- B: REMOVE category pill bubbles from main content
- C: Left sidebar always visible (same as /chat — Quick Searches + Categories with icons)
- D: Main content = scrollable catalog grid with Netflix/Amazon-style horizontal rows per category, product IMAGE + name + rating + price + one-line summary, clickable to start research
- E: Sticky bottom search bar pinned to viewport at all times

### 5. CHAT PAGE REFINEMENTS
- Keep left sidebar as-is
- Product cards ALWAYS have images
- Sticky bottom input
- Typing/shimmer animation while waiting
- "Compare" button on product cards

### 6. RESPONSIVE & POLISH
- Sidebar = slide-out drawer on mobile
- Catalog grid = vertical scrolling cards on mobile
- Smooth transitions, micro-animations, hover effects
- Loading skeletons with shimmer (not blank space)
- Premium, polished, product-forward feel

## Image Strategy

### Real Product Images (for product cards)
1. Affiliate provider images (eBay, Serper Shopping, Amazon PA-API)
2. Amazon CDN via ASIN: `images-na.ssl-images-amazon.com/images/I/{ASIN}._SL300_.jpg`
3. Serper Image Search fallback (search for product name)
4. Branded category placeholder (last resort)

### Generated Images (for UI chrome)
- Nano Banana MCP (Gemini 2.5 Flash Image) for:
  - Homepage hero art
  - Category header images
  - Trending topic cards
  - Branded placeholders when no real image available

## Nano Banana MCP Setup
- Package: `@anthropic-ai/nano-banana-mcp` or community fork from ConechoAI
- Requires: `GOOGLE_AI_API_KEY` (Gemini API key)
- GitHub: https://github.com/ConechoAI/Nano-Banana-MCP

## Competitive Reference
- **Amazon:** Product imagery everywhere, category grids, deal cards
- **Best Buy:** Bold hero banner, visual category tiles, price-driven blocks
- **RTINGS:** Full-bleed hero, massive typography, stats, real product photography catalog grid
