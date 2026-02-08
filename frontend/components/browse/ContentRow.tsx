
'use client';

import React, { useRef } from 'react';
import { ProductItem } from '@/lib/browseData';
import ProductCard from './ProductCard';
import { ChevronLeft, ChevronRight, ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface ContentRowProps {
    title: string;
    subtitle?: string;
    items: ProductItem[];
    showSourceBadges?: boolean;
    viewAllLink?: string;
    onItemClick?: (item: ProductItem) => void;
}

export default function ContentRow({ title, subtitle, items, viewAllLink, onItemClick }: ContentRowProps) {
    const scrollRef = useRef<HTMLDivElement>(null);

    const scroll = (direction: 'left' | 'right') => {
        if (scrollRef.current) {
            const container = scrollRef.current;
            const scrollAmount = container.clientWidth * 0.8;
            container.scrollBy({
                left: direction === 'left' ? -scrollAmount : scrollAmount,
                behavior: 'smooth'
            });
        }
    };

    if (!items || items.length === 0) return null;

    return (
        <div className="group/row py-3 sm:py-4 relative">
            <div className="px-4 sm:px-6 md:px-8 mb-3 sm:mb-4 flex items-end justify-between">
                <div>
                    <h2 className="text-xl sm:text-2xl font-bold text-[var(--text)] tracking-tight">{title}</h2>
                    {subtitle && (
                        <p className="text-sm sm:text-base text-[var(--text-secondary)] mt-1">{subtitle}</p>
                    )}
                </div>

                {viewAllLink && (
                    <Link href={viewAllLink} className="hidden sm:flex items-center text-sm font-semibold text-[var(--accent-teal)] hover:text-[var(--primary)] transition-colors gap-1">
                        See All <ArrowRight size={14} />
                    </Link>
                )}
            </div>

            <div className="relative">
                {/* Left Arrow */}
                <button
                    onClick={() => scroll('left')}
                    className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-[var(--surface)]/90 backdrop-blur border border-[var(--border)] text-[var(--text)] p-2 rounded-full shadow-lg opacity-0 group-hover/row:opacity-100 transition-opacity disabled:opacity-0 hidden sm:block mx-2 hover:bg-[var(--surface-hover)] hover:scale-110"
                    aria-label="Scroll left"
                >
                    <ChevronLeft size={24} />
                </button>

                {/* Scroll Container */}
                <div
                    ref={scrollRef}
                    className="flex gap-3 sm:gap-4 overflow-x-auto px-4 sm:px-6 md:px-8 pb-4 scrollbar-hide snap-x snap-mandatory"
                    style={{ scrollBehavior: 'smooth' }}
                >
                    {items.map((item) => (
                        <div key={item.id} className="min-w-[260px] sm:min-w-[280px] md:min-w-[300px] snap-center">
                            <ProductCard item={item} onClick={onItemClick} />
                        </div>
                    ))}

                    {/* See All Card at the end */}
                    {viewAllLink && (
                        <Link href={viewAllLink} className="min-w-[150px] sm:min-w-[180px] snap-center flex flex-col items-center justify-center text-[var(--primary)] text-center group/more bg-[var(--surface)] border border-[var(--border)] rounded-xl hover:border-[var(--primary)] hover:bg-[var(--surface-hover)] transition-all cursor-pointer">
                            <div className="p-3 rounded-full bg-[var(--surface)] text-[var(--primary)] group-hover/more:scale-110 transition-transform shadow-sm mb-2">
                                <ArrowRight size={24} />
                            </div>
                            <span className="font-bold text-sm">See all in {title}</span>
                        </Link>
                    )}
                </div>

                {/* Right Arrow */}
                <button
                    onClick={() => scroll('right')}
                    className="absolute right-0 top-1/2 -translate-y-1/2 z-20 bg-[var(--surface)]/90 backdrop-blur border border-[var(--border)] text-[var(--text)] p-2 rounded-full shadow-lg opacity-0 group-hover/row:opacity-100 transition-opacity hidden sm:block mx-2 hover:bg-[var(--surface-hover)] hover:scale-110"
                    aria-label="Scroll right"
                >
                    <ChevronRight size={24} />
                </button>
            </div>
        </div>
    );
}
