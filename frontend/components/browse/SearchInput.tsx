
'use client';

import React, { useState } from 'react';
import { Search, ArrowUp, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface SearchInputProps {
    placeholder?: string;
}

export default function SearchInput({ placeholder = "Ask AI anything..." }: SearchInputProps) {
    const [query, setQuery] = useState('');
    const router = useRouter();

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            // Navigate to chat with the initial message and force new session
            console.log('[SearchInput] Submitting query:', query);
            const url = `/chat?q=${encodeURIComponent(query)}&new=1`;
            console.log('[SearchInput] Navigating to:', url);
            router.push(url);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="relative group w-full">
            <div className="relative flex items-center bg-[var(--surface)] border border-[var(--border)] rounded-full shadow-[var(--shadow-lg)] hover:shadow-[var(--shadow-xl)] transition-all duration-300 focus-within:ring-2 focus-within:ring-[var(--primary)] focus-within:border-transparent overflow-hidden">

                {/* Icon - REMOVED per user request */}
                <div className="pl-4 text-[var(--text-muted)]">
                    <Search size={20} />
                </div>

                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={placeholder}
                    className="w-full flex-1 py-3.5 sm:py-4 px-3 bg-transparent text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none text-base sm:text-lg"
                />

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={!query.trim()}
                    className="mr-2 p-2 rounded-full bg-[var(--primary)] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--primary-hover)] transition-colors"
                >
                    <ArrowUp size={20} strokeWidth={2.5} />
                </button>
            </div>
        </form>
    );
}
