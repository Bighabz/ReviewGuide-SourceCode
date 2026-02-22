import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useStreamReducer, streamReducer } from '../hooks/useStreamReducer'
import type { StreamState, StreamAction } from '../hooks/useStreamReducer'

// ─── Pure reducer tests (all 7 state transitions) ────────────────────────────

describe('streamReducer — state transitions', () => {
  // 1. idle → SEND_MESSAGE → placeholder
  it('transitions idle → placeholder on SEND_MESSAGE', () => {
    const next = streamReducer('idle', { type: 'SEND_MESSAGE' })
    expect(next).toBe('placeholder')
  })

  // 2. placeholder → RECEIVE_STATUS → receiving_status
  it('transitions placeholder → receiving_status on RECEIVE_STATUS', () => {
    const next = streamReducer('placeholder', { type: 'RECEIVE_STATUS', text: 'Searching...' })
    expect(next).toBe('receiving_status')
  })

  // 3. receiving_status → RECEIVE_CONTENT → receiving_content
  it('transitions receiving_status → receiving_content on RECEIVE_CONTENT', () => {
    const next = streamReducer('receiving_status', { type: 'RECEIVE_CONTENT', token: 'Hello' })
    expect(next).toBe('receiving_content')
  })

  // 4. receiving_content → RECEIVE_STATUS → receiving_content (no-op)
  it('keeps receiving_content on RECEIVE_STATUS (no-op — status suppressed)', () => {
    const next = streamReducer('receiving_content', { type: 'RECEIVE_STATUS', text: 'Still working...' })
    expect(next).toBe('receiving_content')
  })

  // 5. receiving_content → RECEIVE_DONE → finalized
  it('transitions receiving_content → finalized on RECEIVE_DONE', () => {
    const next = streamReducer('receiving_content', { type: 'RECEIVE_DONE', data: {} })
    expect(next).toBe('finalized')
  })

  // 6. any → RECEIVE_ERROR → errored (tested from receiving_content)
  it('transitions receiving_content → errored on RECEIVE_ERROR', () => {
    const next = streamReducer('receiving_content', {
      type: 'RECEIVE_ERROR',
      error: { message: 'network failure' },
    })
    expect(next).toBe('errored')
  })

  // 7. any → STREAM_INTERRUPTED → interrupted (tested from receiving_content)
  it('transitions receiving_content → interrupted on STREAM_INTERRUPTED', () => {
    const next = streamReducer('receiving_content', { type: 'STREAM_INTERRUPTED' })
    expect(next).toBe('interrupted')
  })

  // RESET returns to idle from any state
  it('transitions finalized → idle on RESET', () => {
    const next = streamReducer('finalized', { type: 'RESET' })
    expect(next).toBe('idle')
  })

  it('transitions errored → idle on RESET', () => {
    const next = streamReducer('errored', { type: 'RESET' })
    expect(next).toBe('idle')
  })

  it('transitions interrupted → idle on RESET', () => {
    const next = streamReducer('interrupted', { type: 'RESET' })
    expect(next).toBe('idle')
  })

  // RECEIVE_DONE transitions from any streaming state
  it('transitions placeholder → finalized on RECEIVE_DONE', () => {
    const next = streamReducer('placeholder', { type: 'RECEIVE_DONE', data: {} })
    expect(next).toBe('finalized')
  })

  // RECEIVE_ERROR from any state
  it('transitions idle → errored on RECEIVE_ERROR', () => {
    const next = streamReducer('idle', { type: 'RECEIVE_ERROR', error: { message: 'err' } })
    expect(next).toBe('errored')
  })

  it('transitions placeholder → errored on RECEIVE_ERROR', () => {
    const next = streamReducer('placeholder', { type: 'RECEIVE_ERROR', error: { message: 'err' } })
    expect(next).toBe('errored')
  })

  // SEND_MESSAGE is a no-op when not idle
  it('keeps receiving_content on SEND_MESSAGE (no double-fire)', () => {
    const next = streamReducer('receiving_content', { type: 'SEND_MESSAGE' })
    expect(next).toBe('receiving_content')
  })

  // RECEIVE_ARTIFACT is always a no-op
  it('keeps current state on RECEIVE_ARTIFACT', () => {
    const states: StreamState[] = [
      'idle', 'placeholder', 'receiving_status', 'receiving_content', 'finalized',
    ]
    for (const state of states) {
      const next = streamReducer(state, { type: 'RECEIVE_ARTIFACT', blocks: [] })
      expect(next).toBe(state)
    }
  })

  // placeholder → RECEIVE_CONTENT → receiving_content (direct skip)
  it('transitions placeholder → receiving_content on RECEIVE_CONTENT (skip receiving_status)', () => {
    const next = streamReducer('placeholder', { type: 'RECEIVE_CONTENT', token: 'Hi' })
    expect(next).toBe('receiving_content')
  })
})

