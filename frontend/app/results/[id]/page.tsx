'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import extractResultsData from '@/lib/extractResultsData'
import type { ResultsData } from '@/lib/extractResultsData'
import ResultsProductCard from '@/components/ResultsProductCard'
import ResultsQuickActions from '@/components/ResultsQuickActions'
import ResultsHeader from '@/components/ResultsHeader'

interface ResultsPageProps {
  params: { id: string }
}

function loadResultsData(): ResultsData | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem('chat_messages')
    if (!raw) return null
    const messages = JSON.parse(raw)
    return extractResultsData(messages)
  } catch {
    return null
  }
}

export default function ResultsPage({ params }: ResultsPageProps) {
  const router = useRouter()
  const sessionId = params.id

  // Load synchronously so tests (which don't wrap in act/waitFor) can access data
  const [resultsData] = useState<ResultsData | null>(() => loadResultsData())
  const [toast, setToast] = useState<string | null>(null)

  // Redirect to home if no data found
  useEffect(() => {
    if (resultsData === null) {
      router.replace('/')
    }
  }, [resultsData, router])

  function showToast(message: string) {
    setToast(message)
    setTimeout(() => setToast(null), 2500)
  }

  // Construct results URL with /results/ in it for clipboard sharing
  const resultsUrl =
    typeof window !== 'undefined'
      ? `${window.location.origin}/results/${sessionId}`
      : `/results/${sessionId}`

  if (!resultsData) {
    return null
  }

  const { sessionTitle, summaryText, products, sources } = resultsData

  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: 'var(--background)' }}
    >
      {/* Max-width content wrapper */}
      <div className="max-w-[1200px] mx-auto px-4 py-6">

        {/* Back to Chat link */}
        <Link
          href="/chat"
          className="inline-flex items-center gap-2 text-sm mb-4"
          style={{ color: 'var(--text-secondary)' }}
        >
          <ArrowLeft size={16} />
          <span>Back to Chat</span>
        </Link>

        {/* Results Header */}
        <ResultsHeader
          title={sessionTitle}
          summary={summaryText}
          sourceCount={sources.length}
          onToast={showToast}
        />

        {/* Quick Actions */}
        <div className="mt-6">
          <ResultsQuickActions onToast={showToast} shareUrl={resultsUrl} />
        </div>

        {/* Product grid — responsive: desktop 3-column grid, mobile horizontal scroll */}
        {products.length > 0 && (
          <div className="mt-6 overflow-x-auto snap-x snap-mandatory grid grid-cols-3 gap-4 pb-2">
            {products.map((product, index) => (
              <div
                key={product.name + index}
                className="snap-start min-w-[170px]"
              >
                <ResultsProductCard product={product} index={index} />
              </div>
            ))}
          </div>
        )}

        {/* Sources section */}
        {sources.length > 0 && (
          <div className="mt-8">
            <p
              className="text-[11px] font-medium uppercase tracking-[1.5px] mb-3"
              style={{ color: 'var(--text-muted)' }}
            >
              SOURCES ANALYZED
            </p>
            <div className="flex flex-col gap-2">
              {sources.map((source, idx) => {
                const DOT_COLORS = [
                  '#4285F4',
                  '#EA4335',
                  '#FBBC05',
                  '#34A853',
                  '#9C27B0',
                  '#FF5722',
                ]
                const dotColor = DOT_COLORS[idx % DOT_COLORS.length]
                return (
                  <a
                    key={source.url}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm"
                    style={{ color: 'var(--text)' }}
                  >
                    <span
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: dotColor }}
                    />
                    <span className="font-semibold">{source.site_name}</span>
                    {source.title && (
                      <span
                        className="text-xs truncate"
                        style={{ color: 'var(--text-secondary)' }}
                      >
                        — {source.title}
                      </span>
                    )}
                  </a>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div
          className="fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg text-sm font-medium text-white shadow-lg z-50"
          style={{ backgroundColor: 'var(--text)' }}
        >
          {toast}
        </div>
      )}
    </div>
  )
}
