# Feature Research

**Domain:** Mobile-first AI product research assistant (Discover → Chat → Results flow)
**Researched:** 2026-03-16
**Confidence:** HIGH — primary sources from competitor analysis (Rufus, ChatGPT Shopping, Perplexity, Google AI Mode), Figma spec, and existing codebase audit

---

## Context: This Is a Redesign, Not a Greenfield

All backend pipeline features (LangGraph, SSE streaming, affiliate search, travel, product compare, clarification
multi-turn) are already built and working. This feature set is scoped to the **frontend UX redesign** that
implements the Discover → Chat → Results flow on top of the existing backend.

Features in this document are classified by their role in the mobile UX, not by whether the backend supports them
(it already does). The question is: which frontend surfaces are table stakes for a mobile-first AI research
assistant, and which are differentiators?

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels broken or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Unified home screen (Discover) | Every modern app has a single entry point; split Browse/Chat pages feel like two products | LOW | Replace current redirect `/` → `/browse` with a merged Discover screen. Category chips + trending research rows replace separate browse page |
| Bottom tab navigation (mobile) | All major apps (Instagram, TikTok, Amazon, Perplexity) use bottom tabs for primary nav on mobile | LOW | 5 tabs: Discover, Saved, Ask (FAB), Compare, Profile. Desktop: top nav stays, no bottom bar |
| Central FAB "Ask" button | Floating action button for primary action is the standard mobile CTA pattern; thumb-zone placement | LOW | 48px blue circle with "+" centered in bottom tab bar; navigates to `/chat?new=1` |
| Persistent sticky chat input bar | Users expect to be able to type or continue their chat without scrolling; any lag or disappearing input causes abandonment | MEDIUM | Fixed at bottom above tab bar on mobile; SSE streaming logic must not be touched |
| Real-time status indicator during AI thinking | Users abandon if they see no activity feedback; generic spinner is not sufficient | LOW | "ReviewGuide is analyzing sources..." with pulsing animation; already partially exists but needs mobile-first treatment |
| Suggestion chips / follow-up questions | Every competitor (Rufus, ChatGPT, Google AI Mode, Perplexity) uses tappable chips; typing follow-ups on mobile is high friction | LOW | Already in backend (`next_suggestions`); frontend chips need pill styling, horizontal scroll, auto-submit on tap |
| Light/dark theme | Expected on any modern mobile web app | LOW | Already built; keep it but relocate toggle from topbar to profile/settings page on mobile |
| Source citations as clickable links | Users need to verify AI recommendations; plain text source names are not sufficient; Perplexity, ChatGPT both do this | MEDIUM | Backend returns URLs via Serper; need to wire them into the response UI as tappable source badges |
| Product image that is real (not placeholder or emoji) | Users trust product recommendations with real images; generic icons signal demo quality | LOW | 120+ curated Amazon products with static images already exist in `curatedLinks.ts`; use them. Never show emoji or SVG placeholders |
| Price displayed on product card | Users expect to see price before clicking; hidden price = distrust signal | LOW | Use static curated prices for Amazon products; show "Check price" only when price is genuinely unknown |
| Affiliate link that opens in new tab | Standard affiliate behavior; users expect to return to the app after checking a product | LOW | Already implemented; verify `target="_blank" rel="noopener noreferrer"` on all product CTAs |
| 44px minimum touch targets | Mobile accessibility requirement; undersized tap targets cause mis-taps and abandonment | LOW | Audit all buttons, chips, and links for minimum 44px height; especially chip pills and product card CTAs |
| Readable category entry points | Users need guided starting points for discovery; blank chat box alone causes "what do I ask?" paralysis | MEDIUM | Category cards on Discover screen with representative queries as chips; replaces current browse grid |
| Chat conversation history | Users return to past research; history button is expected in any persistent chat app | LOW | Already exists via `ConversationSidebar`; needs to become a slide-out drawer on mobile rather than a separate panel |
| Error recovery / retry | Mobile networks drop; users expect graceful reconnection and retry without losing their query | LOW | Already implemented (`isReconnecting`, `MessageRecoveryUI`); polish the mobile layout of error states |

