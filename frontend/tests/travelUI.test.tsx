/**
 * Phase 24 — Travel Response UI Overhaul: Test Scaffold
 *
 * Tests covering TRVL-01 through TRVL-07:
 *   TRVL-01 — ResortCards renders attraction strings as card elements (not bullet list items)
 *   TRVL-02 — ResortCards falls back to generic image when no resort name matches the lookup map
 *   TRVL-03 — HotelCards PLPLinkCard renders a hero image element (img tag present)
 *   TRVL-04 — HotelCards PLPLinkCard CTA button text reads "Search on Expedia"
 *   TRVL-05 — FlightCards PLPLinkCard CTA button text reads "Search on Expedia"
 *   TRVL-06 — FlightCards PLPLinkCard destination text does not use tracking-wider class
 *   TRVL-07 — BlockRegistry conclusion block renders with a tinted background style (color-mix)
 *
 * TRVL-01 and TRVL-02: RED until Task 2 (ResortCards created)
 * TRVL-03 through TRVL-07: RED until Plan 02 executes
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

// ── Module-level mocks (must be before component imports) ─────────────────────

vi.mock('@/lib/trackAffiliate', () => ({
  trackAffiliateClick: vi.fn(),
}))

vi.mock('next/link', () => ({
  default: ({ href, children, className, ...props }: any) => (
    <a href={href} className={className} {...props}>{children}</a>
  ),
}))

// ── Component imports ─────────────────────────────────────────────────────────

import ResortCards from '@/components/ResortCards'
import HotelCards from '@/components/HotelCards'
import FlightCards from '@/components/FlightCards'
import { UIBlocks } from '@/components/blocks/BlockRegistry'
import type { NormalizedBlock } from '@/lib/normalizeBlocks'

// ── TRVL-01: ResortCards renders cards not bullet list items ──────────────────

describe('TRVL-01: ResortCards card rendering', () => {
  it('renders attraction strings as card elements, not <li> bullet items', () => {
    const items = ['Seven Mile Beach, Negril', 'Dunn\'s River Falls']
    const { container } = render(<ResortCards items={items} title="Must-See Attractions" />)

    // Should NOT render <li> elements (that's the ListBlock pattern)
    const listItems = container.querySelectorAll('li')
    expect(listItems).toHaveLength(0)

    // Should render card-like elements with the attraction names
    expect(screen.getByText('Seven Mile Beach, Negril')).toBeInTheDocument()
    expect(screen.getByText('Dunn\'s River Falls')).toBeInTheDocument()
  })

  it('renders the section title', () => {
    render(<ResortCards items={['Test Beach']} title="Must-See Attractions" />)
    expect(screen.getByText('Must-See Attractions')).toBeInTheDocument()
  })

  it('returns null when items array is empty', () => {
    const { container } = render(<ResortCards items={[]} title="Must-See Attractions" />)
    expect(container.firstChild).toBeNull()
  })
})

// ── TRVL-02: ResortCards uses deterministic image fallback ────────────────────

describe('TRVL-02: ResortCards deterministic image lookup', () => {
  it('renders an img element for each attraction card', () => {
    const items = ['Seven Mile Beach, Negril']
    const { container } = render(<ResortCards items={items} />)
    const images = container.querySelectorAll('img')
    expect(images.length).toBeGreaterThanOrEqual(1)
  })

  it('uses fallback image for unrecognised resort names', () => {
    const items = ['Unknown Resort XYZ 12345']
    const { container } = render(<ResortCards items={items} />)
    const images = container.querySelectorAll('img')
    expect(images.length).toBeGreaterThanOrEqual(1)
    // Fallback image path should be used
    const firstImg = images[0] as HTMLImageElement
    expect(firstImg.src).toContain('/images/products/fallback-hotel.webp')
  })

  it('does not use Math.random (images are deterministic)', () => {
    const items = ['Unknown Place A', 'Unknown Place B']
    const { container: c1 } = render(<ResortCards items={items} />)
    const { container: c2 } = render(<ResortCards items={items} />)
    const imgs1 = Array.from(c1.querySelectorAll('img')).map((i: any) => i.src)
    const imgs2 = Array.from(c2.querySelectorAll('img')).map((i: any) => i.src)
    expect(imgs1).toEqual(imgs2)
  })
})

// ── TRVL-03: HotelCards PLPLinkCard renders hero image ───────────────────────

describe('TRVL-03: HotelCards PLPLinkCard hero image', () => {
  it('renders an img element in the PLP link card', () => {
    const hotels = [
      {
        type: 'plp_link' as const,
        provider: 'expedia',
        destination: 'Jamaica',
        search_url: 'https://expedia.com/search',
        title: 'Hotels in Jamaica',
      },
    ]
    const { container } = render(<HotelCards hotels={hotels} />)
    const images = container.querySelectorAll('img')
    // TRVL-03: RED until Plan 02 adds hero image to PLPLinkCard
    expect(images.length).toBeGreaterThanOrEqual(1)
  })
})

// ── TRVL-04: HotelCards PLPLinkCard CTA text ─────────────────────────────────

describe('TRVL-04: HotelCards PLPLinkCard CTA text', () => {
  it('CTA button reads "Search on Expedia" not "Search Properties"', () => {
    const hotels = [
      {
        type: 'plp_link' as const,
        provider: 'expedia',
        destination: 'Jamaica',
        search_url: 'https://expedia.com/search',
        title: 'Hotels in Jamaica',
      },
    ]
    render(<HotelCards hotels={hotels} />)
    // TRVL-04: RED until Plan 02 updates CTA text
    expect(screen.getByText('Search on Expedia')).toBeInTheDocument()
    expect(screen.queryByText('Search Properties')).not.toBeInTheDocument()
  })
})

// ── TRVL-05: FlightCards PLPLinkCard CTA text ────────────────────────────────

describe('TRVL-05: FlightCards PLPLinkCard CTA text', () => {
  it('CTA button reads "Search on Expedia" not "Search Flights"', () => {
    const flights = [
      {
        type: 'plp_link' as const,
        provider: 'expedia',
        origin: 'JFK',
        destination: 'MBJ',
        search_url: 'https://expedia.com/flights',
        title: 'Flights to Jamaica',
      },
    ]
    render(<FlightCards flights={flights} />)
    // TRVL-05: RED until Plan 02 updates CTA text
    expect(screen.getByText('Search on Expedia')).toBeInTheDocument()
    expect(screen.queryByText('Search Flights')).not.toBeInTheDocument()
  })
})

// ── TRVL-06: FlightCards PLPLinkCard destination no tracking-wider ────────────

describe('TRVL-06: FlightCards PLPLinkCard destination text class', () => {
  it('destination span does not have tracking-wider class (Caribbean wrap fix)', () => {
    const flights = [
      {
        type: 'plp_link' as const,
        provider: 'expedia',
        origin: 'JFK',
        destination: 'MBJ',
        search_url: 'https://expedia.com/flights',
        title: 'Flights to Jamaica',
      },
    ]
    const { container } = render(<FlightCards flights={flights} />)
    // TRVL-06: RED until Plan 02 removes tracking-wider from destination span
    const trackingWiderSpans = container.querySelectorAll('span.tracking-wider')
    // The destination text (MBJ) should not have tracking-wider
    const destinationSpans = Array.from(trackingWiderSpans).filter((el) =>
      el.textContent?.includes('MBJ')
    )
    expect(destinationSpans).toHaveLength(0)
  })
})

// ── TRVL-07: BlockRegistry conclusion block tinted background ─────────────────

describe('TRVL-07: BlockRegistry conclusion block tinted background', () => {
  it('conclusion block container has color-mix in its inline style', () => {
    const blocks: NormalizedBlock[] = [
      {
        type: 'conclusion',
        data: { text: 'This is a great destination for your next vacation.' },
      },
    ]
    const { container } = render(<UIBlocks blocks={blocks} />)
    // TRVL-07: RED until Plan 02 adds color-mix tinted bg to conclusion block
    const allElements = container.querySelectorAll('*')
    const hasColorMix = Array.from(allElements).some((el) => {
      const style = (el as HTMLElement).getAttribute('style') ?? ''
      return style.includes('color-mix')
    })
    expect(hasColorMix).toBe(true)
  })
})
