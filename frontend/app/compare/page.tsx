'use client'

import { ArrowLeftRight } from 'lucide-react'

export default function ComparePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <div
        className="w-20 h-20 rounded-2xl flex items-center justify-center mb-6"
        style={{ background: 'var(--primary-light)' }}
      >
        <ArrowLeftRight size={36} className="text-[var(--primary)]" />
      </div>
      <h1 className="font-serif text-2xl font-bold text-[var(--text)] mb-2">
        Compare Products
      </h1>
      <p className="text-sm text-[var(--text-secondary)] max-w-sm mb-6">
        Add products to your comparison board to see specs, prices, and ratings side by side.
      </p>
      <div className="w-full max-w-lg">
        <div className="grid grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-40 rounded-xl border border-dashed border-[var(--border)] flex items-center justify-center"
              style={{ background: 'var(--surface)', opacity: 0.5 }}
            >
              <span className="text-2xl text-[var(--text-muted)]">+</span>
            </div>
          ))}
        </div>
      </div>
      <p className="text-xs text-[var(--text-muted)] mt-6">Coming soon</p>
    </div>
  )
}
