'use client'

import { Star, ExternalLink, TrendingUp } from 'lucide-react'
import { motion } from 'framer-motion'

interface ReviewSourceItem {
  site_name: string
  url: string
  title: string
  snippet: string
  rating?: number | null
  favicon_url?: string
  date?: string | null
}

interface ReviewProduct {
  name: string
  avg_rating: number
  total_reviews: number
  consensus: string
  editorial_label?: string | null
  sources: ReviewSourceItem[]
}

interface ReviewSourcesProps {
  data: {
    products: ReviewProduct[]
  }
  title?: string
}

function formatReviewCount(count: number): string {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1).replace(/\.0$/, '')}K`
  }
  return count.toLocaleString()
}

function StarRatingCompact({ value, size = 12 }: { value: number; size?: number }) {
  const fullStars = Math.floor(value)
  const hasHalf = value - fullStars >= 0.5
  const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0)

  return (
    <div className="flex items-center gap-px">
      {Array.from({ length: fullStars }).map((_, i) => (
        <Star key={`full-${i}`} size={size} fill="#E5A100" stroke="#E5A100" strokeWidth={0} />
      ))}
      {hasHalf && (
        <div className="relative" style={{ width: size, height: size }}>
          <Star size={size} fill="none" stroke="#D6D3CD" strokeWidth={1.5} />
          <div className="absolute inset-0 overflow-hidden" style={{ width: '50%' }}>
            <Star size={size} fill="#E5A100" stroke="#E5A100" strokeWidth={0} />
          </div>
        </div>
      )}
      {Array.from({ length: emptyStars }).map((_, i) => (
        <Star key={`empty-${i}`} size={size} fill="none" stroke="#D6D3CD" strokeWidth={1.5} />
      ))}
    </div>
  )
}

export default function ReviewSources({ data, title = 'What Reviewers Say' }: ReviewSourcesProps) {
  const products = data?.products || []

  if (products.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full mb-6"
    >
      {/* Section header */}
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={16} className="text-[var(--primary)]" strokeWidth={2} />
        <h3 className="font-serif text-lg font-semibold text-[var(--text)] tracking-tight">
          {title}
        </h3>
      </div>

      <div className="space-y-5">
        {products.map((product, productIdx) => (
          <div
            key={productIdx}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 sm:p-5 shadow-card"
          >
            {/* Product header: name + rating + review count */}
            <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mb-2">
              <h4 className="font-serif text-base font-semibold text-[var(--text)] tracking-tight">
                {product.name}
              </h4>
              {product.editorial_label && (
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase ${
                  product.editorial_label === 'Best Overall'
                    ? 'bg-[#E85D3A]/10 text-[#E85D3A] dark:bg-[#E85D3A]/20'
                    : 'bg-[#1B4DFF]/10 text-[#1B4DFF] dark:bg-[#1B4DFF]/20'
                }`}>
                  {product.editorial_label}
                </span>
              )}
              {product.avg_rating > 0 && (
                <div className="flex items-center gap-1.5">
                  <StarRatingCompact value={product.avg_rating} size={13} />
                  <span className="text-sm font-medium text-[var(--text)]">
                    {product.avg_rating}
                  </span>
                </div>
              )}
              {product.total_reviews > 0 && (
                <span className="text-xs text-[var(--text-muted)]">
                  {formatReviewCount(product.total_reviews)} reviews
                </span>
              )}
            </div>

            {/* Consensus summary */}
            {product.consensus && (
              <p className="text-sm sm:text-base text-[var(--text)] leading-relaxed mb-4">
                {product.consensus}
              </p>
            )}

            {/* Source tags */}
            {product.sources.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {product.sources.map((source, sourceIdx) => (
                  source.url ? (
                    <a
                      key={sourceIdx}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border border-[var(--border)] bg-[var(--background)] text-[11px] font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:border-[var(--primary)] transition-colors cursor-pointer"
                    >
                      {source.favicon_url && (
                        <img
                          src={source.favicon_url}
                          alt=""
                          className="w-3 h-3 rounded-sm flex-shrink-0"
                          loading="lazy"
                        />
                      )}
                      {source.site_name}
                      <ExternalLink size={9} className="flex-shrink-0 opacity-60" />
                    </a>
                  ) : (
                    <span
                      key={sourceIdx}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border border-[var(--border)] bg-[var(--background)] text-[11px] font-medium text-[var(--text-muted)]"
                    >
                      {source.favicon_url && (
                        <img
                          src={source.favicon_url}
                          alt=""
                          className="w-3 h-3 rounded-sm flex-shrink-0"
                          loading="lazy"
                        />
                      )}
                      {source.site_name}
                    </span>
                  )
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </motion.div>
  )
}
