'use client'

export type SkeletonBlockType =
  | 'product_cards'
  | 'hotel_results'
  | 'flight_results'
  | 'comparison_table'
  | 'itinerary'

export interface BlockSkeletonProps {
  blockType: SkeletonBlockType
  count: number
  layout: 'grid' | 'list' | 'horizontal-scroll'
}

// --- Individual skeleton shape primitives ---

function SkeletonBar({ className }: { className: string }) {
  return <div className={`rounded bg-stone-200 dark:bg-stone-700 ${className}`} />
}

// --- Per-block-type skeleton cards ---

function ProductCardSkeleton() {
  return (
    <div className="rounded-xl border border-stone-200 dark:border-stone-700 bg-[var(--surface)] p-3 flex flex-col gap-3">
      {/* Image placeholder */}
      <SkeletonBar className="h-48 w-full rounded-lg" />
      {/* Title */}
      <SkeletonBar className="h-4 w-4/5" />
      {/* Subtitle */}
      <SkeletonBar className="h-3 w-3/5" />
      {/* Price */}
      <SkeletonBar className="h-5 w-2/5" />
    </div>
  )
}

function HotelRowSkeleton() {
  return (
    <div className="rounded-xl border border-stone-200 dark:border-stone-700 bg-[var(--surface)] overflow-hidden flex flex-row h-24">
      {/* Image left */}
      <SkeletonBar className="w-32 h-24 rounded-none shrink-0" />
      {/* Content right */}
      <div className="flex-1 flex flex-col justify-center gap-2 p-4">
        {/* Hotel name */}
        <SkeletonBar className="h-4 w-3/5" />
        {/* Rating */}
        <SkeletonBar className="h-3 w-2/5" />
        {/* Price */}
        <SkeletonBar className="h-4 w-1/4" />
      </div>
    </div>
  )
}

function FlightRowSkeleton() {
  return (
    <div className="rounded-xl border border-stone-200 dark:border-stone-700 bg-[var(--surface)] p-5 flex flex-row items-center gap-4">
      {/* Airline icon */}
      <SkeletonBar className="w-10 h-10 rounded-full shrink-0" />
      {/* Departure time */}
      <SkeletonBar className="h-6 w-14 shrink-0" />
      {/* Duration bar */}
      <div className="flex-1 flex flex-col items-center gap-1">
        <SkeletonBar className="h-3 w-16" />
        <SkeletonBar className="h-1.5 w-full" />
        <SkeletonBar className="h-3 w-12" />
      </div>
      {/* Arrival time */}
      <SkeletonBar className="h-6 w-14 shrink-0" />
      {/* Price */}
      <SkeletonBar className="h-7 w-16 shrink-0" />
    </div>
  )
}

function ComparisonTableSkeleton() {
  // 4 columns, 1 header + 3 data rows
  const cols = 4
  const dataRows = 3

  return (
    <div className="rounded-xl border border-stone-200 dark:border-stone-700 bg-[var(--surface)] overflow-hidden">
      {/* Header row */}
      <div className="flex border-b border-stone-200 dark:border-stone-700 bg-stone-100 dark:bg-stone-800 px-4 py-3 gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <SkeletonBar key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* Data rows */}
      {Array.from({ length: dataRows }).map((_, row) => (
        <div
          key={row}
          className="flex px-4 py-3 gap-4 border-b last:border-b-0 border-stone-200 dark:border-stone-700"
        >
          {Array.from({ length: cols }).map((_, col) => (
            <SkeletonBar
              key={col}
              className={`flex-1 ${col === 0 ? 'h-4 w-2/3' : 'h-3'}`}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

function ItineraryDaySkeleton() {
  return (
    <div className="flex gap-4 py-4 border-b last:border-b-0 border-stone-200 dark:border-stone-700">
      {/* Day number circle */}
      <SkeletonBar className="w-10 h-10 rounded-full shrink-0" />
      {/* Activity content */}
      <div className="flex-1 flex flex-col gap-2 pt-1">
        {/* Activity title */}
        <SkeletonBar className="h-4 w-3/5" />
        {/* Description line 1 */}
        <SkeletonBar className="h-3 w-full" />
        {/* Description line 2 */}
        <SkeletonBar className="h-3 w-4/5" />
      </div>
    </div>
  )
}

// --- Main export ---

export default function BlockSkeleton({ blockType, count, layout }: BlockSkeletonProps) {
  const items = Array.from({ length: count })

  if (blockType === 'product_cards') {
    return (
      <div className="animate-pulse space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {items.map((_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      </div>
    )
  }

  if (blockType === 'hotel_results') {
    return (
      <div className="animate-pulse space-y-4">
        {items.map((_, i) => (
          <HotelRowSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (blockType === 'flight_results') {
    return (
      <div className="animate-pulse space-y-4">
        {items.map((_, i) => (
          <FlightRowSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (blockType === 'comparison_table') {
    return (
      <div className="animate-pulse">
        <ComparisonTableSkeleton />
      </div>
    )
  }

  if (blockType === 'itinerary') {
    return (
      <div className="animate-pulse rounded-xl border border-stone-200 dark:border-stone-700 bg-[var(--surface)] px-4">
        {items.map((_, i) => (
          <ItineraryDaySkeleton key={i} />
        ))}
      </div>
    )
  }

  return null
}
