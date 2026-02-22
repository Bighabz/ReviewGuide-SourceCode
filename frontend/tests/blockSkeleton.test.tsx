import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import BlockSkeleton from '@/components/BlockSkeleton'
import { TOOL_BLOCK_MAP } from '@/lib/skeletonMap'

describe('BlockSkeleton', () => {
  it('test_skeleton_renders_for_product_cards', () => {
    render(
      <BlockSkeleton blockType="product_cards" count={4} layout="grid" />
    )
    // 4 product card skeletons — each has an image bar (h-48), title bar, subtitle bar, price bar
    // We identify them by the wrapping grid: expect 4 cards rendered inside the 2×2 grid
    const grid = document.querySelector('.grid')
    expect(grid).not.toBeNull()
    // Each card is a direct child of the grid
    const cards = grid!.children
    expect(cards).toHaveLength(4)
  })

  it('test_skeleton_renders_for_hotel_results', () => {
    render(
      <BlockSkeleton blockType="hotel_results" count={3} layout="list" />
    )
    // 3 hotel row skeletons — each has a flex row with w-32 image placeholder
    const imageBlocks = document.querySelectorAll('.w-32')
    expect(imageBlocks).toHaveLength(3)
  })

  it('test_skeleton_renders_for_flight_results', () => {
    render(
      <BlockSkeleton blockType="flight_results" count={3} layout="list" />
    )
    // 3 flight row skeletons — each has a carrier icon (w-10 h-10 rounded-full)
    const airlineIcons = document.querySelectorAll('.w-10.h-10.rounded-full')
    expect(airlineIcons).toHaveLength(3)
  })

  it('test_skeleton_renders_for_comparison_table', () => {
    render(
      <BlockSkeleton blockType="comparison_table" count={1} layout="list" />
    )
    // Comparison table skeleton has 1 wrapper plus rows; the wrapper exists
    const wrapper = document.querySelector('.rounded-xl')
    expect(wrapper).not.toBeNull()
  })

  it('test_skeleton_renders_for_itinerary', () => {
    render(
      <BlockSkeleton blockType="itinerary" count={5} layout="list" />
    )
    // 5 itinerary day skeletons — each has a day number circle (w-10 h-10 rounded-full)
    const dayCircles = document.querySelectorAll('.w-10.h-10.rounded-full')
    expect(dayCircles).toHaveLength(5)
  })

  it('test_tool_block_map_covers_all_expected_tools', () => {
    const expectedTools = [
      'product_search',
      'product_compose',
      'travel_search_hotels',
      'travel_search_flights',
      'travel_itinerary',
    ]

    expectedTools.forEach((tool) => {
      expect(TOOL_BLOCK_MAP).toHaveProperty(tool)
    })

    // Also verify the total key count matches exactly
    expect(Object.keys(TOOL_BLOCK_MAP)).toHaveLength(expectedTools.length)
  })

  it('test_skeleton_uses_animate_pulse', () => {
    const { container } = render(
      <BlockSkeleton blockType="product_cards" count={4} layout="grid" />
    )
    // The outermost wrapper must carry the animate-pulse class
    const pulsing = container.querySelector('.animate-pulse')
    expect(pulsing).not.toBeNull()
  })
})
