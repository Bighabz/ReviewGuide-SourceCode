
'use client';

import React, { useState, createContext, useContext } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import UnifiedTopbar from '../UnifiedTopbar';
import CategorySidebar from '../CategorySidebar';
import SearchInput from './SearchInput';

// Keep filter state type for compatibility with browse page
export interface FilterState {
    categories: string[];
    priceRange: [number, number] | null;
    minRating: number | null;
    sortBy: 'relevance' | 'price_low' | 'price_high' | 'rating' | 'reviews';
}

// Context for sharing filter state between layout and page
interface FilterContextType {
    filters: FilterState;
    setFilters: (filters: FilterState) => void;
    isHomepage: boolean;
    setIsHomepage: (value: boolean) => void;
}

const FilterContext = createContext<FilterContextType | null>(null);

export function useFilters() {
    const context = useContext(FilterContext);
    if (!context) {
        return {
            filters: {
                categories: [],
                priceRange: null,
                minRating: null,
                sortBy: 'relevance' as const
            },
            setFilters: () => { },
            isHomepage: true,
            setIsHomepage: () => { }
        };
    }
    return context;
}

export default function BrowseLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isHomepage, setIsHomepage] = useState(true);
    const [filters, setFilters] = useState<FilterState>({
        categories: [],
        priceRange: null,
        minRating: null,
        sortBy: 'relevance'
    });

    const handleSearch = (query: string) => {
        // Navigate to chat with the search query
        router.push(`/chat?q=${encodeURIComponent(query)}&new=1`);
    };

    // Minimal layout for homepage (no topbar, sidebar, or sticky bar)
    if (isHomepage && pathname === '/browse') {
        return (
            <FilterContext.Provider value={{ filters, setFilters, isHomepage, setIsHomepage }}>
                <div className="min-h-screen bg-[var(--background)] text-[var(--text)]">
                    {children}
                </div>
            </FilterContext.Provider>
        );
    }

    return (
        <FilterContext.Provider value={{ filters, setFilters, isHomepage, setIsHomepage }}>
            <div className="min-h-screen bg-[var(--background)] text-[var(--text)]">
                {/* Unified Navigation */}
                <UnifiedTopbar
                    onMenuClick={() => setSidebarOpen(!sidebarOpen)}
                    onSearch={handleSearch}
                    onNewChat={() => router.push('/chat?new=1')}
                    onHistoryClick={() => router.push('/chat')}
                />

                {/* Category Sidebar (desktop) - Consistent across all browse pages */}
                <aside className="hidden lg:block fixed left-0 top-14 sm:top-16 bottom-0 w-56 z-30">
                    <CategorySidebar />
                </aside>

                {/* Mobile Sidebar Overlay - Only render when open */}
                {sidebarOpen && (
                    <CategorySidebar
                        isOpen={sidebarOpen}
                        onClose={() => setSidebarOpen(false)}
                    />
                )}

                {/* Main Content - Left-aligned, tighter to sidebar */}
                <main className="lg:ml-56 pt-16 w-full overflow-x-hidden min-h-[calc(100vh-4rem)] pb-24">
                    <div className="w-full">
                        {children}
                    </div>
                </main>

                {/* Sticky Chat Bar at Bottom */}
                <div className="fixed bottom-0 left-0 right-0 z-40 bg-[var(--background)]/80 backdrop-blur-xl border-t border-[var(--border)] p-4 lg:pl-[15rem]">
                    <div className="max-w-3xl mx-auto px-4">
                        <SearchInput placeholder="Ask AI about any product..." />
                    </div>
                </div>
            </div>
        </FilterContext.Provider>
    );
}
