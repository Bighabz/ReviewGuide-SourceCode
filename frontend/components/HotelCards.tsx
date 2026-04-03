'use client'

import { MapPin, Star, ExternalLink, Hotel as HotelIcon } from 'lucide-react'
import { trackAffiliateClick } from '@/lib/trackAffiliate'

// Traditional hotel card with full details
interface HotelCard {
  type?: 'hotel_card'
  name: string
  city: string
  country: string
  price_nightly: number
  currency: string
  rating?: number
  amenities?: string[]
  deeplink: string
  thumbnail_url?: string
}

// PLP link - search results page link
interface HotelPLPLink {
  type: 'plp_link'
  provider: string
  destination: string
  search_url: string
  title: string
  check_in?: string
  check_out?: string
  guests?: number
}

type Hotel = HotelCard | HotelPLPLink

interface HotelCardsProps {
  hotels: Hotel[]
  fullHeight?: boolean  // When true, card stretches to fill container height
}

// Type guard to check if hotel is a PLP link
function isPLPLink(hotel: Hotel): hotel is HotelPLPLink {
  return hotel.type === 'plp_link'
}

// PLP Link Card Component
function PLPLinkCard({ hotel, fullHeight = false }: { hotel: HotelPLPLink; fullHeight?: boolean }) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  return (
    <a
      href={hotel.search_url}
      target="_blank"
      rel="noopener noreferrer"
      className={`block border border-[var(--border)] rounded-xl p-0 overflow-clip transition-all bg-[var(--surface)] hover:shadow-card-hover product-card-hover ${fullHeight ? 'h-full flex flex-col' : ''}`}
      onClick={(e) => {
        e.preventDefault()
        trackAffiliateClick({
          provider: hotel.provider || 'hotel',
          product_name: hotel.title,
          category: 'hotel',
          url: hotel.search_url,
        })
      }}
    >
      {/* Hero image */}
      <div className="relative h-[120px] sm:h-[140px] overflow-clip">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/images/products/fallback-hotel.webp" alt="" aria-hidden="true" className="w-full h-full object-cover" loading="lazy" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
      </div>

      <div className={`flex flex-col p-5 ${fullHeight ? 'flex-1 justify-between' : ''}`}>
        {/* Title */}
        <h4 className="font-sans font-bold text-lg sm:text-xl mb-3 text-[var(--text)]">
          {hotel.title}
        </h4>

        {/* Date range if available */}
        {(hotel.check_in || hotel.check_out) && (
          <p className="text-sm mb-2 text-[var(--text-secondary)]">
            {formatDate(hotel.check_in)} {hotel.check_out && `- ${formatDate(hotel.check_out)}`}
          </p>
        )}

        {/* Guests if available */}
        {hotel.guests && (
          <p className="text-sm mb-5 text-[var(--text-secondary)]">
            {hotel.guests} guest{hotel.guests > 1 ? 's' : ''}
          </p>
        )}

        {/* Provider badge */}
        <div className="text-[10px] px-2 py-1 rounded-full mb-4 opacity-60 bg-[var(--surface)] text-[var(--text-muted)] border border-[var(--border)]">
          Powered by {hotel.provider.charAt(0).toUpperCase() + hotel.provider.slice(1)}
        </div>

        {/* CTA Button */}
        <button
          className="w-full px-5 py-3 rounded-lg transition-all flex items-center justify-center gap-2 text-base font-medium bg-[var(--primary)] text-white hover:shadow-card-hover"
        >
          Search on Expedia
          <ExternalLink size={16} strokeWidth={1.5} />
        </button>
      </div>
    </a>
  )
}

