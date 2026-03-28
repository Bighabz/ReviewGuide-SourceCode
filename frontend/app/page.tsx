'use client'

import { useState } from 'react'
import DiscoverSearchBar from '@/components/discover/DiscoverSearchBar'
import TrendingCards from '@/components/discover/TrendingCards'
import CategoryChipRow from '@/components/discover/CategoryChipRow'
import CategorySidebar from '@/components/CategorySidebar'

export default function DiscoverPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <CategorySidebar isOpen={true} />
      </div>
      {/* Mobile sidebar overlay */}
      <div className="lg:hidden">
        <CategorySidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col px-4 sm:px-6 md:px-8 pb-20 md:pb-8">
        {/* Hero section */}
        <div className="flex flex-col items-center pt-8 sm:pt-12 pb-6">
          <h1
            className="font-serif text-[32px] sm:text-4xl md:text-5xl text-center leading-tight tracking-tight"
            style={{ color: 'var(--text)' }}
          >
            What are you{' '}
            <span className="italic" style={{ color: 'var(--primary)' }}>
              researching
            </span>
            {' '}today?
          </h1>
          <p
            className="text-sm text-center mt-2 max-w-md"
            style={{ color: 'var(--text-secondary)' }}
          >
            Expert reviews, real data, zero fluff.
          </p>
        </div>

        {/* Search bar — inline, not sticky */}
        <div className="w-full max-w-xl mx-auto">
          <DiscoverSearchBar />
        </div>

        {/* Category chips */}
        <div className="mt-4 max-w-xl mx-auto w-full">
          <CategoryChipRow />
        </div>

        {/* Trending Research */}
        <div className="mt-6 max-w-xl mx-auto w-full">
          <TrendingCards />
        </div>
      </div>
    </div>
  )
}
