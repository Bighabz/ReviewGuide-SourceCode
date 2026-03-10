import Link from 'next/link'

export const metadata = {
  title: 'Affiliate Disclosure — ReviewGuide.ai',
  description: 'Affiliate disclosure for ReviewGuide.ai',
}

export default function AffiliateDisclosurePage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
      <Link
        href="/browse"
        className="inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--text)] transition-colors mb-8"
      >
        &larr; Back to Browse
      </Link>

      <h1 className="font-serif text-3xl sm:text-4xl font-semibold text-[var(--text)] tracking-tight mb-10">
        Affiliate Disclosure
      </h1>

      <div className="space-y-6">
        <p className="text-[var(--text-secondary)] leading-relaxed">
          ReviewGuide.ai participates in various affiliate marketing programs.
          This means we may earn a commission when users purchase products through
          links on our website, at no additional cost to you.
        </p>

        <p className="text-[var(--text-secondary)] leading-relaxed font-medium text-[var(--text)]">
          As an Amazon Associate, we earn from qualifying purchases.
        </p>

        <p className="text-[var(--text-secondary)] leading-relaxed">
          Our product summaries and recommendations are generated independently
          to help users make informed decisions. Affiliate partnerships do not
          influence our analysis, opinions, or product evaluations.
        </p>

        <div className="border-t border-[var(--border)] pt-6 mt-8">
          <p className="text-sm text-[var(--text-muted)]">
            Questions?{' '}
            <a
              href="mailto:mike@reviewguide.ai"
              className="text-[var(--primary)] hover:underline"
            >
              mike@reviewguide.ai
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
