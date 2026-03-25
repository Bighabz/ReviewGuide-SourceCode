import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { UIBlocks } from '@/components/blocks/BlockRegistry'
import type { NormalizedBlock } from '@/lib/normalizeBlocks'

describe('BlockRegistry top_pick dispatch', () => {
    it('renders top_pick block type via registry', () => {
        const blocks: NormalizedBlock[] = [
            {
                type: 'top_pick',
                data: {
                    product_name: 'Test Product',
                    headline: 'Great choice',
                    best_for: 'Everyone',
                    not_for: 'Nobody',
                },
            },
        ]
        render(<UIBlocks blocks={blocks} />)
        expect(screen.getByText('Test Product')).toBeInTheDocument()
        expect(screen.getByText('Our Top Pick')).toBeInTheDocument()
    })

    it('renders top_pick before product_review blocks', () => {
        const blocks: NormalizedBlock[] = [
            {
                type: 'top_pick',
                data: {
                    product_name: 'Top Pick Product',
                    headline: 'Best in class',
                    best_for: 'Power users',
                    not_for: 'Budget shoppers',
                },
            },
            {
                type: 'product_review',
                data: {
                    product_name: 'Review Product',
                    rating: '4.5/5',
                    summary: 'Good product',
                    affiliate_links: [],
                },
            },
        ]
        const { container } = render(<UIBlocks blocks={blocks} />)
        const allText = container.textContent ?? ''
        const topPickPos = allText.indexOf('Top Pick Product')
        const reviewPos = allText.indexOf('Review Product')
        expect(topPickPos).toBeGreaterThan(-1)
        expect(reviewPos).toBeGreaterThan(-1)
        expect(topPickPos).toBeLessThan(reviewPos)
    })

    it('does not crash when top_pick data is empty', () => {
        const blocks: NormalizedBlock[] = [
            {
                type: 'top_pick',
                data: {},
            },
        ]
        // Should not throw
        expect(() => render(<UIBlocks blocks={blocks} />)).not.toThrow()
    })
})
