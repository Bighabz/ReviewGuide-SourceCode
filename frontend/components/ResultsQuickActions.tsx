'use client'

import { BarChart2, Download, Share2 } from 'lucide-react'

interface ResultsQuickActionsProps {
  onToast: (message: string) => void
  /** URL to copy when Share is clicked. Defaults to window.location.href. */
  shareUrl?: string
}

export default function ResultsQuickActions({ onToast, shareUrl }: ResultsQuickActionsProps) {
  async function handleShare() {
    const url = shareUrl ?? window.location.href
    try {
      await navigator.clipboard.writeText(url)
      onToast('Link copied!')
    } catch {
      onToast('Could not copy link')
    }
  }

  return (
    <div>
      <p
        className="text-[11px] font-medium uppercase tracking-[1.5px] mb-3"
        style={{ color: 'var(--text-muted)' }}
      >
        QUICK ACTIONS
      </p>

      <div className="flex flex-col">
        {/* Compare */}
        <button
          type="button"
          onClick={() => onToast('Coming soon')}
          className="h-11 flex items-center gap-3 w-full rounded-lg px-2 text-sm"
          onMouseEnter={(e) => {
            ;(e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--surface-hover)'
          }}
          onMouseLeave={(e) => {
            ;(e.currentTarget as HTMLButtonElement).style.backgroundColor = ''
          }}
        >
          <BarChart2 size={18} strokeWidth={1.5} style={{ color: 'var(--text-secondary)' }} />
          <span style={{ color: 'var(--text)' }}>Compare</span>
        </button>

        {/* Export */}
        <button
          type="button"
          onClick={() => onToast('Coming soon')}
          className="h-11 flex items-center gap-3 w-full rounded-lg px-2 text-sm"
          onMouseEnter={(e) => {
            ;(e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--surface-hover)'
          }}
          onMouseLeave={(e) => {
            ;(e.currentTarget as HTMLButtonElement).style.backgroundColor = ''
          }}
        >
          <Download size={18} strokeWidth={1.5} style={{ color: 'var(--text-secondary)' }} />
          <span style={{ color: 'var(--text)' }}>Export</span>
        </button>

        {/* Share */}
        <button
          type="button"
          onClick={handleShare}
          className="h-11 flex items-center gap-3 w-full rounded-lg px-2 text-sm"
          onMouseEnter={(e) => {
            ;(e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--surface-hover)'
          }}
          onMouseLeave={(e) => {
            ;(e.currentTarget as HTMLButtonElement).style.backgroundColor = ''
          }}
        >
          <Share2 size={18} strokeWidth={1.5} style={{ color: 'var(--text-secondary)' }} />
          <span style={{ color: 'var(--text)' }}>Share</span>
        </button>
      </div>
    </div>
  )
}
