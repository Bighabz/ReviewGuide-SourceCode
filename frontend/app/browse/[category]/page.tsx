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
        return notFound();
    }

    return (
        <div className="bg-[var(--background)]">
            <CategoryHero
                title={data.title}
                description={data.description}
                heroGradient={data.heroGradient}
                stats={data.stats}
            />

            {/* Editorial rule separator */}
            <div className="editorial-rule mx-4 sm:mx-6 md:mx-8" />

            {/* Content rows */}
            <div className="py-4 space-y-2">
                {data.rows.map((row) => (
                    <ContentRow
                        key={row.id}
                        title={row.title}
                        subtitle={row.subtitle}
                        items={row.items}
                    />
                ))}

                {data.rows.length === 0 && (
                    <div className="text-center py-20 text-[var(--text-muted)]">
                        <p className="font-serif text-lg italic">More content coming soon...</p>
                    </div>
                )}
            </div>
        </div>
    );
}
