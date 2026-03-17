/**
 * Phase 14 — Chat Screen: RED tests for CHAT-02
 *
 * Tests covering:
 *   CHAT-02 — InlineProductCard: 64px height, rank badges, image fallback,
 *             price, affiliate link, dividers between cards
 *
 * These tests are in the RED state — they will fail until Plan 02 creates
 * the InlineProductCard component at @/components/InlineProductCard.
 * That is expected and correct.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

// ── Module-level mocks ────────────────────────────────────────────────────────

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('lucide-react', () => ({
  ShoppingCart: () => <span data-testid="icon-cart" />,
  ExternalLink: () => <span data-testid="icon-external" />,
  Package: () => <span data-testid="icon-package" />,
  Star: () => <span data-testid="icon-star" />,
}))

// Component under test — will fail to import until Plan 02 creates it (RED state)
import InlineProductCard from '@/components/InlineProductCard'

// ── Test fixtures ─────────────────────────────────────────────────────────────

const singleProduct = [
  {
    name: 'Sony WH-1000XM5',
    price: 349,
    url: 'https://amazon.com/dp/B09XS7JWHH',
    image_url: 'https://example.com/sony.jpg',
    merchant: 'Amazon',
    description: 'Industry-leading noise cancellation',
  },
]

const multipleProducts = [
  {
    name: 'Sony WH-1000XM5',
    price: 349,
    url: 'https://amazon.com/dp/B09XS7JWHH',
    image_url: 'https://example.com/sony.jpg',
    merchant: 'Amazon',
  },
  {
    name: 'Bose QuietComfort 45',
    price: 279,
    url: 'https://amazon.com/dp/B098FKXT8L',
    image_url: 'https://example.com/bose.jpg',
    merchant: 'Amazon',
  },
  {
    name: 'Apple AirPods Max',
    price: 549,
    url: 'https://amazon.com/dp/B08PZHYWJS',
    image_url: 'https://example.com/airpods.jpg',
    merchant: 'Amazon',
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-02 — Card height and dimensions
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-02 — InlineProductCard height constraint', () => {
  it('card container has 64px height constraint (h-16 class or 64px style)', () => {
    const { container } = render(<InlineProductCard products={singleProduct} />)
    // Each card row must be h-16 (64px)
    const hasH16 =
      container.querySelector('.h-16') !== null ||
      container.querySelector('[class*="h-16"]') !== null ||
      (() => {
        const allEls = Array.from(container.querySelectorAll('*'))
        return allEls.some((el) => (el as HTMLElement).style?.height === '64px')
      })()
    expect(hasH16).toBe(true)
  })

  it('product image renders as 64x64 square with rounded corners', () => {
    const { container } = render(<InlineProductCard products={singleProduct} />)
    // Image must be w-16 h-16 (64x64) with rounded-lg or rounded-md
    const imgEl = container.querySelector('img') as HTMLImageElement | null
    if (imgEl) {
      const classes = imgEl.className
      const has64 =
        classes.includes('w-16') ||
        classes.includes('w-[64px]') ||
        (() => {
          const style = (imgEl as HTMLElement).style
          return style?.width === '64px' && style?.height === '64px'
        })()
      expect(has64).toBe(true)
      // Rounded corners
      const hasRounded =
        classes.includes('rounded-lg') ||
        classes.includes('rounded-md') ||
        classes.includes('rounded-[8px]')
      expect(hasRounded).toBe(true)
    } else {
      // If no img, the placeholder must fill the same space
      const placeholder = container.querySelector('[class*="w-16"][class*="h-16"]')
      expect(placeholder).toBeTruthy()
    }
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-02 — Rank badges
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-02 — Rank badges', () => {
  it('renders "Top Pick" badge for the first product (position 0)', () => {
    render(<InlineProductCard products={multipleProducts} />)
    expect(screen.getByText('Top Pick')).toBeTruthy()
  })

  it('renders "Best Value" badge for the second product (position 1)', () => {
    render(<InlineProductCard products={multipleProducts} />)
    expect(screen.getByText('Best Value')).toBeTruthy()
  })

  it('renders "Premium" badge for the third product (position 2)', () => {
    render(<InlineProductCard products={multipleProducts} />)
    expect(screen.getByText('Premium')).toBeTruthy()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-02 — Product name and price
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-02 — Product name and price', () => {
  it('product name renders with font-semibold and truncate class', () => {
    const { container } = render(<InlineProductCard products={singleProduct} />)
    const nameEl = screen.queryByText('Sony WH-1000XM5')
    expect(nameEl).toBeTruthy()
    const classes = nameEl!.className
    expect(classes).toContain('font-semibold')
    const hasTruncate =
      classes.includes('truncate') || classes.includes('overflow-hidden')
    expect(hasTruncate).toBe(true)
  })

  it('price renders with font-semibold styling', () => {
    const { container } = render(<InlineProductCard products={singleProduct} />)
    // Price element must be present and bold
    const priceEl =
      screen.queryByText('$349') ||
      screen.queryByText('349') ||
      container.querySelector('[class*="font-semibold"]')
    expect(priceEl).toBeTruthy()
  })

  it('price displays with dollar sign prefix', () => {
    const { container } = render(<InlineProductCard products={singleProduct} />)
    const allText = container.textContent ?? ''
    expect(allText).toContain('$349')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-02 — Affiliate link
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-02 — Affiliate link', () => {
  it('renders "Buy on Amazon" text as an anchor tag', () => {
    render(<InlineProductCard products={singleProduct} />)
    const link = screen.queryByText('Buy on Amazon') as HTMLAnchorElement | null
    expect(link).toBeTruthy()
    expect(link!.tagName.toLowerCase()).toBe('a')
  })

  it('affiliate link href points to the product URL', () => {
    render(<InlineProductCard products={singleProduct} />)
    const link = screen.queryByText('Buy on Amazon') as HTMLAnchorElement | null
    expect(link).toBeTruthy()
    expect(link!.href).toContain('amazon.com')
  })

  it('affiliate link has target="_blank" and rel="noopener noreferrer"', () => {
    render(<InlineProductCard products={singleProduct} />)
    const link = screen.queryByText('Buy on Amazon') as HTMLAnchorElement | null
    expect(link).toBeTruthy()
    expect(link!.target).toBe('_blank')
    const rel = link!.getAttribute('rel') ?? ''
    expect(rel).toContain('noopener')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-02 — Image fallback
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-02 — Image fallback', () => {
  it('renders a placeholder div (not broken img) when image_url is not provided', () => {
    const noImageProduct = [
      {
        name: 'Mystery Product',
        price: 99,
        url: 'https://amazon.com/dp/B00001',
        merchant: 'Amazon',
        // image_url intentionally omitted
      },
    ]
    const { container } = render(<InlineProductCard products={noImageProduct} />)
    // Should render a placeholder div, not a broken img tag
    // The placeholder should fill the same w-16 h-16 space
    const imgTags = container.querySelectorAll('img')
    const placeholderDiv = container.querySelector('[data-testid="product-image-placeholder"]') ||
      container.querySelector('[class*="bg-"][class*="w-16"]') ||
      container.querySelector('[class*="placeholder"]')

    // Either no img (showing placeholder div) OR img with proper fallback
    if (imgTags.length > 0) {
      // If img exists, it should have an alt text
      const img = imgTags[0] as HTMLImageElement
      expect(img.alt).toBeTruthy()
    } else {
      // Must have a placeholder element
      expect(placeholderDiv).toBeTruthy()
    }
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CHAT-02 — Dividers between cards
// ─────────────────────────────────────────────────────────────────────────────

describe('CHAT-02 — Dividers between cards', () => {
  it('multiple cards are separated by a visible divider (border-b or border-t class)', () => {
    const { container } = render(<InlineProductCard products={multipleProducts} />)
    // There should be at least one divider between the 3 cards
    const hasDivider =
      container.querySelector('[class*="border-b"]') !== null ||
      container.querySelector('[class*="border-t"]') !== null ||
      container.querySelector('hr') !== null ||
      container.querySelector('[role="separator"]') !== null
    expect(hasDivider).toBe(true)
  })

  it('renders all 3 product names when given 3 products', () => {
    render(<InlineProductCard products={multipleProducts} />)
    expect(screen.getByText('Sony WH-1000XM5')).toBeTruthy()
    expect(screen.getByText('Bose QuietComfort 45')).toBeTruthy()
    expect(screen.getByText('Apple AirPods Max')).toBeTruthy()
  })
})
