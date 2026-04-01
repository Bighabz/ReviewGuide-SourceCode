'use client'

import { useRouter } from 'next/navigation'

interface ChipConfig {
  label: string
  query?: string // if absent, navigates to /chat?new=1
}

const CHIPS: ChipConfig[] = [
  { label: 'For You' },
  { label: 'Tech', query: 'Best noise-cancelling headphones' },
  { label: 'Travel', query: 'Top all-inclusive resorts in the Caribbean' },
  { label: 'Kitchen', query: 'Best robot vacuums for pet hair' },
  { label: 'Fitness', query: 'Best hiking boots for beginners' },
  { label: 'Audio', query: 'Best wireless earbuds and headphones' },
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
              height: '38px',
              padding: '0 18px',
              borderRadius: '20px',
              background: isActive ? 'var(--primary)' : 'var(--surface)',
              border: isActive ? '1px solid var(--primary)' : '1.5px solid var(--border)',
              color: isActive ? '#fff' : 'var(--text)',
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
