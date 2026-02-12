'use client'

import { Check, X, ExternalLink } from 'lucide-react'

interface ProductCard {
  // Old format fields
  rank?: number
  title?: string
  price?: number
  currency?: string
  image_url?: string
  affiliate_link?: string
  merchant?: string
  specs?: string[]
  pros?: string[]
  cons?: string[]
  rating?: number
  review_count?: number

  // New format fields (from MCP)
  id?: string
  name?: string
  url?: string
  snippet?: string
  score?: number
  best_offer?: {
    merchant: string
    price: number
    currency: string
    url: string
  }
  badges?: string[]
}

interface ProductCardsProps {
  products: ProductCard[]
}

export default function ProductCards({ products }: ProductCardsProps) {
  if (!products || products.length === 0) {
    return null
  }

  return (
    <div className="space-y-4 w-full">
      {products.map((product, index) => {
        // Support both old and new formats
        const displayTitle = product.title || product.name || 'Product'
        const displayRank = product.rank !== undefined ? product.rank : index + 1
        const displayPrice = product.price || product.best_offer?.price
        const displayCurrency = product.currency || product.best_offer?.currency || 'USD'
        const displayMerchant = product.merchant || product.best_offer?.merchant
        const displayLink = product.affiliate_link || product.best_offer?.url || product.url || '#'
        const displayPros = product.pros || []
        const displayCons = product.cons || []

        return (
          <div
            key={product.id || product.rank || index}
            className="group relative bg-[var(--card-bg)] border border-[var(--border)] rounded-xl overflow-hidden hover:shadow-md transition-all duration-300"
          >
            <div className="p-4 sm:p-5">
              {/* Product Header */}
              <div className="flex justify-between items-start gap-4 mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-[var(--primary)] text-white text-xs font-bold shadow-sm">
                      {displayRank}
                    </span>
                    {displayMerchant && (
                      <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--text-secondary)] border border-[var(--border)] px-1.5 py-0.5 rounded bg-[var(--surface)]">
                        {displayMerchant}
                      </span>
                    )}
                  </div>
                  <h3 className="font-heading text-lg font-semibold text-[var(--text)] leading-snug group-hover:text-[var(--primary)] transition-colors">
                    <a href={displayLink} target="_blank" rel="noopener noreferrer" className="hover:underline decoration-2 decoration-[var(--primary)] underline-offset-2">
                      {displayTitle}
                    </a>
                  </h3>
                </div>
                {displayPrice !== undefined && (
                  <div className="text-right shrink-0">
                    <p className="text-lg font-bold text-[var(--text)] font-heading">
                      {displayCurrency} {displayPrice.toFixed(2)}
                    </p>
                  </div>
                )}
              </div>

              {/* Specs */}
              {product.specs && product.specs.length > 0 && (
                <ul className="mb-4 flex flex-wrap gap-2">
                  {product.specs.map((spec, idx) => (
                    <li key={idx} className="text-xs font-medium px-2 py-1 bg-[var(--surface)] border border-[var(--border)] rounded-md text-[var(--text-secondary)]">
                      {spec}
                    </li>
                  ))}
                </ul>
              )}

              {/* Pros & Cons Grid */}
              {(displayPros.length > 0 || displayCons.length > 0) && (
                <div className="grid sm:grid-cols-2 gap-4 mb-4 p-3 rounded-lg bg-[var(--surface)]/50 border border-[var(--border)]/50">
                  {displayPros.length > 0 && (
                    <div>
                      <p className="text-[10px] font-bold text-green-600 mb-2 uppercase tracking-wide flex items-center gap-1">
                        <Check size={12} strokeWidth={3} /> Pros
                      </p>
                      <ul className="space-y-1.5">
                        {displayPros.map((pro, idx) => (
                          <li key={idx} className="text-sm text-[var(--text)] flex items-start gap-2 leading-relaxed">
                            <span className="w-1 h-1 rounded-full bg-green-500 mt-2 shrink-0" />
                            <span className="opacity-90">{pro}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {displayCons.length > 0 && (
                    <div className={`${displayPros.length > 0 ? 'border-t sm:border-t-0 sm:border-l border-[var(--border)] pt-3 sm:pt-0 sm:pl-4' : ''}`}>
                      <p className="text-[10px] font-bold text-red-500 mb-2 uppercase tracking-wide flex items-center gap-1">
                        <X size={12} strokeWidth={3} /> Cons
                      </p>
                      <ul className="space-y-1.5">
                        {displayCons.map((con, idx) => (
                          <li key={idx} className="text-sm text-[var(--text)] flex items-start gap-2 leading-relaxed">
                            <span className="w-1 h-1 rounded-full bg-red-400 mt-2 shrink-0" />
                            <span className="opacity-90">{con}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Footer Action */}
              <div className="flex justify-end pt-2">
                <a
                  href={displayLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-5 py-2 bg-[var(--primary)] text-white text-sm font-medium rounded-full hover:bg-[var(--primary-hover)] hover:shadow-md hover:-translate-y-0.5 transition-all"
                >
                  View Deal <ExternalLink size={14} strokeWidth={2.5} />
                </a>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
