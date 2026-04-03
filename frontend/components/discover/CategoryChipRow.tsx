'use client'

import { useRouter } from 'next/navigation'

interface ChipConfig {
  label: string
  query?: string // if absent, navigates to /chat?new=1
  accentColor: string  // CSS variable reference for accent tinting
}

const CHIPS: ChipConfig[] = [
  { label: 'For You', accentColor: 'var(--primary)' },
  { label: 'Tech', query: 'Best noise-cancelling headphones', accentColor: 'var(--bold-blue)' },
  { label: 'Travel', query: 'Top all-inclusive resorts in the Caribbean', accentColor: 'var(--bold-amber)' },
  { label: 'Kitchen', query: 'Best kitchen appliances and gadgets', accentColor: 'var(--bold-green)' },
  { label: 'Fitness', query: 'Best hiking boots for beginners', accentColor: 'var(--accent)' },
  { label: 'Audio', query: 'Best wireless earbuds and headphones', accentColor: 'var(--bold-blue)' },
]

export default function CategoryChipRow() {
  const router = useRouter()

  function handleChipClick(chip: ChipConfig) {
    if (chip.query) {
      router.push(`/chat?q=${encodeURIComponent(chip.query)}&new=1`)
    } else {
      router.push('/chat?new=1')
    }
  }

  // First chip ("For You") always active per Figma
  const activeIndex = 0

  return (
    <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
      {CHIPS.map((chip, idx) => {
        const isActive = idx === activeIndex
        return (
          <button
            key={chip.label}
            onClick={() => handleChipClick(chip)}
            className="flex-shrink-0 focus-ring"
            style={{
              height: '44px',
              padding: '0 20px',
              borderRadius: '22px',
              background: isActive
                ? 'var(--primary)'
                : `color-mix(in srgb, ${chip.accentColor} 12%, var(--surface))`,
              border: isActive
                ? '1.5px solid var(--primary)'
                : `1.5px solid color-mix(in srgb, ${chip.accentColor} 35%, transparent)`,
              color: isActive ? '#fff' : chip.accentColor,
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease',
            }}
          >
            {chip.label}
          </button>
        )
      })}
    </div>
  )
}
