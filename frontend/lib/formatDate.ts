/**
 * Format a YYYY-MM-DD or ISO date string as "Apr 21, 2026".
 *
 * Returns null if `dateStr` is falsy; returns the original string
 * if parsing throws (so bad input degrades to raw display, not crash).
 *
 * Extracted 2026-04-21 from HotelCards/FlightCards/CarRentalCard where
 * three identical copies had drifted — single source of truth now.
 */
export function formatDate(dateStr?: string): string | null {
  if (!dateStr) return null
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}
