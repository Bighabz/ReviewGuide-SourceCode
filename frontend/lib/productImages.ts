import { curatedLinks } from '@/lib/curatedLinks'

const CATEGORY_PLACEHOLDERS: Record<string, string> = {
  headphones:
    'data:image/svg+xml,' +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#8892A4" stroke-width="1.5"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>',
    ),
  laptop:
    'data:image/svg+xml,' +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#8892A4" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M2 20h20"/></svg>',
    ),
  default:
    'data:image/svg+xml,' +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#8892A4" stroke-width="1.5"><rect x="2" y="2" width="20" height="20" rx="2"/><circle cx="12" cy="12" r="3"/></svg>',
    ),
}

function detectCategory(name: string): string {
  const lower = name.toLowerCase()
  if (lower.match(/headphone|earbud|speaker|audio|airpod|bose|sony wh|jabra/)) return 'headphones'
  if (lower.match(/laptop|macbook|chromebook|notebook|computer/)) return 'laptop'
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
  return url.startsWith('data:image/svg+xml')
}
