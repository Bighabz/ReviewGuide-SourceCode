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
    <div className="w-full space-y-4">
      {/* Weather */}
      {weather && (
        <div
          className="p-4 rounded-xl border"
          style={{
            background: 'var(--gpt-assistant-message)',
            borderColor: 'rgba(0,0,0,0.08)',
          }}
        >
          <div className="flex items-start gap-3">
            <div
              className="p-2 rounded-lg"
              style={{
                background: 'rgba(59, 130, 246, 0.1)',
              }}
            >
              <Cloud size={20} style={{ color: '#3b82f6' }} />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-sm mb-1" style={{ color: 'var(--gpt-text)' }}>
                Weather & Climate
              </h4>
              <p className="text-sm" style={{ color: 'var(--gpt-text-muted)' }}>
                {weather}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Best Season */}
      {best_season && (
        <div
          className="p-4 rounded-xl border"
          style={{
            background: 'var(--gpt-assistant-message)',
            borderColor: 'rgba(0,0,0,0.08)',
          }}
        >
          <div className="flex items-start gap-3">
            <div
              className="p-2 rounded-lg"
              style={{
                background: 'rgba(245, 158, 11, 0.1)',
              }}
            >
              <Calendar size={20} style={{ color: '#f59e0b' }} />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-sm mb-1" style={{ color: 'var(--gpt-text)' }}>
                Best Time to Visit
              </h4>
              <p className="text-sm" style={{ color: 'var(--gpt-text-muted)' }}>
                {best_season}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Travel Tips */}
      {tips && tips.length > 0 && (
        <div
          className="p-4 rounded-xl border"
          style={{
            background: 'var(--gpt-assistant-message)',
            borderColor: 'rgba(0,0,0,0.08)',
          }}
        >
          <div className="flex items-start gap-3">
            <div
              className="p-2 rounded-lg"
              style={{
                background: 'rgba(16, 185, 129, 0.1)',
              }}
            >
              <Lightbulb size={20} style={{ color: '#10b981' }} />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-sm mb-2" style={{ color: 'var(--gpt-text)' }}>
                Travel Tips
              </h4>
              <ul className="space-y-1.5">
                {tips.map((tip, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm" style={{ color: 'var(--gpt-text-muted)' }}>
                    <span className="text-green-500 font-bold mt-0.5">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Local Customs */}
      {local_customs && (
        <div
          className="p-4 rounded-xl border"
          style={{
            background: 'var(--gpt-assistant-message)',
            borderColor: 'rgba(0,0,0,0.08)',
          }}
        >
          <div className="flex items-start gap-3">
            <div
              className="p-2 rounded-lg"
              style={{
                background: 'rgba(139, 92, 246, 0.1)',
              }}
            >
              <Users size={20} style={{ color: '#8b5cf6' }} />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-sm mb-1" style={{ color: 'var(--gpt-text)' }}>
                Local Customs & Etiquette
              </h4>
              <p className="text-sm" style={{ color: 'var(--gpt-text-muted)' }}>
                {local_customs}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
