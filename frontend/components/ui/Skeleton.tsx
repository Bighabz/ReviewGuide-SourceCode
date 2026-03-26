'use client'

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular' | 'card'
  width?: string
  height?: string
}

export default function Skeleton({
  className = '',
  variant = 'text',
  width,
  height,
}: SkeletonProps) {
  const variantClasses = {
    text: 'h-4 rounded-md',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
    card: 'rounded-xl h-40',
  }

  return (
    <div
      className={`animate-shimmer ${variantClasses[variant]} ${className}`}
      style={{
        width: width || (variant === 'circular' ? '40px' : '100%'),
        height: height || undefined,
        background: 'linear-gradient(90deg, var(--surface) 25%, var(--surface-hover) 50%, var(--surface) 75%)',
        backgroundSize: '200% 100%',
      }}
    />
  )
}

export function ProductCardSkeleton() {
  return (
    <div className="p-5 rounded-xl border border-[var(--border)]" style={{ background: 'var(--surface-elevated)' }}>
      <div className="flex gap-4">
        <Skeleton variant="rectangular" width="96px" height="96px" />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="70%" height="20px" />
          <Skeleton variant="text" width="40%" height="14px" />
          <Skeleton variant="text" width="90%" height="14px" />
          <Skeleton variant="text" width="30%" height="32px" className="mt-2" />
        </div>
      </div>
    </div>
  )
}
