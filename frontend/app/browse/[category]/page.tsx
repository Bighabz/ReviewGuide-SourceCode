
'use client';

import React from 'react';
import { CATEGORIES } from '@/lib/browseData';
import ContentRow from '@/components/browse/ContentRow';
import CategoryHero from '@/components/browse/CategoryHero';
import { notFound } from 'next/navigation';

export default function CategoryPage({ params }: { params: { category: string } }) {
    const categoryId = params.category;
    const data = CATEGORIES[categoryId];

    if (!data) {
        // If not found in known categories, try to find one that matches? 
        // For now, strict match or 404
        return notFound();
    }

    return (
        <div className="bg-[var(--background)] min-h-screen">
            <CategoryHero
                title={data.title}
                description={data.description}
                heroGradient={data.heroGradient}
                stats={data.stats}
            />

            <div className="py-8 space-y-8">
                {data.rows.map((row) => (
                    <ContentRow
                        key={row.id}
                        title={row.title}
                        subtitle={row.subtitle}
                        items={row.items}
                    />
                ))}

                {/* Fallback if no rows */}
                {data.rows.length === 0 && (
                    <div className="text-center py-20 text-[var(--text-muted)]">
                        <p>More content coming soon to {data.title}...</p>
                    </div>
                )}
            </div>
        </div>
    );
}
