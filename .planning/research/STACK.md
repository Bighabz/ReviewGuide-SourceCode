# Stack Research

**Domain:** Mobile-first frontend UX redesign — Next.js 14 / React 18 / Tailwind (brownfield)
**Researched:** 2026-03-16
**Confidence:** HIGH

---

## Context: What Already Exists (Do Not Re-Research)

The existing stack is locked and validated:

- Next.js 14 with App Router — `package.json` confirms `^14.2.35`
- React 18 with TypeScript — `^18.2.0`
- Tailwind CSS 3 with custom design tokens — `tailwind.config.ts` has full editorial theme
- framer-motion — **already installed at `^12.26.2`** (installed version: 12.26.2)
- lucide-react — **already installed at `^0.294.0`** (latest is ~0.577.0)
- clsx + tailwind-merge — already installed
- `@tailwindcss/typography` — already installed

This research covers only **new stack additions** required for the v2.0 milestone features.

---

## Recommended Stack

### Core Technologies — No Changes Needed

The existing core handles everything. No new frameworks required.

| Technology | Current Version | Role in Redesign |
|------------|-----------------|------------------|
| Next.js 14 App Router | ^14.2.35 | Route structure for `/saved`, `/compare`, `/profile`; `useSelectedLayoutSegment` for active tab state |
| Tailwind CSS 3 | ^3.3.6 | All layout, responsive breakpoints, bottom nav, FAB positioning |
| framer-motion | ^12.26.2 (installed: 12.26.2) | Navigation transitions, FAB scale animation, card entrance — already imported in UnifiedTopbar, ProductCarousel |

### New Additions Required

| Library | Version to Install | Purpose | Why This Over Alternatives |
|---------|-------------------|---------|---------------------------|
| `tailwindcss-safe-area` | `^0.8.0` | iOS safe area insets (`pb-safe`, `h-safe`) for bottom tab nav and FAB | The only clean way to use `env(safe-area-inset-*)` via Tailwind classes. 88k weekly downloads, healthy maintenance. Tailwind 3 compatible via plugin. Required for iPhone notch/home indicator clearance on fixed bottom nav. |

That is the only new `npm install` this milestone needs.

---

### Supporting Libraries — All Already Present

| Library | Installed Version | How It Serves This Milestone |
|---------|------------------|------------------------------|
| `framer-motion` | 12.26.2 | FAB scale spring, bottom nav active indicator (layoutId), card entrance (AnimatePresence). Import from `"framer-motion"` — the `"motion/react"` alias is for framer-motion v12+ and works as an alias, but `"framer-motion"` continues to work and is already used across the codebase. |
| `lucide-react` | 0.294.0 (pinned) | Tab bar icons (Home, MessageSquare, Bookmark, SlidersHorizontal, User), FAB Plus icon. All needed icons exist at this version. Do NOT upgrade mid-milestone — breaking icon renames occurred between 0.294 and 0.577. |
| `clsx` + `tailwind-merge` | installed | Active tab conditional classes in bottom nav |
| `next/navigation` | built-in | `useSelectedLayoutSegment` for tab active state — the correct App Router pattern, avoids `usePathname` string matching |

---

## Implementation Patterns (No Library Needed)

These features are pure Tailwind + React — no new dependency required:

### Bottom Tab Navigation

Build in `components/BottomTabBar.tsx`, rendered in the root layout below the `{children}` div. Use `fixed bottom-0` + `pb-safe` (from tailwindcss-safe-area) + `md:hidden` to suppress on desktop. Track active tab with `useSelectedLayoutSegment` from `next/navigation`.

```typescript
// Pattern — no library needed
<nav className="fixed bottom-0 inset-x-0 md:hidden pb-safe bg-[var(--surface-elevated)] border-t border-[var(--border)] z-50">
  {tabs.map(tab => (
    <Link key={tab.href} href={tab.href} className={isActive ? 'text-[var(--primary)]' : 'text-[var(--text-muted)]'}>
      <tab.icon size={22} />
      <span>{tab.label}</span>
    </Link>
  ))}
</nav>
```

### FAB (Floating Action Button)

Fixed position, sits above bottom tab bar. `fixed bottom-20 right-4 md:hidden` with `pb-safe` on the containing wrapper. Spring scale animation via framer-motion `whileTap={{ scale: 0.93 }}`. No library needed beyond existing framer-motion.

### Horizontal Scroll Carousels

Native CSS scroll snap — no new library. Already partially used in `ProductCarousel.tsx` (currently uses prev/next buttons). The upgrade: add `overflow-x-auto snap-x snap-mandatory` on the container and `snap-center shrink-0` on each card. Hide the scrollbar with a global CSS rule in `globals.css`:

```css
.scroll-hidden::-webkit-scrollbar { display: none; }
.scroll-hidden { -ms-overflow-style: none; scrollbar-width: none; }
```

### Desktop Split-Panel Layout

Pure CSS Grid in the chat page layout: `grid-cols-[1fr_400px]` on `lg:`. No resize library needed — the split is fixed proportion (content left, sidebar right), not user-resizable. The framer-motion `AnimatePresence` handles the sidebar appearing/disappearing when results are present.

### Page Navigation Transitions

Use framer-motion `AnimatePresence` with a `template.tsx` file in each route segment (the App Router pattern that works reliably in Next.js 14). Do NOT use the `viewTransition` experimental flag — it requires Next.js ≥15.2.0 and this project is on 14. Do NOT use `AnimatePresence` at the layout level — it breaks in App Router because layouts don't unmount on navigation.

```
app/
  chat/
    template.tsx  ← motion.div with initial/animate/exit
    page.tsx
  browse/
    template.tsx
```

---

## Installation

```bash
# Only new dependency
cd frontend && npm install tailwindcss-safe-area@^0.8.0
```

