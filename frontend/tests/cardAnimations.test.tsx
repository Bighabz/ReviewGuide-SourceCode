/**
 * Phase 21 — Chat Results Card Polish: Wave 0 test scaffolds for CARD-04
 *
 * Tests covering:
 *   CARD-04 — Spring-physics hover animations on InlineProductCard rows
 *           — ProductReview does NOT use layout prop (prevents streaming frame drops)
 *           — TopPickBlock does NOT have product-card-hover class (Framer Motion owns hover)
 *
 * Some tests define RED contracts that Task 3 will make green.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

// ── Module-level mocks ────────────────────────────────────────────────────────

// We deliberately do NOT fully mock framer-motion here — we need to detect
// whether motion.div is being used (the rendered div will carry data attributes
// or style attributes injected by framer-motion). For the "motion.div" check
// we use a partial spy that passes through but records what props were used.

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, whileHover, transition, ...props }: any) => (
      <div
        className={className}
        data-has-while-hover={whileHover ? 'true' : undefined}
        data-transition-type={transition?.type}
        data-transition-stiffness={transition?.stiffness}
        data-transition-damping={transition?.damping}
        {...props}
      >
        {children}
      </div>
    ),
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('lucide-react', () => ({
  Award: () => <span data-testid="icon-award" />,
  ExternalLink: () => <span data-testid="icon-external" />,
  Star: () => <span data-testid="icon-star" />,
  ChevronDown: () => <span data-testid="icon-chevron-down" />,
  ChevronUp: () => <span data-testid="icon-chevron-up" />,
}))

import InlineProductCard from '@/components/InlineProductCard'
import ProductReview from '@/components/ProductReview'
import TopPickBlock from '@/components/TopPickBlock'

// ── Test fixtures ─────────────────────────────────────────────────────────────

const twoProducts = [
  {
    name: 'Sony WH-1000XM5',
    price: 349,
    url: 'https://amazon.com/dp/B09XS7JWHH',
    image_url: 'https://example.com/sony.jpg',
    merchant: 'Amazon',
    description: 'Industry-leading noise cancellation',
  },
  {
    name: 'Bose QuietComfort 45',
    price: 279,
    url: 'https://amazon.com/dp/B098FKXT8L',
    image_url: 'https://example.com/bose.jpg',
    merchant: 'Amazon',
  },
]

const minimalProduct = {
  product_name: 'Sony WH-1000XM5',
  rating: '4.5/5',
  summary: 'Great headphones.',
  features: [],
  pros: [],
  cons: [],
  affiliate_links: [
    {
      product_id: 'p1',
      title: 'Sony WH-1000XM5',
      price: 349,
      currency: 'USD',
      affiliate_link: 'https://www.amazon.com/dp/B09XS7JWHH',
      merchant: 'Amazon',
    },
  ],
  rank: 1,
}

const topPickProps = {
  productName: 'Sony WH-1000XM5',
  headline: 'Best ANC headphones on the market',
  bestFor: 'Commuters and frequent flyers',
  notFor: 'Audiophiles who need flat response',
}

// ─────────────────────────────────────────────────────────────────────────────
// CARD-04 — InlineProductCard rows use motion.div with whileHover
// ─────────────────────────────────────────────────────────────────────────────

describe('CARD-04 — InlineProductCard spring hover animation', () => {
  it('renders product rows with whileHover prop (motion.div)', () => {
    const { container } = render(<InlineProductCard products={twoProducts} />)
    // Our mock sets data-has-while-hover="true" when whileHover prop is present
    const motionRows = container.querySelectorAll('[data-has-while-hover="true"]')
    expect(motionRows.length).toBeGreaterThanOrEqual(2)
  })

  it('product rows use spring transition type', () => {
    const { container } = render(<InlineProductCard products={twoProducts} />)
    const springRows = container.querySelectorAll('[data-transition-type="spring"]')
    expect(springRows.length).toBeGreaterThanOrEqual(2)
  })

  it('product rows use stiffness of 400 for snappy spring', () => {
    const { container } = render(<InlineProductCard products={twoProducts} />)
    const rows = container.querySelectorAll('[data-transition-stiffness="400"]')
    expect(rows.length).toBeGreaterThanOrEqual(2)
  })

  it('product rows use damping of 28 for spring', () => {
    const { container } = render(<InlineProductCard products={twoProducts} />)
    const rows = container.querySelectorAll('[data-transition-damping="28"]')
    expect(rows.length).toBeGreaterThanOrEqual(2)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CARD-04 — ProductReview does NOT use layout prop (streaming frame-drop risk)
// ─────────────────────────────────────────────────────────────────────────────

describe('CARD-04 — ProductReview layout prop guard', () => {
  it('outer element does NOT have layout attribute (prevents streaming frame drops)', () => {
    const { container } = render(<ProductReview product={minimalProduct} />)
    const outer = container.firstChild as HTMLElement
    // The layout prop from framer-motion would be forwarded as attribute or data attr
    expect(outer?.getAttribute('layout')).toBeNull()
    expect(outer?.getAttribute('data-layout')).toBeNull()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CARD-04 — TopPickBlock does NOT have product-card-hover class
// ─────────────────────────────────────────────────────────────────────────────

describe('CARD-04 — TopPickBlock product-card-hover upgrade', () => {
  it('TopPickBlock root element does NOT contain product-card-hover class (Framer Motion owns hover)', () => {
    const { container } = render(<TopPickBlock {...topPickProps} />)
    const root = container.firstChild as HTMLElement
    // After upgrade, product-card-hover CSS class should be removed in favour of
    // Framer Motion whileHover. This test defines the contract for Plan 02.
    expect(root?.className).not.toContain('product-card-hover')
  })
})
