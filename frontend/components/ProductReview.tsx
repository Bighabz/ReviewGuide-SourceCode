'use client'

import { motion } from 'framer-motion'
import { ThumbsUp, ThumbsDown, ExternalLink, Star } from 'lucide-react'

interface AffiliateLink {
  product_id: string
  title: string
  price: number
  currency: string
  affiliate_link: string
  merchant: string
  image_url?: string
  rating?: number
  review_count?: number
}

interface ProductReviewProps {
  product: {
    product_name: string
    rating: string
    summary: string
    image_url?: string
    features: string[]
    pros: Array<{
      description: string
      source_ids?: number[]
      citations?: Array<{
        id: number
        url: string
        title: string
      }>
    }>
    cons: Array<{
      description: string
      source_ids?: number[]
      citations?: Array<{
        id: number
        url: string
        title: string
      }>
    }>
    affiliate_links: AffiliateLink[]
    rank: number
  }
}

export default function ProductReview({ product }: ProductReviewProps) {
  const {
    product_name,
    rating,
    summary,
    image_url,
    features,
    pros,
    cons,
    affiliate_links,
  } = product

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      whileHover={{ y: -2, boxShadow: '0 8px 30px rgba(0,0,0,0.08)' }}
      className="border border-[var(--border)] rounded-xl p-3 sm:p-6 bg-[var(--surface-elevated)] shadow-card transition-colors">
      {/* Product Header with Image */}
      <div className="mb-3 sm:mb-4">
        <div className="flex gap-3 sm:gap-4">
          {image_url && (
            <div className="flex-shrink-0">
              <img
                src={image_url}
                alt={product_name}
                className="w-16 h-16 sm:w-28 sm:h-28 object-contain rounded-lg sm:rounded-xl bg-white"
                loading="lazy"
              />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-base sm:text-xl font-bold font-serif text-[var(--text)] tracking-tight">{product_name}</h3>
              {rating && rating !== 'N/A' && rating !== '0/5' && (
                <div className="flex items-center gap-1 text-amber-500">
                  <Star size={16} fill="currentColor" />
                  <span className="text-sm font-medium">{rating}</span>
                </div>
              )}
            </div>
            {summary && (
              <p className="mt-2 text-[var(--text-secondary)] text-sm">{summary}</p>
            )}
          </div>
        </div>
      </div>

      {/* Features */}
      {features && features.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold font-serif text-[var(--text-secondary)] mb-2">Key Features</h4>
          <ul className="list-disc list-inside space-y-1">
            {features.map((feature, idx) => (
              <li key={idx} className="text-sm text-[var(--text-secondary)]">{feature}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Pros and Cons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {/* Pros */}
        {pros && pros.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold font-serif text-[var(--success)] mb-2 flex items-center gap-1">
              <ThumbsUp size={14} />
              Pros
            </h4>
            <ul className="space-y-2">
              {pros.map((pro, idx) => (
                <li key={idx} className="text-sm text-[var(--text-secondary)] flex items-start gap-2">
                  <span className="text-[var(--success)] mt-0.5">&#10003;</span>
                  <span>{pro.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Cons */}
        {cons && cons.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold font-serif text-[var(--error)] mb-2 flex items-center gap-1">
              <ThumbsDown size={14} />
              Cons
            </h4>
            <ul className="space-y-2">
              {cons.map((con, idx) => (
                <li key={idx} className="text-sm text-[var(--text-secondary)] flex items-start gap-2">
                  <span className="text-[var(--error)] mt-0.5">&#10007;</span>
                  <span>{con.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Affiliate Links */}
      {affiliate_links && affiliate_links.length > 0 && (
        <div className="mt-4 pt-4 border-t border-[var(--border)]">
          <h4 className="text-sm font-semibold font-serif text-[var(--text-secondary)] mb-3">Where to Buy</h4>
          <div className={`grid gap-2 sm:gap-3 ${affiliate_links.length >= 3 ? 'grid-cols-1 md:grid-cols-3' : affiliate_links.length === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 max-w-sm'}`}>
            {affiliate_links.map((link, idx) => {
              // Clean merchant name: "eBay (lawrenow-0)" → "eBay"
              const cleanMerchant = link.merchant
                .replace(/\s*\(.*?\)\s*/g, '')
                .replace(/^ebay.*/i, 'eBay')
                .trim() || 'Retailer'
              const priceStr = link.price > 0
                ? (link.currency === 'USD' ? `$${link.price.toFixed(2)}` : `${link.currency} ${link.price.toFixed(2)}`)
                : null
              return (
                <a
                  key={idx}
                  href={link.affiliate_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between p-3 border border-[var(--border)] rounded-lg hover:border-[var(--primary)] hover:bg-[var(--surface-hover)] transition-colors group"
                >
                  <div className="flex-1 min-w-0">
                    <span className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">{cleanMerchant}</span>
                    {link.rating && (
                      <span className="inline-flex items-center gap-0.5 text-amber-500 ml-2">
                        <Star size={10} fill="currentColor" />
                        <span className="text-xs">{link.rating}</span>
                      </span>
                    )}
                    <p className="text-base sm:text-lg font-bold text-[var(--text)] mt-1">
                      {priceStr || 'Check price →'}
                    </p>
                  </div>
                  <ExternalLink size={16} className="text-[var(--text-muted)] group-hover:text-[var(--primary)] flex-shrink-0 ml-2" />
                </a>
              )
            })}
          </div>
        </div>
      )}
    </motion.div>
  )
}
