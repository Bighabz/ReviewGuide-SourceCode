import type { SkeletonBlockType } from '@/components/BlockSkeleton'

/**
 * Maps MCP tool names (as they appear in status event text) to the rich block
 * type that the tool will eventually produce.  When a `status` SSE event
 * contains one of these tool names, ChatContainer renders a BlockSkeleton of
 * the corresponding type until the real `artifact` event arrives.
 */
export const TOOL_BLOCK_MAP: Record<string, SkeletonBlockType> = {
  'product_search':        'product_cards',
  'product_compose':       'product_cards',
  'travel_search_hotels':  'hotel_results',
  'travel_search_flights': 'flight_results',
  'travel_itinerary':      'itinerary',
}

export const BLOCK_SKELETON_CONFIG: Record<
  SkeletonBlockType,
  { count: number; layout: 'grid' | 'list' | 'horizontal-scroll' }
> = {
  product_cards:    { count: 4, layout: 'grid' as const },
  hotel_results:    { count: 3, layout: 'list' as const },
  flight_results:   { count: 3, layout: 'list' as const },
  comparison_table: { count: 1, layout: 'list' as const },
  itinerary:        { count: 5, layout: 'list' as const },
}
