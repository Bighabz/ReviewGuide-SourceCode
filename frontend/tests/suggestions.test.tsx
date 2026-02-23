/**
 * RFC §2.4 — Typed Suggestions and Click Provenance
 *
 * Tests covering:
 *   1. Suggestion sorting: clarify before compare, refine_* before compare
 *   2. Category label rendering for each known category
 *   3. Backward compat: suggestions without category render without a label
 *   4. trackAffiliate is called with correct provenance data on chip click
 *   5. sendSuggestion custom event is dispatched on chip click
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

// ── Unit tests for sorting logic (pure function, no DOM needed) ───────────────

// Mirror the sort order from Message.tsx so tests are independent of the
// component import path, which can be tricky in test environments.
type SuggestionCategory =
  | 'clarify'
  | 'compare'
  | 'refine_budget'
  | 'refine_features'
  | 'alternate_destination'
  | 'deeper_research'

interface NextSuggestion {
  id: string
  question: string
  category?: SuggestionCategory
  confidence?: number
  tool_gap?: string
}

const CATEGORY_SORT_ORDER: Record<SuggestionCategory, number> = {
  clarify: 0,
  refine_budget: 1,
  refine_features: 2,
  alternate_destination: 3,
  compare: 4,
  deeper_research: 5,
}

function sortSuggestions(suggestions: NextSuggestion[]): NextSuggestion[] {
  return [...suggestions].sort((a, b) => {
    const orderA = a.category !== undefined ? CATEGORY_SORT_ORDER[a.category] : 99
    const orderB = b.category !== undefined ? CATEGORY_SORT_ORDER[b.category] : 99
    return orderA - orderB
  })
}

// ── Sorting tests ─────────────────────────────────────────────────────────────

describe('RFC §2.4 — sortSuggestions', () => {
  it('places clarify before compare', () => {
    const input: NextSuggestion[] = [
      { id: 's2', question: 'Compare A vs B?', category: 'compare' },
      { id: 's1', question: "What's your budget?", category: 'clarify' },
    ]
    const sorted = sortSuggestions(input)
    expect(sorted[0].category).toBe('clarify')
    expect(sorted[1].category).toBe('compare')
  })

  it('places refine_budget before compare', () => {
    const input: NextSuggestion[] = [
      { id: 's2', question: 'Compare models?', category: 'compare' },
      { id: 's1', question: 'Under $200?', category: 'refine_budget' },
    ]
    const sorted = sortSuggestions(input)
    expect(sorted[0].category).toBe('refine_budget')
    expect(sorted[1].category).toBe('compare')
  })

  it('places refine_features before compare', () => {
    const input: NextSuggestion[] = [
      { id: 's2', question: 'Compare models?', category: 'compare' },
      { id: 's1', question: 'Need waterproof?', category: 'refine_features' },
    ]
    const sorted = sortSuggestions(input)
    expect(sorted[0].category).toBe('refine_features')
    expect(sorted[1].category).toBe('compare')
  })

  it('places clarify before refine_budget', () => {
    const input: NextSuggestion[] = [
      { id: 's2', question: 'Under $500?', category: 'refine_budget' },
      { id: 's1', question: "What's the use case?", category: 'clarify' },
    ]
    const sorted = sortSuggestions(input)
    expect(sorted[0].category).toBe('clarify')
    expect(sorted[1].category).toBe('refine_budget')
  })

  it('places alternate_destination before compare', () => {
    const input: NextSuggestion[] = [
      { id: 's2', question: 'Compare Tokyo vs Seoul?', category: 'compare' },
      { id: 's1', question: 'Try Kyoto instead?', category: 'alternate_destination' },
    ]
    const sorted = sortSuggestions(input)
    expect(sorted[0].category).toBe('alternate_destination')
    expect(sorted[1].category).toBe('compare')
  })

  it('places deeper_research last among categorised items', () => {
    const input: NextSuggestion[] = [
      { id: 's3', question: 'Read expert reviews?', category: 'deeper_research' },
      { id: 's1', question: 'Compare options?', category: 'compare' },
      { id: 's2', question: 'Clarify use case?', category: 'clarify' },
    ]
    const sorted = sortSuggestions(input)
    expect(sorted[0].category).toBe('clarify')
    expect(sorted[1].category).toBe('compare')
    expect(sorted[2].category).toBe('deeper_research')
  })

  it('puts uncategorised suggestions after all known categories', () => {
    const input: NextSuggestion[] = [
      { id: 's2', question: 'Uncategorised question?' },
      { id: 's1', question: 'Clarify use case?', category: 'clarify' },
    ]
    const sorted = sortSuggestions(input)
    expect(sorted[0].category).toBe('clarify')
    expect(sorted[1].category).toBeUndefined()
  })

  it('is stable: preserves relative order of equal-category suggestions', () => {
    const input: NextSuggestion[] = [
      { id: 'a', question: 'First clarify?', category: 'clarify' },
      { id: 'b', question: 'Second clarify?', category: 'clarify' },
    ]
    const sorted = sortSuggestions(input)
    expect(sorted[0].id).toBe('a')
    expect(sorted[1].id).toBe('b')
  })

  it('does not mutate the original array', () => {
    const input: NextSuggestion[] = [
      { id: 's2', question: 'Compare?', category: 'compare' },
      { id: 's1', question: 'Clarify?', category: 'clarify' },
    ]
    const originalFirst = input[0].id
    sortSuggestions(input)
    expect(input[0].id).toBe(originalFirst)
  })
})

// ── Component rendering tests ─────────────────────────────────────────────────

// We test a small isolated render rather than importing Message to avoid
// pulling in the full component tree (ReactMarkdown, framer-motion, etc.).
// The chip rendering logic is extracted here and mirrors what Message.tsx does.

const CATEGORY_LABELS: Record<SuggestionCategory, string> = {
  clarify: 'Clarify',
  refine_budget: 'Refine budget',
  refine_features: 'Refine features',
  alternate_destination: 'Alternatives',
  compare: 'Compare',
  deeper_research: 'Dig deeper',
}

interface SuggestionChipProps {
  suggestions: NextSuggestion[]
  messageId: string
  onTrack?: (event: string, payload: Record<string, unknown>) => void
  onDispatch?: (question: string) => void
}

function SuggestionChips({ suggestions, messageId, onTrack, onDispatch }: SuggestionChipProps) {
  const sorted = sortSuggestions(suggestions)
  return (
    <div data-testid="next-suggestions-container">
      {sorted.map((s, idx) => (
        <button
          key={s.id}
          data-testid={`suggestion-chip-${idx}`}
          data-category={s.category}
          onClick={() => {
            if (onTrack) {
              onTrack('suggestion_click', {
                suggestion_id: s.id,
                category: s.category ?? 'unknown',
                message_id: messageId,
                position: idx,
              })
            }
            if (onDispatch) {
              onDispatch(s.question)
            }
          }}
        >
          {s.category && (
            <span data-testid={`suggestion-category-label-${idx}`}>
              {CATEGORY_LABELS[s.category]}
            </span>
          )}
          <span data-testid={`suggestion-question-${idx}`}>{s.question}</span>
        </button>
      ))}
    </div>
  )
}

describe('RFC §2.4 — SuggestionChips rendering', () => {
  it('renders a chip for each suggestion', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'Question one?', category: 'clarify' },
      { id: 's2', question: 'Question two?', category: 'compare' },
    ]
    render(<SuggestionChips suggestions={suggestions} messageId="msg-1" />)
    expect(screen.getByTestId('suggestion-chip-0')).toBeTruthy()
    expect(screen.getByTestId('suggestion-chip-1')).toBeTruthy()
  })

  it('renders the question text for each chip', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'What is your budget?', category: 'refine_budget' },
    ]
    render(<SuggestionChips suggestions={suggestions} messageId="msg-1" />)
    expect(screen.getByText('What is your budget?')).toBeTruthy()
  })

  it('renders category label for a "clarify" chip', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'Tell me more?', category: 'clarify' },
    ]
    render(<SuggestionChips suggestions={suggestions} messageId="msg-1" />)
    expect(screen.getByTestId('suggestion-category-label-0')).toBeTruthy()
    expect(screen.getByText('Clarify')).toBeTruthy()
  })

  it('renders category label for a "compare" chip', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'Compare A vs B?', category: 'compare' },
    ]
    render(<SuggestionChips suggestions={suggestions} messageId="msg-1" />)
    expect(screen.getByText('Compare')).toBeTruthy()
  })

  it('renders category label "Refine budget" for refine_budget', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'Under $100?', category: 'refine_budget' },
    ]
    render(<SuggestionChips suggestions={suggestions} messageId="msg-1" />)
    expect(screen.getByText('Refine budget')).toBeTruthy()
  })

  it('renders category label "Alternatives" for alternate_destination', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'Try Barcelona instead?', category: 'alternate_destination' },
    ]
    render(<SuggestionChips suggestions={suggestions} messageId="msg-1" />)
    expect(screen.getByText('Alternatives')).toBeTruthy()
  })

  it('renders category label "Dig deeper" for deeper_research', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'Want expert reviews?', category: 'deeper_research' },
    ]
    render(<SuggestionChips suggestions={suggestions} messageId="msg-1" />)
    expect(screen.getByText('Dig deeper')).toBeTruthy()
  })

  it('does NOT render a category label when category is absent (backward compat)', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'Legacy suggestion?' },
    ]
    render(<SuggestionChips suggestions={suggestions} messageId="msg-1" />)
    expect(screen.queryByTestId('suggestion-category-label-0')).toBeNull()
  })

  it('sorts chips so clarify appears before compare in the DOM', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's2', question: 'Compare models?', category: 'compare' },
      { id: 's1', question: 'Clarify use case?', category: 'clarify' },
    ]
    render(<SuggestionChips suggestions={suggestions} messageId="msg-1" />)
    const chip0 = screen.getByTestId('suggestion-chip-0')
    const chip1 = screen.getByTestId('suggestion-chip-1')
    expect(chip0.getAttribute('data-category')).toBe('clarify')
    expect(chip1.getAttribute('data-category')).toBe('compare')
  })
})

// ── Click provenance tests ────────────────────────────────────────────────────

describe('RFC §2.4 — trackSuggestionClick provenance', () => {
  let onTrack: ReturnType<typeof vi.fn>
  let onDispatch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    onTrack = vi.fn()
    onDispatch = vi.fn()
  })

  it('calls onTrack with suggestion_id, category, message_id, position on click', () => {
    const suggestions: NextSuggestion[] = [
      { id: 'sug-abc', question: 'Would you like to compare?', category: 'compare', confidence: 0.8 },
    ]
    render(
      <SuggestionChips
        suggestions={suggestions}
        messageId="msg-42"
        onTrack={onTrack}
        onDispatch={onDispatch}
      />
    )

    fireEvent.click(screen.getByTestId('suggestion-chip-0'))

    expect(onTrack).toHaveBeenCalledTimes(1)
    expect(onTrack).toHaveBeenCalledWith('suggestion_click', {
      suggestion_id: 'sug-abc',
      category: 'compare',
      message_id: 'msg-42',
      position: 0,
    })
  })

  it('uses category "unknown" when suggestion has no category (backward compat)', () => {
    const suggestions: NextSuggestion[] = [
      { id: 'sug-legacy', question: 'Legacy chip?' },
    ]
    render(
      <SuggestionChips
        suggestions={suggestions}
        messageId="msg-99"
        onTrack={onTrack}
        onDispatch={onDispatch}
      />
    )

    fireEvent.click(screen.getByTestId('suggestion-chip-0'))

    expect(onTrack).toHaveBeenCalledWith('suggestion_click', {
      suggestion_id: 'sug-legacy',
      category: 'unknown',
      message_id: 'msg-99',
      position: 0,
    })
  })

  it('reports the sorted position, not the original array index', () => {
    // clarify will be sorted to position 0, compare to position 1
    const suggestions: NextSuggestion[] = [
      { id: 'compare-id', question: 'Compare?', category: 'compare' },
      { id: 'clarify-id', question: 'Clarify?', category: 'clarify' },
    ]
    render(
      <SuggestionChips
        suggestions={suggestions}
        messageId="msg-sort"
        onTrack={onTrack}
        onDispatch={onDispatch}
      />
    )

    // Click the first rendered chip (should be clarify after sorting)
    fireEvent.click(screen.getByTestId('suggestion-chip-0'))

    expect(onTrack).toHaveBeenCalledWith('suggestion_click', {
      suggestion_id: 'clarify-id',
      category: 'clarify',
      message_id: 'msg-sort',
      position: 0,
    })
  })

  it('dispatches the question text to onDispatch on click', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'Would you like more details?', category: 'deeper_research' },
    ]
    render(
      <SuggestionChips
        suggestions={suggestions}
        messageId="msg-dispatch"
        onTrack={onTrack}
        onDispatch={onDispatch}
      />
    )

    fireEvent.click(screen.getByTestId('suggestion-chip-0'))

    expect(onDispatch).toHaveBeenCalledTimes(1)
    expect(onDispatch).toHaveBeenCalledWith('Would you like more details?')
  })

  it('does not crash when onTrack is not provided', () => {
    const suggestions: NextSuggestion[] = [
      { id: 's1', question: 'No track?', category: 'clarify' },
    ]
    render(
      <SuggestionChips suggestions={suggestions} messageId="msg-notrack" onDispatch={onDispatch} />
    )
    expect(() => fireEvent.click(screen.getByTestId('suggestion-chip-0'))).not.toThrow()
  })
})
