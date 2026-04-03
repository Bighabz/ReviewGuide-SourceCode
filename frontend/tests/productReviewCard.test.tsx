/**
 * Phase 21 — Chat Results Card Polish: Wave 0 test scaffolds for CARD-01, CARD-02
 *
 * Tests covering:
 *   CARD-01 — ProductReview premium spacing classes (rounded-xl, p-3, sm:p-6, shadow-card)
 *   CARD-02 — Merchant name derivation logic: URL-based, eBay suffix cleaning, fallback domain cap
 *
 * Some tests intentionally define contracts for future implementation (Wave 0).
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

// ── Module-level mocks ────────────────────────────────────────────────────────

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, ...props }: any) => (
      <div className={className} {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('lucide-react', () => ({
  ExternalLink: () => <span data-testid="icon-external" />,
  Star: () => <span data-testid="icon-star" />,
}))

import ProductReview from '@/components/ProductReview'

// ── Fixture helpers ───────────────────────────────────────────────────────────

interface AffiliateLink {
  product_id: string
  title: string
  price: number
  currency: string
  affiliate_link: string
  merchant: string
  image_url?: string
  rating?: number
  review_count?: number
}

function makeAffiliateLink(overrides: Partial<AffiliateLink> = {}): AffiliateLink {
  return {
    product_id: 'prod-1',
    title: 'Test Product',
    price: 299.99,
    currency: 'USD',
    affiliate_link: 'https://www.amazon.com/dp/B09XS7JWHH',
    merchant: 'Amazon',
    ...overrides,
  }
}

function makeProduct(affiliateLinks: AffiliateLink[] = [makeAffiliateLink()]) {
  return {
    product_name: 'Sony WH-1000XM5',
    rating: '4.5/5',
    summary: 'Industry-leading noise cancellation with exceptional comfort.',
    image_url: 'https://example.com/sony.jpg',
    features: ['Noise Cancellation', 'Wireless', '30hr Battery'],
    pros: [{ description: 'Excellent ANC' }],
    cons: [{ description: 'Expensive' }],
    affiliate_links: affiliateLinks,
    rank: 1,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CARD-01 — Premium spacing classes
// ─────────────────────────────────────────────────────────────────────────────

describe('CARD-01 — ProductReview premium spacing classes', () => {
  it('renders with rounded-xl class', () => {
    const { container } = render(<ProductReview product={makeProduct()} />)
    // The outer motion.div (rendered as div) should have rounded-xl
    const outer = container.firstChild as HTMLElement
    expect(outer?.className).toContain('rounded-xl')
  })

  it('renders with p-3 mobile padding class', () => {
    const { container } = render(<ProductReview product={makeProduct()} />)
    const outer = container.firstChild as HTMLElement
    expect(outer?.className).toContain('p-3')
  })

  it('renders with sm:p-6 desktop padding class', () => {
    const { container } = render(<ProductReview product={makeProduct()} />)
    const outer = container.firstChild as HTMLElement
    expect(outer?.className).toContain('sm:p-6')
  })

  it('renders with shadow-card elevation class', () => {
    const { container } = render(<ProductReview product={makeProduct()} />)
    const outer = container.firstChild as HTMLElement
    expect(outer?.className).toContain('shadow-card')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CARD-02 — Affiliate link cap at 3
// ─────────────────────────────────────────────────────────────────────────────

describe('CARD-02 — Affiliate links capped at 3', () => {
  it('caps affiliate links at 3 when 5 are provided', () => {
    const fiveLinks = [
      makeAffiliateLink({ product_id: 'p1', merchant: 'Amazon', affiliate_link: 'https://www.amazon.com/dp/1' }),
      makeAffiliateLink({ product_id: 'p2', merchant: 'eBay', affiliate_link: 'https://www.ebay.com/itm/2' }),
      makeAffiliateLink({ product_id: 'p3', merchant: 'Walmart', affiliate_link: 'https://www.walmart.com/ip/3' }),
      makeAffiliateLink({ product_id: 'p4', merchant: 'Best Buy', affiliate_link: 'https://www.bestbuy.com/site/4' }),
      makeAffiliateLink({ product_id: 'p5', merchant: 'Target', affiliate_link: 'https://www.target.com/p/5' }),
    ]
    const { container } = render(<ProductReview product={makeProduct(fiveLinks)} />)
    // Only 3 <a target="_blank"> links should appear in the affiliate section
    const affiliateLinks = Array.from(container.querySelectorAll('a[target="_blank"]'))
    expect(affiliateLinks.length).toBeLessThanOrEqual(3)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// CARD-02 — Merchant name derivation from URL
// ─────────────────────────────────────────────────────────────────────────────

describe('CARD-02 — Merchant name derivation', () => {
  it('derives "Best Buy" from bestbuy.com URL when merchant field is empty', () => {
    const link = makeAffiliateLink({
      merchant: '',
      affiliate_link: 'https://www.bestbuy.com/product/123',
    })
    render(<ProductReview product={makeProduct([link])} />)
    expect(screen.getByText(/best buy/i)).toBeInTheDocument()
  })

  it('derives "Walmart" from walmart.com URL when merchant is generic "Retailer"', () => {
    const link = makeAffiliateLink({
      merchant: 'Retailer',
      affiliate_link: 'https://www.walmart.com/ip/456',
    })
    render(<ProductReview product={makeProduct([link])} />)
    // The merchant display should show "Walmart" not "Retailer"
    expect(screen.getByText(/walmart/i)).toBeInTheDocument()
  })

  it('cleans eBay merchant suffix like "eBay (lawrenow-0)" to just "eBay"', () => {
    const link = makeAffiliateLink({
      merchant: 'eBay (lawrenow-0)',
      affiliate_link: 'https://www.ebay.com/itm/789',
    })
    render(<ProductReview product={makeProduct([link])} />)
    expect(screen.getByText('eBay')).toBeInTheDocument()
  })

  it('falls back to capitalized domain name for unknown merchants', () => {
    const link = makeAffiliateLink({
      merchant: '',
      affiliate_link: 'https://www.newegg.com/product/abc',
    })
    render(<ProductReview product={makeProduct([link])} />)
    expect(screen.getByText(/newegg/i)).toBeInTheDocument()
  })
})
