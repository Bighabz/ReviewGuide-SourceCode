/**
 * Phase 23 Plan 02 — QAR-10
 *
 * Tests for the custom 404 (not-found) page.
 * Verifies editorial luxury theme: font-serif heading, "404" text,
 * "Back to home" link pointing to "/", and CSS variable color usage.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

// ── Module-level mocks ────────────────────────────────────────────────────────

vi.mock('next/link', () => ({
  default: ({ href, children, className, ...props }: any) => (
    <a href={href} className={className} {...props}>{children}</a>
  ),
}))

import NotFound from '@/app/not-found'

// ─────────────────────────────────────────────────────────────────────────────
// QAR-10 — Custom 404 page
// ─────────────────────────────────────────────────────────────────────────────

describe('QAR-10 — Custom 404 not-found page', () => {
  it('renders "404" text', () => {
    render(<NotFound />)
    expect(screen.getByText('404')).toBeTruthy()
  })

  it('renders a "Back to home" link pointing to "/"', () => {
    const { container } = render(<NotFound />)
    const link = container.querySelector('a[href="/"]')
    expect(link).toBeTruthy()
    expect(link!.textContent).toContain('Back to home')
  })

  it('404 heading uses font-serif class (editorial theme)', () => {
    const { container } = render(<NotFound />)
    const heading = screen.getByText('404')
    expect(heading.className).toContain('font-serif')
  })

  it('404 heading uses CSS variable for text color (not hardcoded)', () => {
    const { container } = render(<NotFound />)
    const heading = screen.getByText('404')
    // Should use var(--text) or var(--primary), not hardcoded colors
    const hasVarColor =
      heading.className.includes('var(--text)') ||
      heading.className.includes('var(--primary)') ||
      heading.className.includes('var(--')
    expect(hasVarColor).toBe(true)
  })

  it('Back to home link uses CSS variable for background (var(--primary))', () => {
    const { container } = render(<NotFound />)
    const link = container.querySelector('a[href="/"]')
    expect(link).toBeTruthy()
    const classes = link!.className
    expect(classes).toContain('var(--primary)')
  })
})
