'use client'

import React, { useState } from 'react'
import { ChevronDown, ChevronUp, Star, X } from 'lucide-react'

export interface FilterState {
  categories: string[]
  priceRange: [number, number] | null
  minRating: number | null
  sortBy: 'relevance' | 'price_low' | 'price_high' | 'rating' | 'reviews'
}

interface FilterSidebarProps {
  filters: FilterState
  onFilterChange: (filters: FilterState) => void
  availableCategories?: string[]
  onClose?: () => void
  isMobile?: boolean
}

const PRICE_RANGES: { label: string; value: [number, number] }[] = [
  { label: 'Under $50', value: [0, 50] },
  { label: '$50 - $100', value: [50, 100] },
  { label: '$100 - $250', value: [100, 250] },
  { label: '$250 - $500', value: [250, 500] },
  { label: '$500 - $1000', value: [500, 1000] },
  { label: 'Over $1000', value: [1000, 100000] }
]

const SORT_OPTIONS: { label: string; value: FilterState['sortBy'] }[] = [
  { label: 'Most Relevant', value: 'relevance' },
  { label: 'Price: Low to High', value: 'price_low' },
  { label: 'Price: High to Low', value: 'price_high' },
  { label: 'Highest Rated', value: 'rating' },
  { label: 'Most Reviews', value: 'reviews' }
]

const DEFAULT_CATEGORIES = [
  'Electronics',
  'Travel',
  'Home & Kitchen',
  'Sports & Outdoors',
  'Beauty & Personal Care',
  'Books',
  'Fashion',
  'Automotive'
]

export default function FilterSidebar({
  filters,
  onFilterChange,
  availableCategories = DEFAULT_CATEGORIES,
  onClose,
  isMobile = false
}: FilterSidebarProps) {
  const [expandedSections, setExpandedSections] = useState({
    category: true,
    price: true,
    rating: true,
    sort: true
  })

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  const toggleCategory = (category: string) => {
    const newCategories = filters.categories.includes(category)
      ? filters.categories.filter((c) => c !== category)
      : [...filters.categories, category]
    onFilterChange({ ...filters, categories: newCategories })
  }

  const setPriceRange = (range: [number, number] | null) => {
    onFilterChange({ ...filters, priceRange: range })
  }

  const setMinRating = (rating: number | null) => {
    onFilterChange({ ...filters, minRating: rating })
  }

  const setSortBy = (sortBy: FilterState['sortBy']) => {
    onFilterChange({ ...filters, sortBy })
  }

  const clearAllFilters = () => {
    onFilterChange({
      categories: [],
      priceRange: null,
      minRating: null,
      sortBy: 'relevance'
    })
  }

  const hasActiveFilters =
    filters.categories.length > 0 ||
    filters.priceRange !== null ||
    filters.minRating !== null ||
    filters.sortBy !== 'relevance'

  return (
    <div className="h-full overflow-y-auto bg-[var(--surface)] border-r border-[var(--border)]">
      {/* Header */}
      <div className="sticky top-0 bg-[var(--surface)] border-b border-[var(--border)] p-4 flex items-center justify-between z-10">
        <h2 className="font-bold text-[var(--text)]">Filters</h2>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="text-xs text-[var(--accent)] hover:underline font-medium"
            >
              Clear all
            </button>
          )}
          {isMobile && onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-[var(--surface-hover)] text-[var(--text-secondary)]"
              aria-label="Close filters"
            >
              <X size={20} />
            </button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Sort By */}
        <div className="border-b border-[var(--border)] pb-4">
          <button
            onClick={() => toggleSection('sort')}
            className="w-full flex items-center justify-between text-sm font-semibold text-[var(--text)] mb-2"
          >
            Sort By
            {expandedSections.sort ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {expandedSections.sort && (
            <div className="space-y-1">
              {SORT_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setSortBy(option.value)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                    filters.sortBy === option.value
                      ? 'bg-[var(--primary)] text-white'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Categories */}
        <div className="border-b border-[var(--border)] pb-4">
          <button
            onClick={() => toggleSection('category')}
            className="w-full flex items-center justify-between text-sm font-semibold text-[var(--text)] mb-2"
          >
            Category
            {expandedSections.category ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {expandedSections.category && (
            <div className="space-y-1">
              {availableCategories.map((category) => (
                <label
                  key={category}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-[var(--surface-hover)] cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={filters.categories.includes(category)}
                    onChange={() => toggleCategory(category)}
                    className="w-4 h-4 rounded border-[var(--border)] text-[var(--accent)] focus:ring-[var(--accent)] cursor-pointer"
                  />
                  <span className="text-sm text-[var(--text)]">{category}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Price Range */}
        <div className="border-b border-[var(--border)] pb-4">
          <button
            onClick={() => toggleSection('price')}
            className="w-full flex items-center justify-between text-sm font-semibold text-[var(--text)] mb-2"
          >
            Price
            {expandedSections.price ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {expandedSections.price && (
            <div className="space-y-1">
              <button
                onClick={() => setPriceRange(null)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                  filters.priceRange === null
                    ? 'bg-[var(--primary)] text-white'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]'
                }`}
              >
                Any Price
              </button>
              {PRICE_RANGES.map((range) => (
                <button
                  key={range.label}
                  onClick={() => setPriceRange(range.value)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                    filters.priceRange?.[0] === range.value[0] &&
                    filters.priceRange?.[1] === range.value[1]
                      ? 'bg-[var(--primary)] text-white'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Rating */}
        <div className="pb-4">
          <button
            onClick={() => toggleSection('rating')}
            className="w-full flex items-center justify-between text-sm font-semibold text-[var(--text)] mb-2"
          >
            Customer Rating
            {expandedSections.rating ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {expandedSections.rating && (
            <div className="space-y-1">
              <button
                onClick={() => setMinRating(null)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                  filters.minRating === null
                    ? 'bg-[var(--primary)] text-white'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]'
                }`}
              >
                Any Rating
              </button>
              {[4, 3, 2, 1].map((rating) => (
                <button
                  key={rating}
                  onClick={() => setMinRating(rating)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all flex items-center gap-2 ${
                    filters.minRating === rating
                      ? 'bg-[var(--primary)] text-white'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]'
                  }`}
                >
                  <div className="flex items-center">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star
                        key={i}
                        size={14}
                        className={i < rating ? 'fill-[var(--star-color)] text-[var(--star-color)]' : 'text-[var(--border)]'}
                      />
                    ))}
                  </div>
                  <span>& Up</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
