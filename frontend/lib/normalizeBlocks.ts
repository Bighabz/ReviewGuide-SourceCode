/**
 * Block Normalizer
 *
 * Normalizes the two coexisting UI block schemas into a single canonical shape.
 * Old format: { block_type, payload, title }
 * New format: { type, data, title }
 * Canonical:  { type, data, title? }
 */

export interface NormalizedBlock {
    type: string
    data: unknown
    title?: string
}

/** Map old block_type values to canonical type names */
const BLOCK_TYPE_MAP: Record<string, string> = {
    carousel: 'carousel',
    product_cards: 'product_cards',
    product_review: 'product_review',
    product_recommendations: 'product_recommendations',
    affiliate_links: 'affiliate_links',
    hotel_cards: 'hotels',
    flight_cards: 'flights',
    itinerary: 'itinerary',
}

export function normalizeBlocks(rawBlocks: any[]): NormalizedBlock[] {
    if (!rawBlocks?.length) return []

    return rawBlocks.map((block): NormalizedBlock => {
        // New format: already has type + data
        if (block.type && block.data !== undefined) {
            return { type: block.type, data: block.data, title: block.title }
        }

        // Old format: block_type + payload
        if (block.block_type) {
            const canonicalType = BLOCK_TYPE_MAP[block.block_type] ?? block.block_type
            return { type: canonicalType, data: block.payload, title: block.title }
        }

        // Fallback: return as-is
        return { type: block.type ?? 'unknown', data: block.data, title: block.title }
    })
}
