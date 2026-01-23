'use client'

import React, { useState } from 'react'
import { ProductItem } from '@/lib/browseData'
import { StarRating } from '../StarRating'
import Link from 'next/link'
import { ImageOff, ExternalLink } from 'lucide-react'

interface ProductCardCompactProps {
  item: ProductItem
  aiSummary?: string
  onClick?: (item: ProductItem) => void
}

export default function ProductCardCompact({ item, aiSummary, onClick }: ProductCardCompactProps) {
  const [imageError, setImageError] = useState(false)

  // Use AI summary if provided, otherwise fall back to description or generate from pros
  const displaySummary = aiSummary || item.description ||
    (item.topPros && item.topPros.length > 0
      ? `${item.topPros[0].title}. ${item.topPros[1]?.title || ''}`
      : '')

  return (
    <Link href={`/product/${item.id}`} className="block group">
      <div
        className="bg-[var(--card-bg)] border border-[var(--border)] rounded-lg overflow-hidden hover:shadow-[var(--shadow-md)] hover:border-[var(--accent)] transition-all duration-200 h-full flex flex-col cursor-pointer"
        onClick={(e) => {
          if (onClick) {
            e.preventDefault()
            onClick(item)
          }
        }}
      >
        {/* Square Image Container */}
        <div className="aspect-square relative bg-[var(--surface)] overflow-hidden">
          {imageError ? (
            <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-[var(--surface)] to-[var(--surface-hover)] text-[var(--text-muted)]">
              <div className="p-3 rounded-full bg-[var(--background)]/50 mb-1">
                <ImageOff size={20} className="opacity-50" />
              </div>
              <span className="text-[10px] font-medium opacity-70">No image</span>
            </div>
          ) : (
            <img
              src={item.image}
              alt={item.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
              onError={() => setImageError(true)}
            />
          )}
        </div>

        {/* Content */}
        <div className="p-3 flex-1 flex flex-col gap-1.5">
          {/* Title - 2 lines max */}
          <h3 className="text-sm font-medium text-[var(--text)] line-clamp-2 leading-snug group-hover:text-[var(--accent)] transition-colors">
            {item.title}
          </h3>

          {/* Rating + Price Row */}
          <div className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-1">
              <StarRating value={item.rating} size={12} />
              <span className="text-[11px] text-[var(--text-muted)]">
                ({item.reviewCount >= 1000 ? `${(item.reviewCount / 1000).toFixed(1)}k` : item.reviewCount})
              </span>
            </div>
            <span className="text-sm font-bold text-[var(--text)]">
              {item.currency}{item.price.toLocaleString()}
            </span>
          </div>

          {/* AI Summary */}
          {displaySummary && (
            <p className="text-[11px] text-[var(--text-secondary)] line-clamp-2 leading-relaxed">
              {displaySummary}
            </p>
          )}

          {/* View Deal Button */}
          <div className="mt-auto pt-2">
            <button
              className="w-full py-1.5 px-2 rounded-md bg-[var(--primary)] text-white text-xs font-medium hover:bg-[var(--primary-hover)] transition-colors flex items-center justify-center gap-1"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (item.affiliateLink) {
                  window.open(item.affiliateLink, '_blank')
                }
              }}
            >
              View Deal
              <ExternalLink size={12} />
            </button>
          </div>
        </div>
      </div>
    </Link>
  )
}
