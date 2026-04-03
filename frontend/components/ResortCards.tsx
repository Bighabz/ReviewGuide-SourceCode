'use client'

import { MapPin } from 'lucide-react'

interface ResortCardsProps {
  title?: string
  items: string[] // plain strings from backend: "Seven Mile Beach, Negril"
}

/**
 * Deterministic image map: lowercase name fragments → image paths.
 * Pre-populated with Caribbean-specific entries.
 * These will be upgraded to proper AI-generated images in Plan 03.
 */
const RESORT_IMAGE_MAP: Record<string, string> = {
  'seven mile': '/images/products/fallback-hotel.webp',
  "dunn": '/images/categories/cat-travel.webp',
  'blue mountain': '/images/categories/cat-travel.webp',
  'rick': '/images/products/fallback-hotel.webp',
  'negril': '/images/products/fallback-hotel.webp',
  'montego': '/images/categories/cat-travel.webp',
  'ocho rios': '/images/products/fallback-hotel.webp',
  'bob marley': '/images/categories/cat-travel.webp',
}

const FALLBACK_IMAGE = '/images/products/fallback-hotel.webp'

/**
 * Deterministic image lookup — NO Math.random().
 * Loops through RESORT_IMAGE_MAP keys and checks if the name contains the key.
 * Returns fallback image if no match found.
 */
function getResortImage(name: string): string {
  const lower = name.toLowerCase()
  for (const key of Object.keys(RESORT_IMAGE_MAP)) {
    if (lower.includes(key)) {
      return RESORT_IMAGE_MAP[key]
    }
  }
  return FALLBACK_IMAGE
}

/**
 * Extract a location hint from a comma-separated attraction name.
 * "Seven Mile Beach, Negril" → location = "Negril", name = "Seven Mile Beach"
 * "Dunn's River Falls" → no comma, location = null
 */
function parseName(fullName: string): { primary: string; location: string | null } {
  const commaIdx = fullName.indexOf(',')
  if (commaIdx === -1) {
    return { primary: fullName.trim(), location: null }
  }
  return {
    primary: fullName.slice(0, commaIdx).trim(),
    location: fullName.slice(commaIdx + 1).trim(),
  }
}

export default function ResortCards({ title = 'Must-See Attractions', items }: ResortCardsProps) {
  if (!items || items.length === 0) return null

  return (
    <section>
      {/* Section header with MapPin icon in amber-tinted pill — matches ListBlock attractions style */}
      <h3 className="font-sans font-bold text-lg sm:text-xl text-[var(--text)] flex items-center gap-2.5 mb-4">
        <span
          className="inline-flex items-center justify-center p-2.5 rounded-lg"
          style={{ backgroundColor: 'color-mix(in srgb, var(--bold-amber) 10%, transparent)' }}
        >
          <MapPin size={20} style={{ color: 'var(--bold-amber)' }} />
        </span>
        {title}
      </h3>

      {/* Card grid: 1-column mobile, 2-column sm+ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        {items.map((name, idx) => {
          const imageUrl = getResortImage(name)
          const { primary, location } = parseName(name)

          return (
            <div
              key={idx}
              className="border border-[var(--border)] rounded-xl overflow-clip bg-[var(--surface)] shadow-card product-card-hover transition-all"
            >
              {/* Hero image */}
              <div className="relative h-[140px] sm:h-[160px]">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={imageUrl}
                  alt=""
                  aria-hidden="true"
                  className="w-full h-full object-cover"
                  loading={idx === 0 ? 'eager' : 'lazy'}
                />
              </div>

              {/* Content */}
              <div className="p-4">
                <h4 className="font-sans font-bold text-base sm:text-lg text-[var(--text)] leading-tight line-clamp-2">
                  {primary}
                </h4>
                {location && (
                  <p className="mt-1 text-sm text-[var(--text-muted)] leading-snug">{location}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
