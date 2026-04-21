import Link from 'next/link'
import { Home, MessageSquare } from 'lucide-react'

/**
 * Custom 404 page — replaces the unstyled Next.js default.
 * Added 2026-04-21 as part of the stabilization sprint (was a known P1 from audit).
 *
 * Inspired by v3's `cef2f33` but adapted to v2's editorial palette and tone.
 */
export default function NotFound() {
  return (
    <div className="min-h-full flex items-center justify-center px-4 py-16 sm:py-24">
      <div className="w-full max-w-xl text-center">
        <p className="text-xs uppercase tracking-widest text-[var(--text-muted)] mb-4">
          404
        </p>
        <h1
          className="font-serif text-3xl sm:text-4xl md:text-5xl leading-tight tracking-tight mb-4"
          style={{ color: 'var(--text)' }}
        >
          This page{' '}
          <span className="italic" style={{ color: 'var(--primary)' }}>
            wandered off.
          </span>
        </h1>
        <p className="text-sm sm:text-base text-[var(--text-secondary)] max-w-md mx-auto mb-8">
          The URL you requested doesn&apos;t exist anymore — or never did. Try
          starting a new research session or heading back to Discover.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
            style={{
              background: 'var(--primary)',
              color: 'var(--primary-foreground, #fff)',
            }}
          >
            <Home size={16} />
            Back to Discover
          </Link>
          <Link
            href="/chat?new=1"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors border border-[var(--border)] hover:bg-[var(--surface)]"
            style={{ color: 'var(--text)' }}
          >
            <MessageSquare size={16} />
            Ask ReviewGuide
          </Link>
        </div>

        <p className="text-xs text-[var(--text-muted)] mt-8">
          If you got here from a link on our site, please let us know at{' '}
          <a
            href="mailto:mike@reviewguide.ai"
            className="underline"
            style={{ color: 'var(--text-secondary)' }}
          >
            mike@reviewguide.ai
          </a>
          .
        </p>
      </div>
    </div>
  )
}
