import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="w-full border-t border-[var(--border)] bg-[var(--surface)]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[var(--text-muted)]">
          <div className="flex items-center gap-1">
            <span className="font-serif font-semibold text-[var(--text-secondary)]">ReviewGuide.ai</span>
            <span>&copy; {new Date().getFullYear()}</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/privacy" className="hover:text-[var(--text)] transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-[var(--text)] transition-colors">Terms</Link>
            <Link href="/affiliate-disclosure" className="hover:text-[var(--text)] transition-colors">Affiliate Disclosure</Link>
            <a href="mailto:mike@reviewguide.ai" className="hover:text-[var(--text)] transition-colors">Contact</a>
          </div>
        </div>
      </div>
    </footer>
  )
}
