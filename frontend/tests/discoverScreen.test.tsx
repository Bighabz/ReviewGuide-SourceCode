/**
 * Phase 13 — DISC-01 through DISC-05
 *
 * Behavioral contracts for the Discover screen.
 * Components expected at:
 *   - frontend/app/page.tsx  (DiscoverPage — default export)
 *
 * Updated in Phase 22 to match Phase 20 redesign:
 * - CategoryChipRow has 6 chips (For You, Tech, Travel, Kitchen, Fitness, Audio)
 * - ProductCarousel replaces old trending cards — uses class-based carousel, no data-testid="trending-card"
 * - "For You" chip is always shown as the active first chip (not conditional on recent searches)
 * - DiscoverSearchBar is a <form> with an <input> inside — not a standalone button element
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

// ────────────────────────────────────────────────────────────────
// Module-level router mock (captured before any import of components)
// ────────────────────────────────────────────────────────────────
const mockPush = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock recentSearches lib so DISC-04 tests can control the data.
vi.mock('@/lib/recentSearches', () => ({
  getRecentSearches: vi.fn(() => []),
}))

import { getRecentSearches } from '@/lib/recentSearches'
import DiscoverPage from '@/app/page'

// ────────────────────────────────────────────────────────────────
// DISC-01 — Hero section
// ────────────────────────────────────────────────────────────────
describe('DiscoverPage — hero section (DISC-01)', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('renders a heading that contains "researching" in an italic span', () => {
    render(<DiscoverPage />)
    // The hero heading must contain the word "researching" inside an <em> or <i>
    // or a span with italic styling.
    const italicEl =
      document.querySelector('em') ||
      document.querySelector('i') ||
      document.querySelector('[class*="italic"]') ||
      document.querySelector('span[style*="italic"]')
    expect(italicEl).toBeTruthy()
    expect(italicEl!.textContent?.toLowerCase()).toContain('researching')
  })

  it('renders the subline "Expert reviews, real data, zero fluff."', () => {
    render(<DiscoverPage />)
    expect(screen.getByText('Expert reviews, real data, zero fluff.')).toBeTruthy()
  })
})

// ────────────────────────────────────────────────────────────────
// DISC-02 — Category chip row
// ────────────────────────────────────────────────────────────────
describe('DiscoverPage — category chip row (DISC-02)', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('renders at least 4 category chips (Tech, Travel, Kitchen, Fitness)', () => {
    render(<DiscoverPage />)
    // CategoryChipRow renders: For You, Tech, Travel, Kitchen, Fitness, Audio
    // Use queryAllByText to handle cases where labels may appear multiple times
    const chipLabels = ['Tech', 'Travel', 'Kitchen', 'Fitness']
    const found = chipLabels.filter(
      (label) => screen.queryAllByText(label).length > 0
    )
    expect(found.length).toBeGreaterThanOrEqual(4)
  })

  it('tapping a category chip calls router.push with /chat?q=...&new=1', () => {
    render(<DiscoverPage />)
    // Find ANY chip that is a button with a query (not "For You" which goes to /chat?new=1)
    const chipLabels = ['Tech', 'Travel', 'Kitchen', 'Fitness', 'Audio']
    let chipButton: HTMLElement | null = null
    for (const label of chipLabels) {
      const el = screen.queryByText(label)
      if (el) {
        chipButton = el.closest('button') ?? el.closest('[role="button"]') ?? el as HTMLElement
        break
      }
    }
    expect(chipButton).toBeTruthy()
    fireEvent.click(chipButton!)
    expect(mockPush).toHaveBeenCalledTimes(1)
    const calledUrl: string = mockPush.mock.calls[0][0]
    expect(calledUrl).toMatch(/^\/chat\?q=.+&new=1$/)
  })
})

// ────────────────────────────────────────────────────────────────
// DISC-03 — Product Carousel (replaces old trending cards)
// ────────────────────────────────────────────────────────────────
describe('DiscoverPage — product carousel (DISC-03)', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('renders at least one product/trending card with title and subtitle text', () => {
    render(<DiscoverPage />)
    // ProductCarousel renders a single visible card with h3 (title) + p (subtitle)
    // No data-testid="trending-card" — uses class-based carousel with h3/p structure
    const headings = document.querySelectorAll('h3')
    expect(headings.length).toBeGreaterThanOrEqual(1)
    // Each heading should have non-empty text content
    const hasContent = Array.from(headings).some(
      (h) => (h.textContent?.trim().length ?? 0) > 0
    )
    expect(hasContent).toBe(true)
  })

  it('tapping the carousel card calls router.push with an encoded query parameter', () => {
    render(<DiscoverPage />)
    // The carousel card is a clickable div with onClick -> router.push(/chat?q=...&new=1)
    // Find any element with a click handler that navigates with q= param
    const clickableCards = document.querySelectorAll('[class*="cursor-pointer"]')
    expect(clickableCards.length).toBeGreaterThan(0)
    const firstCard = clickableCards[0] as HTMLElement
    fireEvent.click(firstCard)
    expect(mockPush).toHaveBeenCalledTimes(1)
    const calledUrl: string = mockPush.mock.calls[0][0]
    // URL must contain a query parameter (q=...).
    expect(calledUrl).toContain('q=')
  })
})

// ────────────────────────────────────────────────────────────────
// DISC-04 — "For You" chip always visible (Phase 20 redesign)
// ────────────────────────────────────────────────────────────────
describe('DiscoverPage — "For You" chip (DISC-04)', () => {
  beforeEach(() => {
    mockPush.mockClear()
    vi.mocked(getRecentSearches).mockReturnValue([])
  })

  it('renders "For You" chip regardless of recent searches (always first chip)', () => {
    vi.mocked(getRecentSearches).mockReturnValue([])
    render(<DiscoverPage />)
    // CategoryChipRow always shows "For You" as the first active chip
    expect(screen.getByText('For You')).toBeTruthy()
  })

  it('renders "For You" chip when localStorage returns at least one recent search', () => {
    vi.mocked(getRecentSearches).mockReturnValue([
      {
        query: 'best headphones',
        productNames: ['Sony WH-1000XM5'],
        category: 'electronics',
        timestamp: Date.now(),
      },
    ])
    render(<DiscoverPage />)
    expect(screen.getByText('For You')).toBeTruthy()
  })
})

// ────────────────────────────────────────────────────────────────
// DISC-05 — Search bar
// ────────────────────────────────────────────────────────────────
describe('DiscoverPage — search bar (DISC-05)', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('submitting the search form with empty query calls router.push("/chat?new=1")', () => {
    render(<DiscoverPage />)
    // DiscoverSearchBar is a <form data-testid="discover-search-bar"> with an <input>
    const searchForm = document.querySelector('[data-testid="discover-search-bar"]')
    expect(searchForm).toBeTruthy()
    // Submit the form with empty input to trigger /chat?new=1
    fireEvent.submit(searchForm as HTMLElement)
    expect(mockPush).toHaveBeenCalledWith('/chat?new=1')
  })

  it('search bar renders with an input element for text entry', () => {
    render(<DiscoverPage />)
    // DiscoverSearchBar is a form containing a text input — not a bare button
    const searchForm = document.querySelector('[data-testid="discover-search-bar"]')
    expect(searchForm).toBeTruthy()
    const tagName = (searchForm as HTMLElement).tagName.toLowerCase()
    // The outer element is a <form>
    expect(tagName).toBe('form')
    // Must contain a text input
    const input = (searchForm as HTMLElement).querySelector('input[type="text"]')
    expect(input).toBeTruthy()
  })
})
