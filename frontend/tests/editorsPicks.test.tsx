/**
 * Phase 7 -- Editor's Picks: RED tests for AFFL-05
 *
 * Tests covering:
 *   AFFL-05 -- EditorsPicks: renders product images from Amazon CDN,
 *              returns null for travel, wires affiliate links from curatedLinks
 *
 * These tests are in the RED state -- they will fail until Plan 03 creates
 * the EditorsPicks component at @/components/EditorsPicks.
 * That is expected and correct.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

// -- Module-level mocks -------------------------------------------------------

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('lucide-react', () => ({
  ExternalLink: () => <span data-testid="icon-external" />,
  Package: () => <span data-testid="icon-package" />,
}))

vi.mock('@/lib/curatedLinks', () => ({
  curatedLinks: {
    electronics: [
      {
        title: 'Best Noise-Cancelling Headphones',
        description: 'Block out the world',
        products: [
          { asin: 'B0C3HCD34R', url: 'https://amzn.to/4cg2c2g' },
          { asin: 'B0CQXMXJC5', url: 'https://amzn.to/46sYSNy' },
        ],
      },
    ],
  },
}))

// Component under test -- will fail to import until Plan 03 creates it (RED state)
import EditorsPicks from '@/components/EditorsPicks'

// -- Tests --------------------------------------------------------------------

describe('EditorsPicks', () => {
  it('renders product images for a category with curated data', () => {
    const { container } = render(<EditorsPicks categorySlug="electronics" />)
    const images = container.querySelectorAll('img')
    expect(images.length).toBeGreaterThanOrEqual(1)
    // Each image src should contain an ASIN from the mocked data
    const asins = ['B0C3HCD34R', 'B0CQXMXJC5']
    images.forEach((img) => {
      const src = img.getAttribute('src') || ''
      const matchesAsin = asins.some((asin) => src.includes(asin))
      expect(matchesAsin).toBe(true)
    })
  })

  it('returns null for travel category (no curated data)', () => {
    const { container } = render(<EditorsPicks categorySlug="travel" />)
    expect(container.firstChild).toBeNull()
  })

  it('uses Amazon CDN URL pattern for images, not placehold.co', () => {
    const { container } = render(<EditorsPicks categorySlug="electronics" />)
    const images = container.querySelectorAll('img')
    expect(images.length).toBeGreaterThanOrEqual(1)
    images.forEach((img) => {
      const src = img.getAttribute('src') || ''
      expect(src).toContain('images-na.ssl-images-amazon.com/images/I/')
      expect(src).not.toContain('placehold.co')
    })
  })

  it('wires affiliate links from curatedLinks to product cards', () => {
    const { container } = render(<EditorsPicks categorySlug="electronics" />)
    const links = container.querySelectorAll('a[target="_blank"]')
    expect(links.length).toBeGreaterThanOrEqual(1)
    const hrefs = Array.from(links).map((a) => a.getAttribute('href'))
    const expectedUrls = ['https://amzn.to/4cg2c2g', 'https://amzn.to/46sYSNy']
    const hasMatch = hrefs.some((href) =>
      expectedUrls.some((expected) => href === expected)
    )
    expect(hasMatch).toBe(true)
  })
})
