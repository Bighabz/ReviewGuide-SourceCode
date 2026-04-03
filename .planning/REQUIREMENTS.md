# Requirements: ReviewGuide.ai v3.0 Visual Overhaul — Bold Editorial

**Defined:** 2026-04-01
**Core Value:** Conversational product discovery that searches live reviews and returns blog-style editorial responses with cross-retailer affiliate links.

## v3.0 Requirements

### Design Tokens

- [x] **TOK-01**: Bold accent color palette added to CSS variables (vibrant blues, terracotta, energetic greens) with light mode values
- [x] **TOK-02**: Typography scale upgraded — larger/bolder headings, tighter line heights, stronger visual hierarchy
- [x] **TOK-03**: All new tokens have matching `[data-theme="dark"]` counterparts (no dark mode regressions)

### AI Image Generation

- [x] **IMG-01**: Generate 15+ bold & colorful product category hero images (headphones, laptops, kitchen, travel, fitness, etc.) using consistent style prompt
- [x] **IMG-02**: Generate 8+ mosaic tile images (diverse products at varied angles) for landing page hero collage
- [x] **IMG-03**: All generated images pre-optimized (WebP, <200KB each) and stored in public/images/

### Mosaic Hero

- [x] **HERO-01**: User sees Shopify-style mosaic collage of product images as the landing page hero background
- [x] **HERO-02**: Search bar and headline float centered over the mosaic with readable contrast
- [x] **HERO-03**: Mosaic uses CSS Grid with tilted/overlapping cards — no additional JS library
- [x] **HERO-04**: First visible image uses loading="eager" to avoid LCP regression

### Discover Page Polish

- [x] **DISC-06**: Category chips and trending cards use bolder colors and stronger visual presence
- [x] **DISC-07**: Product carousel uses real product images with loading="eager" on first slide

### Browse Pages Polish

- [x] **BRW-01**: Category hero sections use new AI-generated bold images as backgrounds
- [x] **BRW-02**: Editor's Picks cards have bolder styling consistent with new visual language

### Chat Page Polish

- [x] **CHT-01**: AI response bubbles have updated typography (bolder headings, better spacing)
- [x] **CHT-02**: Inline product cards have subtle hover animations and bolder price display

### Product Cards

- [x] **CARD-01**: ProductReview cards have premium spacing, stronger typography, and subtle entrance animations
- [x] **CARD-02**: "Where to Buy" section uses clean 3-column layout with merchant labels derived from URL
- [x] **CARD-03**: TopPickBlock has bolder visual treatment — stronger gradient CTA, larger product image
- [x] **CARD-04**: Card hover effects use spring animations via Framer Motion

### Results Page Polish

- [x] **RES-07**: Product grid cards match new bold visual language
- [x] **RES-08**: Sources section has stronger visual presence with bolder dot colors

### Visual QA

- [ ] **QA-01**: Full site screenshot walk-through on mobile and desktop confirms visual consistency
- [ ] **QA-02**: designTokens.test.ts updated to cover new tokens
- [ ] **QA-03**: No hardcoded colors remain in refreshed components (all use CSS variables)

## v4.0 Requirements (Deferred)

### Affiliate Overhaul

- **AFF-01**: Real eBay EPN campaign ID configured on Railway
- **AFF-02**: CJ activated on Railway with real credentials
- **AFF-03**: Expedia affiliate integration
- **AFF-04**: Amazon PA-API application and integration

## Out of Scope

| Feature | Reason |
|---------|--------|
| Dark mode as default | User chose light base with bold accents |
| Page transition redesign | Existing Framer Motion transitions work well |
| Video backgrounds | Performance concern, bandwidth cost |
| Glassmorphism effects | Fragile across browsers, not editorial |
| Custom cursors | Gimmicky, accessibility concern |
| Message.tsx structural changes | Protected SSE streaming pipeline |
| BlockRegistry.tsx changes | Protected block dispatch architecture |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TOK-01 | Phase 17 | Complete |
| TOK-02 | Phase 17 | Complete |
| TOK-03 | Phase 17 | Complete |
| IMG-01 | Phase 18 | Complete |
| IMG-02 | Phase 18 | Complete |
| IMG-03 | Phase 18 | Complete |
| HERO-01 | Phase 19 | Complete |
| HERO-02 | Phase 19 | Complete |
| HERO-03 | Phase 19 | Complete |
| HERO-04 | Phase 19 | Complete |
| DISC-06 | Phase 20 | Complete |
| DISC-07 | Phase 20 | Complete |
| BRW-01 | Phase 20 | Complete |
| BRW-02 | Phase 20 | Complete |
| CHT-01 | Phase 21 | Complete |
| CHT-02 | Phase 21 | Complete |
| CARD-01 | Phase 21 | Complete |
| CARD-02 | Phase 21 | Complete |
| CARD-03 | Phase 21 | Complete |
| CARD-04 | Phase 21 | Complete |
| RES-07 | Phase 21 | Complete |
| RES-08 | Phase 21 | Complete |
| QA-01 | Phase 22 | Pending |
| QA-02 | Phase 22 | Pending |
| QA-03 | Phase 22 | Pending |

**Coverage:**
- v3.0 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0

---
*Requirements defined: 2026-04-01*
*Traceability mapped: 2026-04-01*
