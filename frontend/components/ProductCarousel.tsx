'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, ExternalLink, Star } from 'lucide-react'
import { motion } from 'framer-motion'

interface Product {
  product_id: string
  title: string
  price?: number
  currency: string
  affiliate_link: string
  merchant: string
  image_url?: string
  rating?: number
  review_count?: number
  description?: string
}

interface ProductCarouselProps {
  items: Product[]
  title?: string
}

function StarRatingInline({ value, size = 12 }: { value: number; size?: number }) {
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

export default function ProductCarousel({ items, title }: ProductCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [itemsPerPage, setItemsPerPage] = useState(3)

  if (!items || items.length === 0) return null

  useEffect(() => {
    const updateItemsPerPage = () => {
      if (window.innerWidth < 640) setItemsPerPage(1)
      else if (window.innerWidth < 1024) setItemsPerPage(2)
      else setItemsPerPage(3)
    }
    updateItemsPerPage()
    window.addEventListener('resize', updateItemsPerPage)
    return () => window.removeEventListener('resize', updateItemsPerPage)
  }, [])

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev === 0 ? items.length - 1 : prev - 1))
  }

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === items.length - 1 ? 0 : prev + 1))
  }

  const visibleItems = items.slice(currentIndex, currentIndex + itemsPerPage)
  if (visibleItems.length < itemsPerPage && items.length >= itemsPerPage) {
    visibleItems.push(...items.slice(0, itemsPerPage - visibleItems.length))
  }

  return (
    <div className="w-full mb-6">
      {/* Section Title */}
      {title && (
        <div className="flex items-center gap-3 mb-4">
          <h3 className="font-serif text-lg sm:text-xl text-[var(--text)]">{title}</h3>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>
      )}

      <div className="relative">
        {/* Navigation Arrows */}
        {items.length > itemsPerPage && (
          <>
            <button
              onClick={handlePrev}
              className="absolute -left-3 top-1/2 -translate-y-1/2 z-10 w-9 h-9 rounded-full bg-[var(--surface-elevated)] border border-[var(--border)] shadow-card flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text)] hover:shadow-card-hover transition-all"
              aria-label="Previous"
            >
              <ChevronLeft size={18} />
            </button>
            <button
              onClick={handleNext}
              className="absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-9 h-9 rounded-full bg-[var(--surface-elevated)] border border-[var(--border)] shadow-card flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text)] hover:shadow-card-hover transition-all"
              aria-label="Next"
            >
              <ChevronRight size={18} />
            </button>
          </>
        )}

        {/* Product Grid */}
        <div className="flex gap-4 overflow-hidden px-1">
          {visibleItems.map((item, idx) => (
            <motion.div
              key={`${item.product_id}-${idx}`}
              className="flex-1 min-w-0"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.05 }}
            >
              <a
                href={item.affiliate_link}
                target="_blank"
                rel="noopener noreferrer"
                className="block group"
              >
                <div className="bg-[var(--surface-elevated)] border border-[var(--border)] rounded-xl overflow-hidden product-card-hover">
                  {/* Image */}
                  <div className="aspect-square overflow-hidden bg-[var(--surface)]">
                    {item.image_url ? (
                      <img
                        src={item.image_url}
                        alt={item.title}
                        loading="lazy"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-[var(--text-muted)] text-sm">
                        No Image
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-4 space-y-2">
                    {/* Merchant */}
                    <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-muted)]">
                      {item.merchant}
                    </span>

                    {/* Title */}
                    <h4 className="text-sm font-semibold text-[var(--text)] line-clamp-2 leading-snug group-hover:text-[var(--primary)] transition-colors">
                      {item.title}
                    </h4>

                    {/* Rating */}
                    {item.rating && (
                      <div className="flex items-center gap-1.5">
                        <StarRatingInline value={item.rating} size={13} />
                        <span className="text-xs text-[var(--text-muted)]">
                          {item.rating}
                          {item.review_count && ` (${item.review_count.toLocaleString()})`}
                        </span>
                      </div>
                    )}

                    {/* Description */}
                    {item.description && (
                      <p className="text-sm text-[var(--text-secondary)] line-clamp-2 leading-relaxed">
                        {item.description}
                      </p>
                    )}

                    {/* Price + CTA */}
                    <div className="flex items-center justify-between pt-2 border-t border-[var(--border)]">
                      <div>
                        <span className="text-lg font-bold text-[var(--text)]">
                          {item.currency === 'USD' ? '$' : item.currency}{' '}
                          {item.price?.toFixed(2) ?? 'N/A'}
                        </span>
                      </div>
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-[var(--primary)] group-hover:text-[var(--primary-hover)]">
                        View Deal
                        <ExternalLink size={12} />
                      </span>
                    </div>
                  </div>
                </div>
              </a>
            </motion.div>
          ))}
        </div>

        {/* Pagination Dots */}
        {items.length > itemsPerPage && (
          <div className="flex justify-center gap-1.5 mt-4">
            {Array.from({ length: Math.ceil(items.length / itemsPerPage) }).map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentIndex(idx * itemsPerPage)}
                className={`h-1.5 rounded-full transition-all ${Math.floor(currentIndex / itemsPerPage) === idx
                  ? 'w-6 bg-[var(--primary)]'
                  : 'w-1.5 bg-[var(--border-strong)] hover:bg-[var(--text-muted)]'
                  }`}
                aria-label={`Page ${idx + 1}`}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
