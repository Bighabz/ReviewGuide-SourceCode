'use client';

import React, { useState } from 'react';

// Category-specific source mappings as requested
const CATEGORY_SOURCES: Record<string, string[]> = {
    'Electronics': ['Amazon', 'Reddit', 'YouTube', 'BestBuy'],
    'Smartphones': ['Amazon', 'Reddit', 'YouTube', 'BestBuy'],
    'Headphones': ['Amazon', 'Reddit', 'YouTube', 'BestBuy'],
    'Laptops': ['Amazon', 'Reddit', 'YouTube', 'BestBuy'],
    'Tablets': ['Amazon', 'Reddit', 'YouTube', 'BestBuy'],
    'Gaming': ['Reddit', 'YouTube', 'Steam', 'IGN'],
    'Games': ['Reddit', 'YouTube', 'Steam', 'IGN'],
    'PCs': ['Reddit', 'YouTube', 'Amazon', 'BestBuy'],
    'Travel': ['TripAdvisor', 'Google', 'Expedia', 'Booking'],
    'Hotels': ['TripAdvisor', 'Google', 'Expedia', 'Booking'],
    'Flights': ['Google', 'Expedia', 'Kayak', 'Skyscanner'],
    'Destinations': ['TripAdvisor', 'Google', 'Reddit', 'YouTube'],
    'Beauty': ['TikTok', 'Sephora', 'Instagram', 'YouTube'],
    'Skincare': ['TikTok', 'Sephora', 'Instagram', 'Reddit'],
    'Tools': ['Amazon', 'YouTube', 'Reddit', 'TikTok'],
    'Fashion': ['Instagram', 'TikTok', 'Reddit', 'Amazon'],
    'Sneakers': ['Instagram', 'Reddit', 'StockX', 'YouTube'],
    'Home': ['Amazon', 'Reddit', 'YouTube', 'Wirecutter'],
    'Kitchen': ['Amazon', 'Reddit', 'YouTube', 'Wirecutter'],
    'Sports': ['Amazon', 'Reddit', 'YouTube', 'REI'],
    'Equipment': ['Amazon', 'Reddit', 'YouTube', 'REI'],
    'Baby': ['Amazon', 'Reddit', 'BabyCenter', 'YouTube'],
    'Gear': ['Amazon', 'Reddit', 'BabyCenter', 'Wirecutter'],
    'Feeding': ['Amazon', 'Reddit', 'BabyCenter', 'YouTube'],
    'Sleep': ['Amazon', 'Reddit', 'BabyCenter', 'YouTube'],
    'Strollers': ['Amazon', 'Reddit', 'BabyCenter', 'Wirecutter'],
    'Monitors': ['Amazon', 'Reddit', 'BabyCenter', 'Wirecutter'],
    'Pet': ['Amazon', 'Reddit', 'Chewy', 'YouTube'],
    'Toys': ['Amazon', 'Reddit', 'Chewy', 'YouTube'],
    'Grooming': ['Amazon', 'Reddit', 'Chewy', 'YouTube'],
    'Water': ['Amazon', 'Reddit', 'Chewy', 'YouTube'],
    'Cleaning': ['Amazon', 'Reddit', 'YouTube', 'Wirecutter'],
    'Vacuums': ['Amazon', 'Reddit', 'YouTube', 'Wirecutter'],
    'Robot Vacuums': ['Amazon', 'Reddit', 'YouTube', 'Wirecutter'],
    'Wet/Dry': ['Amazon', 'Reddit', 'YouTube', 'Wirecutter'],
    'Mops': ['Amazon', 'Reddit', 'YouTube', 'Wirecutter'],
    'Smart Mops': ['Amazon', 'Reddit', 'YouTube', 'Wirecutter'],
};

// Source logo colors and initials
const SOURCE_CONFIG: Record<string, { bg: string; text: string; initial: string }> = {
    'Amazon': { bg: '#FF9900', text: '#000', initial: 'A' },
    'Reddit': { bg: '#FF4500', text: '#FFF', initial: 'R' },
    'YouTube': { bg: '#FF0000', text: '#FFF', initial: 'Y' },
    'BestBuy': { bg: '#0046BE', text: '#FFF', initial: 'BB' },
    'TripAdvisor': { bg: '#34E0A1', text: '#000', initial: 'TA' },
    'Google': { bg: '#4285F4', text: '#FFF', initial: 'G' },
    'Expedia': { bg: '#00355F', text: '#FFC72C', initial: 'E' },
    'Booking': { bg: '#003580', text: '#FFF', initial: 'B' },
    'Kayak': { bg: '#FF690F', text: '#FFF', initial: 'K' },
    'Skyscanner': { bg: '#0770E3', text: '#FFF', initial: 'S' },
    'TikTok': { bg: '#000000', text: '#FFF', initial: 'TT' },
    'Sephora': { bg: '#000000', text: '#FFF', initial: 'S' },
    'Instagram': { bg: '#E1306C', text: '#FFF', initial: 'IG' },
    'Steam': { bg: '#1B2838', text: '#FFF', initial: 'S' },
    'IGN': { bg: '#BF1313', text: '#FFF', initial: 'IGN' },
    'StockX': { bg: '#006340', text: '#FFF', initial: 'SX' },
    'Wirecutter': { bg: '#E53935', text: '#FFF', initial: 'W' },
    'REI': { bg: '#000000', text: '#FFF', initial: 'REI' },
    'BabyCenter': { bg: '#7B3F98', text: '#FFF', initial: 'BC' },
    'Chewy': { bg: '#1C49C2', text: '#FFF', initial: 'C' },
};

const DEFAULT_SOURCES = ['Amazon', 'Reddit', 'YouTube', 'Forums'];

interface SourceStackProps {
    category?: string;
    subcategory?: string;
    sourceCount?: number;
    className?: string;
}

export default function SourceStack({ category, subcategory, sourceCount = 47, className = '' }: SourceStackProps) {
    const [showTooltip, setShowTooltip] = useState(false);

    // Get sources based on subcategory first, then category, then default
    const sources = CATEGORY_SOURCES[subcategory || '']
        || CATEGORY_SOURCES[category || '']
        || DEFAULT_SOURCES;

    // Take first 4 sources for the stack
    const displaySources = sources.slice(0, 4);

    return (
        <div
            className={`relative inline-flex items-center ${className}`}
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
        >
            {/* Stacked source logos */}
            <div className="flex -space-x-1.5">
                {displaySources.map((source, index) => {
                    const config = SOURCE_CONFIG[source] || { bg: '#6B7280', text: '#FFF', initial: source[0] };
                    return (
                        <div
                            key={source}
                            className="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold border-2 border-[var(--card-bg)] shadow-sm"
                            style={{
                                backgroundColor: config.bg,
                                color: config.text,
                                zIndex: displaySources.length - index
                            }}
                            title={source}
                        >
                            {config.initial.length > 2 ? config.initial[0] : config.initial}
                        </div>
                    );
                })}
            </div>

            {/* +More indicator */}
            <span className="ml-1.5 text-[10px] text-[var(--text-muted)] font-medium">
                +{sourceCount}
            </span>

            {/* Tooltip */}
            {showTooltip && (
                <div className="absolute bottom-full left-0 mb-2 px-2 py-1 bg-[var(--surface)] border border-[var(--border)] rounded-md shadow-lg text-xs text-[var(--text)] whitespace-nowrap z-50">
                    Aggregated from 100+ trusted websites
                    <div className="absolute top-full left-4 w-2 h-2 bg-[var(--surface)] border-r border-b border-[var(--border)] transform rotate-45 -mt-1"></div>
                </div>
            )}
        </div>
    );
}
