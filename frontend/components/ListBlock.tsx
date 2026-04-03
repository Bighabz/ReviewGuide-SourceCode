'use client'

import React from 'react'
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

const styleMap: Record<string, { bg: React.CSSProperties; text: React.CSSProperties; bullet: React.CSSProperties }> = {
  activities: {
    bg: { backgroundColor: 'color-mix(in srgb, var(--bold-blue) 10%, transparent)' },
    text: { color: 'var(--bold-blue)' },
    bullet: { backgroundColor: 'var(--bold-blue)' },
  },
  attractions: {
    bg: { backgroundColor: 'color-mix(in srgb, var(--bold-amber) 10%, transparent)' },
    text: { color: 'var(--bold-amber)' },
    bullet: { backgroundColor: 'var(--bold-amber)' },
  },
  restaurants: {
    bg: { backgroundColor: 'color-mix(in srgb, var(--bold-red) 10%, transparent)' },
    text: { color: 'var(--bold-red)' },
    bullet: { backgroundColor: 'var(--bold-red)' },
  },
}

export default function ListBlock({ title, items, type }: ListBlockProps) {
  const Icon = iconMap[type]
  const styles = styleMap[type]

  if (!items || items.length === 0) {
    return null
  }

  return (
    <div className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card transition-shadow hover:shadow-md">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2.5 rounded-lg" style={styles.bg}>
          <Icon size={20} style={styles.text} />
        </div>
        <h3 className="font-serif font-bold text-lg text-[var(--text)]">
          {title}
        </h3>
      </div>
      <ul className="space-y-3">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-start gap-3 text-[var(--text)]">
            <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={styles.bullet} />
            <span className="flex-1 text-base leading-relaxed opacity-90">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
