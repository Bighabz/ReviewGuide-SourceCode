'use client'

import { Cloud, Calendar, Lightbulb, Users } from 'lucide-react'

interface DestinationInfoProps {
  data: {
    weather?: string
    best_season?: string
    tips?: string[]
    local_customs?: string
  }
}

export default function DestinationInfo({ data }: DestinationInfoProps) {
  const { weather, best_season, tips, local_customs } = data

  return (
    <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
      {/* Weather */}
      {weather && (
        <div className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card transition-shadow hover:shadow-md">
          <div className="flex items-start gap-4">
            <div
              className="p-3 rounded-xl"
              style={{ backgroundColor: 'color-mix(in srgb, var(--bold-blue) 10%, transparent)', color: 'var(--bold-blue)' }}
            >
              <Cloud size={22} />
            </div>
            <div className="flex-1">
              <h4 className="font-sans font-bold text-[15px] text-[var(--text)] mb-1">
                Weather & Climate
              </h4>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {weather}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Best Season */}
      {best_season && (
        <div className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card transition-shadow hover:shadow-md">
          <div className="flex items-start gap-4">
            <div
              className="p-3 rounded-xl"
              style={{ backgroundColor: 'color-mix(in srgb, var(--bold-amber) 10%, transparent)', color: 'var(--bold-amber)' }}
            >
              <Calendar size={22} />
            </div>
            <div className="flex-1">
              <h4 className="font-sans font-bold text-[15px] text-[var(--text)] mb-1">
                Best Time to Visit
              </h4>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {best_season}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Travel Tips */}
      {tips && tips.length > 0 && (
        <div className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card transition-shadow hover:shadow-md sm:col-span-2">
          <div className="flex items-start gap-4">
            <div
              className="p-3 rounded-xl"
              style={{ backgroundColor: 'var(--success-light)', color: 'var(--bold-green)' }}
            >
              <Lightbulb size={22} />
            </div>
            <div className="flex-1">
              <h4 className="font-sans font-bold text-[15px] text-[var(--text)] mb-3">
                Travel Tips
              </h4>
              <ul className="grid sm:grid-cols-2 gap-x-6 gap-y-2">
                {tips.map((tip, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-[var(--text-secondary)]">
                    <span className="font-bold mt-1" style={{ color: 'var(--bold-green)' }}>•</span>
                    <span className="leading-snug">{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Local Customs */}
      {local_customs && (
        <div className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card transition-shadow hover:shadow-md sm:col-span-2">
          <div className="flex items-start gap-4">
            <div
              className="p-3 rounded-xl"
              style={{ backgroundColor: 'color-mix(in srgb, var(--secondary) 10%, transparent)', color: 'var(--secondary)' }}
            >
              <Users size={22} />
            </div>
            <div className="flex-1">
              <h4 className="font-sans font-bold text-[15px] text-[var(--text)] mb-1">
                Local Customs & Etiquette
              </h4>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {local_customs}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
