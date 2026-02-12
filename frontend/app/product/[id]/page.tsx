
'use client';

import React, { useState } from 'react';
import { CATEGORIES, HOME_ROWS, ProductItem } from '@/lib/browseData';
import { FEATURED_DEALS } from '@/lib/constants';
import BrowseLayout from '@/components/browse/BrowseLayout';
import { StarRating } from '@/components/StarRating';
import SentimentBar from '@/components/browse/SentimentBar';
import SourceBadge from '@/components/browse/SourceBadge';
import QuickQuestion from '@/components/browse/QuickQuestion';
import SourcesModal from '@/components/browse/SourcesModal';
import { notFound, useRouter } from 'next/navigation';
import { ArrowLeft, ExternalLink, Check, AlertTriangle, MessageSquare, Quote } from 'lucide-react';
import Link from 'next/link';

// Helper to convert featured deal to ProductItem format
interface FeaturedDeal {
    id: string;
    title: string;
    image: string;
    rating: number;
    review_count: number;
    price: number;
    original_price: number;
    description: string;
    affiliate_link: string;
    merchant: string;
}

const convertDealToProduct = (deal: FeaturedDeal, category: string): ProductItem => ({
    id: deal.id,
    title: deal.title,
    image: deal.image,
    images: [deal.image],
    price: deal.price,
    originalPrice: deal.original_price,
    currency: '$',
    rating: deal.rating,
    reviewCount: deal.review_count,
    category: category,
    subcategory: 'Featured Deal',
    description: deal.description,
    sourceCount: 12,
    affiliateLink: deal.affiliate_link !== '#' ? deal.affiliate_link : 'https://amazon.com',
    merchant: deal.merchant,
    bestFor: 'everyday use',
    tags: ['Featured Deal', 'Top Pick'],
    sentiment: { positive: 85, neutral: 10, negative: 5 },
    topPros: [
        { title: 'Great value', count: 450 },
        { title: 'High quality', count: 380 },
        { title: 'Fast delivery', count: 290 }
    ],
    topCons: [
        { title: 'Limited availability', count: 45 },
        { title: 'Premium pricing', count: 32 }
    ],
    topSources: ['Amazon', 'Reddit', 'YouTube'],
    quotes: [
        { text: 'Excellent product, highly recommended!', author: 'Verified Buyer', source: 'Amazon' },
        { text: 'Best in its category for the price.', author: 'Tech Reviewer', source: 'YouTube' }
    ]
});

// Helper to find product by ID from all data
const findProduct = (id: string): ProductItem | undefined => {
    // Check categories
    for (const cat of Object.values(CATEGORIES)) {
        for (const row of cat.rows) {
            const found = row.items.find(original => original.id === id);
            if (found) return found;
        }
    }
    // Check home rows
    for (const row of HOME_ROWS) {
        const found = row.items.find(original => original.id === id);
        if (found) return found;
    }
    // Check featured deals
    for (const [category, deals] of Object.entries(FEATURED_DEALS)) {
        const found = deals.find(deal => deal.id === id);
        if (found) return convertDealToProduct(found, category);
    }
    return undefined;
};

