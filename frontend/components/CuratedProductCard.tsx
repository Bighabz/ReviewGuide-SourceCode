'use client'

import React, { useState } from 'react'
import { ExternalLink, ImageOff } from 'lucide-react'

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

function ProductThumbnail({ asin, url, label }: CuratedProduct) {
  const [imgError, setImgError] = useState(false)
  const imageUrl = `https://m.media-amazon.com/images/P/${asin}.01._SCLZZZZZZZ_SX220_.jpg`

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="group/thumb flex flex-col items-center gap-1.5 min-w-0"
      title={label || 'View on Amazon'}
    >
      <div className="relative w-[72px] h-[72px] sm:w-[80px] sm:h-[80px] rounded-lg border border-[var(--border)] bg-white overflow-hidden flex items-center justify-center group-hover/thumb:border-[var(--border-strong)] group-hover/thumb:shadow-sm transition-all">
        {!imgError ? (
          <img
            src={imageUrl}
            alt={label || 'Product'}
            className="w-full h-full object-contain p-1.5 group-hover/thumb:scale-110 transition-transform duration-300"
            loading="lazy"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-[var(--text-muted)]">
            <ImageOff size={18} strokeWidth={1.5} />
          </div>
        )}
        <div className="absolute inset-0 bg-black/0 group-hover/thumb:bg-black/5 transition-colors rounded-lg" />
        <div className="absolute bottom-1 right-1 opacity-0 group-hover/thumb:opacity-100 transition-opacity">
          <ExternalLink size={10} className="text-[var(--text-muted)]" />
        </div>
      </div>
      {label && (
        <span className="text-[10px] text-[var(--text-muted)] group-hover/thumb:text-[var(--text-secondary)] transition-colors text-center leading-tight max-w-[80px] line-clamp-2">
          {label}
        </span>
      )}
    </a>
  )
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

      {/* Product thumbnails */}
      <div className="px-4 pb-4">
        <div className="flex gap-2.5 overflow-x-auto pb-1 -mx-0.5 px-0.5 scrollbar-hide">
          {products.map((product, idx) => (
            <ProductThumbnail key={idx} {...product} />
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
