'use client'

import { useMemo } from 'react'
import { ArrowUpRight, Bookmark, RefreshCw } from 'lucide-react'
import type { Message } from './ChatContainer'
import ResultsProductCard from './ResultsProductCard'
import { stripMarkdown } from '@/lib/stripMarkdown'

interface ResultsMainPanelProps {
  messages: Message[]
  sessionTitle: string
}

function extractProducts(messages: Message[]): any[] {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i]
    if (msg.role === 'assistant' && msg.ui_blocks) {
      const products: any[] = []
      for (const block of msg.ui_blocks) {
        const type = block.type || ''
        if (['inline_product_card', 'products', 'product_cards'].includes(type)) {
          const items = block.data?.products || block.products || (Array.isArray(block.data) ? block.data : [])
          products.push(...items)
        }
      }
      if (products.length > 0) return products
    }
  }
  return []
}

function extractSources(messages: Message[]): any[] {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i]
    if (msg.role === 'assistant' && msg.ui_blocks) {
      for (const block of msg.ui_blocks) {
        if (block.type === 'review_sources') {
          const reviewProducts = block.data?.products || []
          const sources: any[] = []
          for (const p of reviewProducts) {
            for (const s of (p.sources || [])) {
              if (s.url && !sources.find((x: any) => x.url === s.url)) {
                sources.push(s)
              }
            }
          }
          if (sources.length > 0) return sources
        }
      }
    }
  }
  return []
}

function extractSummary(messages: Message[]): string {
  const assistant = messages.find(m => m.role === 'assistant' && m.content)
  return assistant?.content || ''
}

const SOURCE_COLORS = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']

export default function ResultsMainPanel({ messages, sessionTitle }: ResultsMainPanelProps) {
  const products = useMemo(() => extractProducts(messages), [messages])
  const sources = useMemo(() => extractSources(messages), [messages])
  const summary = useMemo(() => extractSummary(messages), [messages])

  if (products.length === 0 && !summary) {
    return (
      <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>
        <p className="text-sm">Ask a question to see results here</p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div
        className="sticky top-0 z-10 flex items-center justify-between px-7 py-4 border-b"
        style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
      >
        <h2 className="font-serif text-xl font-normal italic" style={{ color: 'var(--text)' }}>
          {sessionTitle || 'Research Results'}
        </h2>
        <div className="flex gap-2">
          {[
            { icon: ArrowUpRight, label: 'Share' },
            { icon: Bookmark, label: 'Save' },
            { icon: RefreshCw, label: 'Refresh' },
          ].map(({ icon: Icon, label }) => (
            <button
              key={label}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors hover:bg-[var(--surface-hover)]"
              style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
            >
              <Icon size={14} /> {label}
            </button>
          ))}
        </div>
      </div>

      <div className="px-7 py-6 flex flex-col gap-5">
        {summary && (
          <p className="text-sm leading-relaxed max-w-[680px]" style={{ color: 'var(--text-secondary)' }}>
            {stripMarkdown(summary).slice(0, 500)}
          </p>
        )}

        {products.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {products.slice(0, 6).map((product: any, index: number) => (
              <ResultsProductCard
                key={(product.name || '') + index}
                product={{
                  name: product.name || product.title || '',
                  price: product.price || product.best_offer?.price,
                  url: product.url || product.best_offer?.url || product.affiliate_link,
                  image_url: product.image_url || product.best_offer?.image_url,
                  merchant: product.merchant || product.best_offer?.merchant,
                  description: product.description || product.snippet,
                }}
                index={index}
              />
            ))}
          </div>
        )}

        {sources.length > 0 && (
          <div className="mt-4">
            <h4 className="text-[11px] font-semibold uppercase tracking-[1.5px] mb-3" style={{ color: 'var(--text-muted)' }}>
              Sources Analyzed
            </h4>
            <div className="flex flex-col gap-2">
              {sources.slice(0, 8).map((source: any, idx: number) => (
                <a
                  key={source.url}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2.5 text-sm hover:underline transition-colors hover:text-[var(--primary)]"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: SOURCE_COLORS[idx % SOURCE_COLORS.length] }} />
                  <span className="font-medium" style={{ color: 'var(--text)' }}>{source.site_name}</span>
                  {source.title && <span className="text-xs truncate">— {source.title}</span>}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
