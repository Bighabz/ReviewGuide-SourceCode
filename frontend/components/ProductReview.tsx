'use client'

import { motion } from 'framer-motion'
import { ExternalLink, Star } from 'lucide-react'

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

function deriveMerchant(link: AffiliateLink): string {
  // 1. Try cleaning the merchant field
  const cleaned = link.merchant
    .replace(/\s*\(.*?\)\s*/g, '')
    .trim()
  if (cleaned && cleaned.toLowerCase() !== 'retailer') {
    if (/^ebay/i.test(cleaned)) return 'eBay'
    return cleaned
  }
  // 2. Fall back to URL parsing
  if (!link.affiliate_link) return 'Retailer'
  try {
    const host = new URL(link.affiliate_link).hostname.replace(/^www\./, '')
    const domainMap: Record<string, string> = {
      'amazon.com': 'Amazon', 'amzn.to': 'Amazon',
      'ebay.com': 'eBay',
      'walmart.com': 'Walmart',
      'bestbuy.com': 'Best Buy',
      'target.com': 'Target',
      'newegg.com': 'Newegg',
      'bhphotovideo.com': 'B&H Photo',
      'costco.com': 'Costco',
    }
    for (const [domain, label] of Object.entries(domainMap)) {
      if (host.includes(domain)) return label
    }
    return host.split('.')[0].replace(/(^|\-)(\w)/g, (_, sep, c) => (sep ? ' ' : '') + c.toUpperCase()).trim()
  } catch {
    return 'Retailer'
  }
}

const cardVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: 'easeOut' },
  },
  hover: {
    y: -4,
    boxShadow: '0 12px 32px rgba(28,25,23,0.10)',
    transition: { type: 'spring', stiffness: 400, damping: 28 },
  },
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
    affiliate_links,
  } = product

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
      className="border border-[var(--border)] rounded-xl p-3 sm:p-6 bg-[var(--surface-elevated)] shadow-card">
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
              <p className="mt-2 text-[var(--text-secondary)] text-sm line-clamp-2">{summary}</p>
            )}
          </div>
        </div>
      </div>

      {/* Editorial label badges */}
      {features && features.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {features.map((feature, idx) => (
            <span key={idx} className="text-xs font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full bg-[var(--primary)]/10 text-[var(--primary)]">{feature}</span>
          ))}
        </div>
      )}

      {/* Affiliate Links */}
      {affiliate_links && affiliate_links.length > 0 && (
        <div className="mt-3 pt-3 border-t border-[var(--border)]">
          <div className={`grid gap-2 sm:gap-3 ${affiliate_links.slice(0, 3).length >= 3 ? 'grid-cols-1 md:grid-cols-3' : affiliate_links.slice(0, 3).length === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 max-w-sm'}`}>
            {affiliate_links.slice(0, 3).map((link, idx) => {
              const cleanMerchant = deriveMerchant(link)
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
