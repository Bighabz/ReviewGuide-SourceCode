
import React from 'react';
import SourceBadge from './SourceBadge';
import SentimentBar from './SentimentBar';
import { X } from 'lucide-react';

interface SourcesModalProps {
    isOpen: boolean;
    onClose: () => void;
    productTitle: string;
    sourceCount: number;
    totalReviews: number;
}

export default function SourcesModal({ isOpen, onClose, productTitle, sourceCount, totalReviews }: SourcesModalProps) {
    if (!isOpen) return null;

    // Mock source data for the modal since we just have aggregate data in the ProductItem currently
    const SOURCES = [
        { name: 'Reddit', type: 'Community', count: Math.floor(totalReviews * 0.4), positive: 85, neutral: 10, negative: 5 },
        { name: 'Amazon', type: 'Marketplace', count: Math.floor(totalReviews * 0.3), positive: 78, neutral: 15, negative: 7 },
        { name: 'YouTube', type: 'Video Reviews', count: Math.floor(totalReviews * 0.15), positive: 92, neutral: 5, negative: 3 },
        { name: 'TechRadar', type: 'Professional', count: Math.floor(totalReviews * 0.05), positive: 88, neutral: 8, negative: 4 },
    ];

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            <div className="relative bg-[var(--surface)] text-[var(--text)] rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-6 border-b border-[var(--border)] flex justify-between items-start">
                    <div>
                        <h2 className="text-xl font-bold">Review Sources</h2>
                        <p className="text-sm text-[var(--text-secondary)] mt-1">Data for {productTitle}</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-[var(--background)] rounded-full">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 max-h-[70vh] overflow-y-auto">
                    <div className="mb-6 p-4 bg-[var(--background)] rounded-xl border border-[var(--border)]">
                        <p className="text-base sm:text-lg">
                            We analyzed <strong>{totalReviews.toLocaleString()}</strong> reviews from <strong>{sourceCount}</strong> sources to form this recommendation.
                        </p>
                    </div>

                    <div className="space-y-4">
                        {SOURCES.map((source, i) => (
                            <div key={i} className="flex items-center justify-between p-3 sm:p-4 bg-[var(--background)] rounded-lg hover:bg-[var(--surface-hover)] transition-colors">
                                <div className="flex items-center gap-3">
                                    <SourceBadge source={source.name} />
                                    <div>
                                        <p className="font-medium text-sm sm:text-base">{source.name}</p>
                                        <p className="text-xs text-[var(--text-muted)]">{source.type}</p>
                                    </div>
                                </div>
                                <div className="flex flex-col items-end gap-1">
                                    <div className="text-right">
                                        <p className="font-bold text-sm">{source.count.toLocaleString()}</p>
                                        <p className="text-[10px] text-[var(--text-muted)]">reviews</p>
                                    </div>
                                    <div className="w-16">
                                        <SentimentBar positive={source.positive} neutral={source.neutral} negative={source.negative} />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <p className="text-xs text-[var(--text-muted)] mt-6 text-center">
                        Last updated: Today • Updates every 24 hours
                    </p>
                </div>
            </div>
        </div>
    );
}