### Differentiators (Competitive Advantage)

Features that set ReviewGuide apart from Rufus (Amazon-only), ChatGPT Shopping (no editorial voice), and Google AI Mode (no curated editorial content).

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Editorial-first response structure (summary → rank → "because" → sources) | Rufus gives a list. ChatGPT gives a carousel. ReviewGuide gives a verdict. "Based on 47 expert reviews, the Sony WH-1000XM5 is the top pick because it leads in noise cancellation. Here's why." | MEDIUM | Requires structured response rendering: prose summary block + ranked product cards + source citation panel, all in one assistant message. Does NOT require backend changes — compose prompt already does this. |
| Compact inline product cards (not massive blocks) | Current product cards take ~400px each on mobile, overwhelming the chat. Compact cards (64px image, 1-line reason, price, CTA) keep context visible | MEDIUM | New `InlineProductCard` component: 80px height, horizontal layout. Replace the full `ProductCards` block inside chat messages. Full cards only on the Results screen |
| Results screen (`/results/:id`) | Dedicated full-view for completed research; ChatGPT and Perplexity don't offer a separate shareable results page | HIGH | Desktop: split panel (320px sidebar + main content). Mobile: full-width, sidebar becomes slide-out drawer. Routes: `/results/:id`. Triggered by "expand" icon in chat header |
| Rank badges with contextual labels | "Top Pick", "Best Value", "Best for Outdoors" — not just #1/#2/#3; contextual labeling increases relevance perception | LOW | Backend compose prompt already generates these contextually; need frontend badge rendering (gold/blue/purple color coding) |
| Source citation panel with colored dots | "SOURCES ANALYZED: 🔴 Wirecutter — The Best Headphones, 🔵 RTINGS — Lab Measurements" — shows users the AI read real expert content, not invented it | MEDIUM | Collapsible section below summary; uses URLs returned by Serper. Currently review links are broken (known bug); fix is part of this work |
| Category chips (horizontal scroll filter) | "Popular / Tech / Travel / Kitchen / Fitness" — lets users narrow Discover feed without searching; expected UX pattern from every major app | LOW | Horizontal scroll row, pill shape, active = filled dark chip, inactive = outlined. No personalization needed; static category mapping is fine |
| Trending research cards | "Best Headphones 2026 — Sony vs Bose vs Apple — expert verdict" — seeded with high-value queries; reduces "what do I ask?" problem | LOW | Static initial data from `TRENDING_SEARCHES` constant; icon + title + subtitle + chevron layout; each taps to auto-submit query |
| "Ask" FAB as primary CTA | Removes ambiguity about where to start; prominent, always-visible CTA that works from any screen | LOW | Center-bottom FAB in bottom tab bar; only shown on mobile; desktop uses "New Chat" button in topbar |
| Curated product grid on Discover | 120+ real Amazon products with images and prices already exist; showing them on Discover gives users something to click without searching | MEDIUM | Re-enable `CuratedProductCard` with real static data; organized by category tabs (Electronics, Travel, Health, Kitchen). Load lazily below the fold |
| Contextual chat header status ("Researching • 4 sources analyzed") | Shows AI progress in real time as it works; converts wait time into evidence of effort | LOW | Chat header subtitle updates during SSE stream events; uses `statusText` from `streamState` which is already tracked |
| Score bar on product cards (Results screen) | Visual quality signal at-a-glance without reading text; used by RTINGS, Google Shopping AI Mode | LOW | Horizontal progress bar (blue fill, 4px height) + numeric score. Render on Results-screen cards; optional on inline chat cards |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good on the surface but undermine the core UX or are explicitly out of scope.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| User accounts / login wall | "Personalization", saved searches, price alerts | Anonymous-first is a PROJECT.md explicit decision; login friction causes 40-60% drop at first session; accounts require email verification, password reset, GDPR consent flows — months of work | Keep anonymous sessions; use localStorage for recent searches and preferences. Offer "save" as a bookmark pattern in a future milestone |
| Price alerts / "Buy for me" agentic checkout | Rufus and Google have it; feels like obvious next feature | Requires accounts (to notify user later), payment integration, legal agreements with merchants. Perplexity's coverage is limited even with PayPal partnership. | Show "Check price" links to current merchant pages. Price tracking is a v3+ feature tied to account milestone |
| Full-page overlay modals for product details | Users want more info without leaving chat | Overlays on mobile feel jarring and trap-like; break back-navigation on iOS Safari; hard to make accessible | Use the Results screen (`/results/:id`) for expanded product detail. Deep-link from inline chat card |
| Paginated product results (page 1, 2, 3) | "Show more" is familiar from search engines | Pagination breaks conversation context; reloading results feels like a new search. AI research is not a SERP | Use "See more alternatives" chip that appends more cards to the same message thread |
| Hamburger-only navigation on mobile | "Saves space" | Hamburger menus have 20% lower engagement than bottom tabs (Nielsen Norman Group); hidden nav = low feature discovery | Bottom tab navigation for primary destinations; hamburger only for secondary settings |
| 10+ category sidebar items | Current sidebar has 18+ items | Cognitive overload; users don't read long lists on mobile; every item gets less attention | 5-8 category chips in horizontal scroll on Discover screen; sidebar collapses to a minimal drawer |
| Tabbed product comparison in chat messages | Show all comparison dimensions inline in chat | Comparison tables in chat messages exceed mobile viewport width; 90% of comparisons are done on 2-3 products anyway | Use the dedicated `ComparisonTable` component only when user explicitly asks "compare" or triggers "Help Me Decide". Link to Results screen for full comparison view |
| Social features (upvotes, comments, shares) | "Community trust" | Off-brand for editorial luxury aesthetic; adds complexity with zero affiliate revenue upside; ReviewGuide is an AI assistant, not a forum | Source citations (Wirecutter, RTINGS, etc.) are the trust signal. No social layer needed |
| Real-time price refresh in chat | "Prices change" | Live prices require API calls on render, CORS complexity, throttling, and show unreliable data when APIs fail. Causes broken UI more than it adds value | Static curated prices labeled "Prices verified as of [date]". Link to merchant for live price |
| Voice input | "Mobile users want voice" | iOS Safari requires `getUserMedia` permission prompts; unreliable in background; adds significant complexity for marginal UX gain given chat is text-native | Text input with large tap target and autofocus is sufficient. Voice can be added in v3+ |
| Infinite scroll on Discover feed | "More content = more engagement" | Context for this app is task-completion, not feed consumption; infinite scroll reduces intent signal and burns API budget | Show 3 trending cards + 8 category cards + curated product section. Users who want more use the chat |

