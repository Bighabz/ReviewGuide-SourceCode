'use client'

import { ExternalLink, Star } from 'lucide-react'

interface AffiliateLink {
  product_id: string
  title: string
  price: number
  currency: string
  affiliate_link: string
  merchant: string
  image_url?: string
  rating?: number
  review_count?: number
}

interface AffiliateLinksProps {
  productName: string
  affiliateLinks: AffiliateLink[]
  rank?: number
}

export default function AffiliateLinks({ productName, affiliateLinks, rank }: AffiliateLinksProps) {
  if (!affiliateLinks || affiliateLinks.length === 0) {
    return null
  }

  return (
    <div className="border border-[var(--border)] rounded-xl p-4 my-4 shadow-card">
      {/* Product Header */}
      <div className="mb-3 pb-3 border-b border-[var(--border)]">
        <h3 className="text-base font-semibold font-serif text-[var(--text)]">
          {rank && `${rank}. `}{productName}
        </h3>
      </div>

      {/* Affiliate Links Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {affiliateLinks.map((link, idx) => (
          <a
            key={idx}
            href={link.affiliate_link}
            target="_blank"
            rel="noopener noreferrer"
            className="flex flex-col p-3 border border-[var(--border)] rounded-xl bg-[var(--surface)] hover:bg-[var(--surface-hover)] transition-colors group"
          >
            {/* Merchant and Rating */}
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-[var(--text-secondary)] uppercase">
                {link.merchant}
              </span>
              {link.rating && (
                <div className="flex items-center gap-1">
                  <Star size={12} fill="currentColor" className="text-[var(--text)]" />
                  <span className="text-xs font-medium text-[var(--text)]">{link.rating}</span>
                </div>
              )}
            </div>

            {/* Product Title */}
            <p className="text-sm text-[var(--text)] mb-2 line-clamp-2">
              {link.title}
            </p>

            {/* Price */}
            <p className="text-lg font-semibold text-[var(--text)] mb-1">
              {link.currency} {link.price.toFixed(2)}
            </p>

            {/* Review Count */}
            {link.review_count && link.review_count > 0 && (
              <p className="text-xs text-[var(--text-muted)] mb-2">
                {link.review_count.toLocaleString()} reviews
              </p>
            )}

            {/* External Link */}
            <div className="flex items-center gap-1 text-xs text-[var(--text-secondary)] group-hover:text-[var(--text)] mt-auto pt-2 border-t border-[var(--border)]">
              <span>View on {link.merchant}</span>
              <ExternalLink size={12} />
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}
