'use client'

import { Share2, Bookmark, RefreshCw } from 'lucide-react'

interface ResultsHeaderProps {
  title: string
  summary: string
  sourceCount: number
  onToast: (message: string) => void
}

function enrichSummary(summary: string, sourceCount: number): React.ReactNode {
  // Try to bold a number followed by "source" in the summary
  const sourcePattern = /(\d+)\s+(source)/gi
  const match = sourcePattern.exec(summary)
  if (match) {
    const idx = match.index
    const before = summary.slice(0, idx)
    const num = match[1]
    const after = summary.slice(idx + match[0].length)
    return (
      <>
        {before}
        <strong>{num}</strong>
        {' source'}
        {after}
      </>
    )
  }
  // No natural source count — append it
  return (
    <>
      {summary}
      {summary ? ' — based on ' : 'Based on '}
      <strong>{sourceCount}</strong>
      {` source${sourceCount === 1 ? '' : 's'} analyzed.`}
    </>
  )
}

export default function ResultsHeader({
  title,
  summary,
  sourceCount,
  onToast,
}: ResultsHeaderProps) {
  async function handleShare() {
    try {
      await navigator.clipboard.writeText(window.location.href)
      onToast('Link copied!')
    } catch {
      onToast('Could not copy link')
    }
  }

  return (
    <div>
      {/* Title */}
      <h1
        className="font-serif italic text-2xl md:text-[28px] font-bold line-clamp-2"
        style={{ color: 'var(--text)' }}
      >
        {title}
      </h1>

      {/* Action buttons */}
      <div className="flex items-center gap-6 mt-3">
        <button
          type="button"
          onClick={handleShare}
          className="flex items-center gap-1.5 cursor-pointer transition-opacity text-xs font-medium"
          style={{ color: 'var(--text-secondary)' }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = '0.7' }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = '1' }}
        >
          <Share2 size={16} />
          <span>Copy Link</span>
        </button>

        <button
          type="button"
          onClick={() => onToast('Coming soon')}
          className="flex items-center gap-1.5 cursor-pointer transition-opacity text-xs font-medium"
          style={{ color: 'var(--text-secondary)' }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = '0.7' }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = '1' }}
        >
          <Bookmark size={16} />
          <span>Save</span>
        </button>

        <button
          type="button"
          onClick={() => window.location.reload()}
          className="flex items-center gap-1.5 cursor-pointer transition-opacity text-xs font-medium"
          style={{ color: 'var(--text-secondary)' }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = '0.7' }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = '1' }}
        >
          <RefreshCw size={16} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Summary paragraph */}
      {summary && (
        <p
          className="mt-4 text-sm leading-relaxed"
          style={{ color: 'var(--text-secondary)' }}
        >
          {enrichSummary(summary, sourceCount)}
        </p>
      )}
    </div>
  )
}
