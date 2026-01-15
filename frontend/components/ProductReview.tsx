'use client'

import { ThumbsUp, ThumbsDown, ExternalLink, Star } from 'lucide-react'

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

interface ProductReviewProps {
  product: {
    product_name: string
    rating: string
    summary: string
    features: string[]
    pros: Array<{
      description: string
      source_ids?: number[]
      citations?: Array<{
        id: number
        url: string
        title: string
      }>
    }>
    cons: Array<{
      description: string
      source_ids?: number[]
      citations?: Array<{
        id: number
        url: string
        title: string
      }>
    }>
    affiliate_links: AffiliateLink[]
    rank: number
  }
}

export default function ProductReview({ product }: ProductReviewProps) {
  const {
    product_name,
    rating,
    summary,
    features,
    pros,
    cons,
    affiliate_links,
  } = product

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      {/* Product Header */}
      <div className="mb-4">
        <div className="flex items-start justify-between">
          <h3 className="text-xl font-semibold text-gray-900">{product_name}</h3>
          {rating && rating !== 'N/A' && (
            <div className="flex items-center gap-1 text-amber-500">
              <Star size={16} fill="currentColor" />
              <span className="text-sm font-medium">{rating}</span>
            </div>
          )}
        </div>
        {summary && (
          <p className="mt-2 text-gray-600 text-sm">{summary}</p>
        )}
      </div>

      {/* Features */}
      {features && features.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Features</h4>
          <ul className="list-disc list-inside space-y-1">
            {features.map((feature, idx) => (
              <li key={idx} className="text-sm text-gray-600">{feature}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Pros and Cons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {/* Pros */}
        {pros && pros.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-1">
              <ThumbsUp size={14} />
              Pros
            </h4>
            <ul className="space-y-2">
              {pros.map((pro, idx) => (
                <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-green-600 mt-0.5">✓</span>
                  <span>{pro.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Cons */}
        {cons && cons.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-1">
              <ThumbsDown size={14} />
              Cons
            </h4>
            <ul className="space-y-2">
              {cons.map((con, idx) => (
                <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-red-600 mt-0.5">✗</span>
                  <span>{con.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Affiliate Links */}
      {affiliate_links && affiliate_links.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Where to Buy</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {affiliate_links.map((link, idx) => (
              <a
                key={idx}
                href={link.affiliate_link}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 border rounded-lg hover:border-gray-300 hover:bg-gray-50 transition-colors group"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-gray-500 uppercase">{link.merchant}</span>
                    {link.rating && (
                      <div className="flex items-center gap-0.5 text-amber-500">
                        <Star size={10} fill="currentColor" />
                        <span className="text-xs">{link.rating}</span>
                      </div>
                    )}
                  </div>
                  <p className="text-sm font-semibold text-gray-900 truncate">{link.title}</p>
                  <p className="text-lg font-bold text-gray-900 mt-1">
                    {link.currency} {link.price.toFixed(2)}
                  </p>
                </div>
                <ExternalLink size={16} className="text-gray-400 group-hover:text-gray-600 flex-shrink-0 ml-2" />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
