import { curatedLinks } from '@/lib/curatedLinks'

/**
 * Look up a curated product by name across all categories.
 *
 * Returns an Amazon image URL (constructed from the stored ASIN) and the
 * affiliate URL for the first matching topic, or {null, null} if no match.
 *
 * Extracted 2026-04-21 from InlineProductCard.tsx and ResultsProductCard.tsx
 * where identical copies had drifted — single source of truth now.
 */
export function lookupCuratedProduct(
  name: string
): { imageUrl: string | null; affiliateUrl: string | null } {
  const nameLower = name.toLowerCase()
  for (const category of Object.values(curatedLinks)) {
    for (const topic of category) {
      const topicTitleLower = topic.title.toLowerCase()
      const topicTitleTail = topicTitleLower.split(' ').slice(1).join(' ').toLowerCase()
      if (
        topicTitleLower.includes(nameLower) ||
        (topicTitleTail && nameLower.includes(topicTitleTail))
      ) {
        const firstProduct = topic.products[0]
        if (firstProduct) {
          return {
            imageUrl: `https://images-na.ssl-images-amazon.com/images/I/${firstProduct.asin}._SL300_.jpg`,
            affiliateUrl: firstProduct.url,
          }
        }
      }
    }
  }
  return { imageUrl: null, affiliateUrl: null }
}
