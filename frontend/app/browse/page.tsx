'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ExternalLink } from 'lucide-react'
import ChatInput from '@/components/ChatInput'
import { categories } from '@/lib/categoryConfig'
import { getRecentSearches, RecentSearch } from '@/lib/recentSearches'

export default function BrowsePage() {
  const router = useRouter()
  const [heroInput, setHeroInput] = useState('')
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([])

  useEffect(() => {
    setRecentSearches(getRecentSearches())
  }, [])

  const handleHeroSend = useCallback(() => {
    if (heroInput.trim()) {
      router.push(`/chat?q=${encodeURIComponent(heroInput.trim())}&new=1`)
    } else {
      router.push('/chat?new=1')
    }
  }, [heroInput, router])

  return (
    <div className="flex flex-col pb-16">
      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center px-4 lg:pr-28 pb-10 sm:pb-14">
        <img
          src="/images/ezgif-7b66ba24abcfdab0.gif"
          alt="ReviewGuide.Ai"
          className="h-32 sm:h-44 md:h-56 w-auto mb-4"
        />
        <h1 className="font-serif text-2xl sm:text-3xl md:text-4xl text-center text-[var(--text)] leading-tight tracking-tight">
          What are you{' '}
          <span className="italic text-[var(--primary)]">researching</span>{' '}
          today?
        </h1>
        <p className="text-sm sm:text-base text-[var(--text-secondary)] text-center mt-3 max-w-md">
          AI-powered product reviews, travel planning, and price comparison — all in one conversation.
        </p>

        <div className="w-full max-w-xl mx-auto mt-8">
          <ChatInput
            value={heroInput}
            onChange={setHeroInput}
            onSend={handleHeroSend}
            disabled={false}
            placeholder="Ask anything — best headphones, Tokyo trip, laptop deals..."
          />
        </div>
      </div>

      {/* Recently Researched — only if populated */}
      {recentSearches.length > 0 && (
        <section className="px-4 sm:px-6 md:px-8 mb-10">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="font-serif text-xl text-[var(--text)] tracking-tight">
              Recently Researched
            </h2>
            <div className="flex-1 h-px bg-[var(--border)]" />
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
            {recentSearches.map((search, idx) => (
              <a
                key={idx}
                href={`/chat?q=${encodeURIComponent(search.query)}&new=1`}
                className="flex-shrink-0 rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4 w-[220px] product-card-hover group"
              >
                <p className="text-sm font-semibold text-[var(--text)] line-clamp-2 group-hover:text-[var(--primary)] transition-colors">
                  {search.query}
                </p>
                {search.productNames.length > 0 && (
                  <div className="mt-2 space-y-0.5">
                    {search.productNames.map((name, i) => (
                      <p
                        key={i}
                        className="text-[11px] text-[var(--text-muted)] truncate"
                      >
                        {name}
                      </p>
                    ))}
                  </div>
                )}
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Editorial rule separator */}
      <div className="editorial-rule mx-8" />

      {/* Category Cards */}
      <section className="px-4 sm:px-6 md:px-8 py-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((category) => (
            <div
              key={category.slug}
              id={`category-${category.slug}`}
              className="scroll-mt-24 rounded-xl border border-[var(--border)] overflow-hidden shadow-card group"
            >
              {/* Hero Image */}
              <div
                className="relative h-44 sm:h-48 bg-[var(--surface)] overflow-hidden cursor-pointer"
                onClick={() =>
                  router.push(`/chat?q=${encodeURIComponent(category.queries[0])}&new=1`)
                }
              >
                <img
                  src={category.image}
                  alt={category.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                  onError={(e) => {
                    // Fallback gradient if image missing
                    const target = e.currentTarget
                    target.style.display = 'none'
                    target.parentElement!.classList.add(
                      'bg-gradient-to-br',
                      'from-[var(--surface)]',
                      'to-[var(--surface-elevated)]'
                    )
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-5">
                  <h3 className="font-serif text-xl font-semibold text-white tracking-tight">
                    {category.name}
                  </h3>
                  <p className="text-sm text-white/75 mt-0.5">
                    {category.tagline}
                  </p>
                </div>
              </div>

              {/* Query Chips */}
              <div className="p-4 bg-[var(--surface-elevated)] space-y-2">
                {category.queries.map((query, qIdx) => (
                  <button
                    key={qIdx}
                    onClick={() =>
                      router.push(
                        `/chat?q=${encodeURIComponent(query)}&new=1`
                      )
                    }
                    className="w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg text-left text-sm text-[var(--text-secondary)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] border border-transparent hover:border-[var(--border)] transition-all group/chip"
                  >
                    <span className="line-clamp-1">{query}</span>
                    <ExternalLink
                      size={12}
                      className="flex-shrink-0 opacity-0 group-hover/chip:opacity-100 transition-opacity text-[var(--text-muted)]"
                    />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
