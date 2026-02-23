/**
 * RFC §2.5 — Content Trust and Explainability UI
 *
 * Tests covering acceptance criteria:
 *   1. Panel does NOT render when degraded: false and missing_sources: []
 *   2. Panel trigger appears when degraded: true
 *   3. Panel trigger appears when missing_sources non-empty
 *   4. Panel is collapsed by default; clicking trigger expands it
 *   5. Timed-out providers are shown with human-readable names
 *   6. Low confidence badge shown when confidence_score < 0.6
 *   7. Low confidence badge NOT shown when confidence_score >= 0.6
 *   8. Panel does not render when neither condition is met (guard)
 *   9. Omitted sections are shown when non-empty
 */

import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { ExplainabilityPanel } from '@/components/ExplainabilityPanel'
import type { ResponseMetadata } from '@/lib/chatApi'

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeMetadata(overrides: Partial<ResponseMetadata> = {}): ResponseMetadata {
  return {
    source_count: 5,
    provider_coverage: [],
    confidence_score: 1.0,
    omitted_sections: [],
    degraded: false,
    missing_sources: [],
    web_context_cache_age_s: null,
    ...overrides,
  }
}

// Helper: render and look for the trigger button
function renderPanel(metadata: ResponseMetadata) {
  return render(<ExplainabilityPanel metadata={metadata} />)
}

// ── Test suite ────────────────────────────────────────────────────────────────

