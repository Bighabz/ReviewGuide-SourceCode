import { useReducer, useRef, useCallback, useEffect } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────

export type StreamState =
  | 'idle'
  | 'placeholder'          // Request sent, awaiting first event
  | 'receiving_status'     // status events arriving, no content yet
  | 'receiving_content'    // content events arriving
  | 'finalized'            // done event received
  | 'errored'              // error event received
  | 'interrupted'          // stream closed without terminal event

export interface UIBlock {
  [key: string]: any
}

export interface DoneChunk {
  session_id?: string
  user_id?: number
  ui_blocks?: UIBlock[]
  followups?: string[]
  itinerary?: any[]
  next_suggestions?: any[]
  status?: string
  intent?: string
  create_new_message?: boolean
  [key: string]: any
}

export interface ErrorChunk {
  message: string
}

export type StreamAction =
  | { type: 'SEND_MESSAGE' }
  | { type: 'RECEIVE_STATUS'; text: string }
  | { type: 'RECEIVE_CONTENT'; token: string }
  | { type: 'RECEIVE_ARTIFACT'; blocks: UIBlock[] }
  | { type: 'RECEIVE_DONE'; data: DoneChunk }
  | { type: 'RECEIVE_ERROR'; error: ErrorChunk }
  | { type: 'STREAM_INTERRUPTED' }
  | { type: 'RESET' }

// ─── Reducer ──────────────────────────────────────────────────────────────────

/**
 * State transition table:
 *
 * idle               + SEND_MESSAGE      → placeholder
 * placeholder        + RECEIVE_STATUS    → receiving_status
 * receiving_status   + RECEIVE_CONTENT   → receiving_content
 * receiving_content  + RECEIVE_STATUS    → receiving_content  (no-op — status suppressed)
 * receiving_content  + RECEIVE_DONE      → finalized
 * any                + RECEIVE_ERROR     → errored
 * any (120 s)        + STREAM_INTERRUPTED→ interrupted
 * any                + RESET             → idle
 */
export function streamReducer(state: StreamState, action: StreamAction): StreamState {
  switch (action.type) {
    case 'SEND_MESSAGE':
      return state === 'idle' ? 'placeholder' : state

    case 'RECEIVE_STATUS':
      if (state === 'placeholder') return 'receiving_status'
      if (state === 'receiving_content') return 'receiving_content' // no-op — status suppressed
      return state

    case 'RECEIVE_CONTENT':
      if (state === 'placeholder' || state === 'receiving_status') return 'receiving_content'
      if (state === 'receiving_content') return 'receiving_content'
      return state

    case 'RECEIVE_ARTIFACT':
      return state // artifact doesn't change FSM state

    case 'RECEIVE_DONE':
      // Only accept RECEIVE_DONE from active streaming states.
      // A late done event from a retried SSE connection must not overwrite
      // an already-errored or interrupted state.
      if (
        state === 'placeholder' ||
        state === 'receiving_status' ||
        state === 'receiving_content'
      ) {
        return 'finalized'
      }
      return state

    case 'RECEIVE_ERROR':
      return 'errored'

    case 'STREAM_INTERRUPTED':
      return 'interrupted'

    case 'RESET':
      return 'idle'

    default:
      return state
  }
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

const INTERRUPT_TIMEOUT_MS = 120_000

const TERMINAL_ACTIONS = new Set<StreamAction['type']>([
  'RECEIVE_DONE',
  'RECEIVE_ERROR',
  'STREAM_INTERRUPTED',
  'RESET',
])

/**
 * useStreamReducer — typed FSM for chat streaming state.
 *
 * Returns:
 *   streamState  — current FSM state
 *   dispatch     — action dispatcher (wraps useReducer dispatch with timeout logic)
 *   isStreaming   — true while in placeholder | receiving_status | receiving_content
 */
export function useStreamReducer() {
  const [streamState, rawDispatch] = useReducer(streamReducer, 'idle' as StreamState)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const dispatch = useCallback((action: StreamAction) => {
    // On SEND_MESSAGE: arm a 120 s watchdog that fires STREAM_INTERRUPTED
    if (action.type === 'SEND_MESSAGE') {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      timeoutRef.current = setTimeout(() => {
        rawDispatch({ type: 'STREAM_INTERRUPTED' })
      }, INTERRUPT_TIMEOUT_MS)
    }

    // On any terminal event: disarm the watchdog
    if (TERMINAL_ACTIONS.has(action.type)) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }

    rawDispatch(action)
  }, [])

  // Clean up watchdog on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [])

  const isStreaming =
    streamState === 'placeholder' ||
    streamState === 'receiving_status' ||
    streamState === 'receiving_content'

  return { streamState, dispatch, isStreaming }
}
