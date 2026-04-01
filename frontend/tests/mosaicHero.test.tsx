import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import MosaicHero from '@/components/discover/MosaicHero'

describe('MosaicHero (HERO-01, HERO-03, HERO-04)', () => {
  it('renders at least 8 img elements for mosaic tiles', () => {
    const { container } = render(<MosaicHero />)
    const imgs = container.querySelectorAll('img')
    expect(imgs.length).toBeGreaterThanOrEqual(8)
  })

  it('first img uses loading="eager" (HERO-04)', () => {
    const { container } = render(<MosaicHero />)
    const firstImg = container.querySelector('img')
    expect(firstImg?.getAttribute('loading')).toBe('eager')
  })

  it('first img uses fetchPriority="high" (HERO-04)', () => {
    const { container } = render(<MosaicHero />)
    const firstImg = container.querySelector('img')
    expect(firstImg?.getAttribute('fetchpriority')).toBe('high')
  })

  it('all img elements have explicit width and height (CLS guard)', () => {
    const { container } = render(<MosaicHero />)
    const imgs = container.querySelectorAll('img')
    imgs.forEach((img) => {
      expect(img.getAttribute('width')).toBeTruthy()
      expect(img.getAttribute('height')).toBeTruthy()
    })
  })

  it('root element has aria-hidden="true" (decorative)', () => {
    const { container } = render(<MosaicHero />)
    const root = container.firstElementChild
    expect(root?.getAttribute('aria-hidden')).toBe('true')
  })
})
