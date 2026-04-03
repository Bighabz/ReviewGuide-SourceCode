/**
 * Phase 20 -- Browse Hero Upgrades: tests for BRW-01 and BRW-02
 *
 * Tests covering:
 *   BRW-01 -- categoryConfig uses /images/categories/cat-*.webp paths
 *   BRW-01 -- hero gradient deepened to from-black/80 via-black/50 to-black/10
 *   BRW-02 -- EditorsPicks cards rendered at w-44 width (covered in editorsPicks.test.tsx too)
 *   DISC-06 -- CategoryChipRow 44px height + color-mix accent backgrounds
 *   DISC-06 -- TrendingCards 80px thumbnails with accent border rings
 */

import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import * as fs from 'fs'
import * as path from 'path'

import { categories } from '@/lib/categoryConfig'
import CategoryChipRow from '@/components/discover/CategoryChipRow'
import TrendingCards from '@/components/discover/TrendingCards'

// lucide-react mock (ChevronRight used in TrendingCards)
vi.mock('lucide-react', () => ({
  ChevronRight: () => <span data-testid="icon-chevron" />,
}))

// ---------------------------------------------------------------------------
// BRW-01: categoryConfig image paths
// ---------------------------------------------------------------------------

describe('BRW-01 — categoryConfig image paths', () => {
  it('every category image field starts with /images/categories/', () => {
    categories.forEach((cat) => {
      expect(cat.image).toMatch(/^\/images\/categories\//)
    })
  })

  it('every category image field ends with .webp', () => {
    categories.forEach((cat) => {
      expect(cat.image).toMatch(/\.webp$/)
    })
  })

  it('every referenced WebP file actually exists on disk', () => {
    // Resolve relative to the frontend/public directory
    const publicDir = path.resolve(__dirname, '..', 'public')
    categories.forEach((cat) => {
      // Strip leading slash before joining
      const relativePath = cat.image.replace(/^\//, '')
      const fullPath = path.join(publicDir, relativePath)
      const exists = fs.existsSync(fullPath)
      expect(exists, `Missing file: ${fullPath}`).toBe(true)
    })
  })

  it('no category image path contains /images/browse/ (old paths eliminated)', () => {
    categories.forEach((cat) => {
      expect(cat.image).not.toContain('/images/browse/')
    })
  })
})

// ---------------------------------------------------------------------------
// BRW-01: hero gradient deepened (source-level assertion)
// ---------------------------------------------------------------------------

describe('BRW-01 — hero gradient deepened', () => {
  const pageSource = fs.readFileSync(
    path.resolve(__dirname, '..', 'app', 'browse', '[category]', 'page.tsx'),
    'utf-8'
  )

  it('hero gradient uses from-black/80 (deepened overlay)', () => {
    expect(pageSource).toContain('from-black/80')
  })

  it('hero gradient does NOT contain from-black/70 (old overlay removed)', () => {
    expect(pageSource).not.toContain('from-black/70')
  })
})

// ---------------------------------------------------------------------------
// DISC-06: CategoryChipRow bold accent treatment
// ---------------------------------------------------------------------------

describe('DISC-06: CategoryChipRow bold accent treatment', () => {
  it('renders chips with 44px height', () => {
    const { container } = render(<CategoryChipRow />)
    const buttons = container.querySelectorAll('button')
    expect(buttons.length).toBeGreaterThanOrEqual(2)
    buttons.forEach((btn) => {
      expect(btn.style.height).toBe('44px')
    })
  })

  it('inactive chips use color-mix accent background', () => {
    const { container } = render(<CategoryChipRow />)
    const buttons = container.querySelectorAll('button')
    // Second button (index 1) is inactive — should have color-mix background
    const inactiveBtn = buttons[1]
    expect(inactiveBtn.style.background).toContain('color-mix')
  })
})

// ---------------------------------------------------------------------------
// DISC-06: TrendingCards larger thumbnails
// ---------------------------------------------------------------------------

describe('DISC-06: TrendingCards larger thumbnails', () => {
  it('renders thumbnails at 80px width', () => {
    const { container } = render(<TrendingCards />)
    // The thumbnail containers are the first div inside each button
    const cards = container.querySelectorAll('[data-testid="trending-card"]')
    expect(cards.length).toBeGreaterThanOrEqual(1)
    cards.forEach((card) => {
      const thumbContainer = card.querySelector('div[aria-hidden="true"]')
      expect(thumbContainer).toBeTruthy()
      expect((thumbContainer as HTMLElement).style.width).toBe('80px')
    })
  })
})
