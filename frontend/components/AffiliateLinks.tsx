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
    <div className="border border-gray-200 rounded-lg p-4 my-4">
      {/* Product Header */}
      <div className="mb-3 pb-3 border-b border-gray-200">
        <h3 className="text-base font-semibold text-gray-900">
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
            className="flex flex-col p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors group"
          >
            {/* Merchant and Rating */}
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-gray-600 uppercase">
                {link.merchant}
              </span>
              {link.rating && (
                <div className="flex items-center gap-1">
                  <Star size={12} fill="currentColor" className="text-gray-900" />
                  <span className="text-xs font-medium text-gray-900">{link.rating}</span>
                </div>
              )}
            </div>

            {/* Product Title */}
            <p className="text-sm text-gray-900 mb-2 line-clamp-2">
              {link.title}
            </p>

            {/* Price */}
            <p className="text-lg font-semibold text-gray-900 mb-1">
              {link.currency} {link.price.toFixed(2)}
            </p>

            {/* Review Count */}
            {link.review_count && link.review_count > 0 && (
              <p className="text-xs text-gray-500 mb-2">
                {link.review_count.toLocaleString()} reviews
              </p>
            )}

            {/* External Link */}
            <div className="flex items-center gap-1 text-xs text-gray-600 group-hover:text-gray-900 mt-auto pt-2 border-t border-gray-100">
              <span>View on {link.merchant}</span>
              <ExternalLink size={12} />
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}
