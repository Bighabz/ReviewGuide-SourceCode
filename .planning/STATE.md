---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Visual Overhaul â Bold Editorial
status: executing
stopped_at: "24-03 Task 1 complete — checkpoint:human-verify pending"
last_updated: "2026-04-03T23:10:37.861Z"
last_activity: 2026-04-01 — 18-02 complete (15 category hero images approved)
progress:
  total_phases: 24
  completed_phases: 22
  total_plans: 69
  completed_plans: 66
  percent: 92
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-01)

**Core value:** Conversational product discovery that searches live reviews and returns blog-style editorial responses with cross-retailer affiliate links.
**Current focus:** Milestone v3.0 — Visual Overhaul "Bold Editorial" — Phase 17 ready to plan

## Current Position

Phase: 18 of 22 (AI Image Generation)
Plan: 02 complete, ready for 03
Status: In Progress
Last activity: 2026-04-01 — 18-02 complete (15 category hero images approved)

Progress: [█████████░] 92%

## Performance Metrics

**Velocity:**
- Total plans completed: 0 (v3.0)
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

*Updated after each plan completion*
| Phase 17-token-foundation-dark-mode-fixes P01 | 2 | 2 tasks | 1 files |
| Phase 17-token-foundation-dark-mode-fixes P02 | 110s | 3 tasks | 3 files |
| Phase 18-ai-image-generation P01 | 8 | 2 tasks | 2 files |
| Phase 18-ai-image-generation P02 | 5 | 1 tasks | 16 files |
| Phase 18-ai-image-generation P03 | 8 | 2 tasks | 54 files |
| Phase 18-ai-image-generation P03 | 35 | 3 tasks | 54 files |
| Phase 19-mosaic-hero P01 | 12 | 1 tasks | 3 files |
| Phase 19-mosaic-hero P02 | 6 | 1 tasks | 1 files |
| Phase 23-qa-remediation-unified-bug-fixes P00 | 8 | 1 tasks | 1 files |
| Phase 23-qa-remediation-unified-bug-fixes P03 | 382 | 2 tasks | 9 files |
| Phase 23-qa-remediation-unified-bug-fixes P02 | 581 | 2 tasks | 7 files |
| Phase 23-qa-remediation-unified-bug-fixes P01 | 609 | 2 tasks | 2 files |
| Phase 23-qa-remediation-unified-bug-fixes P04 | 344 | 2 tasks | 3 files |
| Phase 23-qa-remediation-unified-bug-fixes P05 | 435 | 2 tasks | 6 files |
| Phase 23-qa-remediation-unified-bug-fixes P06 | 18 | 2 tasks | 2 files |
| Phase 20-discover-browse-page-upgrades P02 | 6 | 2 tasks | 4 files |
| Phase 21-chat-results-card-polish P01 | 7 | 3 tasks | 5 files |
| Phase 20-discover-browse-page-upgrades P01 | 8 | 2 tasks | 6 files |
| Phase 21-chat-results-card-polish P02 | 796 | 2 tasks | 3 files |
| Phase 21-chat-results-card-polish P03 | 12 | 2 tasks | 4 files |
| Phase 22-visual-qa-consistency-pass P02 | 291 | 2 tasks | 12 files |
| Phase 22-visual-qa-consistency-pass P01 | 321 | 2 tasks | 6 files |
| Phase 24-travel-response-ui-overhaul P01 | 310 | 2 tasks | 3 files |
| Phase 24-travel-response-ui-overhaul P02 | 331 | 2 tasks | 6 files |
| Phase 24-travel-response-ui-overhaul P03 | 525 | 1 tasks | 10 files |

## Accumulated Context

### Decisions

