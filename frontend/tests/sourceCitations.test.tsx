/**
 * Phase 14 — Chat Screen: RED tests for CHAT-04
 *
 * Tests covering:
 *   CHAT-04 — SourceCitations: clickable links with target=_blank,
 *             colored dots by position, source name text,
 *             "+X more" toggle for > 4 sources
 *
 * These tests are in the RED state — they will fail until Plan 02 creates
 * the SourceCitations component at @/components/SourceCitations.
 * That is expected and correct.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

// ── Module-level mocks ────────────────────────────────────────────────────────

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('lucide-react', () => ({
  ExternalLink: () => <span data-testid="icon-external" />,
  ChevronDown: () => <span data-testid="icon-chevron-down" />,
  ChevronUp: () => <span data-testid="icon-chevron-up" />,
  Globe: () => <span data-testid="icon-globe" />,
  BookOpen: () => <span data-testid="icon-book" />,
}))

// Component under test — will fail to import until Plan 02 creates it (RED state)
import SourceCitations from '@/components/SourceCitations'

// ── Test fixtures ─────────────────────────────────────────────────────────────

const singleProductFewSources = {
  products: [
    {
      name: 'Sony WH-1000XM5',
      sources: [
        {
          site_name: 'Wirecutter',
          url: 'https://www.nytimes.com/wirecutter/reviews/best-noise-canceling-headphones/',
          title: 'Best Noise-Canceling Headphones of 2026',
          snippet: 'The Sony WH-1000XM5 remains our top pick.',
        },
        {
          site_name: 'RTINGS',
          url: 'https://www.rtings.com/headphones/reviews/sony/wh-1000xm5',
          title: 'Sony WH-1000XM5 Review',
          snippet: 'Exceptional noise cancellation performance.',
        },
        {
          site_name: 'SoundGuys',
          url: 'https://www.soundguys.com/sony-wh-1000xm5-review/',
          title: 'Sony WH-1000XM5 Review',
          snippet: 'Best-in-class ANC with improved microphone.',
        },
      ],
    },
  ],
}

const singleProductManySources = {
  products: [
    {
      name: 'Sony WH-1000XM5',
      sources: [
        {
          site_name: 'Wirecutter',
          url: 'https://wirecutter.com/reviews/sony',
          title: 'Best Noise-Canceling Headphones',
        },
        {
          site_name: 'RTINGS',
          url: 'https://rtings.com/sony',
          title: 'Sony XM5 Review',
        },
        {
          site_name: 'SoundGuys',
          url: 'https://soundguys.com/sony',
          title: 'SoundGuys Review',
        },
        {
          site_name: 'Head-Fi',
          url: 'https://head-fi.org/sony',
          title: 'Head-Fi Discussion',
        },
        {
          site_name: 'TechRadar',
          url: 'https://techradar.com/sony',
          title: 'TechRadar Review',
        },
        {
          site_name: 'PCMag',
          url: 'https://pcmag.com/sony',
          title: 'PCMag Review',
        },
      ],
    },
  ],
}

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-04 — Clickable citation links
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-04 — Clickable citation links', () => {
  it('renders each citation as an anchor tag', () => {
    const { container } = render(<SourceCitations data={singleProductFewSources} />)
    const links = container.querySelectorAll('a')
    expect(links.length).toBeGreaterThanOrEqual(3)
  })

  it('each citation link has target="_blank"', () => {
    const { container } = render(<SourceCitations data={singleProductFewSources} />)
    const links = Array.from(container.querySelectorAll('a'))
    const sourceLinks = links.filter((a) =>
      a.href.startsWith('http') || a.getAttribute('href')?.startsWith('http')
    )
    expect(sourceLinks.length).toBeGreaterThan(0)
    sourceLinks.forEach((link) => {
      expect(link.target).toBe('_blank')
    })
  })

  it('each citation link has rel="noopener noreferrer"', () => {
    const { container } = render(<SourceCitations data={singleProductFewSources} />)
    const links = Array.from(container.querySelectorAll('a'))
    const sourceLinks = links.filter((a) =>
      a.href.startsWith('http') || a.getAttribute('href')?.startsWith('http')
    )
    sourceLinks.forEach((link) => {
      const rel = link.getAttribute('rel') ?? ''
      expect(rel).toContain('noopener')
      expect(rel).toContain('noreferrer')
    })
  })

  it('citation href points to the source URL', () => {
    const { container } = render(<SourceCitations data={singleProductFewSources} />)
    const links = Array.from(container.querySelectorAll('a')) as HTMLAnchorElement[]
    const wirecutterLink = links.find((a) => a.href.includes('wirecutter') || a.href.includes('nytimes'))
    expect(wirecutterLink).toBeTruthy()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-04 — Colored dots by position
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-04 — Colored dots by position', () => {
  it('renders colored dot elements for each source', () => {
    const { container } = render(<SourceCitations data={singleProductFewSources} />)
    // Colored dots can be: div/span with bg-[#color] or bg-red-500 etc.
    const coloredDots =
      container.querySelectorAll('[class*="bg-[#EF4444]"]').length > 0
        ? container.querySelectorAll('[class*="bg-[#EF4444]"]')
        : container.querySelectorAll('[class*="rounded-full"][class*="bg-"]')
    expect(coloredDots.length).toBeGreaterThanOrEqual(1)
  })

  it('index 0 dot has red color (#EF4444 or red-500)', () => {
    const { container } = render(<SourceCitations data={singleProductFewSources} />)
    // First dot: red
    const redDot =
      container.querySelector('[class*="bg-[#EF4444]"]') ||
      container.querySelector('[class*="bg-red-"]') ||
      container.querySelector('[style*="#EF4444"]') ||
      container.querySelector('[style*="rgb(239, 68, 68)"]')
    expect(redDot).toBeTruthy()
  })

  it('index 1 dot has blue color (#3B82F6 or blue-500)', () => {
    const { container } = render(<SourceCitations data={singleProductFewSources} />)
    const blueDot =
      container.querySelector('[class*="bg-[#3B82F6]"]') ||
      container.querySelector('[class*="bg-blue-"]') ||
      container.querySelector('[style*="#3B82F6"]') ||
      container.querySelector('[style*="rgb(59, 130, 246)"]')
    expect(blueDot).toBeTruthy()
  })

  it('index 2 dot has green color (#22C55E or green-500)', () => {
    const { container } = render(<SourceCitations data={singleProductFewSources} />)
    const greenDot =
      container.querySelector('[class*="bg-[#22C55E]"]') ||
      container.querySelector('[class*="bg-green-"]') ||
      container.querySelector('[style*="#22C55E"]') ||
      container.querySelector('[style*="rgb(34, 197, 94)"]')
    expect(greenDot).toBeTruthy()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-04 — Source name text
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-04 — Source name text', () => {
  it('renders source site name text (e.g. "Wirecutter")', () => {
    render(<SourceCitations data={singleProductFewSources} />)
    expect(screen.getByText('Wirecutter')).toBeTruthy()
  })

  it('renders multiple source names', () => {
    render(<SourceCitations data={singleProductFewSources} />)
    expect(screen.getByText('Wirecutter')).toBeTruthy()
    expect(screen.getByText('RTINGS')).toBeTruthy()
    expect(screen.getByText('SoundGuys')).toBeTruthy()
  })

  it('renders a "Sources" header label', () => {
    render(<SourceCitations data={singleProductFewSources} />)
    const sourcesHeader =
      screen.queryByText('Sources') ||
      screen.queryByText(/sources/i)
    expect(sourcesHeader).toBeTruthy()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-04 — "+X more" toggle for > 4 sources
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-04 — "+X more" toggle', () => {
  it('renders a "+X more" button when there are more than 4 sources', () => {
    render(<SourceCitations data={singleProductManySources} />)
    // With 6 sources, should show "+2 more" or similar
    const moreButton =
      screen.queryByText(/\+\d+ more/i) ||
      screen.queryByText(/show more/i) ||
      screen.queryByText(/more sources/i)
    expect(moreButton).toBeTruthy()
  })

  it('initially only shows 4 sources (hides the rest behind toggle)', () => {
    const { container } = render(<SourceCitations data={singleProductManySources} />)
    // Before clicking "+X more", only 4 source names should be visible
    const visibleLinks = container.querySelectorAll('a[target="_blank"]')
    // Should show first 4, hide last 2
    expect(visibleLinks.length).toBeLessThanOrEqual(4)
  })

  it('clicking "+X more" reveals the hidden sources', () => {
    const { container } = render(<SourceCitations data={singleProductManySources} />)
    const moreButton =
      screen.queryByText(/\+\d+ more/i) ||
      screen.queryByText(/show more/i)
    expect(moreButton).toBeTruthy()

    fireEvent.click(moreButton!)

    // After clicking, all 6 sources should be visible
    const allLinks = container.querySelectorAll('a[target="_blank"]')
    expect(allLinks.length).toBe(6)
  })

  it('does NOT render "+X more" when there are 4 or fewer sources', () => {
    render(<SourceCitations data={singleProductFewSources} />)
    // 3 sources — no "+X more" button needed
    const moreButton = screen.queryByText(/\+\d+ more/i)
    expect(moreButton).toBeNull()
  })
})
