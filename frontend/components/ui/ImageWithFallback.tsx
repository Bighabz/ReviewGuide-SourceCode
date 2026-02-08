'use client'

import { useState } from 'react'
import { Package } from 'lucide-react'

interface ImageWithFallbackProps {
  src: string
  alt: string
  category?: string
  className?: string
}

const CATEGORY_PLACEHOLDERS: Record<string, string> = {
  electronics: '/placeholders/electronics.svg',
  travel: '/placeholders/travel.svg',
  gaming: '/placeholders/gaming.svg',
  home: '/placeholders/home.svg',
  fashion: '/placeholders/fashion.svg',
  beauty: '/placeholders/beauty.svg',
  sports: '/placeholders/sports.svg',
  default: '/placeholders/default.svg',
}

export function ImageWithFallback({ src, alt, category, className = '' }: ImageWithFallbackProps) {
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(true)

  const fallbackSrc = category
    ? CATEGORY_PLACEHOLDERS[category.toLowerCase()] || CATEGORY_PLACEHOLDERS.default
    : CATEGORY_PLACEHOLDERS.default

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-[var(--surface)] ${className}`}>
        <div className="text-center p-4">
          <Package size={32} className="mx-auto text-[var(--text-muted)] mb-2" />
          <span className="text-xs text-[var(--text-muted)]">{alt}</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      {loading && (
        <div className="absolute inset-0 bg-[var(--surface)] animate-pulse" />
      )}
      <img
        src={src}
        alt={alt}
        className={`w-full h-full object-cover ${loading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
        onLoad={() => setLoading(false)}
        onError={() => {
          setError(true)
          setLoading(false)
        }}
        loading="lazy"
      />
    </div>
  )
}
