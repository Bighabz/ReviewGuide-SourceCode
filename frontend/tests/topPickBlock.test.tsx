import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TopPickBlock from '@/components/TopPickBlock'

const defaultProps = {
    productName: 'Sony WH-1000XM5',
    headline: 'Best ANC headphones',
    bestFor: 'Commuters',
    notFor: 'Audiophiles',
}

describe('TopPickBlock', () => {
    it('renders product name as heading', () => {
        render(<TopPickBlock {...defaultProps} />)
        expect(screen.getByText('Sony WH-1000XM5')).toBeInTheDocument()
    })

    it('renders headline reason', () => {
        render(<TopPickBlock {...defaultProps} />)
        expect(screen.getByText('Best ANC headphones')).toBeInTheDocument()
    })

    it('renders best-for and not-for sections', () => {
        render(<TopPickBlock {...defaultProps} />)
        expect(screen.getByText('Commuters')).toBeInTheDocument()
        expect(screen.getByText('Audiophiles')).toBeInTheDocument()
        expect(screen.getByText('Best for:')).toBeInTheDocument()
        expect(screen.getByText('Look elsewhere if:')).toBeInTheDocument()
    })

    it('renders Our Top Pick badge', () => {
        render(<TopPickBlock {...defaultProps} />)
        expect(screen.getByText('Our Top Pick')).toBeInTheDocument()
    })

    it('renders affiliate link when provided', () => {
        render(<TopPickBlock {...defaultProps} affiliateUrl="https://amazon.com/sony" />)
        const links = screen.getAllByRole('link')
        const ctaLink = links.find((l) => l.getAttribute('href') === 'https://amazon.com/sony')
        expect(ctaLink).toBeDefined()
        expect(ctaLink).toHaveAttribute('href', 'https://amazon.com/sony')
    })

    it('renders without affiliate link when not provided', () => {
        render(<TopPickBlock {...defaultProps} />)
        const links = screen.queryAllByRole('link')
        const amazonLinks = links.filter((l) => l.getAttribute('href')?.includes('amazon'))
        expect(amazonLinks).toHaveLength(0)
    })
})