// Traditional Hotel Card Component - Booking.com Style (Horizontal)
function TraditionalHotelCard({ hotel }: { hotel: HotelCard }) {
  return (
    <a
      href={hotel.deeplink}
      target="_blank"
      rel="noopener noreferrer"
      className="block border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--surface)] shadow-card hover:shadow-card-hover transition-all product-card-hover group"
      onClick={(e) => {
        e.preventDefault()
        trackAffiliateClick({
          provider: 'hotel',
          product_name: hotel.name,
          category: 'hotel',
          url: hotel.deeplink,
        })
      }}
    >
      <div className="flex flex-col sm:flex-row h-full">
        {/* Image Section (Left) */}
        <div className="relative w-full sm:w-56 h-48 sm:h-auto shrink-0 bg-[var(--background)]">
          {hotel.thumbnail_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={hotel.thumbnail_url}
              alt={hotel.name}
              className="w-full h-full object-cover"
            />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img src="/images/products/fallback-hotel.webp" alt="Hotel" className="w-full h-full object-cover" />
          )}
          {/* Rating Badge Overlay */}
          {hotel.rating && (
            <div className="absolute top-3 right-3 sm:left-3 sm:right-auto text-white text-sm font-semibold px-2.5 py-1.5 rounded-md shadow-card" style={{ backgroundColor: '#E5A100' }}>
              {hotel.rating}
            </div>
          )}
        </div>

        {/* Content Section (Right) */}
        <div className="flex-1 p-5 flex flex-col">
          {/* Header */}
          <div className="flex justify-between items-start mb-2">
            <div className="flex-1">
              <h4 className="font-sans font-bold text-lg text-[var(--text)] line-clamp-2 leading-tight group-hover:text-[var(--primary)] transition-colors">
                {hotel.name}
              </h4>
              <div className="flex items-center gap-1.5 mt-1.5 text-sm text-[var(--text-secondary)]">
                <MapPin size={14} strokeWidth={1.5} className="text-[var(--text-muted)]" />
                <span className="line-clamp-1">{hotel.city}, {hotel.country}</span>
              </div>
            </div>
          </div>

          {/* Amenities */}
          {hotel.amenities && hotel.amenities.length > 0 && (
            <div className="flex flex-wrap gap-2 my-4">
              {hotel.amenities.slice(0, 3).map((amenity, i) => (
                <span
                  key={i}
                  className="text-xs px-2.5 py-1 rounded border border-[var(--border)] text-[var(--text-secondary)] bg-[var(--background)]"
                >
                  {amenity}
                </span>
              ))}
              {hotel.amenities.length > 3 && (
                <span className="text-xs px-2 py-1 text-[var(--text-muted)]">
                  +{hotel.amenities.length - 3}
                </span>
              )}
            </div>
          )}

          <div className="mt-auto pt-4 flex items-end justify-between gap-4 border-t border-[var(--border)]">
            {/* Price section */}
            <div className="flex flex-col items-start text-left">
              <span className="text-xs text-[var(--text-muted)] mb-0.5">per night</span>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-[var(--text)]">{hotel.currency} {hotel.price_nightly?.toFixed(0)}</span>
              </div>
            </div>

            {/* Action Button */}
            <div className="hidden sm:flex items-center gap-1.5 text-sm font-medium text-[var(--primary)]">
              See availability
              <ExternalLink size={14} strokeWidth={1.5} />
            </div>
          </div>
        </div>
      </div>
    </a>
  )
}

export default function HotelCards({ hotels, fullHeight = false }: HotelCardsProps) {
  if (!hotels || hotels.length === 0) return null

  // Check if all hotels are PLP links
  const allPLPLinks = hotels.every(isPLPLink)

  return (
    <div className={`space-y-5 ${fullHeight ? 'h-full flex flex-col' : ''}`}>
      {/* Section title with editorial rule */}
      <div className="space-y-3">
        <h3 className="font-sans font-bold text-xl flex items-center gap-2.5 text-[var(--text)]">
          <HotelIcon size={22} strokeWidth={1.5} className="text-[var(--primary)]" />
          Recommended Hotels
        </h3>
        <div className="h-px bg-[var(--border)]"></div>
      </div>

      {/* Count badge for non-PLP results */}
      {!allPLPLinks && (
        <div className="flex justify-end">
          <span className="text-xs font-medium px-3 py-1.5 rounded-full bg-[var(--surface)] text-[var(--text-secondary)] border border-[var(--border)]">
            {hotels.length} options
          </span>
        </div>
      )}

      {allPLPLinks ? (
        // PLP links - grid
        <div className={`grid grid-cols-1 gap-5 ${fullHeight ? 'flex-1' : ''}`}>
          {hotels.map((hotel, idx) => (
            <PLPLinkCard key={idx} hotel={hotel as HotelPLPLink} fullHeight={fullHeight} />
          ))}
        </div>
      ) : (
        // List layout for traditional cards (better for details)
        <div className="flex flex-col gap-5">
          {hotels.map((hotel, idx) => (
            isPLPLink(hotel) ? (
              <PLPLinkCard key={idx} hotel={hotel} />
            ) : (
              <TraditionalHotelCard key={idx} hotel={hotel} />
            )
          ))}
        </div>
      )}
    </div>
  )
}
