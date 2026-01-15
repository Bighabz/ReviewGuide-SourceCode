'use client'

import { Check, X } from 'lucide-react'

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
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="space-y-8">
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
          <div key={product.id || product.rank || index} className="border-b border-gray-200 last:border-b-0 pb-6 last:pb-0">
            {/* Product Number and Title */}
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              {displayRank}. {displayTitle}
            </h3>

            {/* Specs */}
            {product.specs && product.specs.length > 0 && (
              <ul className="space-y-1 mb-3">
                {product.specs.map((spec, idx) => (
                  <li key={idx} className="text-sm text-gray-700">
                    • {spec}
                  </li>
                ))}
              </ul>
            )}

            {/* Price */}
            {displayPrice !== undefined && (
              <p className="text-sm text-gray-700 mb-2">
                <span className="font-semibold">Price:</span> {displayCurrency} {displayPrice.toFixed(2)}
              </p>
            )}

            {/* Pros */}
            {displayPros.length > 0 && (
              <div className="mb-2">
                <p className="text-sm font-semibold text-green-700 mb-1">Pros:</p>
                <ul className="space-y-1">
                  {displayPros.map((pro, idx) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                      <Check size={14} className="text-green-600 flex-shrink-0 mt-0.5" />
                      <span>{pro}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Cons */}
            {displayCons.length > 0 && (
              <div className="mb-3">
                <p className="text-sm font-semibold text-red-700 mb-1">Cons:</p>
                <ul className="space-y-1">
                  {displayCons.map((con, idx) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                      <X size={14} className="text-red-600 flex-shrink-0 mt-0.5" />
                      <span>{con}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Buy Link */}
            {displayMerchant && (
              <a
                href={displayLink}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-900 hover:text-black hover:underline font-medium"
              >
                View on {displayMerchant.split(' ')[0] || 'eBay'}
              </a>
            )}
          </div>
          )
        })}
      </div>
    </div>
  )
}
