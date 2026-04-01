'use client'

import { useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { curatedLinks } from '@/lib/curatedLinks'

interface EditorsPicksProps {
  categorySlug: string
}

const IMAGE_URLS = [
  (asin: string) => `https://m.media-amazon.com/images/P/${asin}.01._SCLZZZZZZZ_SX300_.jpg`,
  (asin: string) => `https://images-na.ssl-images-amazon.com/images/P/${asin}.01._SCLZZZZZZZ_SL300_.jpg`,
]

function ProductImage({ asin, alt }: { asin: string; alt: string }) {
  const [urlIdx, setUrlIdx] = useState(0)
  const [allFailed, setAllFailed] = useState(false)

  if (allFailed) {
    return null
  }

  return (
    <img
      src={IMAGE_URLS[urlIdx](asin)}
      alt={alt}
      loading="lazy"
      onError={() => {
        if (urlIdx < IMAGE_URLS.length - 1) {
          setUrlIdx(urlIdx + 1)
        } else {
          setAllFailed(true)
        }
      }}
      className="aspect-[4/3] object-contain rounded-lg w-full bg-[var(--surface-hover)] p-2"
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

            {/* Product grid */}
            <div className="flex gap-3 overflow-x-auto pb-2">
              {topic.products.map((product, idx) => (
                <a
                  key={idx}
                  href={product.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-shrink-0 w-36 rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] overflow-hidden shadow-card product-card-hover"
                >
                  <ProductImage
                    asin={product.asin}
                    alt={`${topic.title} Option ${idx + 1}`}
                  />
                  <div className="flex items-center justify-between px-2.5 py-2">
                    <span className="text-xs font-medium text-[var(--text-secondary)]">
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
