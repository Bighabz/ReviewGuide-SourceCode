'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';

interface HomeSearchBarProps {
  onSearch?: (query: string) => void;
  placeholder?: string;
}

export default function HomeSearchBar({
  onSearch,
  placeholder = 'What are you looking for?'
}: HomeSearchBarProps) {
  const [query, setQuery] = useState('');
  const router = useRouter();

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    onSearch?.(value);
  }, [onSearch]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch?.(query.trim());
    }
  }, [query, onSearch]);

  const handleAskAI = useCallback(() => {
    if (query.trim()) {
      router.push(`/chat?q=${encodeURIComponent(query.trim())}&new=1`);
    } else {
      router.push('/chat?new=1');
    }
  }, [query, router]);

  return (
    <div className="w-full max-w-xl mx-auto">
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <Search
            size={20}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
          />
          <input
            type="text"
            value={query}
            onChange={handleChange}
            placeholder={placeholder}
            className="w-full pl-12 pr-4 py-4 rounded-2xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20 focus:border-[var(--primary)]/30 transition-all text-base"
          />
        </div>
      </form>

      {/* Ask AI link - appears when there's a query */}
      <div className="h-8 flex justify-center items-center mt-3">
        {query.trim() ? (
          <button
            onClick={handleAskAI}
            className="text-sm text-[var(--primary)] hover:text-[var(--primary-hover)] transition-colors"
          >
            Ask AI instead &rarr;
          </button>
        ) : (
          <button
            onClick={handleAskAI}
            className="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors"
          >
            or chat with AI
          </button>
        )}
      </div>
    </div>
  );
}
