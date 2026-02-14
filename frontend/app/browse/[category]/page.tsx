'use client'

import React, { useState, useCallback } from 'react'
import { useRouter, notFound } from 'next/navigation'
import { ExternalLink, ArrowLeft } from 'lucide-react'
import ChatInput from '@/components/ChatInput'
import { categories } from '@/lib/categoryConfig'
import Link from 'next/link'

export default function CategoryPage({ params }: { params: { category: string } }) {
  const router = useRouter()
  const category = categories.find((c) => c.slug === params.category)
  const [input, setInput] = useState('')

  if (!category) return notFound()

  const handleSend = useCallback(() => {
    if (input.trim()) {
      router.push(`/chat?q=${encodeURIComponent(input.trim())}&new=1`)
    }
  }, [input, router])

  return (
    <div className="flex flex-col pb-16">
      {/* Back link */}
      <div className="px-4 sm:px-6 md:px-8 pt-4">
        <Link
          href="/browse"
          className="inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--text)] transition-colors"
        >
          <ArrowLeft size={14} />
          All Categories
        </Link>
      </div>

      {/* Hero */}
      <div className="relative h-56 sm:h-72 mx-4 sm:mx-6 md:mx-8 mt-4 rounded-xl overflow-hidden">
        <img
          src={category.image}
          alt={category.name}
          className="w-full h-full object-cover"
          onError={(e) => {
            const target = e.currentTarget
            target.style.display = 'none'
            target.parentElement!.classList.add(
              'bg-gradient-to-br',
              'from-[var(--surface)]',
              'to-[var(--surface-elevated)]'
            )
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-6 sm:p-8">
          <h1 className="font-serif text-3xl sm:text-4xl font-semibold text-white tracking-tight">
            {category.name}
          </h1>
          <p className="text-sm sm:text-base text-white/75 mt-1 max-w-md">
            {category.tagline}
          </p>
        </div>
      </div>

      {/* Search input */}
      <div className="w-full max-w-xl mx-auto mt-8 px-4">
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          disabled={false}
          placeholder={`Ask anything about ${category.name.toLowerCase()}...`}
        />
      </div>

      {/* Editorial rule */}
      <div className="editorial-rule mx-8 mt-8" />

      {/* Curated Queries */}
      <section className="px-4 sm:px-6 md:px-8 py-8">
        <div className="flex items-center gap-3 mb-5">
          <h2 className="font-serif text-xl text-[var(--text)] tracking-tight">
            Popular Questions
          </h2>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {category.queries.map((query, idx) => (
            <button
              key={idx}
              onClick={() =>
                router.push(`/chat?q=${encodeURIComponent(query)}&new=1`)
              }
              className="flex items-center justify-between gap-3 px-4 py-4 rounded-xl text-left text-sm text-[var(--text-secondary)] bg-[var(--surface-elevated)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] border border-[var(--border)] hover:border-[var(--border-strong)] transition-all group shadow-card"
            >
              <span className="leading-relaxed">{query}</span>
              <ExternalLink
                size={13}
                className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-[var(--text-muted)]"
              />
            </button>
          ))}
        </div>
      </section>

      {/* Other categories */}
      <section className="px-4 sm:px-6 md:px-8 pb-8">
        <div className="flex items-center gap-3 mb-5">
          <h2 className="font-serif text-xl text-[var(--text)] tracking-tight">
            Explore Other Categories
          </h2>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>

        <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
          {categories
            .filter((c) => c.slug !== category.slug)
            .map((c) => (
              <Link
                key={c.slug}
                href={`/browse/${c.slug}`}
                className="flex-shrink-0 rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] overflow-hidden w-[200px] product-card-hover group"
              >
                <div className="h-24 overflow-hidden">
                  <img
                    src={c.image}
                    alt={c.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none'
                    }}
                  />
                </div>
                <div className="p-3">
                  <p className="text-sm font-semibold text-[var(--text)] group-hover:text-[var(--primary)] transition-colors">
                    {c.name}
                  </p>
                  <p className="text-[11px] text-[var(--text-muted)] mt-0.5 line-clamp-1">
                    {c.tagline}
                  </p>
                </div>
              </Link>
            ))}
        </div>
      </section>
    </div>
  )
}
