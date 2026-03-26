'use client'

import { Award, ExternalLink } from 'lucide-react'

interface TopPickBlockProps {
    productName: string
    headline: string
    bestFor: string
    notFor: string
    imageUrl?: string
    affiliateUrl?: string
}

export default function TopPickBlock({
    productName,
    headline,
    bestFor,
    notFor,
    imageUrl,
    affiliateUrl,
}: TopPickBlockProps) {
    if (!productName) return null

    return (
        <div className="rounded-xl border-2 border-[var(--primary)] bg-[var(--surface-elevated)] p-5 mb-4 shadow-card">
            <div className="flex items-center gap-2 mb-3">
                <Award size={16} className="text-[var(--primary)]" />
                <span className="text-xs font-bold uppercase tracking-wider text-[var(--primary)]">
                    Our Top Pick
                </span>
            </div>

            <div className="flex gap-4">
                {imageUrl && (
                    <div className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden bg-[var(--surface)]">
                        <img
                            src={imageUrl}
                            alt={productName}
                            className="w-full h-full object-contain"
                            loading="lazy"
                        />
                    </div>
                )}
                <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-serif font-bold text-[var(--text)] mb-1">
                        {affiliateUrl ? (
                            <a
                                href={affiliateUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="hover:text-[var(--primary)] transition-colors inline-flex items-center gap-1.5"
                            >
                                {productName}
                                <ExternalLink size={14} className="opacity-50" />
                            </a>
                        ) : (
                            productName
                        )}
                    </h3>
                    {headline && (
                        <p className="text-sm text-[var(--text)] leading-relaxed mb-3">
                            {headline}
                        </p>
                    )}
                </div>
            </div>

            <div className="mt-3 space-y-1.5 text-sm">
                {bestFor && (
                    <p className="text-[var(--text-secondary)]">
                        <span className="font-semibold text-emerald-600 dark:text-emerald-400">Best for:</span>{' '}
                        {bestFor}
                    </p>
                )}
                {notFor && (
                    <p className="text-[var(--text-secondary)]">
                        <span className="font-semibold text-[var(--accent)]">Look elsewhere if:</span>{' '}
                        {notFor}
                    </p>
                )}
            </div>
        </div>
    )
}
