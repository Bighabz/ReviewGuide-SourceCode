
import React from 'react';

// Different colors per source as requested
const SOURCE_COLORS: Record<string, { bg: string; text: string }> = {
    'Reddit': { bg: '#FF4500', text: 'white' },
    'Amazon': { bg: '#FF9900', text: 'black' },
    'YouTube': { bg: '#FF0000', text: 'white' },
    'Twitter': { bg: '#1DA1F2', text: 'white' },
    'Forums': { bg: '#6B7280', text: 'white' },
    // Fallback
    'default': { bg: '#6B7280', text: 'white' }
};

interface SourceBadgeProps {
    source: string;
    className?: string;
}

export default function SourceBadge({ source, className = '' }: SourceBadgeProps) {
    const colors = SOURCE_COLORS[source] || SOURCE_COLORS['default'];

    return (
        <span
            className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold shadow-sm ${className}`}
            style={{ backgroundColor: colors.bg, color: colors.text }}
        >
            {source}
        </span>
    );
}
