
'use client';

import React from 'react';
import Link from 'next/link';
import { Menu, Search, MessageSquarePlus } from 'lucide-react';
import { useState, useEffect } from 'react';

// Reusing the theme toggle logic from main Topbar or similar, simplified here
export default function BrowseTopbar({ onMenuClick }: { onMenuClick?: () => void }) {
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 10);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <div className={`sticky top-0 z-50 transition-all duration-300 ${scrolled
                ? 'bg-[var(--background)]/80 backdrop-blur-md border-b border-[var(--border)] shadow-sm'
                : 'bg-transparent'
            }`}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">

                {/* Left: Mobile Menu & Logo */}
                <div className="flex items-center gap-4">
                    <button
                        onClick={onMenuClick}
                        className="lg:hidden p-2 text-[var(--text)] hover:bg-[var(--surface-hover)] rounded-full"
                        aria-label="Menu"
                    >
                        <Menu size={24} />
                    </button>

                    <Link href="/browse" className="flex items-center gap-2 group">
                        <img
                            src="/images/ezgif-7b66ba24abcfdab0.gif"
                            alt="ReviewGuide.ai"
                            className="w-9 h-9 rounded-lg object-contain group-hover:scale-105 transition-transform"
                        />
                        <span className="font-bold text-lg text-[var(--text)] tracking-tight">
                            ReviewGuide<span className="text-[var(--primary)]">.ai</span>
                        </span>
                    </Link>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-2 sm:gap-4">
                    {/* Link to Chat - Primary CTA */}
                    <Link href="/chat">
                        <button className="flex items-center gap-2 px-4 py-2 bg-[var(--text)] text-[var(--background)] rounded-full text-sm font-bold hover:bg-[var(--primary)] hover:text-white transition-all shadow-md hover:shadow-lg active:scale-95">
                            <MessageSquarePlus size={18} />
                            <span className="hidden sm:inline">AI Chat</span>
                        </button>
                    </Link>

                    {/* Profile / Auth (Placeholder) */}
                    <div className="w-8 h-8 rounded-full bg-[var(--surface-hover)] border border-[var(--border)] flex items-center justify-center text-[var(--text-secondary)]">
                        <span className="text-xs font-bold">G</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
