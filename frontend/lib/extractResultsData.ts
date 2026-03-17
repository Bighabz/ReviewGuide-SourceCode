/**
 * extractResultsData — Phase 15 Results Screen data extraction utility
 *
 * Walks a Message[] array (from localStorage) and extracts:
 *   - sessionTitle: first user message content
 *   - summaryText: first assistant message content
 *   - products: merged product list from inline_product_card / products blocks
 *   - sources: deduplicated source list from review_sources blocks
 */

import type { Message } from '@/components/ChatContainer'

export interface ExtractedProduct {
  name: string
  price?: number
  url?: string
  image_url?: string
  merchant?: string
  description?: string
}

export interface ExtractedSource {
  site_name: string
  url: string
  title: string
  snippet?: string
}

export interface ResultsData {
  sessionTitle: string
  summaryText: string
  products: ExtractedProduct[]
  sources: ExtractedSource[]
}

/**
 * Resolve products array from a single ui_block, handling both:
 *   - block.data.products (normalized structure)
 *   - block.products (flat structure, no .data wrapper)
 */
function resolveProducts(block: any): ExtractedProduct[] {
  const products =
    (block?.data?.products as any[] | undefined) ??
    (block?.products as any[] | undefined)
  if (!Array.isArray(products)) return []
  return products.map((p: any): ExtractedProduct => ({
    name: p.name ?? '',
    price: p.price,
    url: p.url,
    image_url: p.image_url,
    merchant: p.merchant,
    description: p.description,
  }))
}

/**
 * Extract sources from a review_sources ui_block, handling both:
 *   - block.data.products[].sources[] (normalized structure)
 *   - block.products[].sources[] (flat structure)
 */
function resolveReviewSources(block: any): ExtractedSource[] {
  const productList: any[] =
    (block?.data?.products as any[] | undefined) ??
    (block?.products as any[] | undefined) ??
    []
  const sources: ExtractedSource[] = []
  for (const product of productList) {
    const productSources: any[] = Array.isArray(product?.sources) ? product.sources : []
    for (const s of productSources) {
      if (s?.url && s?.site_name) {
        sources.push({
          site_name: s.site_name,
          url: s.url,
          title: s.title ?? s.site_name,
          snippet: s.snippet,
        })
      }
    }
  }
  return sources
}

/**
 * Deduplicate an array of sources by URL (last occurrence wins — keeps order of first seen).
 */
function deduplicateSources(sources: ExtractedSource[]): ExtractedSource[] {
  const seen = new Set<string>()
  const result: ExtractedSource[] = []
  for (const source of sources) {
    if (!seen.has(source.url)) {
      seen.add(source.url)
      result.push(source)
    }
  }
  return result
}

/**
 * Extract products, sources, sessionTitle and summaryText from a Message array.
 *
 * Block types handled:
 *   'inline_product_card' — compact product card list (chat view)
 *   'products'            — product carousel items
 *   'review_sources'      — source citations with per-product source lists
 */
export default function extractResultsData(messages: Message[]): ResultsData {
  if (!Array.isArray(messages) || messages.length === 0) {
    return { sessionTitle: 'Research Results', summaryText: '', products: [], sources: [] }
  }

  const userMessages = messages.filter((m) => m.role === 'user')
  const assistantMessages = messages.filter((m) => m.role === 'assistant')

  const sessionTitle =
    userMessages.length > 0 && userMessages[0].content
      ? userMessages[0].content
      : 'Research Results'

  const summaryText =
    assistantMessages.length > 0 && assistantMessages[0].content
      ? assistantMessages[0].content
      : ''

  const allProducts: ExtractedProduct[] = []
  const allSources: ExtractedSource[] = []

  for (const msg of assistantMessages) {
    const blocks: any[] = Array.isArray(msg.ui_blocks) ? msg.ui_blocks : []
    for (const block of blocks) {
      const type: string = block?.type ?? ''
      if (type === 'inline_product_card' || type === 'products') {
        allProducts.push(...resolveProducts(block))
      } else if (type === 'review_sources') {
        allSources.push(...resolveReviewSources(block))
      }
    }
  }

  return {
    sessionTitle,
    summaryText,
    products: allProducts,
    sources: deduplicateSources(allSources),
  }
}
