'use client'

import { useState } from 'react'
import { ShoppingCart } from 'lucide-react'
import { lookupCuratedProduct } from '@/lib/curatedProductLookup'
import type { ExtractedProduct } from '@/lib/extractResultsData'

interface ResultsProductCardProps {
  product: ExtractedProduct
  index: number
}

const POSITION_SCORES = [95, 88, 82, 76, 70]

function getCategoryBadge(index: number): { label: string; color: string; bg: string } {
  if (index === 0) {
    return { label: 'Top Pick', color: '#B8860B', bg: 'rgba(184,134,11,0.1)' }
  }
  if (index === 1) {
    return { label: 'Best Value', color: 'var(--primary)', bg: 'var(--primary-light, rgba(27,77,255,0.08))' }
  }
  if (index === 2) {
    return { label: 'Premium', color: '#7C3AED', bg: 'rgba(124,58,237,0.1)' }
  }
  return { label: `#${index + 1}`, color: 'var(--text-secondary)', bg: 'var(--surface-hover)' }
}

function ProductImage({ name, imageUrl }: { name: string; imageUrl: string | null }) {
  const [errored, setErrored] = useState(false)

  if (!imageUrl || errored) {
    return (
      <div
        data-testid="product-image-placeholder"
        className="w-16 h-16 flex items-center justify-center rounded-lg flex-shrink-0"
        style={{ backgroundColor: 'var(--surface-hover)' }}
      >
        <ShoppingCart size={20} style={{ color: 'var(--text-secondary)' }} />
      </div>
    )
  }

  return (
    <img
      src={imageUrl}
      alt={name}
      className="w-16 h-16 object-contain"
      onError={() => setErrored(true)}
    />
  )
}

export default function ResultsProductCard({ product, index }: ResultsProductCardProps) {
  const { imageUrl: curatedImage, affiliateUrl: curatedUrl } = lookupCuratedProduct(product.name)
  const imageUrl = curatedImage || product.image_url || null
  const affiliateUrl = curatedUrl || product.url || null

  const score = POSITION_SCORES[index] ?? 60
  const accentIndex = (index % 4) + 1
  const badge = getCategoryBadge(index)

  const ctaHref =
    affiliateUrl ||
    `https://www.amazon.com/s?k=${encodeURIComponent(product.name)}&tag=revguide-20`

  return (
    <div
      className="rounded-2xl border w-full overflow-hidden product-card-hover"
      style={{
        borderColor: 'var(--border)',
        backgroundColor: 'var(--surface-elevated)',
        padding: '12px',
      }}
    >
      {/* Top section: pastel background with rank badge and product image */}
      <div
        className="rounded-xl h-[100px] relative flex items-center justify-center mb-3"
        style={{ background: `var(--card-accent-${accentIndex})` }}
      >
        {/* Rank badge */}
        <div className="absolute top-2 left-2 w-6 h-6 rounded-full bg-black text-white text-xs font-bold flex items-center justify-center">
          #{index + 1}
        </div>

        {/* Product image */}
        <ProductImage name={product.name} imageUrl={imageUrl} />
      </div>

      {/* Middle section: category badge, name, description, score bar */}
      <div className="mb-3">
        {/* Category badge pill */}
        <span
          className="px-2 py-0.5 rounded-full text-[11px] font-medium inline-block mb-1"
          style={{ color: badge.color, backgroundColor: badge.bg }}
        >
          {badge.label}
        </span>

        {/* Product name */}
        <p
          className="font-semibold text-sm line-clamp-2"
          style={{ color: 'var(--text)' }}
        >
          {product.name}
        </p>

        {/* Description */}
        {product.description && (
          <p
            className="text-[11px] line-clamp-2 mt-0.5"
            style={{ color: 'var(--text-secondary)' }}
          >
            {product.description}
          </p>
        )}

        {/* Score bar */}
        <div className="mt-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Score</span>
            <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
              {score}
            </span>
          </div>
          <div
            className="h-1 rounded-full w-full"
            style={{ backgroundColor: 'var(--surface-hover)' }}
            role="progressbar"
            aria-valuenow={score}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="h-1 rounded-full"
              style={{ width: `${score}%`, backgroundColor: 'var(--primary)' }}
            />
          </div>
        </div>
      </div>

      {/* Bottom section: price + CTA */}
      <div className="flex items-center justify-between">
        {product.price != null ? (
          <span className="font-bold text-lg" style={{ color: 'var(--text)' }}>
            ${product.price}
          </span>
        ) : (
          <span />
        )}

        <a
          href={ctaHref}
          target="_blank"
          rel="noopener noreferrer"
          className="h-9 px-4 text-sm font-medium rounded-lg flex items-center text-white"
          style={{ backgroundColor: 'var(--primary)' }}
        >
          Buy on Amazon
        </a>
      </div>
    </div>
  )
}
