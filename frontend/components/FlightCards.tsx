'use client'

import { Plane, Clock, ExternalLink, Search } from 'lucide-react'

// Traditional flight card with full details
interface FlightCard {
  type?: 'flight_card'
  carrier: string
  flight_number: string
  origin: string
  destination: string
  depart_time: string
  arrive_time: string
  duration_minutes: number
  stops: number
  price: number
  currency: string
  cabin_class: string
  deeplink: string
}

// PLP link - search results page link
interface FlightPLPLink {
  type: 'plp_link'
  provider: string
  origin: string
  destination: string
  search_url: string
  title: string
  departure_date?: string
  return_date?: string
  passengers?: number
}

type Flight = FlightCard | FlightPLPLink

interface FlightCardsProps {
  flights: Flight[]
  fullHeight?: boolean  // When true, card stretches to fill container height
}

// Type guard to check if flight is a PLP link
function isPLPLink(flight: Flight): flight is FlightPLPLink {
  return flight.type === 'plp_link'
}

// PLP Link Card Component
function PLPLinkCard({ flight, fullHeight = false }: { flight: FlightPLPLink; fullHeight?: boolean }) {
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

  const isRoundTrip = !!flight.return_date

  return (
    <a
      href={flight.search_url}
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
          {flight.title}
        </h4>

        {/* Route visualization */}
        <div className="flex items-center gap-3 mb-3">
          <span className="text-lg sm:text-xl font-bold" style={{ color: 'var(--gpt-text)' }}>
            {flight.origin}
          </span>
          <div className="flex items-center gap-1">
            <div className="w-8 sm:w-12 h-px" style={{ background: 'var(--gpt-border)' }}></div>
            <Plane size={16} className="sm:w-5 sm:h-5" style={{ color: 'var(--gpt-text-secondary)' }} />
            {isRoundTrip && (
              <>
                <div className="w-8 sm:w-12 h-px" style={{ background: 'var(--gpt-border)' }}></div>
                <Plane size={16} className="sm:w-5 sm:h-5 rotate-180" style={{ color: 'var(--gpt-text-secondary)' }} />
              </>
            )}
            <div className="w-8 sm:w-12 h-px" style={{ background: 'var(--gpt-border)' }}></div>
          </div>
          <span className="text-lg sm:text-xl font-bold" style={{ color: 'var(--gpt-text)' }}>
            {flight.destination}
          </span>
        </div>

        {/* Date info */}
        {flight.departure_date && (
          <p className="text-xs sm:text-sm mb-2" style={{ color: 'var(--gpt-text-secondary)' }}>
            {formatDate(flight.departure_date)}
            {flight.return_date && ` - ${formatDate(flight.return_date)}`}
          </p>
        )}

        {/* Passengers if available */}
        {flight.passengers && (
          <p className="text-xs mb-3" style={{ color: 'var(--gpt-text-secondary)' }}>
            {flight.passengers} passenger{flight.passengers > 1 ? 's' : ''}
          </p>
        )}

        {/* Provider badge */}
        <div className="text-xs px-3 py-1 rounded-full mb-4" style={{ background: 'var(--gpt-hover)', color: 'var(--gpt-text-secondary)' }}>
          Powered by {flight.provider.charAt(0).toUpperCase() + flight.provider.slice(1)}
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
          Search Flights on Expedia
          <ExternalLink size={16} />
        </button>
      </div>
    </a>
  )
}

