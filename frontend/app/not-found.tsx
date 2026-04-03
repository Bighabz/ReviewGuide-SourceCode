import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <h1 className="font-serif text-5xl font-normal text-[var(--text)] mb-4">404</h1>
      <p className="text-[var(--text-secondary)] text-lg mb-8">
        That page doesn&apos;t exist.
      </p>
      <Link
        href="/"
        className="px-6 py-3 rounded-full bg-[var(--primary)] text-white text-sm font-medium hover:bg-[var(--primary-hover)] transition-colors"
      >
        Back to home
      </Link>
    </div>
  )
}