Then add to `tailwind.config.ts` plugins array:
```typescript
plugins: [
  require('@tailwindcss/typography'),
  require('tailwindcss-safe-area'),  // add this
]
```

Then add `viewport-fit=cover` to `layout.tsx` viewport export:
```typescript
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: 'cover',  // add this — enables env(safe-area-inset-*)
  themeColor: [...]
}
```

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `tailwindcss-safe-area` plugin | Raw `env(safe-area-inset-bottom)` in globals.css | Plugin gives responsive composable classes (`pb-safe`, `h-safe`) vs one-off CSS values. Worth the tiny dep. |
| Pure CSS scroll snap carousels | `embla-carousel-react` or `keen-slider` | Both are ~15-25kb for what Tailwind's scroll snap achieves natively. The existing ProductCarousel already has the scroll logic — it needs CSS snap added, not a library swap. |
| framer-motion `template.tsx` pattern | `next-view-transitions` (npm package) | `next-view-transitions` wraps the View Transitions API which has partial browser support (no Firefox stable as of March 2026). framer-motion is already in the bundle. |
| `useSelectedLayoutSegment` for active tab | `usePathname` + string matching | `useSelectedLayoutSegment` is the App Router-native hook for exactly this use case. Avoids fragile pathname prefix matching. |
| Fixed-proportion grid split panel | `react-resizable-panels` | No user resize needed per spec. Adding a 6kb library for a static grid proportion is waste. `lg:grid-cols-[1fr_400px]` is 10 characters. |
| framer-motion (existing) | `@formkit/auto-animate` (2.5kb) | auto-animate handles list reorder animations well but lacks the spring physics needed for FAB/tab indicator animations already designed into the system. framer-motion is already in the bundle. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `next/navigation` `viewTransition` flag | Requires Next.js ≥15.2.0. This project is on 14.x and locked per PROJECT.md constraints. | framer-motion `template.tsx` pattern |
| `react-router` or any client-side router | Already on Next.js App Router. Mixing routers causes hydration chaos. | App Router `Link` + `useRouter` |
| shadcn/ui component library | Would conflict with the existing editorial design system (CSS variables, custom tokens). Individual component primitives from shadcn would require re-theming all tokens. | Build nav/FAB/carousel components directly — they're ~50-100 lines each |
| Radix UI tabs for bottom nav | Radix Tabs is semantically a tab panel (content switching), not navigation. Causes ARIA roles mismatch for a nav bar that routes to separate pages. | `<nav>` + `<Link>` + `useSelectedLayoutSegment` |
| Upgrading lucide-react mid-milestone | Icons were renamed between 0.294 and 0.577 (e.g., `Map` → `MapPin` changes, various renames). Upgrading risks broken icon imports across 20+ components during a visual redesign. | Stay on 0.294.0 until a dedicated upgrade task |
| Inline `style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}` | Works but bypasses Tailwind's responsive system, can't be combined with other Tailwind padding utilities cleanly. | `tailwindcss-safe-area` plugin classes |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `tailwindcss-safe-area@0.8.0` | Tailwind CSS 3.x | Version 0.8.0 explicitly supports Tailwind v3. Do NOT install latest if it drops v3 support. |
| `framer-motion@12.26.2` | React 18, Next.js 14 | `AnimatePresence` in `template.tsx` works. `AnimatePresence` in `layout.tsx` does NOT work in App Router — layouts don't unmount. Already validated in UnifiedTopbar. |
| `useSelectedLayoutSegment` | Next.js 14 App Router only | Client Component hook — must be in a `'use client'` file imported into a Server Component layout. Works in Next.js 14.x (confirmed in official docs). |

---

## Responsive Breakpoints (Existing + Required)

The Tailwind config has no custom breakpoints — uses defaults. The redesign targets:

| Breakpoint | Width | Behavior |
|------------|-------|----------|
| Mobile (default) | < 768px (`md:`) | Bottom tab bar visible, FAB visible, single-column layout, full-width cards |
| Tablet | 768px–1023px (`md:` to `lg:`) | Top bar only (no bottom nav), single column, no split panel |
| Desktop | ≥ 1024px (`lg:`) | Split panel layout, no bottom nav, no FAB |

Classes: `md:hidden` hides bottom nav/FAB on tablet+. `lg:grid-cols-[1fr_400px]` activates split panel. No breakpoint changes to Tailwind config required.

---

## Sources

- framer-motion installed version confirmed via `package-lock.json` — HIGH confidence
- `tailwindcss-safe-area` v0.8.0 — [npm package page](https://www.npmjs.com/package/tailwindcss-safe-area) — HIGH confidence
- Next.js `useSelectedLayoutSegment` — [official docs](https://nextjs.org/docs/app/api-reference/functions/use-selected-layout-segment) — HIGH confidence
- `viewTransition` requires Next.js ≥15.2.0 — [next.config.js docs](https://nextjs.org/docs/app/api-reference/config/next-config-js/viewTransition) — HIGH confidence
- framer-motion App Router `template.tsx` pattern — [community-validated pattern](https://dev.to/abdur_rakibrony_97cea0e9/page-transition-in-nextjs-14-app-router-using-framer-motion-2he7) — MEDIUM confidence (no official framer-motion docs, but widely validated pattern)
- lucide-react icon rename risk between 0.294 and 0.577 — [lucide releases](https://github.com/lucide-icons/lucide/releases) — MEDIUM confidence (renames occur regularly per release notes pattern)
- CSS scroll snap Tailwind approach — [Tailwind docs](https://tailwindcss.com/docs/scroll-snap-type) — HIGH confidence

---

*Stack research for: ReviewGuide.ai v2.0 Frontend UX Redesign*
*Researched: 2026-03-16*
