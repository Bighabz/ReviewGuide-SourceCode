'use client'

import { Bookmark } from 'lucide-react'

export default function SavedPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <div
        className="w-20 h-20 rounded-2xl flex items-center justify-center mb-6"
        style={{ background: 'var(--primary-light)' }}
      >
        <Bookmark size={36} className="text-[var(--primary)]" />
      </div>
      <h1 className="font-serif text-2xl font-bold text-[var(--text)] mb-2">
        Saved Products
      </h1>
      <p className="text-sm text-[var(--text-secondary)] max-w-sm mb-6">
        Save products during your research to compare later. Your saved items will appear here.
      </p>
      <div className="w-full max-w-md space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-16 rounded-xl border border-dashed border-[var(--border)] animate-pulse"
            style={{ background: 'var(--surface)', opacity: 0.5 }}
          />
        ))}
      </div>
      <p className="text-xs text-[var(--text-muted)] mt-6">Coming soon</p>
    </div>
  )
}
