'use client';

import React from 'react';
import { TrendingUp, Globe, Award } from 'lucide-react';

interface CategoryHeroProps {
    title: string;
    description: string;
    heroGradient?: string;
    categorySlug?: string;
    stats: {
        totalReviews: number;
        totalSources: number;
        totalProducts: number;
    };
}

// Map category slugs to AI-generated hero images
const CATEGORY_IMAGES: Record<string, string> = {
    electronics: '/images/categories/cat-laptops.webp',
    travel: '/images/categories/cat-travel.webp',
    'home-appliances': '/images/categories/cat-kitchen.webp',
    'health-wellness': '/images/categories/cat-fitness.webp',
    'outdoor-fitness': '/images/categories/cat-outdoor.webp',
    'fashion-style': '/images/categories/cat-fashion.webp',
    'smart-home': '/images/categories/cat-smart-home.webp',
    'kids-toys': '/images/categories/cat-gaming.webp',
    baby: '/images/categories/cat-home-decor.webp',
    'big-tall': '/images/categories/cat-fashion.webp',
}

function extractAccent(gradient?: string): string {
    if (!gradient) return 'var(--primary)';
    const match = gradient.match(/#[0-9A-Fa-f]{6}/);
    return match ? match[0] : 'var(--primary)';
}

function formatNumber(num: number): string {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
    }
    return num.toString();
}

export default function CategoryHero({ title, description, heroGradient, categorySlug, stats }: CategoryHeroProps) {
    const accent = extractAccent(heroGradient);
    const bgImage = categorySlug ? CATEGORY_IMAGES[categorySlug] : null;

    return (
        <div className="relative px-4 sm:px-6 md:px-8 pt-6 sm:pt-10 pb-8 sm:pb-12 overflow-hidden rounded-2xl mx-4 sm:mx-6 md:mx-8 mt-4">
            {/* AI-generated category background image */}
            {bgImage && (
                <>
                    <img
                        src={bgImage}
                        alt=""
                        className="absolute inset-0 w-full h-full object-cover opacity-20"
                        loading="eager"
                        aria-hidden="true"
                    />
                    <div className="absolute inset-0" style={{ background: 'linear-gradient(135deg, var(--background) 30%, transparent 100%)' }} />
                </>
            )}
            {/* Category accent bar */}
            <div
                className="relative w-10 h-1 rounded-full mb-5 sm:mb-6"
                style={{ background: accent }}
            />

            {/* Headline */}
            <h1 className="relative font-serif text-3xl sm:text-4xl md:text-5xl text-[var(--text)] tracking-tight leading-[1.1]">
                {title}
            </h1>

            {/* Description */}
            <p className="relative text-base sm:text-lg text-[var(--text-secondary)] mt-3 max-w-lg leading-relaxed">
                {description}
            </p>

            {/* Stats — editorial typographic treatment */}
            <div className="relative flex items-center gap-5 sm:gap-8 mt-8 sm:mt-10">
                <StatItem
                    icon={<TrendingUp size={14} strokeWidth={1.5} />}
                    value={formatNumber(stats.totalReviews)}
                    label="Reviews"
                    accent={accent}
                />
                <div className="w-px h-10 bg-[var(--border)]" />
                <StatItem
                    icon={<Globe size={14} strokeWidth={1.5} />}
                    value={stats.totalSources.toString()}
                    label="Sources"
                    accent={accent}
                />
                <div className="w-px h-10 bg-[var(--border)]" />
                <StatItem
                    icon={<Award size={14} strokeWidth={1.5} />}
                    value={formatNumber(stats.totalProducts)}
                    label="Ranked"
                    accent={accent}
                />
            </div>
        </div>
    );
}

function StatItem({ icon, value, label, accent }: { icon: React.ReactNode; value: string; label: string; accent: string }) {
    return (
        <div className="flex flex-col">
            <div className="flex items-center gap-1.5 mb-1">
                <span style={{ color: accent }}>{icon}</span>
                <span className="text-xl sm:text-2xl font-serif font-bold text-[var(--text)] tracking-tight">
                    {value}
                </span>
            </div>
            <span className="text-[10px] sm:text-xs text-[var(--text-muted)] uppercase tracking-[0.15em] font-medium">
                {label}
            </span>
        </div>
    );
}
