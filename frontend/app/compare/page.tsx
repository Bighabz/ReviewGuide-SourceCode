import Link from 'next/link'
import { BarChart3 } from 'lucide-react'

export default function ComparePage() {
  return (
    <div
      className="flex flex-col items-center justify-center min-h-[60vh] gap-6 px-4 text-center"
    >
      <BarChart3
        size={48}
        strokeWidth={1.5}
        style={{ color: 'var(--text-muted)' }}
      />

      <div className="flex flex-col items-center gap-3">
        <h1
          className="font-serif italic text-2xl"
          style={{ color: 'var(--text)' }}
        >
          Compare Products
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          This feature is coming soon. We&apos;re building something great.
        </p>
      </div>

      <Link
        href="/"
        className="rounded-lg px-6 py-2.5 text-sm font-medium text-white"
        style={{ backgroundColor: 'var(--primary)' }}
      >
        Back to Discover
      </Link>
    </div>
  )
}
