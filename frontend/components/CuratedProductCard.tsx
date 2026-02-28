'use client'

import React from 'react'
import { ExternalLink } from 'lucide-react'

export interface CuratedProduct {
  asin: string
  url: string
  label?: string
}

export interface CuratedTopicCardProps {
  title: string
  description: string
  products: CuratedProduct[]
  onTitleClick?: (title: string) => void
}

export default function CuratedProductCard({
  title,
  description,
  products,
  onTitleClick,
}: CuratedTopicCardProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] shadow-card overflow-hidden product-card-hover">
      {/* Header */}
      <div className="p-4 pb-3">
        <button
          onClick={() => onTitleClick?.(title)}
          className="text-left w-full"
        >
          <h3 className="font-serif text-base font-semibold text-[var(--text)] hover:text-[var(--primary)] transition-colors leading-snug">
            {title}
          </h3>
        </button>
        <p className="text-xs text-[var(--text-secondary)] mt-1.5 leading-relaxed line-clamp-2">
          {description}
        </p>
      </div>

      {/* Product links */}
      <div className="px-4 pb-4">
        <div className="flex flex-wrap gap-1.5">
          {products.map((product, idx) => (
            <a
              key={idx}
              href={product.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] transition-all"
            >
              {product.label || `Option ${idx + 1}`}
              <ExternalLink size={10} className="opacity-60" />
            </a>
          ))}
        </div>
      </div>

      {/* Amazon attribution */}
      <div className="px-4 py-2.5 border-t border-[var(--border)] bg-[var(--surface)]">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-[var(--text-muted)] tracking-wide uppercase">
            Available on Amazon
          </span>
          <span className="text-[10px] text-[var(--text-muted)]">
            {products.length} {products.length === 1 ? 'pick' : 'picks'}
          </span>
        </div>
      </div>
    </div>
  )
}