// ─── Hook tests (timeout / cleanup) ──────────────────────────────────────────

describe('useStreamReducer hook', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('starts in idle state', () => {
    const { result } = renderHook(() => useStreamReducer())
    expect(result.current.streamState).toBe('idle')
  })

  it('isStreaming is false in idle', () => {
    const { result } = renderHook(() => useStreamReducer())
    expect(result.current.isStreaming).toBe(false)
  })

  it('transitions to placeholder on SEND_MESSAGE', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
    })

    expect(result.current.streamState).toBe('placeholder')
  })

  it('isStreaming is true in placeholder', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
    })

    expect(result.current.isStreaming).toBe(true)
  })

  it('isStreaming is true in receiving_status', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
      result.current.dispatch({ type: 'RECEIVE_STATUS', text: 'Working...' })
    })

    expect(result.current.isStreaming).toBe(true)
  })

  it('isStreaming is true in receiving_content', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
      result.current.dispatch({ type: 'RECEIVE_STATUS', text: 'Working...' })
      result.current.dispatch({ type: 'RECEIVE_CONTENT', token: 'Hello' })
    })

    expect(result.current.isStreaming).toBe(true)
  })

  it('isStreaming is false in finalized', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
      result.current.dispatch({ type: 'RECEIVE_CONTENT', token: 'Hi' })
      result.current.dispatch({ type: 'RECEIVE_DONE', data: {} })
    })

    expect(result.current.isStreaming).toBe(false)
    expect(result.current.streamState).toBe('finalized')
  })

  it('isStreaming is false in errored', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
      result.current.dispatch({ type: 'RECEIVE_ERROR', error: { message: 'fail' } })
    })

    expect(result.current.isStreaming).toBe(false)
    expect(result.current.streamState).toBe('errored')
  })

  it('isStreaming is false in interrupted', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
      result.current.dispatch({ type: 'STREAM_INTERRUPTED' })
    })

    expect(result.current.isStreaming).toBe(false)
    expect(result.current.streamState).toBe('interrupted')
  })

  // Timeout test — 120 s watchdog dispatches STREAM_INTERRUPTED
  it('auto-dispatches STREAM_INTERRUPTED after 120 s without terminal event', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
    })

    expect(result.current.streamState).toBe('placeholder')

    // Fast-forward 120 seconds
    act(() => {
      vi.advanceTimersByTime(120_000)
    })

    expect(result.current.streamState).toBe('interrupted')
    expect(result.current.isStreaming).toBe(false)
  })

  it('does NOT fire STREAM_INTERRUPTED if RECEIVE_DONE arrives before 120 s', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
      result.current.dispatch({ type: 'RECEIVE_CONTENT', token: 'Hi' })
      result.current.dispatch({ type: 'RECEIVE_DONE', data: {} })
    })

    // Advance past 120 s — timeout should have been cleared
    act(() => {
      vi.advanceTimersByTime(150_000)
    })

    // Should remain finalized, NOT switch to interrupted
    expect(result.current.streamState).toBe('finalized')
  })

  it('does NOT fire STREAM_INTERRUPTED if RECEIVE_ERROR arrives before 120 s', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
      result.current.dispatch({ type: 'RECEIVE_ERROR', error: { message: 'oops' } })
    })

    act(() => {
      vi.advanceTimersByTime(150_000)
    })

    expect(result.current.streamState).toBe('errored')
  })

  it('resets to idle on RESET', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
      result.current.dispatch({ type: 'RECEIVE_CONTENT', token: 'test' })
      result.current.dispatch({ type: 'RESET' })
    })

    expect(result.current.streamState).toBe('idle')
    expect(result.current.isStreaming).toBe(false)
  })

  it('clears existing timeout when RESET is dispatched', () => {
    const { result } = renderHook(() => useStreamReducer())

    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
    })

    // RESET should clear the 120 s watchdog
    act(() => {
      result.current.dispatch({ type: 'RESET' })
    })

    act(() => {
      vi.advanceTimersByTime(150_000)
    })

    // Should remain idle after RESET, not flip to interrupted
    expect(result.current.streamState).toBe('idle')
  })

  it('re-arms timeout on second SEND_MESSAGE (new request)', () => {
    const { result } = renderHook(() => useStreamReducer())

    // First message cycle
    act(() => {
      result.current.dispatch({ type: 'SEND_MESSAGE' })
      result.current.dispatch({ type: 'RECEIVE_DONE', data: {} })
    })

    expect(result.current.streamState).toBe('finalized')

    // RESET then second message
    act(() => {
      result.current.dispatch({ type: 'RESET' })
      result.current.dispatch({ type: 'SEND_MESSAGE' })
    })

    expect(result.current.streamState).toBe('placeholder')

    // 120 s should trigger on the second message
    act(() => {
      vi.advanceTimersByTime(120_000)
    })

    expect(result.current.streamState).toBe('interrupted')
  })
})
