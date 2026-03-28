'use client'

import { useState } from 'react'
import { resolveProductImage, isPlaceholderImage } from '@/lib/productImages'
import type { ExtractedProduct } from '@/lib/extractResultsData'

interface ResultsProductCardProps {
  product: ExtractedProduct
  index: number
}

const GRADIENT_BGS = [
  'linear-gradient(135deg, #EEF2FF, #E0E7FF)',
  'linear-gradient(135deg, #FEF3C7, #FDE68A)',
  'linear-gradient(135deg, #F3E8FF, #E9D5FF)',
  'linear-gradient(135deg, #DCFCE7, #BBF7D0)',
  'linear-gradient(135deg, #FFE4E6, #FECDD3)',
  'linear-gradient(135deg, #E0F2FE, #BAE6FD)',
]

const POSITION_SCORES = [94, 91, 88, 82, 78, 74]

function getBadge(index: number): { label: string; bg: string; color: string } {
  if (index === 0) return { label: 'TOP PICK', bg: '#FEF3C7', color: '#92400E' }
  if (index === 1) return { label: 'BEST VALUE', bg: '#DBEAFE', color: '#1E40AF' }
  if (index === 2) return { label: 'PREMIUM', bg: '#F3E8FF', color: '#6B21A8' }
  return { label: `#${index + 1}`, bg: 'var(--surface-elevated)', color: 'var(--text-secondary)' }
}

export default function ResultsProductCard({ product, index }: ResultsProductCardProps) {
  const [imgError, setImgError] = useState(false)
  const imageUrl = resolveProductImage(product.name, imgError ? null : product.image_url)
  const isPlaceholder = isPlaceholderImage(imageUrl)
  const badge = getBadge(index)
  const score = POSITION_SCORES[index] ?? 70
  const gradient = GRADIENT_BGS[index % GRADIENT_BGS.length]
  const linkUrl = product.url || `https://www.amazon.com/s?k=${encodeURIComponent(product.name)}&tag=revguide-20`

  return (
    <div
      className="rounded-2xl border overflow-hidden product-card-hover"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
    >
      {/* Image area with gradient background */}
      <div
        className="relative h-[140px] flex items-center justify-center"
        style={{ background: gradient }}
      >
        {/* Rank badge */}
        <div
          className="absolute top-3 left-3 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
          style={{ background: 'var(--text)', color: 'var(--background)' }}
        >
          {index + 1}
        </div>
        {isPlaceholder ? (
          <img src={imageUrl} alt="" className="w-12 h-12 opacity-40" />
        ) : (
          <img
            src={imageUrl}
            alt={product.name}
            className="max-h-[100px] max-w-[140px] object-contain drop-shadow-md"
            onError={() => setImgError(true)}
            loading="lazy"
          />
        )}
      </div>

      {/* Body */}
      <div className="p-4">
        {/* Badge */}
        <span
          className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide mb-2"
          style={{ background: badge.bg, color: badge.color }}
        >
          {badge.label}
        </span>

        <h3 className="text-[15px] font-semibold mb-1" style={{ color: 'var(--text)' }}>
          {product.name}
        </h3>

        {product.description && (
          <p className="text-xs mb-2.5 line-clamp-1" style={{ color: 'var(--text-muted)' }}>
            {product.description}
          </p>
        )}

        {/* Score bar */}
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1 rounded-full" style={{ background: 'var(--surface)' }}>
            <div
              className="h-full rounded-full"
              style={{ width: `${score}%`, background: 'var(--primary)' }}
            />
          </div>
          <span className="text-sm font-bold" style={{ color: 'var(--primary)' }}>
            {(score / 10).toFixed(1)}
          </span>
        </div>
      </div>

      {/* Footer */}
      <div
        className="flex items-center justify-between px-4 py-3 border-t"
        style={{ borderColor: 'var(--border)' }}
      >
        <span className="text-base font-bold" style={{ color: 'var(--text)' }}>
          {product.price ? `$${product.price}` : 'Check Price'}
        </span>
        <a
          href={linkUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white transition-all hover:brightness-110 active:scale-[0.97]"
          style={{ background: 'var(--primary)' }}
        >
          Check Price
        </a>
      </div>
    </div>
  )
}