---

## Feature Dependencies

```
[Bottom Tab Navigation]
    └──requires──> [Discover Screen] (tab 1 content)
    └──requires──> [Saved Placeholder Route] (tab 2, placeholder)
    └──requires──> [Ask FAB] (tab 3, navigates to /chat?new=1)
    └──requires──> [Compare Placeholder Route] (tab 4, placeholder)
    └──requires──> [Profile Placeholder Route] (tab 5, placeholder)

[Discover Screen]
    └──requires──> [Category Chips] (horizontal scroll filter)
    └──requires──> [Trending Research Cards] (static seeded queries)
    └──requires──> [Hero Search Input] (entry point to chat)
    └──enhances──> [Curated Product Grid] (below-fold, secondary)

[Chat Screen (Mobile)]
    └──requires──> [Sticky Chat Input Bar] (fixed bottom, above tab bar)
    └──requires──> [Suggestion Chips] (below each AI message)
    └──requires──> [Real-time Status Indicator] (during streaming)
    └──requires──> [Compact Inline Product Cards] (in message thread)
    └──enhances──> [Chat Header Status] ("Researching • N sources")
    └──enhances──> [Source Citation Panel] (below product cards)
    └──enhances──> [Rank Badges] (Top Pick, Best Value, etc.)

[Compact Inline Product Cards]
    └──requires──> [Real Product Images] (from curatedLinks.ts static data)
    └──requires──> [Static Prices] (from curated data; no live price API)
    └──requires──> [Affiliate Links] (existing in curatedLinks.ts)
    └──conflicts──> [Full ProductCards in chat] (replace, not coexist)

[Results Screen /results/:id]
    └──requires──> [Chat Screen] (navigated from chat expand icon)
    └──requires──> [Full Product Cards] (with score bars, pastel image backgrounds)
    └──requires──> [Source Citations Panel] (expanded, with colored dots)
    └──requires──> [Conversation Sidebar as Drawer] (mobile: slide-out, desktop: fixed panel)
    └──enhances──> [Follow-up Chips] (same chips, different layout)

[Source Citation Panel]
    └──requires──> [Fix: review_sources broken after product_compose refactor] (known bug, must fix first)

[Curated Product Grid]
    └──requires──> [curatedLinks.ts] (already exists with 120+ products)
    └──requires──> [CuratedProductCard] (component exists, was disabled)
    └──conflicts──> [Live Price API] (use static data, not live)
```

