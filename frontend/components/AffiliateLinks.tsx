'use client'

import { ExternalLink } from 'lucide-react'

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

      {/* Where to Buy — editorial heading */}
      <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Where to buy
      </h4>

      <div className="space-y-2">
        {affiliateLinks.map((link, idx) => {
          const isLowest = idx === 0
          return (
            <a
              key={idx}
              href={link.affiliate_link}
              target="_blank"
              rel="noopener noreferrer"
              className={`flex items-center justify-between p-3 rounded-lg border transition-all group/link ${
                isLowest
                  ? 'border-green-500/30 bg-green-500/5 hover:bg-green-500/10'
                  : 'border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] hover:border-[var(--primary)]/30'
              }`}
            >
              <div className="flex items-center gap-2">
                {isLowest && (
                  <span className="text-[10px] font-bold uppercase tracking-wider text-green-600 bg-green-100 px-1.5 py-0.5 rounded dark:text-green-400 dark:bg-green-900/30">
                    Best Price
                  </span>
                )}
                <span className="text-sm font-semibold text-[var(--text)]">
                  {link.merchant}
                </span>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className={`text-base font-bold font-serif ${isLowest ? 'text-green-600 dark:text-green-400' : 'text-[var(--text)]'}`}>
                  {link.currency} {link.price.toFixed(2)}
                </span>
                <span className="text-xs font-medium text-[var(--primary)] group-hover/link:text-[var(--primary-hover)] flex items-center gap-1">
                  Buy &rarr;
                </span>
              </div>
            </a>
          )
        })}
      </div>
      <p className="text-xs text-[var(--text-muted)] mt-3 px-1">
        Disclosure: We may earn commissions from qualifying purchases.
      </p>
    </div>
  )
}
