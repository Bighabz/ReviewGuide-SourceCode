'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Mic } from 'lucide-react'

export default function DiscoverSearchBar() {
  const router = useRouter()
  const [query, setQuery] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = query.trim()
    if (trimmed) {
      router.push(`/chat?q=${encodeURIComponent(trimmed)}&new=1`)
    } else {
      router.push('/chat?new=1')
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      data-testid="discover-search-bar"
      className="w-full flex items-center gap-3 px-4"
      style={{
        height: '52px',
        border: '2px solid var(--border-strong, #D4D1CC)',
        borderRadius: '14px',
        background: 'var(--surface)',
        boxShadow: '0 2px 8px rgba(26,24,22,0.08), 0 0 0 1px rgba(26,24,22,0.03)',
      }}
    >
      <Search
        size={18}
        style={{ color: 'var(--text-muted)', flexShrink: 0 }}
        aria-hidden="true"
      />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Best noise-cancelling headphones..."
        className="flex-1 text-sm bg-transparent outline-none min-w-0"
        style={{ color: 'var(--text)', caretColor: 'var(--primary)' }}
      />
      <button type="submit" className="flex-shrink-0" aria-label="Search">
        <Mic
          size={18}
          style={{ color: 'var(--primary)' }}
          aria-hidden="true"
        />
      </button>
    </form>
  )
}