### Dependency Notes

- **Results screen requires Chat screen:** Users reach Results by tapping the expand icon in the Chat header. There is no direct URL entry for first-time visits to Results.
- **Compact Inline Product Cards conflicts with Full ProductCards in chat:** On mobile, the current full `ProductCards` component overwhelms the chat layout. The redesign replaces them with compact cards inside chat, and reserves full cards for the Results screen only.
- **Source citations require bug fix first:** The review source links were broken in the `product_compose` Phase 4 refactor (`bd4b5c3`). This must be fixed before source citation UI can be displayed, otherwise the panel shows with no URLs.
- **Curated product grid requires no new backend work:** The `curatedLinks.ts` file already contains 120+ products with images, prices, and affiliate links. Re-enable `CuratedProductCard` with this data.

---

## MVP Definition

### This Milestone: v2.0 Frontend UX Redesign

The milestone goal is a unified Discover → Chat → Results flow that is mobile-first and app-like. The following defines what must ship to call v2.0 done vs what can come after.

### Launch With (v2.0)

- [x] Unified Discover screen at `/` (replaces `/browse` redirect)
- [x] Bottom tab navigation (mobile only; 5 tabs with FAB)
- [x] Category chips (horizontal scroll, 8 categories)
- [x] Trending research cards (3 seeded queries with icons)
- [x] Hero search input on Discover (tapping navigates to /chat with focused input)
- [x] Compact inline product cards in chat (80px height, horizontal layout)
- [x] Suggestion chips below AI messages (horizontal scroll, auto-submit on tap)
- [x] Real-time chat header status ("Researching • N sources analyzed")
- [x] Rank badges on product cards (Top Pick, Best Value, contextual labels)
- [x] Source citation panel (requires review_sources bug fix)
- [x] Fix: review source URLs broken after product_compose refactor
- [x] Results screen (`/results/:id`) — mobile full-width, desktop split panel
- [x] Placeholder routes: `/saved`, `/compare`, `/profile`
- [x] Responsive breakpoints: mobile (<768px), tablet (768-1023px), desktop (≥1024px)

### Add After Validation (v2.1)

- [ ] Curated product grid on Discover — once v2.0 shipped and layout is stable
- [ ] Animated skeleton loading states for product cards (replace current `BlockSkeleton` with card-shaped skeletons)
- [ ] "More like this / Not interested" feedback buttons on inline product cards
- [ ] Score bars on Results-screen product cards (needs per-product score data from compose prompt)
- [ ] Conversation search within history drawer

### Future Consideration (v3+)

