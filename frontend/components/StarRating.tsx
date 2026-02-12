import { Star, StarHalf } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StarRatingProps {
    value: number
    max?: number
    size?: number
    className?: string
    showCount?: boolean
    count?: number
}

export function StarRating({
    value,
    max = 5,
    size = 16,
    className,
    showCount = false,
    count
}: StarRatingProps) {
    const fullStars = Math.floor(value)
    const hasHalfStar = value % 1 >= 0.5
    const emptyStars = max - fullStars - (hasHalfStar ? 1 : 0)

    return (
        <div className={cn("flex items-center gap-1", className)}>
            <div className="flex text-yellow-500">
                {[...Array(fullStars)].map((_, i) => (
                    <Star key={`full-${i}`} size={size} fill="currentColor" strokeWidth={0} />
                ))}
                {hasHalfStar && (
                    <div className="relative">
                        <Star size={size} className="text-gray-300" fill="currentColor" strokeWidth={0} />
                        <div className="absolute top-0 left-0 overflow-hidden w-1/2">
                            <Star size={size} className="text-yellow-500" fill="currentColor" strokeWidth={0} />
                        </div>
                    </div>
                )}
                {[...Array(emptyStars)].map((_, i) => (
                    <Star key={`empty-${i}`} size={size} className="text-gray-300" fill="currentColor" strokeWidth={0} />
                ))}
            </div>

            {showCount && (
                <span className="text-xs text-[var(--text-secondary)] font-medium ml-1">
                    {value.toFixed(1)} {count !== undefined && `(${count})`}
                </span>
            )}
        </div>
    )
}
