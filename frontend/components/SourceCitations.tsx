'use client'

import { useState } from 'react'
import { ExternalLink } from 'lucide-react'

interface ReviewSourceItem {
  site_name: string
  url: string
  title: string
  snippet?: string
  rating?: number | null
  favicon_url?: string
  date?: string | null
}

interface ReviewProduct {
  name: string
  sources: ReviewSourceItem[]
}

interface SourceCitationsProps {
  data: {
    products: ReviewProduct[]
  }
  title?: string
}

const DOT_COLORS = ['#EF4444', '#3B82F6', '#22C55E', '#F97316']
const DOT_BG_CLASSES = ['bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-orange-500']

export default function SourceCitations({ data, title = 'Sources' }: SourceCitationsProps) {
  const [expanded, setExpanded] = useState(false)

  // Flatten all sources, deduplicate by URL
  const seen = new Set<string>()
  const allSources: ReviewSourceItem[] = []
  for (const product of data.products) {
    for (const source of product.sources) {
      if (!seen.has(source.url)) {
        seen.add(source.url)
        allSources.push(source)
      }
    }
  }

  if (allSources.length === 0) return null

  const visibleSources = expanded ? allSources : allSources.slice(0, 4)
  const hiddenCount = allSources.length - 4

  return (
    <div className="flex flex-col gap-1.5">
      {/* Header */}
      <p
        className="text-xs font-semibold uppercase tracking-wider mb-2"
        style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)' }}
      >
        {title}
      </p>

      {/* Citation rows */}
      {visibleSources.map((source, index) => (
        <a
          key={source.url}
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 group"
          style={{ textDecoration: 'none' }}
        >
          {/* Colored dot */}
          <span
            className={`w-2 h-2 rounded-full flex-shrink-0 ${DOT_BG_CLASSES[index % DOT_BG_CLASSES.length]}`}
            style={{ backgroundColor: DOT_COLORS[index % DOT_COLORS.length] }}
          />

          {/* Source name */}
          <span
            className="font-medium text-sm flex-shrink-0"
            style={{ color: 'var(--text-primary)' }}
          >
            {source.site_name}
          </span>

          {/* Article title */}
          <span
            className="text-xs truncate"
            style={{ color: 'var(--text-secondary)', maxWidth: '200px' }}
          >
            {source.title}
          </span>

          {/* External link icon */}
          <ExternalLink size={12} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
        </a>
      ))}

      {/* +X more toggle */}
      {!expanded && hiddenCount > 0 && (
        <button
          onClick={() => setExpanded(true)}
          className="text-xs text-left cursor-pointer mt-1"
          style={{ color: 'var(--primary)', background: 'none', border: 'none', padding: 0 }}
        >
          +{hiddenCount} more
        </button>
      )}
    </div>
  )
}
