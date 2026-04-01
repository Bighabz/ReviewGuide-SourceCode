'use client'

import { useState } from 'react'
import { Award, ExternalLink, Star, ChevronDown, ChevronUp } from 'lucide-react'
import { stripMarkdown } from '@/lib/stripMarkdown'

interface TopPickBlockProps {
  productName: string
  headline: string
  bestFor: string
  notFor: string
  imageUrl?: string
  affiliateUrl?: string
  price?: number
  currency?: string
  merchant?: string
  rating?: number
  pros?: string[]
  cons?: string[]
}

export default function TopPickBlock({
  productName,
  headline,
  bestFor,
  notFor,
  imageUrl,
  affiliateUrl,
  price,
  currency = 'USD',
  merchant: merchantProp,
  rating,
  pros = [],
  cons = [],
}: TopPickBlockProps) {
  const [showDetails, setShowDetails] = useState(false)

  // Derive merchant from URL if not explicitly provided
  const merchant = merchantProp || (() => {
    if (!affiliateUrl) return 'Amazon'
    const url = affiliateUrl.toLowerCase()
    if (url.includes('amazon.com') || url.includes('amzn.to')) return 'Amazon'
    if (url.includes('ebay.com')) return 'eBay'
    if (url.includes('walmart.com')) return 'Walmart'
    if (url.includes('bestbuy.com')) return 'Best Buy'
    if (url.includes('target.com')) return 'Target'
    return 'retailer'
  })()

  if (!productName) return null

  return (
    <div className="rounded-xl border-2 border-[var(--primary)] bg-[var(--surface-elevated)] p-3 sm:p-5 mb-4 shadow-card product-card-hover">
      <div className="flex items-center gap-2 mb-3">
        <Award size={16} className="text-[var(--primary)]" />
        <span className="text-xs font-bold uppercase tracking-wider text-[var(--primary)]">
          Our Top Pick
        </span>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
        <div className="flex-shrink-0 w-full sm:w-[160px] h-[120px] sm:h-[160px] rounded-xl overflow-hidden bg-[var(--surface)]">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={productName}
              className="w-full h-full object-contain p-2"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Award size={40} className="text-[var(--text-muted)]" />
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="text-base sm:text-lg font-serif font-bold text-[var(--text)] mb-1">
            {affiliateUrl ? (
              <a
                href={affiliateUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-[var(--primary)] transition-colors"
              >
                {productName}
              </a>
            ) : (
              productName
            )}
          </h3>

          {rating != null && (
            <div className="flex items-center gap-1.5 mb-2">
              <div className="flex items-center">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star
                    key={s}
                    size={14}
                    fill={s <= Math.round(rating) ? 'currentColor' : 'none'}
                    className={s <= Math.round(rating) ? 'text-amber-500' : 'text-[var(--text-muted)]'}
                  />
                ))}
              </div>
              <span className="text-sm font-medium text-[var(--text)]">{rating.toFixed(1)}/5</span>
            </div>
          )}

          {headline && (
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-3">
              {stripMarkdown(headline)}
            </p>
          )}

          {affiliateUrl && (
            <a
              href={affiliateUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 sm:px-5 sm:py-2.5 rounded-lg text-xs sm:text-sm font-semibold text-white transition-all hover:brightness-110 active:scale-[0.97]"
              style={{
                background: 'linear-gradient(135deg, var(--primary), var(--accent))',
              }}
            >
              {price ? `Buy on ${merchant} — ${currency === 'USD' ? '$' : currency}${price.toFixed(2)}` : `Buy on ${merchant}`}
              <ExternalLink size={14} />
            </a>
          )}
        </div>
      </div>

      <div className="mt-3 space-y-1.5 text-sm">
        {bestFor && (
          <p className="text-[var(--text-secondary)]">
            <span className="font-semibold text-[var(--success)]">Best for:</span>{' '}
            {bestFor}
          </p>
        )}
        {notFor && (
          <p className="text-[var(--text-secondary)]">
            <span className="font-semibold text-[var(--accent)]">Look elsewhere if:</span>{' '}
            {notFor}
          </p>
        )}
      </div>

      {(pros.length > 0 || cons.length > 0) && (
        <div className="mt-3 pt-3 border-t border-[var(--border)]">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text)] transition-colors"
          >
            {showDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {showDetails ? 'Hide details' : 'Show pros & cons'}
          </button>
          {showDetails && (
            <div className="mt-2 space-y-2 text-sm">
              {pros.length > 0 && (
                <p className="text-[var(--text)]">
                  <span className="font-semibold text-[var(--success)]">Pros:</span>{' '}
                  {pros.join('. ')}.
                </p>
              )}
              {cons.length > 0 && (
                <p className="text-[var(--text)]">
                  <span className="font-semibold text-[var(--error)]">Cons:</span>{' '}
                  {cons.join('. ')}.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
