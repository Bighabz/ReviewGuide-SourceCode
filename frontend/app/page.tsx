'use client'

import { useState, useEffect } from 'react'
import { getRecentSearches } from '@/lib/recentSearches'
import DiscoverSearchBar from '@/components/discover/DiscoverSearchBar'
import TrendingCards from '@/components/discover/TrendingCards'
import CategorySidebar from '@/components/CategorySidebar'

export default function DiscoverPage() {
  const [hasHistory, setHasHistory] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    setHasHistory(getRecentSearches().length > 0)
  }, [])

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      {/* Sidebar — same as chat page */}
      <div className="hidden lg:block">
        <CategorySidebar isOpen={true} />
      </div>
      {/* Mobile sidebar */}
      <div className="lg:hidden">
        <CategorySidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col pb-28 px-4 sm:px-6 md:px-8">
        {/* Hero section */}
        <div className="flex flex-col items-center pt-8 sm:pt-12 pb-8">
          <h1
            className="font-serif text-3xl sm:text-4xl md:text-5xl text-center leading-tight tracking-tight"
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
        </div>

        {/* Trending cards — category pills removed, they live in sidebar now */}
        <div className="mt-6">
          <TrendingCards />
        </div>
      </div>

      {/* Sticky bottom search bar */}
      <div className="fixed bottom-0 left-0 right-0 z-50 p-3 sm:p-4 lg:pl-56"
        style={{
          background: 'var(--surface-float)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderTop: '1px solid var(--border)',
        }}
      >
        <div className="max-w-xl mx-auto">
          <DiscoverSearchBar />
        </div>
      </div>
    </div>
  )
}
