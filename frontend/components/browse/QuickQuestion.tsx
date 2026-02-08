
'use client';

import React from 'react';
import Link from 'next/link';

interface QuickQuestionProps {
    children: React.ReactNode;
    productName: string;
}

export default function QuickQuestion({ children, productName }: QuickQuestionProps) {
    const query = `${children} for ${productName}`;
    const encodedQuery = encodeURIComponent(query);

    return (
        <Link
            href={`/chat?q=${encodedQuery}`}
            className="inline-block px-3 py-1.5 bg-[var(--surface-hover)] border border-[var(--border)] rounded-full text-xs sm:text-sm text-[var(--text-secondary)] hover:bg-[var(--primary-light)] hover:text-[var(--primary)] hover:border-[var(--primary)] transition-all cursor-pointer"
        >
            {children}
        </Link>
    );
}
