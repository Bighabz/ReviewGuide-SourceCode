/**
 * Phase 12 — NAV-04
 *
 * Tests for template.tsx (to be created at frontend/app/template.tsx).
 *
 * These tests are in the RED state — they will fail until Plan 02 creates the
 * production file. That is expected and correct.
 *
 * template.tsx is a Next.js App Router template file that wraps every page in
 * a Framer Motion AnimatePresence + motion.div for animated page transitions.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

// Import from the path that Plan 02 will create.
import Template from '@/app/template'

describe('template.tsx — animated page transitions (NAV-04)', () => {
  it('renders children inside the template wrapper', () => {
    render(
      <Template>
        <div data-testid="page-child">Hello from page</div>
      </Template>
    )
    expect(screen.getByTestId('page-child')).toBeTruthy()
    expect(screen.getByText('Hello from page')).toBeTruthy()
  })

  it('motion.div wraps the children (child content is accessible in the DOM)', () => {
    // Framer Motion renders actual DOM elements — the child should be in the document.
    render(
      <Template>
        <p data-testid="inner-paragraph">Inner content</p>
      </Template>
    )
    expect(screen.getByTestId('inner-paragraph')).toBeTruthy()
  })

  it('renders multiple children correctly', () => {
    render(
      <Template>
        <span data-testid="child-1">First</span>
        <span data-testid="child-2">Second</span>
      </Template>
    )
    expect(screen.getByTestId('child-1')).toBeTruthy()
    expect(screen.getByTestId('child-2')).toBeTruthy()
  })
})
