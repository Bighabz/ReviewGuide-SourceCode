const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TrackClickParams {
  provider: string
  product_name?: string
  category?: string
  url: string
  session_id?: string
}

/**
 * Fire-and-forget POST to track an affiliate click, then open the URL.
 */
export function trackAffiliateClick(params: TrackClickParams) {
  // Fire tracking request (non-blocking)
  fetch(`${API_URL}/v1/affiliate/click`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  }).catch(() => {
    // Silently ignore tracking failures — don't block navigation
  })

  // Open affiliate link in new tab
  window.open(params.url, '_blank', 'noopener,noreferrer')
}
