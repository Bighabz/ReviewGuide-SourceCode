'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import UnifiedTopbar from '../UnifiedTopbar'
import CategorySidebar from '../CategorySidebar'

export default function BrowseLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleSearch = (query: string) => {
    router.push(`/chat?q=${encodeURIComponent(query)}&new=1`)
  }

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--text)]">
      {/* Unified Navigation */}
      <UnifiedTopbar
        onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        onSearch={handleSearch}
        onNewChat={() => router.push('/chat?new=1')}
        onHistoryClick={() => router.push('/chat')}
      />

      {/* Category Sidebar (desktop) */}
      <aside className="hidden lg:block fixed left-0 top-14 sm:top-16 bottom-0 w-56 z-30">
        <CategorySidebar />
      </aside>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <CategorySidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <main className="lg:ml-56 pt-14 sm:pt-16 min-h-[calc(100vh-4rem)]">
        {children}
      </main>
    </div>
  )
}

// Keep export for backward compatibility with any remaining imports
export interface FilterState {
  categories: string[]
  priceRange: [number, number] | null
  minRating: number | null
  sortBy: 'relevance' | 'price_low' | 'price_high' | 'rating' | 'reviews'
}

export function useFilters() {
  return {
    filters: {
      categories: [] as string[],
      priceRange: null as [number, number] | null,
      minRating: null as number | null,
      sortBy: 'relevance' as const,
    },
    setFilters: () => {},
    isHomepage: true,
    setIsHomepage: () => {},
  }
}
