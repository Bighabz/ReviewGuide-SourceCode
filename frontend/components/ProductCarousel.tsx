'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

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
}

interface ProductCarouselProps {
  items: Product[]
  title?: string
}

export default function ProductCarousel({ items, title }: ProductCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [itemsPerPage, setItemsPerPage] = useState(3)

  if (!items || items.length === 0) {
    return null
  }

  // Detect screen size and set items per page
  useEffect(() => {
    const updateItemsPerPage = () => {
      if (window.innerWidth < 640) {
        setItemsPerPage(1) // Mobile: 1 item
      } else if (window.innerWidth < 1024) {
        setItemsPerPage(2) // Tablet: 2 items
      } else {
        setItemsPerPage(3) // Desktop: 3 items
      }
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
    <div className="w-full mb-4 sm:mb-6">
      {/* Carousel Title */}
      {title && (
        <h3 className="text-sm sm:text-base font-semibold mb-2 sm:mb-3" style={{ color: 'var(--gpt-text)' }}>
          {title}
        </h3>
      )}
      <div className="relative rounded-lg border p-4 sm:p-6" style={{ background: 'var(--gpt-assistant-message)', borderColor: 'var(--gpt-border)' }}>
        {/* Navigation Buttons */}
        {items.length > itemsPerPage && (
          <>
            <button
              onClick={handlePrev}
              className="absolute left-1 sm:left-2 top-1/2 -translate-y-1/2 z-10 rounded-full p-1.5 sm:p-2 transition-colors"
              style={{ background: 'var(--gpt-input-bg)', boxShadow: 'var(--gpt-shadow-lg)' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'var(--gpt-hover)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'var(--gpt-input-bg)'
              }}
              aria-label="Previous products"
            >
              <ChevronLeft size={20} style={{ color: 'var(--gpt-text)' }} />
            </button>
            <button
              onClick={handleNext}
              className="absolute right-1 sm:right-2 top-1/2 -translate-y-1/2 z-10 rounded-full p-1.5 sm:p-2 transition-colors"
              style={{ background: 'var(--gpt-input-bg)', boxShadow: 'var(--gpt-shadow-lg)' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'var(--gpt-hover)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'var(--gpt-input-bg)'
              }}
              aria-label="Next products"
            >
              <ChevronRight size={20} style={{ color: 'var(--gpt-text)' }} />
            </button>
          </>
        )}

        {/* Carousel Items */}
        <div className="flex gap-2 sm:gap-4 overflow-hidden">
          {visibleItems.map((item, idx) => (
            <div
              key={`${item.product_id}-${idx}`}
              className="flex-1 min-w-0"
            >
              <a
                href={item.affiliate_link}
                target="_blank"
                rel="noopener noreferrer"
                className="block group"
              >
                {/* Product Image */}
                <div className="aspect-square rounded-lg overflow-hidden mb-2 sm:mb-3" style={{ background: 'var(--gpt-hover)' }}>
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt={item.title}
                      loading="lazy"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs sm:text-sm" style={{ color: 'var(--gpt-text-muted)' }}>
                      No Image
                    </div>
                  )}
                </div>

                {/* Product Info */}
                <div className="space-y-1">
                  <h3 className="font-medium text-xs sm:text-sm line-clamp-2 transition-colors" style={{ color: 'var(--gpt-text)' }}>
                    {item.title}
                  </h3>

                  <div className="flex items-baseline gap-1 sm:gap-2">
                    <span className="text-base sm:text-lg font-bold" style={{ color: 'var(--gpt-text)' }}>
                      {item.currency} {item.price?.toFixed(2) ?? 'N/A'}
                    </span>
                  </div>

                  {item.rating && (
                    <div className="flex items-center gap-1 text-xs" style={{ color: 'var(--gpt-text-secondary)' }}>
                      <span className="text-yellow-500">★</span>
                      <span>{item.rating}</span>
                      {item.review_count && (
                        <span style={{ color: 'var(--gpt-text-muted)' }}>({item.review_count})</span>
                      )}
                    </div>
                  )}

                  <p className="text-xs truncate" style={{ color: 'var(--gpt-text-secondary)' }}>{item.merchant}</p>
                </div>
              </a>
            </div>
          ))}
        </div>

        {/* Pagination Dots */}
        {items.length > itemsPerPage && (
          <div className="flex justify-center gap-2 mt-3 sm:mt-4">
            {Array.from({ length: Math.ceil(items.length / itemsPerPage) }).map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentIndex(idx * itemsPerPage)}
                className="w-2 h-2 rounded-full transition-colors"
                style={{
                  background: Math.floor(currentIndex / itemsPerPage) === idx
                    ? 'var(--gpt-text)'
                    : 'var(--gpt-text-muted)'
                }}
                onMouseEnter={(e) => {
                  if (Math.floor(currentIndex / itemsPerPage) !== idx) {
                    e.currentTarget.style.background = 'var(--gpt-text-secondary)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (Math.floor(currentIndex / itemsPerPage) !== idx) {
                    e.currentTarget.style.background = 'var(--gpt-text-muted)'
                  }
                }}
                aria-label={`Go to page ${idx + 1}`}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
