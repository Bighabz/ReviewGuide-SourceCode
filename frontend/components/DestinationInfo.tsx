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
            <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
              <Cloud size={22} />
            </div>
            <div className="flex-1">
              <h4 className="font-serif font-bold text-base mb-1 text-[var(--text)]">
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
            <div className="p-3 rounded-xl bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">
              <Calendar size={22} />
            </div>
            <div className="flex-1">
              <h4 className="font-serif font-bold text-base mb-1 text-[var(--text)]">
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
            <div className="p-3 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
              <Lightbulb size={22} />
            </div>
            <div className="flex-1">
              <h4 className="font-serif font-bold text-base mb-3 text-[var(--text)]">
                Travel Tips
              </h4>
              <ul className="grid sm:grid-cols-2 gap-x-6 gap-y-2">
                {tips.map((tip, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-[var(--text-secondary)]">
                    <span className="text-emerald-500 font-bold mt-1">•</span>
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
            <div className="p-3 rounded-xl bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400">
              <Users size={22} />
            </div>
            <div className="flex-1">
              <h4 className="font-serif font-bold text-base mb-1 text-[var(--text)]">
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
