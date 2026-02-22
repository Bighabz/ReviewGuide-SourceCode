'use client'

export interface MessageRecoveryUIProps {
  onShowPartial: () => void
  onRetryFull: () => void
  completeness: 'partial' | 'degraded'
  interruptionReason?: string
}

/**
 * MessageRecoveryUI — RFC §2.3
 *
 * Inline recovery indicator rendered below an interrupted assistant message.
 *
 * When `completeness === 'partial'`:
 *   Shows "Response interrupted" with two action buttons:
 *     • "Show what I have" — dismisses the recovery UI; keeps partial content visible
 *     • "Retry" — re-sends the original query as a new user turn
 *
 * When `completeness === 'degraded'`:
 *   The partial content is already showing. Renders only a subtle
 *   "incomplete results" indicator with no action buttons.
 *
 * Design: editorial luxury — uses CSS vars only, no hardcoded hex colours.
 */
export default function MessageRecoveryUI({
  onShowPartial,
  onRetryFull,
  completeness,
  interruptionReason,
}: MessageRecoveryUIProps) {
  // Degraded state: content already visible, just show a quiet indicator
  if (completeness === 'degraded') {
    return (
      <div
        data-testid="incomplete-results-indicator"
        className="flex items-center gap-1.5 mt-3"
        style={{ color: 'var(--text-muted)' }}
      >
        {/* Warning triangle icon — inline SVG, no Math.random() */}
        <svg
          width="13"
          height="13"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          style={{ flexShrink: 0 }}
        >
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <span className="text-[11px] tracking-wide">
          incomplete results
        </span>
      </div>
    )
  }

  // Partial state: stream was interrupted mid-response, offer recovery actions
  const reasonLabel: Record<string, string> = {
    network: 'network error',
    server_error: 'server error',
    timeout: 'timed out',
    provider_failure: 'provider failure',
  }
  const reasonText = interruptionReason ? reasonLabel[interruptionReason] ?? interruptionReason : undefined

  return (
    <div
      data-testid="message-recovery-ui"
      className="flex flex-wrap items-center gap-2 mt-3 pt-3"
      style={{ borderTop: '1px solid var(--border)' }}
    >
      {/* Interrupted label */}
      <div
        className="flex items-center gap-1.5 text-[12px] mr-1"
        style={{ color: 'var(--text-muted)' }}
      >
        <svg
          width="13"
          height="13"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          style={{ flexShrink: 0, color: 'var(--accent)' }}
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <span>
          Response interrupted{reasonText ? ` — ${reasonText}` : ''}
        </span>
      </div>

      {/* Action: Show what I have */}
      <button
        data-testid="show-partial-button"
        onClick={onShowPartial}
        className="text-[12px] px-2.5 py-1 rounded-md transition-colors"
        style={{
          background: 'var(--surface-hover)',
          color: 'var(--text-secondary)',
          border: '1px solid var(--border)',
        }}
        onMouseEnter={(e) => {
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text)'
        }}
        onMouseLeave={(e) => {
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-secondary)'
        }}
      >
        Show what I have
      </button>

      {/* Action: Retry */}
      <button
        data-testid="retry-full-button"
        onClick={onRetryFull}
        className="text-[12px] px-2.5 py-1 rounded-md transition-colors"
        style={{
          background: 'var(--accent)',
          color: '#fff',
          border: '1px solid var(--accent)',
        }}
        onMouseEnter={(e) => {
          ;(e.currentTarget as HTMLButtonElement).style.opacity = '0.88'
        }}
        onMouseLeave={(e) => {
          ;(e.currentTarget as HTMLButtonElement).style.opacity = '1'
        }}
      >
        Retry
      </button>
    </div>
  )
}