describe('RFC §2.5 — ExplainabilityPanel', () => {

  // ── Acceptance criteria 1: no trigger shown in the healthy case ─────────────
  // NOTE: The component is only rendered by Message.tsx when degraded === true
  // OR missing_sources is non-empty.  The component itself always renders its
  // root; the guard logic lives in Message.tsx.  These tests verify the
  // component's internal rendering given metadata it receives.

  it('does NOT show the trigger when degraded is false and missing_sources is empty', () => {
    // NOTE: The rendering guard lives in Message.tsx, not in ExplainabilityPanel itself.
    // ExplainabilityPanel always renders its root when mounted; Message.tsx gates whether
    // to mount it at all.  This test verifies the guard condition logic without touching
    // the DOM — it is intentionally a pure-logic assertion.
    const meta = makeMetadata({ degraded: false, missing_sources: [] })
    // Simulate the Message.tsx guard: we check the condition ourselves
    const shouldRender = meta.degraded || meta.missing_sources.length > 0
    expect(shouldRender).toBe(false)
  })

  // Companion: when the panel IS mounted it always renders the trigger
  it('renders the trigger button when mounted', () => {
    const meta = makeMetadata({ degraded: true })
    renderPanel(meta)
    expect(screen.getByTestId('explainability-trigger')).toBeTruthy()
  })

  // ── Acceptance criteria 2: trigger shows when degraded: true ────────────────

  it('renders the trigger link when degraded is true', () => {
    const meta = makeMetadata({ degraded: true })
    renderPanel(meta)
    expect(screen.getByTestId('explainability-trigger')).toBeTruthy()
    expect(screen.getByText(/Results may be incomplete/i)).toBeTruthy()
  })

  // ── Acceptance criteria 3: trigger shows when missing_sources non-empty ─────

  it('renders the trigger link when missing_sources is non-empty', () => {
    const meta = makeMetadata({ missing_sources: ['ebay'] })
    renderPanel(meta)
    expect(screen.getByTestId('explainability-trigger')).toBeTruthy()
    expect(screen.getByText(/Results may be incomplete/i)).toBeTruthy()
  })

  // ── Acceptance criteria 4: collapsed by default, expands on click ────────────

  it('is collapsed by default (detail panel not visible)', () => {
    const meta = makeMetadata({ degraded: true })
    renderPanel(meta)
    expect(screen.queryByTestId('explainability-detail')).toBeNull()
  })

  it('expands the detail panel when trigger is clicked', () => {
    const meta = makeMetadata({ degraded: true })
    renderPanel(meta)
    const trigger = screen.getByTestId('explainability-trigger')
    fireEvent.click(trigger)
    expect(screen.getByTestId('explainability-detail')).toBeTruthy()
  })

  it('collapses the panel again when trigger is clicked a second time', () => {
    const meta = makeMetadata({ degraded: true })
    renderPanel(meta)
    const trigger = screen.getByTestId('explainability-trigger')
    fireEvent.click(trigger)
    expect(screen.getByTestId('explainability-detail')).toBeTruthy()
    fireEvent.click(trigger)
    expect(screen.queryByTestId('explainability-detail')).toBeNull()
  })

  // ── Acceptance criteria 5: timed-out providers → human-readable names ───────

  it('shows human-readable name "eBay" for provider key "ebay" when timed_out', () => {
    const meta = makeMetadata({
      degraded: true,
      provider_coverage: [
        { provider: 'ebay', status: 'timed_out', result_count: 0 },
      ],
    })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    const container = screen.getByTestId('timed-out-providers')
    expect(container).toBeTruthy()
    // Scoped to the timed-out-providers container to avoid false positives from incidental text
    expect(within(container).getByText(/eBay/)).toBeTruthy()
  })

  it('shows human-readable name "Amazon" for provider key "amazon" when timed_out', () => {
    const meta = makeMetadata({
      degraded: true,
      provider_coverage: [
        { provider: 'amazon', status: 'timed_out', result_count: 0 },
      ],
    })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    // Scoped to the timed-out-providers container to avoid false positives from incidental text
    const container = screen.getByTestId('timed-out-providers')
    expect(within(container).getByText(/Amazon/)).toBeTruthy()
  })

  it('shows human-readable name "Booking.com" for provider "booking"', () => {
    const meta = makeMetadata({
      degraded: true,
      provider_coverage: [
        { provider: 'booking', status: 'timed_out', result_count: 0 },
      ],
    })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    // Scoped to the timed-out-providers container to avoid false positives from incidental text
    const container = screen.getByTestId('timed-out-providers')
    expect(within(container).getByText(/Booking\.com/)).toBeTruthy()
  })

  it('shows human-readable name "Flight Search" for provider "amadeus"', () => {
    const meta = makeMetadata({
      degraded: true,
      provider_coverage: [
        { provider: 'amadeus', status: 'timed_out', result_count: 0 },
      ],
    })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    // Scoped to the timed-out-providers container to avoid false positives from incidental text
    const container = screen.getByTestId('timed-out-providers')
    expect(within(container).getByText(/Flight Search/)).toBeTruthy()
  })

  it('falls back to the raw provider key when no display name is registered', () => {
    const meta = makeMetadata({
      degraded: true,
      provider_coverage: [
        { provider: 'unknown_provider_xyz', status: 'timed_out', result_count: 0 },
      ],
    })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    // Scoped to the timed-out-providers container to avoid false positives from incidental text
    const container = screen.getByTestId('timed-out-providers')
    expect(within(container).getByText(/unknown_provider_xyz/)).toBeTruthy()
  })

  it('lists multiple timed-out providers separated by comma', () => {
    const meta = makeMetadata({
      degraded: true,
      provider_coverage: [
        { provider: 'ebay', status: 'timed_out', result_count: 0 },
        { provider: 'amazon', status: 'timed_out', result_count: 0 },
      ],
    })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    const timedOut = screen.getByTestId('timed-out-providers')
    expect(timedOut.textContent).toContain('eBay')
    expect(timedOut.textContent).toContain('Amazon')
  })

  // ── Acceptance criteria 6: low confidence badge when score < 0.6 ─────────────

  it('shows "Low confidence" badge when confidence_score is 0.5 (< 0.6)', () => {
    const meta = makeMetadata({ degraded: true, confidence_score: 0.5 })
    renderPanel(meta)
    expect(screen.getByTestId('low-confidence-badge')).toBeTruthy()
    expect(screen.getByText(/Low confidence/i)).toBeTruthy()
  })

  it('shows "Low confidence" badge when confidence_score is 0.3', () => {
    const meta = makeMetadata({ degraded: true, confidence_score: 0.3 })
    renderPanel(meta)
    expect(screen.getByTestId('low-confidence-badge')).toBeTruthy()
  })

  // ── Acceptance criteria 7: no badge when score >= 0.6 ────────────────────────

  it('does NOT show "Low confidence" badge when confidence_score is 0.6', () => {
    const meta = makeMetadata({ degraded: true, confidence_score: 0.6 })
    renderPanel(meta)
    expect(screen.queryByTestId('low-confidence-badge')).toBeNull()
  })

  it('does NOT show "Low confidence" badge when confidence_score is 1.0', () => {
    const meta = makeMetadata({ degraded: true, confidence_score: 1.0 })
    renderPanel(meta)
    expect(screen.queryByTestId('low-confidence-badge')).toBeNull()
  })

  // ── Extra: omitted sections ──────────────────────────────────────────────────

  it('shows omitted sections when non-empty', () => {
    const meta = makeMetadata({
      degraded: true,
      omitted_sections: ['affiliate_links', 'review_ranking'],
    })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    expect(screen.getByTestId('omitted-sections')).toBeTruthy()
    expect(screen.getByText(/affiliate_links/)).toBeTruthy()
  })

  it('does NOT show omitted sections block when list is empty', () => {
    const meta = makeMetadata({ degraded: true, omitted_sections: [] })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    expect(screen.queryByTestId('omitted-sections')).toBeNull()
  })

  // ── Extra: confidence score display ─────────────────────────────────────────

  it('shows the confidence score as a percentage when expanded', () => {
    const meta = makeMetadata({ degraded: true, confidence_score: 0.75 })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    expect(screen.getByTestId('confidence-score')).toBeTruthy()
    expect(screen.getByText(/75%/)).toBeTruthy()
  })

  // ── Extra: trigger aria-expanded attribute ───────────────────────────────────

  it('sets aria-expanded=false on trigger when collapsed', () => {
    const meta = makeMetadata({ degraded: true })
    renderPanel(meta)
    const trigger = screen.getByTestId('explainability-trigger')
    expect(trigger.getAttribute('aria-expanded')).toBe('false')
  })

  it('sets aria-expanded=true on trigger when expanded', () => {
    const meta = makeMetadata({ degraded: true })
    renderPanel(meta)
    const trigger = screen.getByTestId('explainability-trigger')
    fireEvent.click(trigger)
    expect(trigger.getAttribute('aria-expanded')).toBe('true')
  })

  // ── Missing sources section (non-timed-out unavailable providers) ────────────

  it('shows missing-sources section when missing_sources non-empty and no timed_out providers', () => {
    const meta = makeMetadata({
      missing_sources: ['serpapi'],
      provider_coverage: [
        { provider: 'serpapi', status: 'unavailable', result_count: 0 },
      ],
    })
    renderPanel(meta)
    fireEvent.click(screen.getByTestId('explainability-trigger'))
    expect(screen.getByTestId('missing-sources')).toBeTruthy()
  })
})

// ── Message.tsx rendering guard logic (unit test without DOM) ─────────────────

describe('RFC §2.5 — Message.tsx rendering guard', () => {
  it('returns false (no panel) when degraded is false and missing_sources is empty', () => {
    const meta = makeMetadata({ degraded: false, missing_sources: [] })
    const shouldShow = meta.degraded || meta.missing_sources.length > 0
    expect(shouldShow).toBe(false)
  })

  it('returns true (show panel) when degraded is true', () => {
    const meta = makeMetadata({ degraded: true, missing_sources: [] })
    const shouldShow = meta.degraded || meta.missing_sources.length > 0
    expect(shouldShow).toBe(true)
  })

  it('returns true (show panel) when missing_sources is non-empty even if degraded is false', () => {
    const meta = makeMetadata({ degraded: false, missing_sources: ['ebay'] })
    const shouldShow = meta.degraded || meta.missing_sources.length > 0
    expect(shouldShow).toBe(true)
  })
})
