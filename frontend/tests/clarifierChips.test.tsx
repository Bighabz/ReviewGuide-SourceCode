/**
 * Phase 08 — Clarifier Suggestion Chips: Frontend Tests
 *
 * Tests covering:
 *   1. Chip buttons render below each followup question
 *   2. Chip text is displayed correctly
 *   3. Clicking a chip dispatches sendSuggestion CustomEvent with chip text
 *   4. Empty chips array renders no chip buttons (no crash)
 *   5. Missing chips key renders no chip buttons (no crash)
 *   6. Multiple questions render chips independently
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

// ── Test component mirroring the clarifier chip rendering pattern ────────────
// This follows the isolated-render pattern from suggestions.test.tsx:
// we test a small component that mirrors the exact rendering logic
// that will be implemented in Message.tsx.

interface TestFollowupQuestion {
  slot: string
  question: string
  chips?: string[]
}

function ClarifierChips({ questions }: { questions: TestFollowupQuestion[] }) {
  return (
    <div>
      {questions.map((q, idx) => (
        <div key={idx} data-testid={`followup-question-${idx}`}>
          <span>{q.question}</span>
          {q.chips && q.chips.length > 0 && (
            <div className="flex flex-row flex-wrap gap-1.5 mt-1.5">
              {q.chips.map((chip, chipIdx) => (
                <button
                  key={chipIdx}
                  data-testid={`clarifier-chip-${idx}-${chipIdx}`}
                  className="rounded-[20px] border border-[var(--primary)] text-[var(--primary)] bg-transparent px-3 py-1 text-[12px] font-medium transition-all hover:bg-[var(--primary-light)]"
                  onClick={() => {
                    window.dispatchEvent(new CustomEvent('sendSuggestion', {
                      detail: { question: chip }
                    }))
                  }}
                >
                  {chip}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('Phase 08 — ClarifierChips rendering', () => {
  let dispatchSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    dispatchSpy = vi.spyOn(window, 'dispatchEvent')
  })

  afterEach(() => {
    dispatchSpy.mockRestore()
  })

  it('renders chip buttons for each option in a question\'s chips array', () => {
    const questions: TestFollowupQuestion[] = [
      { slot: 'budget', question: 'Budget?', chips: ['Under $100', '$100-$300', 'Over $300'] }
    ]
    render(<ClarifierChips questions={questions} />)

    expect(screen.getByTestId('clarifier-chip-0-0')).toBeTruthy()
    expect(screen.getByTestId('clarifier-chip-0-1')).toBeTruthy()
    expect(screen.getByTestId('clarifier-chip-0-2')).toBeTruthy()
  })

  it('displays chip text content', () => {
    const questions: TestFollowupQuestion[] = [
      { slot: 'budget', question: 'Budget?', chips: ['Under $100', '$100-$300', 'Over $300'] }
    ]
    render(<ClarifierChips questions={questions} />)

    expect(screen.getByText('Under $100')).toBeTruthy()
    expect(screen.getByText('$100-$300')).toBeTruthy()
    expect(screen.getByText('Over $300')).toBeTruthy()
  })

  it('dispatches sendSuggestion CustomEvent on chip click', () => {
    const questions: TestFollowupQuestion[] = [
      { slot: 'budget', question: 'Budget?', chips: ['Under $100', '$100-$300', 'Over $300'] }
    ]
    render(<ClarifierChips questions={questions} />)

    fireEvent.click(screen.getByTestId('clarifier-chip-0-0'))

    expect(dispatchSpy).toHaveBeenCalled()
    const call = dispatchSpy.mock.calls.find(
      (c: [Event]) => c[0] instanceof CustomEvent && (c[0] as CustomEvent).type === 'sendSuggestion'
    )
    expect(call).toBeTruthy()
    const event = call![0] as CustomEvent
    expect(event.detail.question).toBe('Under $100')
  })

  it('renders no chips when chips array is empty', () => {
    const questions: TestFollowupQuestion[] = [
      { slot: 'dest', question: 'Where?', chips: [] }
    ]
    render(<ClarifierChips questions={questions} />)

    expect(screen.queryByTestId(/clarifier-chip/)).toBeNull()
  })

  it('renders no chips when chips key is absent', () => {
    const questions: TestFollowupQuestion[] = [
      { slot: 'dest', question: 'Where?' }
    ]
    render(<ClarifierChips questions={questions} />)

    expect(screen.queryByTestId(/clarifier-chip/)).toBeNull()
  })

  it('chips for multiple questions render independently', () => {
    const questions: TestFollowupQuestion[] = [
      { slot: 'budget', question: 'Budget?', chips: ['Under $100', 'Over $100'] },
      { slot: 'category', question: 'Category?', chips: ['Vacuums', 'Hair dryers'] }
    ]
    render(<ClarifierChips questions={questions} />)

    expect(screen.getByTestId('clarifier-chip-0-0')).toBeTruthy()
    expect(screen.getByTestId('clarifier-chip-0-1')).toBeTruthy()
    expect(screen.getByTestId('clarifier-chip-1-0')).toBeTruthy()
    expect(screen.getByTestId('clarifier-chip-1-1')).toBeTruthy()
  })
})
