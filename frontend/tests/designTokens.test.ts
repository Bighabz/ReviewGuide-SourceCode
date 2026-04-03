import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

describe('RFC §2.6 design tokens', () => {
  const globalsPath = path.resolve(__dirname, '../app/globals.css')
  const tailwindPath = path.resolve(__dirname, '../tailwind.config.ts')
  const globals = fs.readFileSync(globalsPath, 'utf-8')
  const tailwind = fs.readFileSync(tailwindPath, 'utf-8')

  it('defines --stream-status-size token', () => {
    expect(globals).toContain('--stream-status-size')
  })

  it('defines --stream-status-color token', () => {
    expect(globals).toContain('--stream-status-color')
  })

  it('defines --stream-content-color token', () => {
    expect(globals).toContain('--stream-content-color')
  })

  it('defines --citation-color token', () => {
    expect(globals).toContain('--citation-color')
  })

  it('defines stream-status-text utility class', () => {
    expect(globals).toContain('.stream-status-text')
  })

  it('defines stream-content-text utility class', () => {
    expect(globals).toContain('.stream-content-text')
  })

  it('defines citation-text utility class', () => {
    expect(globals).toContain('.citation-text')
  })

  it('prefers-reduced-motion block targets real animation classes', () => {
    const motionIdx = globals.indexOf('prefers-reduced-motion: reduce')
    expect(motionIdx).toBeGreaterThan(-1)
    // Extract ~400 chars after the media query declaration to cover the block
    const motionBlock = globals.slice(motionIdx, motionIdx + 400)
    expect(motionBlock).toContain('.animate-card-enter')
    expect(motionBlock).toContain('.animate-pulse')
    expect(motionBlock).toContain('.stream-status-text')
  })

  it('defines card-enter animation in tailwind.config', () => {
    expect(tailwind).toContain('card-enter')
  })

  it('defines stream transition duration in tailwind.config', () => {
    expect(tailwind).toContain("'stream'")
  })

  it('defines stream-out timing function in tailwind.config', () => {
    expect(tailwind).toContain("'stream-out'")
  })

  it('defines stream-inout timing function in tailwind.config', () => {
    expect(tailwind).toContain("'stream-inout'")
  })

  it('preserves legacy --gpt-* variable mappings', () => {
    expect(globals).toContain('--gpt-accent')
    expect(globals).toContain('--gpt-text')
    expect(globals).toContain('--gpt-background')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Phase 17 V3.0 token coverage — QA-02 requirement
// ─────────────────────────────────────────────────────────────────────────────

describe('v3.0 Bold Accent tokens', () => {
  const globalsPath = path.resolve(__dirname, '../app/globals.css')
  const globals = fs.readFileSync(globalsPath, 'utf-8')

  const darkIdx = globals.indexOf('[data-theme="dark"]')
  const darkBlock = darkIdx > -1 ? globals.slice(darkIdx, darkIdx + 3000) : ''

  it('defines --bold-blue in globals.css', () => {
    expect(globals).toContain('--bold-blue')
  })

  it('defines --bold-green in globals.css', () => {
    expect(globals).toContain('--bold-green')
  })

  it('defines --bold-red in globals.css', () => {
    expect(globals).toContain('--bold-red')
  })

  it('defines --bold-amber in globals.css', () => {
    expect(globals).toContain('--bold-amber')
  })

  it('all 4 bold accent tokens exist in [data-theme="dark"] block', () => {
    expect(darkIdx).toBeGreaterThan(-1)
    expect(darkBlock).toContain('--bold-blue')
    expect(darkBlock).toContain('--bold-green')
    expect(darkBlock).toContain('--bold-red')
    expect(darkBlock).toContain('--bold-amber')
  })
})

describe('v3.0 Mosaic scrim token', () => {
  const globalsPath = path.resolve(__dirname, '../app/globals.css')
  const globals = fs.readFileSync(globalsPath, 'utf-8')

  const darkIdx = globals.indexOf('[data-theme="dark"]')
  const darkBlock = darkIdx > -1 ? globals.slice(darkIdx, darkIdx + 3000) : ''

  it('defines --mosaic-scrim in globals.css', () => {
    expect(globals).toContain('--mosaic-scrim')
  })

  it('--mosaic-scrim exists in [data-theme="dark"] block', () => {
    expect(darkIdx).toBeGreaterThan(-1)
    expect(darkBlock).toContain('--mosaic-scrim')
  })
})

describe('v3.0 Typography scale tokens', () => {
  const globalsPath = path.resolve(__dirname, '../app/globals.css')
  const globals = fs.readFileSync(globalsPath, 'utf-8')

  const darkIdx = globals.indexOf('[data-theme="dark"]')
  const darkBlock = darkIdx > -1 ? globals.slice(darkIdx, darkIdx + 3000) : ''

  const TYPOGRAPHY_TOKENS = [
    '--heading-hero',
    '--heading-xl',
    '--heading-lg',
    '--heading-md',
    '--heading-sm',
    '--heading-weight',
    '--heading-line-height',
  ]

  TYPOGRAPHY_TOKENS.forEach((token) => {
    it(`defines ${token} in globals.css`, () => {
      expect(globals).toContain(token)
    })
  })

  it('all 7 typography tokens exist in [data-theme="dark"] block', () => {
    expect(darkIdx).toBeGreaterThan(-1)
    TYPOGRAPHY_TOKENS.forEach((token) => {
      expect(darkBlock).toContain(token)
    })
  })
})
