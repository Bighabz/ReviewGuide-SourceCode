'use client'

import { useState } from 'react'
import DiscoverSearchBar from '@/components/discover/DiscoverSearchBar'
import ProductCarousel from '@/components/discover/ProductCarousel'
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

      {/* Main content — pt-16 on mobile clears the fixed h-14 header + breathing room */}
      <div className="flex-1 flex flex-col px-4 sm:px-6 md:px-8 pt-16 md:pt-0 pb-20 md:pb-8">
        {/* Hero section */}
        <div className="flex flex-col items-center pt-2 sm:pt-8 pb-4">
          <h1
            className="font-serif text-[28px] sm:text-4xl md:text-5xl text-center leading-tight tracking-tight animate-fade-up"
            style={{ color: 'var(--text)' }}
          >
            What are you{' '}
            <span className="italic" style={{ color: 'var(--primary)' }}>
              researching
            </span>
            {' '}today?
          </h1>
          <p
            className="text-sm sm:text-[15px] text-center mt-3 max-w-md leading-relaxed"
            style={{ color: 'var(--text-secondary)' }}
          >
            Expert reviews, real data, zero fluff.
          </p>
        </div>

        {/* Category chips */}
        <div className="mt-3 max-w-xl mx-auto w-full">
          <CategoryChipRow />
        </div>

        {/* Product Carousel */}
        <div className="mt-4 max-w-xl mx-auto w-full">
          <ProductCarousel />
        </div>

        {/* Search bar — below cards */}
        <div className="mt-4 w-full max-w-xl mx-auto">
          <DiscoverSearchBar />
        </div>
      </div>
    </div>
  )
}
