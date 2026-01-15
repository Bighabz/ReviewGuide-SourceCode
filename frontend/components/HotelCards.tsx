'use client'

import { MapPin, Star, ExternalLink, Search } from 'lucide-react'

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
      className={`block border rounded-lg p-4 sm:p-6 transition-shadow ${fullHeight ? 'h-full' : ''}`}
      style={{ background: 'var(--gpt-assistant-message)', borderColor: 'var(--gpt-border)' }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = 'var(--gpt-shadow-lg)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      <div className={`flex flex-col items-center text-center ${fullHeight ? 'h-full justify-between' : ''}`}>
        {/* Search icon */}
        <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full flex items-center justify-center mb-3 sm:mb-4" style={{ background: 'var(--gpt-hover)' }}>
          <Search size={24} className="sm:w-8 sm:h-8" style={{ color: 'rgb(91, 124, 246)' }} />
        </div>

        {/* Title */}
        <h4 className="font-semibold text-base sm:text-lg mb-2" style={{ color: 'var(--gpt-text)' }}>
          {hotel.title}
        </h4>

        {/* Date range if available */}
        {(hotel.check_in || hotel.check_out) && (
          <p className="text-xs sm:text-sm mb-2" style={{ color: 'var(--gpt-text-secondary)' }}>
            {formatDate(hotel.check_in)} {hotel.check_out && `- ${formatDate(hotel.check_out)}`}
          </p>
        )}

        {/* Guests if available */}
        {hotel.guests && (
          <p className="text-xs mb-3" style={{ color: 'var(--gpt-text-secondary)' }}>
            {hotel.guests} guest{hotel.guests > 1 ? 's' : ''}
          </p>
        )}

        {/* Provider badge */}
        <div className="text-xs px-3 py-1 rounded-full mb-4" style={{ background: 'var(--gpt-hover)', color: 'var(--gpt-text-secondary)' }}>
          Powered by {hotel.provider.charAt(0).toUpperCase() + hotel.provider.slice(1)}
        </div>

        {/* CTA Button */}
        <button
          className="w-full px-4 py-2.5 sm:py-3 rounded-lg transition-colors flex items-center justify-center gap-2 text-sm sm:text-base font-medium"
          style={{ background: 'rgb(91, 124, 246)', color: 'white' }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgb(71, 104, 226)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgb(91, 124, 246)'
          }}
        >
          Search Hotels on Expedia
          <ExternalLink size={16} />
        </button>
      </div>
    </a>
  )
}

// Traditional Hotel Card Component
function TraditionalHotelCard({ hotel }: { hotel: HotelCard }) {
  return (
    <a
      href={hotel.deeplink}
      target="_blank"
      rel="noopener noreferrer"
      className="block border rounded-lg p-3 sm:p-4 transition-shadow"
      style={{ background: 'var(--gpt-assistant-message)', borderColor: 'var(--gpt-border)' }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = 'var(--gpt-shadow-lg)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      <div className="flex flex-col h-full">
        {/* Hotel name and rating */}
        <div className="flex justify-between items-start mb-2">
          <h4 className="font-semibold text-sm sm:text-base line-clamp-2 flex-1" style={{ color: 'var(--gpt-text)' }}>
            {hotel.name}
          </h4>
          {hotel.rating && (
            <div className="flex items-center gap-1 ml-2 flex-shrink-0">
              <Star size={12} className="sm:w-3.5 sm:h-3.5 fill-yellow-400 text-yellow-400" />
              <span className="text-xs sm:text-sm font-medium" style={{ color: 'var(--gpt-text)' }}>{hotel.rating}</span>
            </div>
          )}
        </div>

        {/* Location */}
        <p className="text-xs sm:text-sm mb-2 sm:mb-3" style={{ color: 'var(--gpt-text-secondary)' }}>
          {hotel.city}{hotel.country && `, ${hotel.country}`}
        </p>

        {/* Amenities */}
        {hotel.amenities && hotel.amenities.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2 sm:mb-3">
            {hotel.amenities.slice(0, 3).map((amenity, i) => (
              <span
                key={i}
                className="text-xs px-2 py-0.5 sm:py-1 rounded-full"
                style={{ background: 'var(--gpt-hover)', color: 'var(--gpt-text)' }}
              >
                {amenity}
              </span>
            ))}
            {hotel.amenities.length > 3 && (
              <span className="text-xs px-2 py-0.5 sm:py-1" style={{ color: 'var(--gpt-text-secondary)' }}>
                +{hotel.amenities.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Price and book button */}
        <div className="mt-auto pt-2 sm:pt-3 border-t flex justify-between items-center gap-3 sm:gap-4" style={{ borderColor: 'var(--gpt-border)' }}>
          <div>
            <div className="flex items-baseline gap-1">
              <span className="text-base sm:text-lg font-bold" style={{ color: 'var(--gpt-text)' }}>
                {hotel.currency}
              </span>
              <span className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--gpt-text)' }}>
                {hotel.price_nightly?.toFixed(2) ?? '—'}
              </span>
            </div>
            <div className="text-xs" style={{ color: 'var(--gpt-text-secondary)' }}>per night</div>
          </div>
          <button
            className="px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg transition-colors flex items-center gap-2 text-xs sm:text-sm whitespace-nowrap flex-shrink-0"
            style={{ background: 'rgb(91, 124, 246)', color: 'white' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgb(71, 104, 226)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgb(91, 124, 246)'
            }}
          >
            View Deal
            <ExternalLink size={12} className="sm:w-3.5 sm:h-3.5" />
          </button>
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
    <div className={`space-y-2 sm:space-y-3 ${fullHeight ? 'h-full flex flex-col' : ''}`}>
      <h3 className="text-base sm:text-lg font-semibold flex items-center gap-2" style={{ color: 'var(--gpt-text)' }}>
        <MapPin size={18} className="sm:w-5 sm:h-5" />
        Hotels
      </h3>

      {allPLPLinks ? (
        // PLP links - full width to fill container
        <div className={fullHeight ? 'flex-1 flex flex-col' : ''}>
          {hotels.map((hotel, idx) => (
            <PLPLinkCard key={idx} hotel={hotel as HotelPLPLink} fullHeight={fullHeight} />
          ))}
        </div>
      ) : (
        // Grid for traditional hotel cards
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
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
