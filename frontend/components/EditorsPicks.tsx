'use client'

import { useState } from 'react'
import { ExternalLink, Package } from 'lucide-react'
import { curatedLinks } from '@/lib/curatedLinks'

interface EditorsPicksProps {
  categorySlug: string
}

function getImageUrl(asin: string): string {
  return `https://images-na.ssl-images-amazon.com/images/I/${asin}._SL300_.jpg`
}

function ProductImage({ asin, alt }: { asin: string; alt: string }) {
  const [errored, setErrored] = useState(false)

  if (errored) {
    return (
      <div className="aspect-square flex items-center justify-center rounded-lg bg-[var(--surface-hover)]">
        <Package size={24} style={{ color: 'var(--text-muted)' }} />
      </div>
    )
  }

  return (
    <img
      src={getImageUrl(asin)}
      alt={alt}
      loading="lazy"
      onError={() => setErrored(true)}
      className="aspect-square object-cover rounded-lg w-full"
    />
  )
}

export default function EditorsPicks({ categorySlug }: EditorsPicksProps) {
  const topics = curatedLinks[categorySlug]

  if (!topics || topics.length === 0) {
    return null
  }

  return (
    <section className="px-4 sm:px-6 md:px-8 py-8">
      {/* Heading with divider */}
      <div className="flex items-center gap-3 mb-5">
        <h2 className="font-serif text-xl text-[var(--text)] tracking-tight">
          Editor&apos;s Picks
        </h2>
        <div className="flex-1 h-px bg-[var(--border)]" />
      </div>

      {/* Topic groups */}
      <div className="space-y-6">
        {topics.map((topic, topicIdx) => (
          <div key={topicIdx}>
            <h3 className="font-serif text-base font-semibold text-[var(--text)]">
              {topic.title}
            </h3>
            <p className="text-sm text-[var(--text-secondary)] mt-1 mb-3">
              {topic.description}
            </p>

            {/* Product image grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {topic.products.map((product, idx) => (
                <a
                  key={idx}
                  href={product.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] overflow-hidden shadow-card product-card-hover"
                >
                  <ProductImage
                    asin={product.asin}
                    alt={`${topic.title} Option ${idx + 1}`}
                  />
                  <div className="flex items-center justify-between px-2 py-1.5">
                    <span className="text-xs text-[var(--text-secondary)]">
                      Option {idx + 1}
                    </span>
                    <ExternalLink
                      size={10}
                      className="opacity-60"
                      style={{ color: 'var(--text-secondary)' }}
                    />
                  </div>
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
