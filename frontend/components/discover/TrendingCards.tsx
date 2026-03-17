'use client'

import { useRouter } from 'next/navigation'
import { ChevronRight, Headphones, Plane, Laptop2, Bot, Footprints, Speaker } from 'lucide-react'
import { trendingTopics } from '@/lib/trendingTopics'

const iconMap: Record<string, React.ComponentType<{ size?: number; color?: string; 'aria-hidden'?: string }>> = {
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
              className="product-card-hover w-full text-left"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '16px',
                borderRadius: '12px',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                cursor: 'pointer',
                minHeight: '72px',
              }}
            >
              {/* Icon circle */}
              <div
                aria-hidden="true"
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: topic.iconBg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
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