- [v3.0]: Keep light/ivory base, inject bold colors — not switching to dark mode default
- [v3.0]: Bold & colorful AI-generated product imagery — vibrant, eye-catching, strong contrast
- [v3.0]: Rich info cards over minimal — keep pros/cons/ratings but make them premium
- [v3.0]: Never touch Message.tsx or BlockRegistry.tsx structure — streaming pipeline protected
- [v3.0]: Use `gpt-image-1` (not DALL-E 3 — retired March 4, 2026) for image generation
- [v3.0]: Generate all images in one batch session before any component references them
- [v3.0]: Add `class-variance-authority@0.7.1` for ProductCard multi-mode variant API
- [Phase 17-token-foundation-dark-mode-fixes]: Typography tokens declared identically in dark block for completeness even though values are theme-neutral
- [Phase 17-token-foundation-dark-mode-fixes]: Bold accent dark values use Tailwind 400-range pastels for accessible contrast on dark backgrounds
- [Phase 17-token-foundation-dark-mode-fixes]: Global h1/h2/h3 rules unchanged — typography tokens are opt-in utilities for Phase 20+ components
- [Phase 17-token-foundation-dark-mode-fixes]: Removed dark:text-emerald-400 from TopPickBlock.tsx — the data-theme strategy renders all Tailwind dark: prefixes silently inert
- [Phase 18-ai-image-generation]: Tests use existsSync guard + early return (not it.skip) — Vitest throws error if it.skip called inside running test
- [Phase 18-ai-image-generation]: optimize-images.mjs uses createRequire to load sharp from frontend/node_modules so script runs from project root
- [Phase 18-ai-image-generation]: Re-encode at quality=60 if first WebP pass exceeds 200KB — keeps batch automation unattended
- [Phase 18-ai-image-generation]: Used Gemini Imagen 4.0 (imagen-4.0-generate-001) instead of Imagen 3 — Imagen 3 not listed in models; Imagen 4.0 available and produced excellent quality
- [Phase 18-ai-image-generation]: Used direct REST API instead of MCP tool — nano-banana MCP not connected in session, direct API call achieved identical results
- [Phase 18-ai-image-generation]: Used direct Gemini REST API instead of MCP for mosaic image generation (nano-banana not connected — same approach as Plan 18-02)
- [Phase 18-ai-image-generation]: All 53 PNGs converted to WebP at quality=75 in single pass — no quality=60 re-encode needed, largest output 87KB
- [Phase Phase 18-ai-image-generation]: Human visual QA approved all 8 mosaic tiles — varied compositions, vibrant colors, consistent editorial style, no regen needed
- [Phase 19-mosaic-hero]: Use raw <img> tags (not next/image) — consistent with entire codebase convention
- [Phase 19-mosaic-hero]: Static MOSAIC_TILES const array (not Math.random()) — avoids SSR hydration mismatch
- [Phase 19-mosaic-hero]: overflow: visible on MosaicHero container — rotated tile edges should not clip; outer wrapper clips in Plan 02
- [Phase 19-mosaic-hero]: outer hero wrapper gains relative + overflow-hidden + rounded-2xl to clip rotated tile bleed at container boundary
- [Phase 19-mosaic-hero]: scrim uses var(--mosaic-scrim) CSS variable — dark mode gradient works without JS
- [Phase 23-qa-remediation-unified-bug-fixes]: Baseline captures .env affiliate tag (mikejahshan-20) AND code hardcoded fallback (revguide-20) separately — discrepancy is a QAR-07 bug to fix
- [Phase 23-qa-remediation-unified-bug-fixes]: 8 canonical prompts map directly to QAR bug IDs (QAR-01 through QAR-07) rather than generic smoke tests
- [Phase 23-qa-remediation-unified-bug-fixes]: tool_timing uses Dict[str, float] merged via spread pattern — tools do state.get('tool_timing', {}) merge rather than operator.add accumulation
- [Phase 23-qa-remediation-unified-bug-fixes]: Partial data note in travel_compose only shown when fewer than 3 keys are missing — avoids verbose listing when everything failed (recovery path handles that case)
- [Phase 23-qa-remediation-unified-bug-fixes]: Use overflow-clip instead of overflow-hidden everywhere — clip prevents scroll containment issues while hidden creates BFC that crushes flex children
- [Phase 23-qa-remediation-unified-bug-fixes]: Chat input z-index raised to z-[300] (above MobileTabBar z-[200]) so chat bar is always visible on mobile
- [Phase 23-qa-remediation-unified-bug-fixes]: Removed minWidth: fit-content from user bubble — causes 167px collapse in constrained parents on mobile
- [Phase 23-qa-remediation-unified-bug-fixes]: Relaxed multi-provider gate from >=2 providers to >=1 real offer — single-retailer products with valid URLs should not be silently dropped
- [Phase 23-qa-remediation-unified-bug-fixes]: Fallback loop split: cap check uses break, duplicate check uses continue — preserves 5-card cap while iterating past duplicates
- [Phase 23-qa-remediation-unified-bug-fixes]: Label-domain parity: correct Amazon labels pointing to non-Amazon URLs rather than excluding the offer entirely
- [Phase Phase 23-qa-remediation-unified-bug-fixes]: Accessory suppression applied at three layers in compose: products_with_offers loop, review_bundles blog iteration, and fallback card path
- [Phase Phase 23-qa-remediation-unified-bug-fixes]: _parse_budget returns (None, None) on no match — budget filtering only activates when budget string is parseable; all offers preserved if all exceed budget
- [Phase 23-qa-remediation-unified-bug-fixes]: Sentinel bottomRef scroll replaces setInterval polling — reliable iOS Safari behaviour
- [Phase 23-qa-remediation-unified-bug-fixes]: Queue user messages during streaming via useState + useEffect instead of silent drop (QAR-18)
- [Phase 23-qa-remediation-unified-bug-fixes]: trackSessionId helper centralises chat_all_session_ids writes; session ID in URL for browser history continuity
- [Phase Phase 23-qa-remediation-unified-bug-fixes]: Budget enforcement gate tests mixed-offer scenario (some in-budget, some not) per design — all-over-budget products are intentionally kept
- [Phase Phase 23-qa-remediation-unified-bug-fixes]: Regression gate CI commands: python -m pytest tests/test_regression_gate.py -v (backend) + npm run test -- --run tests/regressionGate.test.tsx (frontend)
- [Phase 20-discover-browse-page-upgrades]: color-mix(in srgb) used for tinted chip backgrounds — avoids adding new CSS classes, works inline with CSS variables
- [Phase 20-discover-browse-page-upgrades]: TrendingCards thumbnail uses topic.iconBg as CSS background fallback while lazy images load — prevents empty white box
- [Phase 20-discover-browse-page-upgrades]: Per-item accent color as data field (accentColor in ChipConfig) rather than hardcoded CSS class map
- [Phase 21-chat-results-card-polish]: Wave 0 cardAnimations tests use transparent framer-motion mock recording whileHover/transition as data attributes for spring config assertion without full runtime
- [Phase 21-chat-results-card-polish]: InlineProductCard price color changed from --text-primary to --text (V3 canonical token)
- [Phase 21-chat-results-card-polish]: product-card-hover CSS class removal deferred to Plan 02 per CARD-04 contract
- [Phase 20-discover-browse-page-upgrades]: kids-toys mapped to cat-gaming.webp, baby to cat-home-decor.webp, big-tall reuses cat-fashion.webp as closest editorial match
- [Phase 20-discover-browse-page-upgrades]: CuratedProduct.name is optional field — fallback to Option N preserves backward compat for categories without names
- [Phase 21-chat-results-card-polish]: Use as const on 'spring' and 'easeOut' string literals in Framer Motion variants — Easing union type does not accept bare string
- [Phase 21-chat-results-card-polish]: deriveMerchant pattern: clean merchant field first, fall back to URL hostname domainMap, then capitalize first subdomain segment
- [Phase 21-chat-results-card-polish]: ResultsPage source dots upgraded alongside ResultsMainPanel for visual consistency and test coverage via ResultsPage render
- [Phase 21-chat-results-card-polish]: V3 badge pattern: --bold-amber/--bold-blue/--bold-green bg with white text + px-2.5 py-1 rounded-md font-bold tracking-wider for stronger badge presence
- [Phase 22-visual-qa-consistency-pass]: ListBlock colorMap refactored to styleMap using React.CSSProperties objects instead of Tailwind class strings
- [Phase 22-visual-qa-consistency-pass]: SourceCitations DOT_COLORS changed from hex literals to CSS variable strings for theme-aware dot colors
- [Phase 22-visual-qa-consistency-pass]: sourceCitations test assertions updated to query [style*='--bold-red/blue/green'] matching inline-style dot approach
- [Phase 22-visual-qa-consistency-pass]: MobileTabBar tests updated: 3 Link tabs + 1 Settings button = 4 elements, not 5 buttons; tabs use Link not button
- [Phase 22-visual-qa-consistency-pass]: chatScreen CHAT-03: empty statusText renders dots animation only, no Thinking... text span in DOM
- [Phase 22-visual-qa-consistency-pass]: resultsScreen: ResultsProductCard CTA is Check Price not Buy on Amazon; rank badge shows plain number + TOP PICK badge
- [Phase 22-visual-qa-consistency-pass]: designTokens: 15 new V3.0 token assertions using dark block extraction pattern globals.slice(darkIdx, darkIdx + 3000)
- [Phase 24-travel-response-ui-overhaul]: ResortCards splits comma-separated attraction names into primary + location hint for cleaner card display
- [Phase 24-travel-response-ui-overhaul]: RESORT_IMAGE_MAP uses lowercase substring matching — robust against backend string variations
- [Phase 24-travel-response-ui-overhaul]: Used overflow-clip (not overflow-hidden) on resort cards per Phase 23 convention
- [Phase 24-travel-response-ui-overhaul]: overflow-clip used on PLPLinkCard wrapper (not overflow-hidden) per Phase 23 decision — prevents scroll containment BFC issues
- [Phase 24-travel-response-ui-overhaul]: p-0 outer card + p-5 inner content div pattern for image-top PLPLinkCard layout
- [Phase 24-travel-response-ui-overhaul]: Used OpenAI gpt-image-1 instead of Gemini Imagen — Gemini API key reported as leaked (403 PERMISSION_DENIED); OpenAI key in backend/.env worked and produced equivalent editorial quality

### Pending Todos

- v4.0 planned: Full affiliate overhaul (eBay real campaign ID, CJ activation, Expedia integration, Amazon PA-API application)
- Amazon PA-API v5 retires May 15, 2026 — Phase 5 migration needed before deadline

### Roadmap Evolution

- Phase 23 added: QA Remediation — Unified Bug Fixes

### Blockers/Concerns

- [Phase 18]: gpt-image-1 pricing ($0.015/image) and quality params are MEDIUM confidence — validate with actual API call before generating full batch
- [Phase 20]: WCAG AA contrast for category hero overlays depends on each image's luminance — cannot be pre-calculated; measure during implementation

## Session Continuity

Last session: 2026-04-03T23:10:37.856Z
Stopped at: 24-03 Task 1 complete — checkpoint:human-verify pending
Resume file: None