export default function ProductPage({ params }: { params: { id: string } }) {
    const router = useRouter();
    const product = findProduct(params.id);
    const [sourcesOpen, setSourcesOpen] = useState(false);
    const [chatQuery, setChatQuery] = useState('');

    if (!product) return notFound();

    const handleChatSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (chatQuery.trim()) {
            router.push(`/chat?q=${encodeURIComponent(`${chatQuery} about ${product.title}`)}`);
        }
    };

    return (
        <BrowseLayout>
            <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
                <Link href="/browse" className="inline-flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text)] mb-6 transition-colors">
                    <ArrowLeft size={20} /> Back to Browse
                </Link>

                {/* Hero Section */}
                <div className="grid md:grid-cols-2 gap-8 lg:gap-12 mb-12">
                    {/* Image */}
                    <div className="bg-white rounded-2xl p-4 shadow-sm border border-[var(--border)] relative group">
                        <div className="aspect-square relative overflow-hidden rounded-xl">
                            <img
                                src={product.image}
                                alt={product.title}
                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                            />
                            <button
                                onClick={() => setSourcesOpen(true)}
                                className="absolute bottom-4 left-4 bg-black/70 backdrop-blur text-white px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-2 hover:bg-black/90 transition-colors"
                            >
                                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                {product.sourceCount} Sources Analyzed
                            </button>
                        </div>

                        <div className="mt-4 flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                            {product.images.map((img, i) => (
                                <div key={i} className="w-20 h-20 flex-shrink-0 rounded-lg border border-[var(--border)] overflow-hidden cursor-pointer hover:border-[var(--primary)]">
                                    <img src={img} className="w-full h-full object-cover" />
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Info */}
                    <div>
                        <div className="flex flex-wrap gap-2 mb-3">
                            <span className="px-2 py-1 bg-[var(--surface)] text-[var(--text-secondary)] text-xs rounded border border-[var(--border)] font-medium">
                                {product.category}
                            </span>
                            <span className="px-2 py-1 bg-[var(--surface)] text-[var(--text-secondary)] text-xs rounded border border-[var(--border)] font-medium">
                                {product.subcategory}
                            </span>
                        </div>

                        <h1 className="text-3xl sm:text-4xl font-bold text-[var(--text)] mb-4 leading-tight">
                            {product.title}
                        </h1>

                        <div className="flex items-center gap-4 mb-6">
                            <span className="text-2xl sm:text-3xl font-bold text-[var(--text)]">
                                {product.currency}{product.price.toLocaleString()}
                            </span>
                            {product.originalPrice && (
                                <span className="text-lg text-[var(--text-muted)] line-through">
                                    {product.currency}{product.originalPrice.toLocaleString()}
                                </span>
                            )}
                        </div>

                        <div className="flex items-center gap-3 mb-6 p-3 bg-[var(--surface)] rounded-xl border border-[var(--border)] inline-flex">
                            <StarRating value={product.rating} size={20} />
                            <span className="text-sm font-medium text-[var(--text-secondary)]">
                                {product.reviewCount.toLocaleString()} reviews
                            </span>
                            <div className="w-px h-4 bg-[var(--border)]" />
                            <button
                                onClick={() => setSourcesOpen(true)}
                                className="text-sm text-[var(--primary)] font-bold hover:underline"
                            >
                                View Analysis
                            </button>
                        </div>

                        <p className="text-[var(--text-secondary)] leading-relaxed mb-8">
                            {product.description}
                        </p>

                        <a
                            href={product.affiliateLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white px-8 py-4 rounded-xl font-bold text-lg shadow-[var(--shadow-lg)] hover:shadow-xl transition-all transform hover:-translate-y-0.5 active:translate-y-0"
                        >
                            See Best Price <ExternalLink size={20} />
                        </a>
                        <p className="text-xs text-[var(--text-muted)] mt-2 ml-1">
                            Check {product.merchant} for latest availability
                        </p>
                    </div>
                </div>

                {/* AI Summary Section - The "Netflix" moment */}
                <section className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 sm:p-8 my-8 sm:my-12 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[var(--primary)] via-[var(--accent-yellow)] to-[var(--accent-teal)]" />

                    <h2 className="flex items-center gap-3 text-2xl font-bold text-[var(--text)] mb-6">
                        <span className="text-3xl">🤖</span> AI Review Summary
                    </h2>

                    <p className="text-lg leading-relaxed text-[var(--text)] mb-8 max-w-4xl">
                        "Based on <strong>{product.reviewCount.toLocaleString()} reviews</strong> across <strong>{product.sourceCount} sources</strong>,
                        the {product.title} is consistently rated as the best {product.subcategory} for <strong>{product.bestFor}</strong>.
                        Users particularly love the <span className="text-[var(--accent-teal)] font-medium">{product.topPros[0]?.title.toLowerCase()}</span> and
                        <span className="text-[var(--accent-teal)] font-medium"> {product.topPros[1]?.title.toLowerCase()}</span>.
                        The main criticism ({product.sentiment.negative}% of reviews) mentions <span className="text-[var(--accent-red)] font-medium">{product.topCons[0]?.title.toLowerCase()}</span>."
                    </p>

                    <div className="flex flex-wrap gap-3">
                        {product.topSources.map((source) => (
                            <SourceBadge key={source} source={source} className="text-sm px-3 py-1" />
                        ))}
                        <span className="text-sm text-[var(--text-muted)] flex items-center px-2">
                            + {product.sourceCount - product.topSources.length} more sources
                        </span>
                    </div>
                </section>

                {/* The Verdict Grid */}
                <div className="grid md:grid-cols-2 gap-6 sm:gap-8 mb-12">
                    {/* Pros */}
                    <div className="bg-emerald-50/50 dark:bg-emerald-900/10 rounded-2xl p-6 border border-emerald-100 dark:border-emerald-900/30">
                        <h3 className="text-emerald-700 dark:text-emerald-400 font-bold text-xl mb-6 flex items-center gap-2">
                            <Check strokeWidth={3} size={24} /> What People Love
                        </h3>
                        <ul className="space-y-4">
                            {product.topPros.map((pro, i) => (
                                <li key={i} className="flex items-start gap-3">
                                    <div className="mt-1 min-w-[20px] h-5 rounded-full bg-emerald-100 dark:bg-emerald-800 flex items-center justify-center text-xs font-bold text-emerald-600 dark:text-emerald-300">
                                        {i + 1}
                                    </div>
                                    <div>
                                        <p className="font-semibold text-[var(--text)]">{pro.title}</p>
                                        <p className="text-sm text-[var(--text-muted)]">Mentioned {pro.count.toLocaleString()} times</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Cons */}
                    <div className="bg-rose-50/50 dark:bg-rose-900/10 rounded-2xl p-6 border border-rose-100 dark:border-rose-900/30">
                        <h3 className="text-rose-700 dark:text-rose-400 font-bold text-xl mb-6 flex items-center gap-2">
                            <AlertTriangle strokeWidth={2.5} size={24} /> Common Complaints
                        </h3>
                        <ul className="space-y-4">
                            {product.topCons.map((con, i) => (
                                <li key={i} className="flex items-start gap-3">
                                    <div className="mt-1 min-w-[20px] h-5 rounded-full bg-rose-100 dark:bg-rose-800 flex items-center justify-center text-xs font-bold text-rose-600 dark:text-rose-300">
                                        !
                                    </div>
                                    <div>
                                        <p className="font-semibold text-[var(--text)]">{con.title}</p>
                                        <p className="text-sm text-[var(--text-muted)]">Mentioned {con.count.toLocaleString()} times</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Real User Quotes */}
                <section className="mb-12">
                    <h3 className="font-bold text-2xl mb-6 flex items-center gap-3">
                        <Quote className="text-[var(--primary)]" /> Real User Reviews
                    </h3>
                    <div className="grid sm:grid-cols-2 gap-4">
                        {product.quotes.map((quote, i) => (
                            <blockquote key={i} className="bg-[var(--surface)] p-6 rounded-xl border border-[var(--border)] relative">
                                <p className="italic text-[var(--text)] text-lg mb-4">"{quote.text}"</p>
                                <footer className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
                                    <div className="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs">
                                        {quote.author[0]}
                                    </div>
                                    {quote.author} on <SourceBadge source={quote.source} />
                                </footer>
                            </blockquote>
                        ))}
                    </div>
                </section>

                {/* Ask AI Section */}
                <section className="bg-[var(--background)] rounded-2xl border-2 border-[var(--border)] p-6 sm:p-8">
                    <h3 className="font-bold text-xl mb-4 flex items-center gap-2">
                        <MessageSquare className="text-[var(--secondary)]" /> Ask AI About This Product
                    </h3>

                    <div className="flex flex-wrap gap-2 mb-6">
                        <QuickQuestion productName={product.title}>Does this work with glasses?</QuickQuestion>
                        <QuickQuestion productName={product.title}>How's the battery life really?</QuickQuestion>
                        <QuickQuestion productName={product.title}>Is it worth the price?</QuickQuestion>
                        <QuickQuestion productName={product.title}>Compare to alternatives</QuickQuestion>
                    </div>

                    <form onSubmit={handleChatSubmit} className="relative">
                        <input
                            type="text"
                            value={chatQuery}
                            onChange={(e) => setChatQuery(e.target.value)}
                            placeholder={`Ask anything about ${product.title}...`}
                            className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl py-4 px-4 pr-24 text-[var(--text)] focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent transition-all shadow-sm"
                        />
                        <button
                            type="submit"
                            className="absolute right-2 top-2 bottom-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white px-4 rounded-lg font-bold text-sm transition-colors"
                        >
                            Ask AI
                        </button>
                    </form>
                </section>

                {/* Modals */}
                <SourcesModal
                    isOpen={sourcesOpen}
                    onClose={() => setSourcesOpen(false)}
                    productTitle={product.title}
                    sourceCount={product.sourceCount}
                    totalReviews={product.reviewCount}
                />

            </div>
        </BrowseLayout>
    );
}
