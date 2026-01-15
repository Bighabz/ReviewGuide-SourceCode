'use client'

import { Activity, MapPin, Utensils, LucideIcon } from 'lucide-react'

interface ListBlockProps {
  title: string
  items: string[]
  type: 'activities' | 'attractions' | 'restaurants'
}

const iconMap: Record<string, LucideIcon> = {
  activities: Activity,
  attractions: MapPin,
  restaurants: Utensils,
}

const colorMap = {
  activities: {
    iconBg: 'rgba(59, 130, 246, 0.1)',
    iconColor: '#3b82f6',
    bullet: '#3b82f6',
  },
  attractions: {
    iconBg: 'rgba(245, 158, 11, 0.1)',
    iconColor: '#f59e0b',
    bullet: '#f59e0b',
  },
  restaurants: {
    iconBg: 'rgba(239, 68, 68, 0.1)',
    iconColor: '#ef4444',
    bullet: '#ef4444',
  },
}

export default function ListBlock({ title, items, type }: ListBlockProps) {
  const Icon = iconMap[type]
  const colors = colorMap[type]

  if (!items || items.length === 0) {
    return null
  }

  return (
    <div
      className="p-4 sm:p-5 rounded-xl border"
      style={{
        background: 'var(--gpt-assistant-message)',
        borderColor: 'rgba(0,0,0,0.08)',
      }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div
          className="p-2 rounded-lg"
          style={{
            background: colors.iconBg,
          }}
        >
          <Icon size={20} style={{ color: colors.iconColor }} />
        </div>
        <h3 className="font-semibold text-base sm:text-lg" style={{ color: 'var(--gpt-text)' }}>
          {title}
        </h3>
      </div>
      <ul className="space-y-2.5">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-start gap-2.5 text-sm sm:text-base" style={{ color: 'var(--gpt-text)' }}>
            <span className="font-bold mt-1" style={{ color: colors.bullet }}>•</span>
            <span className="flex-1">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
