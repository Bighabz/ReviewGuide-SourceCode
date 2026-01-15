'use client'

import { useState } from 'react'
import { Check, X, ExternalLink, Star } from 'lucide-react'

interface ComparisonProduct {
  title: string
  price: number
  currency: string
  rating?: number
  review_count?: number
  merchant: string
  url: string
  image_url?: string
  pros?: string[]
  cons?: string[]
}

interface ComparisonTableData {
  products: ComparisonProduct[]
  criteria: string[]
  summary: string
}

interface ComparisonTableProps {
  data: ComparisonTableData
  title?: string
}

export default function ComparisonTable({ data, title }: ComparisonTableProps) {
  const [hoveredColumn, setHoveredColumn] = useState<number | null>(null)

  if (!data || !data.products || data.products.length === 0) {
    return null
  }

  const { products, summary } = data

  // Find best values for highlighting
  const lowestPrice = Math.min(...products.map(p => p.price || Infinity))
  const highestRating = Math.max(...products.map(p => p.rating || 0))
  const mostReviews = Math.max(...products.map(p => p.review_count || 0))

  const formatPrice = (price: number, currency: string) => {
    if (!price) return 'N/A'
    return `${currency} ${price.toFixed(2)}`
  }

  const renderRating = (rating?: number, review_count?: number) => {
    if (!rating) return <span style={{ color: 'var(--gpt-text-muted)' }}>N/A</span>
    return (
      <div className="flex items-center gap-1">
        <Star size={14} className="fill-yellow-400 text-yellow-400" />
        <span className="font-medium">{rating.toFixed(1)}</span>
        {review_count && (
          <span className="text-xs" style={{ color: 'var(--gpt-text-muted)' }}>
            ({review_count.toLocaleString()})
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="w-full mb-4 sm:mb-6">
      {/* Title */}
      {title && (
        <h3 className="text-sm sm:text-base font-semibold mb-2 sm:mb-3" style={{ color: 'var(--gpt-text)' }}>
          {title}
        </h3>
      )}

      {/* Comparison Table Container */}
      <div
        className="rounded-lg border overflow-hidden"
        style={{ background: 'var(--gpt-assistant-message)', borderColor: 'var(--gpt-border)' }}
      >
        {/* Summary */}
        {summary && (
          <div
            className="px-4 py-3 border-b text-sm"
            style={{ borderColor: 'var(--gpt-border)', color: 'var(--gpt-text)' }}
          >
            {summary}
          </div>
        )}

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            {/* Header with Product Images and Names */}
            <thead>
              <tr style={{ borderBottom: '1px solid var(--gpt-border)' }}>
                <th
                  className="p-3 text-left text-xs font-medium uppercase tracking-wider"
                  style={{ color: 'var(--gpt-text-muted)', width: '120px' }}
                >
                  Feature
                </th>
                {products.map((product, idx) => (
                  <th
                    key={idx}
                    className="p-3 text-center transition-colors"
                    style={{
                      background: hoveredColumn === idx ? 'var(--gpt-hover)' : 'transparent',
                      minWidth: '150px'
                    }}
                    onMouseEnter={() => setHoveredColumn(idx)}
                    onMouseLeave={() => setHoveredColumn(null)}
                  >
                    {/* Product Image */}
                    <div className="flex justify-center mb-2">
                      <div
                        className="w-16 h-16 sm:w-20 sm:h-20 rounded-lg overflow-hidden"
                        style={{ background: 'var(--gpt-hover)' }}
                      >
                        {product.image_url ? (
                          <img
                            src={product.image_url}
                            alt={product.title}
                            loading="lazy"
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div
                            className="w-full h-full flex items-center justify-center text-xs"
                            style={{ color: 'var(--gpt-text-muted)' }}
                          >
                            No Image
                          </div>
                        )}
                      </div>
                    </div>
                    {/* Product Title */}
                    <div
                      className="text-xs sm:text-sm font-medium line-clamp-2"
                      style={{ color: 'var(--gpt-text)' }}
                      title={product.title}
                    >
                      {product.title}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {/* Price Row */}
              <tr style={{ borderBottom: '1px solid var(--gpt-border)' }}>
                <td
                  className="p-3 text-sm font-medium"
                  style={{ color: 'var(--gpt-text)' }}
                >
                  Price
                </td>
                {products.map((product, idx) => {
                  const isBest = product.price === lowestPrice && product.price > 0
                  return (
                    <td
                      key={idx}
                      className="p-3 text-center transition-colors"
                      style={{
                        background: hoveredColumn === idx ? 'var(--gpt-hover)' : 'transparent'
                      }}
                      onMouseEnter={() => setHoveredColumn(idx)}
                      onMouseLeave={() => setHoveredColumn(null)}
                    >
                      <span
                        className={`text-sm sm:text-base font-bold ${isBest ? 'text-green-600' : ''}`}
                        style={{ color: isBest ? '#16a34a' : 'var(--gpt-text)' }}
                      >
                        {formatPrice(product.price, product.currency)}
                        {isBest && (
                          <span className="ml-1 text-xs font-normal text-green-600">
                            Best
                          </span>
                        )}
                      </span>
                    </td>
                  )
                })}
              </tr>

              {/* Rating Row */}
              <tr style={{ borderBottom: '1px solid var(--gpt-border)' }}>
                <td
                  className="p-3 text-sm font-medium"
                  style={{ color: 'var(--gpt-text)' }}
                >
                  Rating
                </td>
                {products.map((product, idx) => {
                  const isBest = product.rating === highestRating && (product.rating || 0) > 0
                  return (
                    <td
                      key={idx}
                      className="p-3 transition-colors"
                      style={{
                        background: hoveredColumn === idx ? 'var(--gpt-hover)' : 'transparent'
                      }}
                      onMouseEnter={() => setHoveredColumn(idx)}
                      onMouseLeave={() => setHoveredColumn(null)}
                    >
                      <div className="flex justify-center items-center gap-1">
                        {renderRating(product.rating, product.review_count)}
                        {isBest && product.rating && (
                          <span className="ml-1 text-xs text-green-600">Top</span>
                        )}
                      </div>
                    </td>
                  )
                })}
              </tr>

              {/* Merchant Row */}
              <tr style={{ borderBottom: '1px solid var(--gpt-border)' }}>
                <td
                  className="p-3 text-sm font-medium"
                  style={{ color: 'var(--gpt-text)' }}
                >
                  Merchant
                </td>
                {products.map((product, idx) => (
                  <td
                    key={idx}
                    className="p-3 text-center text-sm transition-colors"
                    style={{
                      color: 'var(--gpt-text-secondary)',
                      background: hoveredColumn === idx ? 'var(--gpt-hover)' : 'transparent'
                    }}
                    onMouseEnter={() => setHoveredColumn(idx)}
                    onMouseLeave={() => setHoveredColumn(null)}
                  >
                    {product.merchant || 'N/A'}
                  </td>
                ))}
              </tr>

              {/* Pros Row (if available) */}
              {products.some(p => p.pros && p.pros.length > 0) && (
                <tr style={{ borderBottom: '1px solid var(--gpt-border)' }}>
                  <td
                    className="p-3 text-sm font-medium align-top"
                    style={{ color: 'var(--gpt-text)' }}
                  >
                    Pros
                  </td>
                  {products.map((product, idx) => (
                    <td
                      key={idx}
                      className="p-3 text-left text-xs transition-colors"
                      style={{
                        background: hoveredColumn === idx ? 'var(--gpt-hover)' : 'transparent'
                      }}
                      onMouseEnter={() => setHoveredColumn(idx)}
                      onMouseLeave={() => setHoveredColumn(null)}
                    >
                      {product.pros && product.pros.length > 0 ? (
                        <ul className="space-y-1">
                          {product.pros.slice(0, 3).map((pro, proIdx) => (
                            <li key={proIdx} className="flex items-start gap-1">
                              <Check size={12} className="text-green-500 flex-shrink-0 mt-0.5" />
                              <span style={{ color: 'var(--gpt-text)' }}>{pro}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <span style={{ color: 'var(--gpt-text-muted)' }}>-</span>
                      )}
                    </td>
                  ))}
                </tr>
              )}

              {/* Cons Row (if available) */}
              {products.some(p => p.cons && p.cons.length > 0) && (
                <tr style={{ borderBottom: '1px solid var(--gpt-border)' }}>
                  <td
                    className="p-3 text-sm font-medium align-top"
                    style={{ color: 'var(--gpt-text)' }}
                  >
                    Cons
                  </td>
                  {products.map((product, idx) => (
                    <td
                      key={idx}
                      className="p-3 text-left text-xs transition-colors"
                      style={{
                        background: hoveredColumn === idx ? 'var(--gpt-hover)' : 'transparent'
                      }}
                      onMouseEnter={() => setHoveredColumn(idx)}
                      onMouseLeave={() => setHoveredColumn(null)}
                    >
                      {product.cons && product.cons.length > 0 ? (
                        <ul className="space-y-1">
                          {product.cons.slice(0, 3).map((con, conIdx) => (
                            <li key={conIdx} className="flex items-start gap-1">
                              <X size={12} className="text-red-500 flex-shrink-0 mt-0.5" />
                              <span style={{ color: 'var(--gpt-text)' }}>{con}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <span style={{ color: 'var(--gpt-text-muted)' }}>-</span>
                      )}
                    </td>
                  ))}
                </tr>
              )}

              {/* Action Row - Buy Links */}
              <tr>
                <td
                  className="p-3 text-sm font-medium"
                  style={{ color: 'var(--gpt-text)' }}
                >
                  Action
                </td>
                {products.map((product, idx) => (
                  <td
                    key={idx}
                    className="p-3 text-center transition-colors"
                    style={{
                      background: hoveredColumn === idx ? 'var(--gpt-hover)' : 'transparent'
                    }}
                    onMouseEnter={() => setHoveredColumn(idx)}
                    onMouseLeave={() => setHoveredColumn(null)}
                  >
                    {product.url ? (
                      <a
                        href={product.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-colors"
                        style={{
                          background: 'var(--gpt-accent)',
                          color: 'white'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.opacity = '0.9'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.opacity = '1'
                        }}
                      >
                        <span>View Deal</span>
                        <ExternalLink size={12} />
                      </a>
                    ) : (
                      <span className="text-xs" style={{ color: 'var(--gpt-text-muted)' }}>
                        N/A
                      </span>
                    )}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
