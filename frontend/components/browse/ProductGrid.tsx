'use client'

import React from 'react'
import { ProductItem } from '@/lib/browseData'
import ProductCardCompact from './ProductCardCompact'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface ProductGridProps {
  items: ProductItem[]
  onItemClick?: (item: ProductItem) => void
  currentPage?: number
  totalPages?: number
  onPageChange?: (page: number) => void
  loading?: boolean
}

export default function ProductGrid({
  items,
  onItemClick,
  currentPage = 1,
  totalPages = 1,
  onPageChange,
  loading = false
}: ProductGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4">
        {Array.from({ length: 10 }).map((_, i) => (
          <div
            key={i}
            className="bg-[var(--surface)] border border-[var(--border)] rounded-lg overflow-hidden animate-pulse"
          >
            <div className="aspect-square bg-[var(--surface-hover)]" />
            <div className="p-3 space-y-2">
              <div className="h-4 bg-[var(--surface-hover)] rounded w-3/4" />
              <div className="h-3 bg-[var(--surface-hover)] rounded w-1/2" />
              <div className="h-5 bg-[var(--surface-hover)] rounded w-1/3 mt-2" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (!items || items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 rounded-full bg-[var(--surface)] flex items-center justify-center mb-4">
          <span className="text-2xl">🔍</span>
        </div>
        <h3 className="text-lg font-semibold text-[var(--text)] mb-2">No products found</h3>
        <p className="text-sm text-[var(--text-secondary)]">Try adjusting your filters or search terms</p>
      </div>
    )
  }

  return (
    <div>
      {/* Product Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4">
        {items.map((item) => (
          <ProductCardCompact key={item.id} item={item} onClick={onItemClick} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-center gap-2 mt-8 pt-6 border-t border-[var(--border)]">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className="p-2 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            aria-label="Previous page"
          >
            <ChevronLeft size={18} />
          </button>

          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(totalPages, 7) }).map((_, i) => {
              let pageNum: number
              if (totalPages <= 7) {
                pageNum = i + 1
              } else if (currentPage <= 4) {
                pageNum = i + 1
              } else if (currentPage >= totalPages - 3) {
                pageNum = totalPages - 6 + i
              } else {
                pageNum = currentPage - 3 + i
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => onPageChange(pageNum)}
                  className={`min-w-[36px] h-9 px-3 rounded-lg text-sm font-medium transition-all ${
                    currentPage === pageNum
                      ? 'bg-[var(--primary)] text-white'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]'
                  }`}
                >
                  {pageNum}
                </button>
              )
            })}
          </div>

          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="p-2 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            aria-label="Next page"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      )}
    </div>
  )
}
