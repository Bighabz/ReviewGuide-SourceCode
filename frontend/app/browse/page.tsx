'use client';

import React, { useMemo, useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProductGrid from '@/components/browse/ProductGrid';
import ContentRow from '@/components/browse/ContentRow';
import { useFilters } from '@/components/browse/BrowseLayout';
import { CATEGORIES, HOME_ROWS, ProductItem } from '@/lib/browseData';
import ChatInput from '@/components/ChatInput';

const ITEMS_PER_PAGE = 20;

export default function BrowsePage() {
    const router = useRouter();
    const { filters, setIsHomepage } = useFilters();
    const [currentPage, setCurrentPage] = useState(1);
    const [searchQuery, setSearchQuery] = useState('');

    // Check if any filters are active (excluding default sort)
    const hasActiveFilters = filters.categories.length > 0 || filters.priceRange !== null || filters.minRating !== null;
    const hasSearch = searchQuery.trim().length > 0;

    // Tell layout we're on homepage when no filters/search active
    useEffect(() => {
        setIsHomepage(!hasActiveFilters && !hasSearch);
    }, [hasActiveFilters, hasSearch, setIsHomepage]);

    // Flatten all products from all categories
    const allProducts = useMemo(() => {
        const products: ProductItem[] = [];
        Object.values(CATEGORIES).forEach((category) => {
            category.rows.forEach((row) => {
                products.push(...row.items);
            });
        });
        return products;
    }, []);

    // Apply filters and search
    const filteredProducts = useMemo(() => {
        let result = [...allProducts];

        // Filter by search query
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            result = result.filter((item) =>
                item.title.toLowerCase().includes(query) ||
                item.category.toLowerCase().includes(query) ||
                item.description?.toLowerCase().includes(query) ||
                item.tags?.some(tag => tag.toLowerCase().includes(query))
            );
        }

        // Filter by category
        if (filters.categories.length > 0) {
            result = result.filter((item) =>
                filters.categories.some(
                    (cat) =>
                        item.category.toLowerCase().includes(cat.toLowerCase()) ||
                        cat.toLowerCase().includes(item.category.toLowerCase())
                )
            );
        }

        // Filter by price range
        if (filters.priceRange) {
            const [min, max] = filters.priceRange;
            result = result.filter((item) => item.price >= min && item.price <= max);
        }

        // Filter by rating
        if (filters.minRating) {
            result = result.filter((item) => item.rating >= filters.minRating!);
        }

        // Sort
        switch (filters.sortBy) {
            case 'price_low':
                result.sort((a, b) => a.price - b.price);
                break;
            case 'price_high':
                result.sort((a, b) => b.price - a.price);
                break;
            case 'rating':
                result.sort((a, b) => b.rating - a.rating);
                break;
            case 'reviews':
                result.sort((a, b) => b.reviewCount - a.reviewCount);
                break;
            default:
                break;
        }

        return result;
    }, [allProducts, filters, searchQuery]);

    // Pagination
    const totalPages = Math.ceil(filteredProducts.length / ITEMS_PER_PAGE);
    const paginatedProducts = filteredProducts.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    );

    // Reset to page 1 when filters/search change
    useEffect(() => {
        setCurrentPage(1);
    }, [filters, searchQuery]);

    const handleSearch = useCallback((query: string) => {
        setSearchQuery(query);
    }, []);

    const [heroInput, setHeroInput] = useState('');

    const handleHeroSend = useCallback(() => {
        if (heroInput.trim()) {
            router.push(`/chat?q=${encodeURIComponent(heroInput.trim())}&new=1`);
        } else {
            router.push('/chat?new=1');
        }
    }, [heroInput, router]);

    // DISCOVERY HOMEPAGE: Hero + Content Rows
    if (!hasActiveFilters && !hasSearch) {
        return (
            <div className="flex flex-col">
                {/* Hero Section: Editorial tagline + ChatInput */}
                <div className="flex flex-col items-center justify-center px-4 pb-10 sm:pb-16">
                    <img
                        src="/images/ezgif-7b66ba24abcfdab0.gif"
                        alt="ReviewGuide.Ai"
                        className="h-32 sm:h-44 md:h-56 w-auto mb-4"
                    />
                    <h1 className="font-serif text-2xl sm:text-3xl md:text-4xl text-center text-[var(--text)] leading-tight tracking-tight">
                        Smart shopping,{' '}
                        <span className="italic text-[var(--primary)]">simplified.</span>
                    </h1>
                    <p className="text-sm sm:text-base text-[var(--text-secondary)] text-center mt-3 max-w-md">
                        AI-powered product reviews, travel planning, and price comparison — all in one conversation.
                    </p>

                    {/* Chat Input — navigates to /chat on send */}
                    <div className="w-full max-w-xl mx-auto mt-8">
                        <ChatInput
                            value={heroInput}
                            onChange={setHeroInput}
                            onSend={handleHeroSend}
                            disabled={false}
                            placeholder="Ask anything — best headphones, Tokyo trip, laptop deals..."
                        />
                    </div>

                    {/* Quick suggestions */}
                    <div className="flex flex-wrap justify-center gap-2 mt-4">
                        {['Best wireless earbuds under $100', 'Plan a 5-day trip to Tokyo', 'Compare MacBook Air vs Pro'].map((suggestion, idx) => (
                            <button
                                key={idx}
                                onClick={() => {
                                    router.push(`/chat?q=${encodeURIComponent(suggestion)}&new=1`);
                                }}
                                className="px-4 py-2 rounded-full text-sm border border-[var(--border)] text-[var(--text-secondary)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] hover:border-[var(--border-strong)] transition-all"
                            >
                                {suggestion}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Editorial rule separator */}
                <div className="editorial-rule mx-8" />

                {/* Content Rows */}
                <div className="py-4 space-y-2">
                    {HOME_ROWS.map((row) => (
                        <ContentRow
                            key={row.id}
                            title={row.title}
                            subtitle={row.subtitle}
                            items={row.items}
                            viewAllLink={`/browse/${row.id}`}
                        />
                    ))}
                </div>

                {/* Browse All */}
                <div className="px-4 sm:px-6 md:px-8 pb-12">
                    <div className="flex items-center gap-4 mb-4">
                        <h2 className="text-xl sm:text-2xl font-serif font-bold text-[var(--text)] tracking-tight">
                            Browse All
                        </h2>
                        <div className="flex-1 h-px bg-[var(--border)]" />
                    </div>
                    <ProductGrid
                        items={allProducts.slice(0, 20)}
                        currentPage={1}
                        totalPages={1}
                    />
                </div>
            </div>
        );
    }

    // SEARCH/FILTER VIEW: Show filtered results with full layout
    return (
        <div className="p-4 sm:p-6 lg:p-8">
            {/* Search Results Header */}
            <div className="mb-6">
                {hasSearch && (
                    <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[var(--text)] mb-2">
                        Results for "{searchQuery}"
                    </h1>
                )}
                {!hasSearch && hasActiveFilters && (
                    <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[var(--text)] mb-2">
                        Filtered Products
                    </h1>
                )}
                <p className="text-sm text-[var(--text-secondary)]">
                    {filteredProducts.length} product{filteredProducts.length !== 1 ? 's' : ''} found
                </p>
            </div>

            {/* Product Grid */}
            <ProductGrid
                items={paginatedProducts}
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setCurrentPage}
            />
        </div>
    );
}
