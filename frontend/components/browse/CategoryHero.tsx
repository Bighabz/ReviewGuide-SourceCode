
import React from 'react';

interface CategoryHeroProps {
    title: string;
    description: string;
    heroGradient?: string;
    stats: {
        totalReviews: number;
        totalSources: number;
        totalProducts: number;
    };
}

export default function CategoryHero({ title, description, heroGradient, stats }: CategoryHeroProps) {
    // Use provided gradient or fallback to checking title/theme - but component prop is cleaner
    const bgStyle = heroGradient ? { background: heroGradient } : { background: 'var(--gradient-hero)' };

    return (
        <div className="relative py-12 sm:py-16 md:py-20 lg:py-24 overflow-hidden" style={bgStyle}>
            {/* Background patterns */}
            <div className="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-repeat" />
            <div className="absolute inset-0 bg-gradient-to-t from-[var(--background)] to-transparent" />

            <div className="relative container mx-auto px-4 sm:px-6 text-center max-w-4xl z-10">
                <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-white mb-4 sm:mb-6 drop-shadow-sm tracking-tight">
                    {title}
                </h1>
                <p className="text-xl sm:text-2xl text-white/90 font-medium mb-8 sm:mb-10 max-w-2xl mx-auto leading-relaxed">
                    {description}
                </p>

                {/* Stats Grid */}
                <div className="flex flex-wrap justify-center gap-4 sm:gap-8 md:gap-12">
                    <StatBadge
                        value={formatNumber(stats.totalReviews)}
                        label="Reviews Analyzed"
                        icon="📊"
                    />
                    <StatBadge
                        value={stats.totalSources.toString()}
                        label="Verified Sources"
                        icon="🌐"
                    />
                    <StatBadge
                        value={formatNumber(stats.totalProducts)}
                        label="Products Ranked"
                        icon="🏆"
                    />
                </div>
            </div>
        </div>
    );
}

function StatBadge({ value, label, icon }: { value: string; label: string; icon: string }) {
    return (
        <div className="flex flex-col items-center bg-white/10 backdrop-blur-md rounded-2xl p-3 sm:p-4 min-w-[120px] transition-transform hover:scale-105 border border-white/10 shadow-lg">
            <div className="text-2xl sm:text-3xl font-bold text-white mb-1 flex items-center gap-2">
                <span className="text-xl">{icon}</span>
                {value}
            </div>
            <div className="text-xs sm:text-sm text-white/80 font-medium uppercase tracking-wider">
                {label}
            </div>
        </div>
    );
}

function formatNumber(num: number): string {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M+';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K+';
    }
    return num.toString();
}
