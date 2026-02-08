'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ExternalLink } from 'lucide-react'
import Link from 'next/link'
import { CategoryTabs } from './CategoryTabs'
import { StarRating } from './StarRating'
import { DEAL_CATEGORIES, FEATURED_DEALS } from '@/lib/constants'

// Define type for deal items from constants
type DealCategory = keyof typeof FEATURED_DEALS

export function FeaturedDeals() {
    const [activeCategory, setActiveCategory] = useState<DealCategory>('electronics')

    const deals = FEATURED_DEALS[activeCategory]

    return (
        <div className="w-full space-y-6 animate-in fade-in duration-700 delay-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-xl font-bold text-[var(--gpt-text)]">Featured Deals</h2>
                    <p className="text-sm text-[var(--gpt-text-secondary)]">Hand-picked drops from top merchants</p>
                </div>

                <CategoryTabs
                    tabs={DEAL_CATEGORIES}
                    activeTab={activeCategory}
                    onTabChange={(id) => setActiveCategory(id as DealCategory)}
                />
            </div>

            <div className="relative min-h-[300px]">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeCategory}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                        className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
                    >
                        {deals.map((deal) => (
                            <Link
                                key={deal.id}
                                href={`/product/${deal.id}`}
                                className="group relative flex flex-col bg-[var(--card-bg)] border border-[var(--border)] rounded-xl overflow-hidden hover:shadow-float hover:-translate-y-1 transition-all duration-300 cursor-pointer"
                            >
                                {/* Image Container - Matte finish with float effect on hover */}
                                <div className="aspect-square relative overflow-hidden bg-white p-6 flex items-center justify-center">
                                    <img
                                        src={deal.image}
                                        alt={deal.title}
                                        className="object-contain max-h-full w-auto mix-blend-multiply group-hover:scale-110 transition-transform duration-500 ease-out"
                                    />
                                </div>

                                {/* Content */}
                                <div className="flex flex-col flex-1 p-5">
                                    <div className="flex items-center gap-2 mb-3">
                                        <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--text-secondary)] border border-[var(--border)] px-2 py-0.5 rounded-full bg-[var(--surface)]">
                                            {deal.merchant}
                                        </span>
                                        {deal.original_price > deal.price && (
                                            <span className="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                                                SAVE {Math.round(((deal.original_price - deal.price) / deal.original_price) * 100)}%
                                            </span>
                                        )}
                                    </div>

                                    <h3 className="font-heading text-base font-semibold text-[var(--text)] line-clamp-2 mb-2 group-hover:text-[var(--primary)] transition-colors leading-snug">
                                        {deal.title}
                                    </h3>

                                    <StarRating
                                        value={deal.rating}
                                        size={14}
                                        showCount
                                        count={deal.review_count}
                                        className="mb-4"
                                    />

                                    <div className="mt-auto pt-4 border-t border-[var(--border)]/50 flex items-center justify-between">
                                        <div suppressHydrationWarning className="flex flex-col">
                                            <div className="text-xl font-bold text-[var(--text)] font-heading">
                                                ${deal.price.toLocaleString()}
                                            </div>
                                            {deal.original_price > deal.price && (
                                                <div className="text-xs text-[var(--text-muted)] line-through">
                                                    ${deal.original_price.toLocaleString()}
                                                </div>
                                            )}
                                        </div>

                                        <button
                                            className="p-2.5 rounded-full bg-[var(--surface-hover)] text-[var(--text-secondary)] group-hover:bg-[var(--primary)] group-hover:text-white transition-all shadow-sm"
                                            title="View Details"
                                        >
                                            <ExternalLink size={18} strokeWidth={2} />
                                        </button>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </motion.div>
                </AnimatePresence>
            </div>
        </div>
    )
}
