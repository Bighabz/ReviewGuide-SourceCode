/**
 * RFC §2.3 — Message-Level Recovery UX
 *
 * Tests for MessageRecoveryUI component covering:
 *   1. Renders the correct buttons in 'partial' state
 *   2. onRetryFull is called when Retry is clicked
 *   3. onShowPartial is called when "Show what I have" is clicked
 *   4. When completeness === 'degraded', no action buttons are shown
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import MessageRecoveryUI from '@/components/MessageRecoveryUI'
import type { MessageRecoveryUIProps } from '@/components/MessageRecoveryUI'

// ─── Helper ──────────────────────────────────────────────────────────────────

function renderUI(overrides: Partial<MessageRecoveryUIProps> = {}) {
  const defaults: MessageRecoveryUIProps = {
    completeness: 'partial',
    onShowPartial: vi.fn(),
    onRetryFull: vi.fn(),
  }
  const props = { ...defaults, ...overrides }
  return { ...render(<MessageRecoveryUI {...props} />), props }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('MessageRecoveryUI — partial state', () => {
  it('renders the recovery container', () => {
    renderUI({ completeness: 'partial' })
    expect(screen.getByTestId('message-recovery-ui')).toBeTruthy()
  })

  it('shows "Response interrupted" label text', () => {
    renderUI({ completeness: 'partial' })
    expect(screen.getByText(/Response interrupted/i)).toBeTruthy()
  })

  it('renders both action buttons', () => {
    renderUI({ completeness: 'partial' })
    expect(screen.getByTestId('show-partial-button')).toBeTruthy()
    expect(screen.getByTestId('retry-full-button')).toBeTruthy()
  })

  it('calls onRetryFull when Retry button is clicked', () => {
    const onRetryFull = vi.fn()
    renderUI({ completeness: 'partial', onRetryFull })
    fireEvent.click(screen.getByTestId('retry-full-button'))
    expect(onRetryFull).toHaveBeenCalledTimes(1)
  })

  it('calls onShowPartial when "Show what I have" button is clicked', () => {
    const onShowPartial = vi.fn()
    renderUI({ completeness: 'partial', onShowPartial })
    fireEvent.click(screen.getByTestId('show-partial-button'))
    expect(onShowPartial).toHaveBeenCalledTimes(1)
  })

  it('does NOT call onRetryFull when Show button is clicked', () => {
    const onRetryFull = vi.fn()
    renderUI({ completeness: 'partial', onRetryFull })
    fireEvent.click(screen.getByTestId('show-partial-button'))
    expect(onRetryFull).not.toHaveBeenCalled()
  })

  it('does NOT call onShowPartial when Retry button is clicked', () => {
    const onShowPartial = vi.fn()
    renderUI({ completeness: 'partial', onShowPartial })
    fireEvent.click(screen.getByTestId('retry-full-button'))
    expect(onShowPartial).not.toHaveBeenCalled()
  })

  it('includes optional interruptionReason in the label text', () => {
    renderUI({ completeness: 'partial', interruptionReason: 'timeout' })
    expect(screen.getByText(/timed out/i)).toBeTruthy()
  })
})

describe('MessageRecoveryUI — degraded state (partial content already visible)', () => {
  it('renders the incomplete-results indicator', () => {
    renderUI({ completeness: 'degraded' })
    expect(screen.getByTestId('incomplete-results-indicator')).toBeTruthy()
  })

  it('shows "incomplete results" text', () => {
    renderUI({ completeness: 'degraded' })
    expect(screen.getByText(/incomplete results/i)).toBeTruthy()
  })

  it('does NOT render action buttons when degraded', () => {
    renderUI({ completeness: 'degraded' })
    expect(screen.queryByTestId('show-partial-button')).toBeNull()
    expect(screen.queryByTestId('retry-full-button')).toBeNull()
  })

  it('does NOT render the recovery container (wrong testid) when degraded', () => {
    renderUI({ completeness: 'degraded' })
    expect(screen.queryByTestId('message-recovery-ui')).toBeNull()
  })
})
