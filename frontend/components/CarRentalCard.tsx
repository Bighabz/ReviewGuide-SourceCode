'use client'

import { Car, ExternalLink, Search, Calendar } from 'lucide-react'

interface CarRental {
  type: 'plp_link'
  provider: string
  location: string
  search_url: string
  title: string
  pickup_date?: string
  dropoff_date?: string
}

interface CarRentalCardProps {
  cars: CarRental[]
}

function formatDate(dateStr?: string) {
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

export default function CarRentalCard({ cars }: CarRentalCardProps) {
  if (!cars || cars.length === 0) return null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h3 className="font-serif text-2xl text-[var(--text)] flex items-center gap-3">
            <Car size={24} strokeWidth={1.5} className="text-[var(--primary)]" />
            Rental Cars
          </h3>
          <div className="h-[1px] bg-[var(--border)] mt-3"></div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {cars.map((car, idx) => (
          <a
            key={idx}
            href={car.search_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block bg-[var(--surface)] border border-[var(--border)] rounded-xl p-8 transition-all shadow-card hover:shadow-card-hover product-card-hover"
          >
            <div className="flex flex-col items-center text-center">
              {/* Search icon */}
              <div className="w-16 h-16 rounded-full flex items-center justify-center mb-5 bg-[var(--primary-light)]">
                <Search size={28} strokeWidth={1.5} className="text-[var(--primary)]" />
              </div>

              {/* Title */}
              <h4 className="font-serif text-xl mb-3 text-[var(--text)]">
                {car.title}
              </h4>

              {/* Location */}
              <p className="text-base font-bold tracking-wider mb-4 text-[var(--text)]">
                {car.location}
              </p>

              {/* Date info */}
              {car.pickup_date && (
                <div className="flex items-center gap-2 mb-2 text-sm text-[var(--text-secondary)]">
                  <Calendar size={14} strokeWidth={1.5} />
                  <span>
                    {formatDate(car.pickup_date)}
                    {car.dropoff_date && ` — ${formatDate(car.dropoff_date)}`}
                  </span>
                </div>
              )}

              {/* Provider badge */}
              <div className="text-xs font-medium px-3 py-1.5 rounded-full mb-6 bg-[var(--surface-strong)] text-[var(--text-muted)] border border-[var(--border)]">
                Powered by {car.provider.charAt(0).toUpperCase() + car.provider.slice(1)}
              </div>

              {/* CTA Button */}
              <button
                className="w-full px-6 py-3 bg-[var(--primary)] text-white rounded-lg transition-all flex items-center justify-center gap-2 text-base font-medium hover:opacity-90"
              >
                Search Rental Cars
                <ExternalLink size={16} strokeWidth={1.5} />
              </button>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}
