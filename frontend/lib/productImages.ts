import { curatedLinks } from '@/lib/curatedLinks'

const CATEGORY_PLACEHOLDERS: Record<string, string> = {
  headphones: '/images/products/fallback-headphones.png',
  laptop: '/images/products/fallback-laptop.png',
  kitchen: '/images/products/fallback-kitchen.png',
  fitness: '/images/products/fallback-fitness.png',
  default: '/images/products/fallback-default.png',
}

function detectCategory(name: string): string {
  const lower = name.toLowerCase()
  if (lower.match(/headphone|earbud|speaker|audio|airpod|bose|sony wh|jabra/)) return 'headphones'
  if (lower.match(/laptop|macbook|chromebook|notebook|computer/)) return 'laptop'
  if (lower.match(/blender|mixer|air fryer|coffee|toaster|oven|cookware|kitchen/)) return 'kitchen'
  if (lower.match(/shoe|sneaker|running|treadmill|yoga|fitness|gym|weight/)) return 'fitness'
  return 'default'
}

/**
 * Look up a curated ASIN image by matching product name against topic titles.
 * curatedLinks products only have asin + url (no name field), so we match
 * against the topic title and return the first product's ASIN image.
 */
function lookupCuratedImage(name: string): string | null {
  const nameLower = name.toLowerCase()
  for (const category of Object.values(curatedLinks)) {
    for (const topic of category) {
      const topicWords = topic.title.toLowerCase().split(' ').slice(1).join(' ')
      if (
        topic.title.toLowerCase().includes(nameLower) ||
        nameLower.includes(topicWords)
      ) {
        const firstProduct = topic.products[0]
        if (firstProduct?.asin) {
          return `https://images-na.ssl-images-amazon.com/images/I/${firstProduct.asin}._SL300_.jpg`
        }
      }
    }
  }
  return null
}

/**
 * Resolve a product image using fallback chain:
 * 1. Direct image_url from API
 * 2. Curated ASIN image matched via topic title in curatedLinks
 * 3. Category placeholder SVG icon
 */
export function resolveProductImage(
  name: string,
  imageUrl?: string | null,
): string {
  if (imageUrl) return imageUrl
  const curated = lookupCuratedImage(name)
  if (curated) return curated
  const category = detectCategory(name)
  return CATEGORY_PLACEHOLDERS[category] ?? CATEGORY_PLACEHOLDERS.default
}

export function isPlaceholderImage(url: string): boolean {
  return url.startsWith('data:image/svg+xml') || url.startsWith('/images/products/fallback-')
}
