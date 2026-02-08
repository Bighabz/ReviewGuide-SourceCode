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

// Keep semantic colors but use CSS variables for consistency where possible
// or cleaner classes. 
const colorMap = {
  activities: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-600 dark:text-blue-400',
    bullet: 'bg-blue-500',
  },
  attractions: {
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    text: 'text-amber-600 dark:text-amber-400',
    bullet: 'bg-amber-500',
  },
  restaurants: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-600 dark:text-red-400',
    bullet: 'bg-red-500',
  },
}

export default function ListBlock({ title, items, type }: ListBlockProps) {
  const Icon = iconMap[type]
  const colors = colorMap[type]

  if (!items || items.length === 0) {
    return null
  }

  return (
    <div className="p-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card transition-shadow hover:shadow-md">
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2.5 rounded-lg ${colors.bg}`}>
          <Icon size={20} className={colors.text} />
        </div>
        <h3 className="font-serif font-bold text-lg text-[var(--text)]">
          {title}
        </h3>
      </div>
      <ul className="space-y-3">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-start gap-3 text-[var(--text)]">
            <div className={`w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 ${colors.bullet}`} />
            <span className="flex-1 text-base leading-relaxed opacity-90">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
