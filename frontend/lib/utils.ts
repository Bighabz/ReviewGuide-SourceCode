// Prefix used when user clicks a suggestion button
// Backend uses this to detect suggestion clicks
export const SUGGESTION_CLICK_PREFIX = 'You chose:'

/**
 * Format timestamp to relative time (e.g., "5 minutes ago", "Just now")
 */
export function formatTimestamp(timestamp: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - timestamp.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  // Just now (< 1 minute)
  if (diffMins < 1) {
    return 'Just now'
  }

  // Minutes ago (< 1 hour)
  if (diffMins < 60) {
    return `${diffMins} ${diffMins === 1 ? 'minute' : 'minutes'} ago`
  }

  // Hours ago (< 24 hours)
  if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`
  }

  // Days ago (< 7 days)
  if (diffDays < 7) {
    return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`
  }

  // Full date for older messages
  const options: Intl.DateTimeFormatOptions = {
    month: 'short',
    day: 'numeric',
    year: timestamp.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  }
  return timestamp.toLocaleDateString(undefined, options)
}

/**
 * Format timestamp to full date and time
 */
export function formatFullTimestamp(timestamp: Date): string {
  return timestamp.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
