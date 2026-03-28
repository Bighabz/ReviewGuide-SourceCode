'use client'

import { useRouter } from 'next/navigation'
import { ChevronRight, Headphones, Plane, Laptop2, Bot, Footprints, Speaker, type LucideIcon } from 'lucide-react'
import { trendingTopics } from '@/lib/trendingTopics'

const iconMap: Record<string, LucideIcon> = {
  Headphones,
  Plane,
  Laptop2,
  Bot,
  Footprints,
  Speaker,
}

export default function TrendingCards() {
  const router = useRouter()

  return (
    <div>
      {/* Section header */}
      <p
        className="mb-4"
        style={{
          textTransform: 'uppercase',
          fontSize: '11px',
          fontWeight: 500,
          color: 'var(--text-muted)',
          letterSpacing: '1.5px',
        }}
      >
        Trending Research
      </p>

      {/* Cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {trendingTopics.map((topic) => {
          const IconComponent = iconMap[topic.icon]

          return (
            <button
              key={topic.id}
              data-testid="trending-card"
              onClick={() =>
                router.push(`/chat?q=${encodeURIComponent(topic.query)}&new=1`)
              }
              className="product-card-hover w-full text-left group"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                padding: '14px',
                borderRadius: '10px',
                background: 'var(--surface)',
                boxShadow: '0 1px 3px rgba(26,24,22,0.06), 0 4px 12px rgba(26,24,22,0.04)',
                cursor: 'pointer',
              }}
            >
              {/* Icon square — Figma: 56x56, rounded 12px, gradient bg */}
              <div
                aria-hidden="true"
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '12px',
                  background: topic.iconBg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  fontSize: '24px',
                }}
              >
                {IconComponent && (
                  <IconComponent
                    size={20}
                    color={topic.iconColor}
                    aria-hidden="true"
                  />
                )}
              </div>

              {/* Text */}
              <div className="flex-1 min-w-0">
                <p
                  style={{
                    fontSize: '15px',
                    fontWeight: 600,
                    color: 'var(--text)',
                    lineHeight: '1.3',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {topic.title}
                </p>
                <p
                  style={{
                    fontSize: '13px',
                    fontWeight: 400,
                    color: 'var(--text-secondary)',
                    lineHeight: '1.4',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {topic.subtitle}
                </p>
              </div>

              {/* Chevron */}
              <ChevronRight
                size={16}
                aria-hidden="true"
                className="transition-transform duration-200 group-hover:translate-x-1"
                style={{ color: 'var(--text-muted)', flexShrink: 0 }}
              />
            </button>
          )
        })}
      </div>

      {/* See more */}
      <button
        onClick={() => router.push('/chat?new=1')}
        className="mt-4 text-sm"
        style={{ color: 'var(--text-secondary)', background: 'none', border: 'none', cursor: 'pointer' }}
      >
        See more topics &rarr;
      </button>
    </div>
  )
}