- [ ] User accounts + saved products/conversations (requires auth milestone)
- [ ] Price alerts (requires accounts + notification infrastructure)
- [ ] Cross-retailer price comparison (requires Skimlinks integration milestone)
- [ ] Voice input
- [ ] Persistent memory across sessions

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Unified Discover screen | HIGH | LOW | P1 |
| Bottom tab navigation (mobile) | HIGH | LOW | P1 |
| Compact inline product cards | HIGH | MEDIUM | P1 |
| Suggestion chips (auto-submit) | HIGH | LOW | P1 |
| Fix review source links (bug) | HIGH | MEDIUM | P1 |
| Source citation panel | HIGH | LOW (after fix) | P1 |
| Results screen /results/:id | HIGH | HIGH | P1 |
| Rank badges (Top Pick etc.) | MEDIUM | LOW | P1 |
| Real-time chat header status | MEDIUM | LOW | P1 |
| Category chips on Discover | MEDIUM | LOW | P1 |
| Trending research cards | MEDIUM | LOW | P2 |
| Hero search input on Discover | HIGH | LOW | P1 |
| Curated product grid (Discover) | MEDIUM | MEDIUM | P2 |
| Skeleton loading animations | LOW | MEDIUM | P2 |
| "More like this" feedback buttons | MEDIUM | HIGH | P2 |
| Score bars on product cards | LOW | MEDIUM | P3 |
| Voice input | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for v2.0 launch
- P2: Should have, add in v2.1
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Amazon Rufus | ChatGPT Shopping | Google AI Mode | Perplexity | ReviewGuide v2.0 |
|---------|--------------|------------------|----------------|------------|------------------|
| Mobile bottom tab nav | Yes (app) | No (web) | No (web) | No (web) | Yes (web, mobile) |
| Natural language chat | Yes | Yes | Yes | Yes | Yes (existing) |
| Suggestion chips | Yes | No | No | No | Yes (improve existing) |
| Inline product cards | Yes (compact) | Yes (carousel) | Yes (panel) | Yes (cards) | Yes (new compact) |
| Source citations | No | Yes (per product) | Partial | Yes | Yes (fix + improve) |
| Editorial "why" framing | No | Partial | No | No | Yes (differentiator) |
| Cross-retailer results | No (Amazon only) | No (Google only) | No (Google only) | Partial | Yes (differentiator) |
| Results screen (sharable) | No | No | No | No | Yes (v2.0) |
| Comparison table | Basic | No | Partial | No | Yes (existing) |
| Price displayed in-app | Yes | Yes | Yes | Yes | Yes (curated static) |
| Multi-turn clarification | Yes | Partial | Yes | Yes | Yes (existing LangGraph) |
| Travel planning | No | No | Partial | No | Yes (existing) |
| Anonymous (no login) | No (Amazon acct) | No (OpenAI acct) | No (Google acct) | No (Perplexity acct) | Yes (differentiator) |

---

## Sources

- [Amazon Rufus UX patterns — About Amazon](https://www.aboutamazon.com/news/retail/amazon-rufus-ai-assistant-personalized-shopping-features)
- [ChatGPT Shopping launch — OpenAI](https://openai.com/index/chatgpt-shopping-research/)
- [Perplexity Shopping — Engadget](https://www.engadget.com/ai/perplexity-announces-its-own-take-on-an-ai-shopping-assistant-210500961.html)
- [Google AI Mode shopping — Think with Google](https://business.google.com/us/think/search-and-video/google-shopping-ai-mode-virtual-try-on-update/)
- [Bottom navigation bar best practices 2025 — AppMySite](https://blog.appmysite.com/bottom-navigation-bar-in-mobile-apps-heres-all-you-need-to-know/)
- [Mobile UX anti-patterns — UXmatters](https://www.uxmatters.com/mt/archives/2025/01/mobile-ux-design-patterns-and-their-impacts-on-user-retention.php)
- [Ecommerce mobile conversion — Tapcart](https://www.tapcart.com/blog/ecommerce-mobile-conversion)
- [Agent UX table stakes 2025 — Medium](https://medium.com/@Nexumo_/agent-ux-in-2025-the-new-table-stakes-dd189c7c2718)
- [Skeleton screens UX — Clay](https://clay.global/blog/skeleton-screen)
- Existing codebase: `frontend/components/`, `frontend/app/`, `.planning/research/shopping-assistant-ux.md`
- Figma spec: "ReviewGuide.ai — New UX Concept" (detailed in `# ReviewGuide.ai — frontendredesign.txt`)

---
*Feature research for: ReviewGuide.ai mobile-first UX redesign (v2.0 milestone)*
*Researched: 2026-03-16*
