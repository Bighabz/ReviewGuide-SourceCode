
'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Plane, Gamepad2, Smartphone, Home, Shirt, Dumbbell, Sparkles, LayoutGrid } from 'lucide-react';

const CATEGORIES = [
    { id: 'all', icon: LayoutGrid, label: 'All Categories', href: '/browse' },
    { id: 'travel', icon: Plane, label: 'Travel', href: '/browse/travel' },
    { id: 'gaming', icon: Gamepad2, label: 'Gaming', href: '/browse/gaming' },
    { id: 'electronics', icon: Smartphone, label: 'Electronics', href: '/browse/electronics' },
    { id: 'home-garden', icon: Home, label: 'Home & Garden', href: '/browse/home-garden' },
    { id: 'fashion', icon: Shirt, label: 'Fashion', href: '/browse/fashion' },
    { id: 'sports', icon: Dumbbell, label: 'Sports', href: '/browse/sports' },
    { id: 'beauty', icon: Sparkles, label: 'Beauty', href: '/browse/beauty' },
];

export default function CategoryNav({ className = '' }: { className?: string }) {
    const pathname = usePathname();

    return (
        <nav className={`h-full bg-[var(--surface)] border-r border-[var(--border)] py-6 overflow-y-auto ${className}`}>
            <div className="px-6 mb-6">
                <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">
                    Browse Categories
                </h3>
            </div>

            <div className="space-y-1 px-3">
                {CATEGORIES.map((category) => {
                    const isActive = pathname === category.href;
                    const Icon = category.icon;

                    return (
                        <Link key={category.id} href={category.href} className="block">
                            <button
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group text-sm font-medium
                  ${isActive
                                        ? 'bg-[var(--primary)] text-white shadow-md shadow-[var(--primary-light)]'
                                        : 'text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)]'
                                    }`}
                            >
                                <Icon size={20} className={isActive ? 'text-white' : 'text-[var(--text-muted)] group-hover:text-[var(--primary)]'} />
                                {category.label}
                            </button>
                        </Link>
                    );
                })}
            </div>

            {/* Promo Card in Sidebar */}
            <div className="mt-8 px-4">
                <div className="bg-gradient-to-br from-[var(--secondary)] to-blue-900 rounded-xl p-4 text-white text-center shadow-lg">
                    <p className="text-sm font-bold mb-2">Need specific advice?</p>
                    <p className="text-xs text-blue-200 mb-3">Our AI can compare products specifically for your needs.</p>
                    <Link href="/chat">
                        <button className="w-full py-2 bg-white text-[var(--secondary)] rounded-lg text-xs font-bold hover:bg-blue-50 transition-colors">
                            Start Chat
                        </button>
                    </Link>
                </div>
            </div>
        </nav>
    );
}
