'use client';

import React, { useMemo, useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProductGrid from '@/components/browse/ProductGrid';
import ContentRow from '@/components/browse/ContentRow';
import { useFilters } from '@/components/browse/BrowseLayout';
import { CATEGORIES, HOME_ROWS, ProductItem } from '@/lib/browseData';
import AnimatedLogo from '@/components/AnimatedLogo';
import HomeSearchBar from '@/components/HomeSearchBar';

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

    // Get featured row (first row from HOME_ROWS)
    const featuredRow = HOME_ROWS[0];
    const remainingRows = HOME_ROWS.slice(1);

    // MINIMAL HOMEPAGE: No filters, no search
    if (!hasActiveFilters && !hasSearch) {
        return (
            <div className="min-h-screen flex flex-col">
                {/* Hero Section: Logo + Search */}
                <div className="flex-1 flex flex-col items-center justify-center px-4 py-12 sm:py-16">
                    <AnimatedLogo className="mb-8 sm:mb-12" />
                    <HomeSearchBar
                        onSearch={handleSearch}
                        placeholder="What are you looking for?"
                    />
                </div>

                {/* Featured Carousel */}
                <div className="pb-4">
                    <ContentRow
                        title={featuredRow.title}
                        subtitle={featuredRow.subtitle}
                        items={featuredRow.items}
                        viewAllLink={`/browse/${featuredRow.id}`}
                    />
                </div>

                {/* Product Grid */}
                <div className="px-4 sm:px-6 md:px-8 pb-12">
                    <h2 className="text-xl sm:text-2xl font-bold text-[var(--text)] tracking-tight mb-4">
                        Browse All
                    </h2>
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
                    <h1 className="text-2xl sm:text-3xl font-bold text-[var(--text)] mb-2">
                        Results for "{searchQuery}"
                    </h1>
                )}
                {!hasSearch && hasActiveFilters && (
                    <h1 className="text-2xl sm:text-3xl font-bold text-[var(--text)] mb-2">
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
