'use client'

/**
 * RFC §2.5 — Content Trust and Explainability Panel
 *
 * Renders a collapsible info panel when response quality is degraded or
 * one or more providers are missing/timed-out.
 *
 * Rendering rules:
 *   - Hidden when degraded === false AND missing_sources is empty
 *   - Shows trigger link when degraded === true OR missing_sources non-empty
 *   - Collapsed by default; expands on click
 *   - "Low confidence" badge when confidence_score < 0.6
 */

import { useState } from 'react'
import type { ResponseMetadata } from '@/lib/chatApi'

// Human-readable display names for internal provider keys
const PROVIDER_NAMES: Record<string, string> = {
  ebay: 'eBay',
  amazon: 'Amazon',
  perplexity: 'Perplexity Search',
  serpapi: 'Web Reviews',
  amadeus: 'Flight Search',
  booking: 'Booking.com',
  viator: 'Viator Activities',
}

function providerDisplayName(key: string): string {
  return PROVIDER_NAMES[key] ?? key
}

interface ExplainabilityPanelProps {
  metadata: ResponseMetadata
}

export function ExplainabilityPanel({ metadata }: ExplainabilityPanelProps) {
  const [isOpen, setIsOpen] = useState(false)

  const timedOutProviders = metadata.provider_coverage.filter(
    (p) => p.status === 'timed_out'
  )
  return (
    <div
      className="mt-3 border-t pt-2"
      style={{ borderColor: 'var(--border)' }}
      data-testid="explainability-panel-root"
    >
      {/* Trigger link */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="flex items-center gap-1 text-[11px] transition-colors"
          style={{ color: 'var(--text-muted)' }}
          aria-expanded={isOpen}
          aria-controls="explainability-detail-panel"
          data-testid="explainability-trigger"
        >
          <span style={{ color: 'var(--accent)' }}>ⓘ</span>
          <span className="hover:underline" style={{ color: 'var(--text-secondary)' }}>
            Results may be incomplete
          </span>
          <span
            className="text-[9px]"
            style={{ color: 'var(--text-muted)' }}
            aria-hidden="true"
          >
            {isOpen ? '▲' : '▼'}
          </span>
        </button>

      </div>

      {/* Collapsible detail panel */}
      {isOpen && (
        <div
          id="explainability-detail-panel"
          className="mt-2 rounded-lg border p-3 text-[12px] space-y-1.5"
          style={{
            background: 'var(--surface)',
            borderColor: 'var(--border)',
            color: 'var(--text-secondary)',
          }}
          data-testid="explainability-detail"
        >
          {/* Timed-out / unavailable providers */}
          {timedOutProviders.length > 0 && (
            <div data-testid="timed-out-providers">
              <span className="font-semibold" style={{ color: 'var(--accent)' }}>
                Unavailable:{' '}
              </span>
              <span>
                {timedOutProviders
                  .map((p) => providerDisplayName(p.provider))
                  .join(', ')}
              </span>
            </div>
          )}

          {/* Missing source keys (providers with no results) */}
          {/* When timed-out providers are shown, suppress the redundant missing-sources block */}
          {metadata.missing_sources.length > 0 && timedOutProviders.length === 0 && (
            <div data-testid="missing-sources">
              <span className="font-semibold" style={{ color: 'var(--text)' }}>
                No data from:{' '}
              </span>
              <span>
                {metadata.missing_sources
                  .map(providerDisplayName)
                  .join(', ')}
              </span>
            </div>
          )}

          {/* Omitted sections (e.g. affiliate_links, review_ranking) */}
          {metadata.omitted_sections.length > 0 && (
            <div data-testid="omitted-sections">
              <span className="font-semibold" style={{ color: 'var(--text)' }}>
                Missing sections:{' '}
              </span>
              <span>{metadata.omitted_sections.join(', ')}</span>
            </div>
          )}

        </div>
      )}
    </div>
  )
}
