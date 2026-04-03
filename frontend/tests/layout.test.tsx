/**
 * Phase 12 — NAV-05
 *
 * Tests that layout.tsx exports viewport.viewportFit = 'cover'.
 *
 * viewportFit: 'cover' is required so the app content extends into the
 * iPhone notch/safe-area, allowing the tab bar to render behind the home
 * indicator while using env(safe-area-inset-bottom) to pad content above it.
 *
 * Implementation note: layout.tsx is a Next.js Server Component, so we
 * cannot render it in jsdom. Instead we use the file-read approach (same
 * pattern as designTokens.test.ts) to assert the static viewport export
 * contains the required string.
 */

import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

// ─────────────────────────────────────────────────────────────────────────────
// QAR-09 — globals.css body uses overflow-x: clip (not hidden)
// ─────────────────────────────────────────────────────────────────────────────

describe('QAR-09 — globals.css overflow-x: clip on body', () => {
  const cssPath = path.resolve(__dirname, '../app/globals.css')
  const cssSource = fs.readFileSync(cssPath, 'utf-8')

  it('body rule uses overflow-x: clip (not overflow-x: hidden)', () => {
    // Extract the body {} rule content
    const bodyRuleMatch = cssSource.match(/\bbody\s*\{([^}]+)\}/)
    expect(bodyRuleMatch).toBeTruthy()
    const bodyRule = bodyRuleMatch![1]
    // Must have clip
    expect(bodyRule).toContain('overflow-x: clip')
    // Must NOT have overflow-x: hidden
    expect(bodyRule).not.toContain('overflow-x: hidden')
  })
})

describe('layout.tsx — viewport export (NAV-05)', () => {
  const layoutPath = path.resolve(__dirname, '../app/layout.tsx')
  const layoutSource = fs.readFileSync(layoutPath, 'utf-8')

  it("viewport export includes viewportFit: 'cover'", () => {
    // layout.tsx must export a viewport object with viewportFit: 'cover'
    // so iOS renders the app content behind the home indicator safe area.
    expect(layoutSource).toContain("viewportFit: 'cover'")
  })

  it('layout.tsx imports Viewport type from next', () => {
    // Ensure the Viewport type is properly imported (already present in current layout.tsx).
    expect(layoutSource).toContain("Viewport")
  })

  it('layout.tsx exports a viewport named export', () => {
    expect(layoutSource).toContain('export const viewport')
  })
})
