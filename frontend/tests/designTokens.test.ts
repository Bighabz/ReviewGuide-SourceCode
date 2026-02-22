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
