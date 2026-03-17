'use client'

import { useState, useEffect } from 'react'
import { getRecentSearches } from '@/lib/recentSearches'
import DiscoverSearchBar from '@/components/discover/DiscoverSearchBar'
import CategoryChipRow from '@/components/discover/CategoryChipRow'
import TrendingCards from '@/components/discover/TrendingCards'

export default function DiscoverPage() {
  const [hasHistory, setHasHistory] = useState(false)

  useEffect(() => {
    setHasHistory(getRecentSearches().length > 0)
  }, [])

  return (
    <div className="flex flex-col pb-20 px-4 sm:px-6 md:px-8">
      {/* Hero section */}
      <div className="flex flex-col items-center pt-8 sm:pt-12 pb-8">
        <h1
          className="font-serif text-2xl sm:text-3xl md:text-4xl text-center leading-tight tracking-tight"
          style={{ color: 'var(--text)' }}
        >
          What are you{' '}
          <span
            className="italic"
            style={{ color: 'var(--primary)' }}
          >
            researching
          </span>
          {' '}today?
        </h1>
        <p
          className="text-sm text-center mt-3 max-w-md"
          style={{ color: 'var(--text-secondary)' }}
        >
          Expert reviews, real data, zero fluff.
        </p>
        <div className="w-full max-w-xl mx-auto mt-8">
          <DiscoverSearchBar />
        </div>
      </div>

      {/* Category chips */}
      <div className="mt-8">
        <CategoryChipRow hasHistory={hasHistory} />
      </div>

      {/* Trending cards */}
      <div className="mt-10">
        <TrendingCards />
      </div>
    </div>
  )
}