// Traditional Flight Card Component
function TraditionalFlightCard({ flight }: { flight: FlightCard }) {
  const formatTime = (datetime: string) => {
    try {
      return new Date(datetime).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      })
    } catch {
      return datetime
    }
  }

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  return (
    <a
      href={flight.deeplink}
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
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 sm:gap-4">
        {/* Flight info */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="font-semibold text-sm sm:text-base" style={{ color: 'var(--gpt-text)' }}>{flight.carrier}</span>
            <span className="text-xs sm:text-sm" style={{ color: 'var(--gpt-text-secondary)' }}>{flight.flight_number}</span>
            <span className="text-xs px-2 py-0.5 sm:py-1 rounded-full" style={{ background: 'var(--gpt-hover)', color: 'var(--gpt-text)' }}>
              {flight.cabin_class}
            </span>
          </div>

          {/* Route and times */}
          <div className="flex items-center gap-2 sm:gap-4 text-xs sm:text-sm">
            <div className="text-center flex-shrink-0">
              <div className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--gpt-text)' }}>{flight.origin}</div>
              <div className="text-xs sm:text-sm" style={{ color: 'var(--gpt-text-secondary)' }}>{formatTime(flight.depart_time)}</div>
            </div>

            <div className="flex-1 flex flex-col items-center min-w-0">
              <div className="text-xs mb-1 flex items-center gap-1" style={{ color: 'var(--gpt-text-secondary)' }}>
                <Clock size={10} className="sm:w-3 sm:h-3" />
                <span className="whitespace-nowrap">{formatDuration(flight.duration_minutes)}</span>
              </div>
              <div className="w-full h-px relative" style={{ background: 'var(--gpt-border)' }}>
                <Plane size={14} className="sm:w-4 sm:h-4 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" style={{ background: 'var(--gpt-assistant-message)', color: 'var(--gpt-text-secondary)' }} />
              </div>
              <div className="text-xs mt-1 whitespace-nowrap" style={{ color: 'var(--gpt-text-secondary)' }}>
                {flight.stops === 0 ? 'Non-stop' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
              </div>
            </div>

            <div className="text-center flex-shrink-0">
              <div className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--gpt-text)' }}>{flight.destination}</div>
              <div className="text-xs sm:text-sm" style={{ color: 'var(--gpt-text-secondary)' }}>{formatTime(flight.arrive_time)}</div>
            </div>
          </div>
        </div>

        {/* Price and book button */}
        <div className="flex md:flex-col items-center md:items-end justify-between md:justify-center gap-3 sm:gap-4 pt-3 md:pt-0 border-t md:border-t-0 md:border-l md:pl-4" style={{ borderColor: 'var(--gpt-border)' }}>
          <div className="text-right">
            <div className="flex items-baseline gap-1 justify-end">
              <span className="text-base sm:text-lg font-bold" style={{ color: 'var(--gpt-text)' }}>
                {flight.currency}
              </span>
              <span className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--gpt-text)' }}>
                {flight.price?.toFixed(2) ?? '—'}
              </span>
            </div>
            <div className="text-xs" style={{ color: 'var(--gpt-text-secondary)' }}>total</div>
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

export default function FlightCards({ flights, fullHeight = false }: FlightCardsProps) {
  if (!flights || flights.length === 0) return null

  // Check if all flights are PLP links
  const allPLPLinks = flights.every(isPLPLink)

  return (
    <div className={`space-y-2 sm:space-y-3 ${fullHeight ? 'h-full flex flex-col' : ''}`}>
      <h3 className="text-base sm:text-lg font-semibold flex items-center gap-2" style={{ color: 'var(--gpt-text)' }}>
        <Plane size={18} className="sm:w-5 sm:h-5" />
        Flights
      </h3>

      {allPLPLinks ? (
        // PLP links - full width to fill container
        <div className={fullHeight ? 'flex-1 flex flex-col' : ''}>
          {flights.map((flight, idx) => (
            <PLPLinkCard key={idx} flight={flight as FlightPLPLink} fullHeight={fullHeight} />
          ))}
        </div>
      ) : (
        // List for traditional flight cards
        <div className="space-y-2 sm:space-y-3">
          {flights.map((flight, idx) => (
            isPLPLink(flight) ? (
              <PLPLinkCard key={idx} flight={flight} />
            ) : (
              <TraditionalFlightCard key={idx} flight={flight} />
            )
          ))}
        </div>
      )}
    </div>
  )
}
