# Requirements: ReviewGuide.ai v2.0 Frontend UX Redesign

**Defined:** 2026-03-16
**Core Value:** Conversational product discovery that searches live reviews and returns blog-style editorial responses with cross-retailer affiliate links.

## v2.0 Requirements

### Navigation

- [ ] **NAV-01**: User sees bottom tab bar with 5 tabs (Discover, Saved, Ask, Compare, Profile) on mobile (<768px)
- [ ] **NAV-02**: User sees desktop top navigation bar with logo and nav links on screens ≥1024px
- [ ] **NAV-03**: User can tap central FAB button to start a new research chat from any screen
- [ ] **NAV-04**: User sees animated page transitions between routes
- [ ] **NAV-05**: Bottom tab bar handles iOS safe area insets correctly

### Discover

- [ ] **DISC-01**: User sees editorial hero headline with serif italic accent and search bar on `/`
- [ ] **DISC-02**: User can scroll horizontal category chips (Popular, Tech, Travel, Kitchen, Fitness, etc.)
- [ ] **DISC-03**: User sees trending research cards with icons, titles, subtitles — tapping navigates to chat
- [ ] **DISC-04**: User sees personalized "For You" chip based on recent search history
- [ ] **DISC-05**: Search bar tap navigates to chat screen with input focused

### Chat

- [ ] **CHAT-01**: AI responses follow structured format: summary → ranked inline product cards → source citations → follow-up chips
- [ ] **CHAT-02**: Inline product cards are compact (64px height) with image, rank, name, price, and affiliate link
- [ ] **CHAT-03**: Chat header shows real-time status ("Researching • 4 sources analyzed") during streaming
- [ ] **CHAT-04**: Source citations are clickable links to actual review article URLs from search results
- [ ] **CHAT-05**: User message bubbles are right-aligned blue, AI bubbles are left-aligned white with "✦ ReviewGuide" label
- [ ] **CHAT-06**: Follow-up suggestion chips appear below AI responses and auto-submit on tap

### Results

- [ ] **RES-01**: User can navigate to `/results/:id` to see full results for a completed research session
- [ ] **RES-02**: Product cards display in 3-column grid on desktop, horizontal scroll on mobile
- [ ] **RES-03**: Product cards show real Amazon images, prices, and affiliate links from curated static data
- [ ] **RES-04**: Each product card shows rank badge (#1 Top Pick, #2 Best Value, etc.), score bar, and CTA button
- [ ] **RES-05**: Quick actions panel shows: Compare side by side, Export to list, Share results
- [ ] **RES-06**: Sources analyzed section shows colored dots, source names, and clickable article links

### Responsive

- [ ] **RESP-01**: All screens render mobile-first single-column layout below 768px
- [ ] **RESP-02**: Desktop layout (≥1024px) shows 3-column product grids, persistent sidebar, top nav, max 1200px content

### Placeholder Routes

- [ ] **PLCH-01**: `/saved` route renders placeholder page indicating feature coming soon
- [ ] **PLCH-02**: `/compare` route renders placeholder page indicating feature coming soon

## Future Requirements

### Tablet Support

- **RESP-03**: Tablet breakpoint (768-1023px) with 2-column grid, optional sidebar toggle

### User Profiles

- **PROF-01**: `/profile` route with user settings, theme toggle, accent picker
- **PROF-02**: User accounts with login/signup

### Desktop Split Panel

- **RES-07**: Results page shows left conversation sidebar + right content on desktop

### Advanced Features

- **SAVE-01**: User can save products and conversations to a persistent saved list
- **COMP-01**: User can compare products side by side on the compare page
- **ALERT-01**: User can set price alerts for tracked products

## Out of Scope

| Feature | Reason |
|---------|--------|
| User accounts / login | Anonymous-first for v2.0, reduces friction |
| Price alerts | Requires accounts and notification infrastructure |
| Voice input | Decorative mic icon only — no speech recognition |
| Social features | Not a social platform |
| Backend response restructuring | Separate workstream — v2.0 is frontend-only |
| Real-time pricing from PA-API | Use curated static Amazon data (120+ products) until key obtained |
| Mobile app | Web-first, responsive design covers mobile |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NAV-01 | TBD | Pending |
| NAV-02 | TBD | Pending |
| NAV-03 | TBD | Pending |
| NAV-04 | TBD | Pending |
| NAV-05 | TBD | Pending |
| DISC-01 | TBD | Pending |
| DISC-02 | TBD | Pending |
| DISC-03 | TBD | Pending |
| DISC-04 | TBD | Pending |
| DISC-05 | TBD | Pending |
| CHAT-01 | TBD | Pending |
| CHAT-02 | TBD | Pending |
| CHAT-03 | TBD | Pending |
| CHAT-04 | TBD | Pending |
| CHAT-05 | TBD | Pending |
| CHAT-06 | TBD | Pending |
| RES-01 | TBD | Pending |
| RES-02 | TBD | Pending |
| RES-03 | TBD | Pending |
| RES-04 | TBD | Pending |
| RES-05 | TBD | Pending |
| RES-06 | TBD | Pending |
| RESP-01 | TBD | Pending |
| RESP-02 | TBD | Pending |
| PLCH-01 | TBD | Pending |
| PLCH-02 | TBD | Pending |

**Coverage:**
- v2.0 requirements: 26 total
- Mapped to phases: 0
- Unmapped: 26 ⚠️

---
*Requirements defined: 2026-03-16*
*Last updated: 2026-03-16 after milestone v2.0 definition*
