
import React, { useState } from 'react';
import { ProductItem } from '@/lib/browseData';
import { StarRating } from '../StarRating';
import Link from 'next/link';
import { Package, ExternalLink } from 'lucide-react';

interface ProductCardProps {
    item: ProductItem;
    aiSummary?: string;
    onClick?: (item: ProductItem) => void;
}

export default function ProductCard({ item, aiSummary, onClick }: ProductCardProps) {
    const [imageError, setImageError] = useState(false);

    // Use AI summary if provided, otherwise fall back to description or generate from pros
    const displaySummary = aiSummary || item.description ||
        (item.topPros && item.topPros.length > 0
            ? `${item.topPros[0].title}. ${item.topPros[1]?.title || ''}`
            : '');

    return (
        <Link href={`/product/${item.id}`} className="block group">
            <div
                className="product-card bg-[var(--card-bg)] hover:bg-[var(--card-hover)] text-[var(--text)] rounded-xl overflow-hidden shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)] border border-[var(--border)] transition-all duration-300 transform hover:scale-[1.02] h-full flex flex-col cursor-pointer"
                onClick={(e) => {
                    if (onClick) {
                        e.preventDefault();
                        onClick(item);
                    }
                }}
            >
                {/* Image Section */}
                <div className="aspect-[4/3] relative bg-[var(--surface)] overflow-hidden">
                    {imageError ? (
                        <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-[var(--primary)]/5 via-[var(--surface)] to-[var(--accent)]/5 text-[var(--text-muted)]">
                            <div className="p-4 rounded-2xl bg-[var(--background)]/60 backdrop-blur-sm mb-2 border border-[var(--border)]">
                                <Package size={32} className="opacity-40" />
                            </div>
                            <span className="text-xs font-medium opacity-60">{item.category}</span>
                        </div>
                    ) : (
                        <img
                            src={item.image}
                            alt={item.title}
                            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                            loading="lazy"
                            onError={() => setImageError(true)}
                        />
                    )}

                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>

                {/* Content Section */}
                <div className="p-3 sm:p-4 flex-1 flex flex-col gap-2">
                    {/* Title */}
                    <h3 className="font-semibold text-sm sm:text-base line-clamp-2 leading-tight group-hover:text-[var(--primary)] transition-colors">
                        {item.title}
                    </h3>

                    {/* Rating + Price Row */}
                    <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
                            <StarRating value={item.rating} size={14} />
                            <span>({item.reviewCount.toLocaleString()})</span>
                        </div>
                        <span className="font-bold text-[var(--text)] whitespace-nowrap text-sm">
                            {item.currency}{item.price.toLocaleString()}
                        </span>
                    </div>

                    {/* AI Summary */}
                    {displaySummary && (
                        <p className="text-xs text-[var(--text-secondary)] line-clamp-2 leading-relaxed mt-1">
                            {displaySummary}
                        </p>
                    )}

                    {/* View Deal Button */}
                    <div className="mt-auto pt-3">
                        <button
                            className="w-full py-2 px-3 rounded-lg bg-[var(--primary)] text-white text-sm font-medium hover:bg-[var(--primary-hover)] transition-colors flex items-center justify-center gap-2"
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                if (item.affiliateLink) {
                                    window.open(item.affiliateLink, '_blank');
                                }
                            }}
                        >
                            View Deal
                            <ExternalLink size={14} />
                        </button>
                    </div>
                </div>
            </div>
        </Link>
    );
}
