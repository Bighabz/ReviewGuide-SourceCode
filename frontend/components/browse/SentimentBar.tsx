
import React from 'react';

interface SentimentBarProps {
    positive: number;   // percentage
    neutral: number;
    negative: number;
    showLabels?: boolean;
    className?: string; // Allow overrides
}

export default function SentimentBar({ positive, neutral, negative, showLabels, className = '' }: SentimentBarProps) {
    // Normalize to ensure they sum to 100 roughly, though input should usually be correct.
    const total = positive + neutral + negative;
    const posPct = (positive / total) * 100;
    const neuPct = (neutral / total) * 100;
    const negPct = (negative / total) * 100;

    return (
        <div className={`w-full ${className}`}>
            <div className="flex h-1.5 w-full rounded-full overflow-hidden bg-[var(--surface-hover)]">
                <div
                    style={{ width: `${posPct}%`, backgroundColor: 'var(--bold-green)' }}
                />
                <div
                    style={{ width: `${neuPct}%` }}
                    className="bg-gray-400"
                />
                <div
                    style={{ width: `${negPct}%` }}
                    className="bg-rose-500"
                />
            </div>
            {showLabels && (
                <div className="flex justify-between text-[10px] sm:text-xs mt-1 text-[var(--text-muted)] font-medium">
                    <span style={{ color: 'var(--bold-green)' }}>{Math.round(posPct)}% Positive</span>
                    {negPct > 5 && <span style={{ color: 'var(--bold-red)' }}>{Math.round(negPct)}% Critiques</span>}
                </div>
            )}
        </div>
    );
}
