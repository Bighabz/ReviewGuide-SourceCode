/**
 * Static pre-cached responses for homepage buttons (suggestion chips + carousel cards).
 * These render instantly without hitting the API. Follow-up questions still go through
 * the live AI pipeline.
 *
 * To update a response: send the query on the live site, open browser DevTools Network tab,
 * find the SSE response, and paste the final message data here.
 */

export interface StaticResponse {
  content: string
  ui_blocks: any[]
  followups?: string[]
}

// Normalize query for matching: lowercase, trim, strip punctuation
function normalizeQuery(q: string): string {
  return q.toLowerCase().trim().replace(/[?.!,]+$/g, '')
}

/**
 * Check if a query matches a static response.
 * Returns the static response data if matched, null otherwise.
 */
export function getStaticResponse(query: string): StaticResponse | null {
  const normalized = normalizeQuery(query)
  for (const [key, value] of Object.entries(STATIC_RESPONSES)) {
    if (normalizeQuery(key) === normalized) return value
  }
  return null
}

/**
 * Static response data keyed by the exact query string from homepage buttons.
 * Each entry contains the full assistant message (content + ui_blocks + followups)
 * that would normally come from the streaming API.
 *
 * PLACEHOLDER: These need to be populated by capturing real API responses.
 * Set STATIC_RESPONSES_ENABLED=false to disable and always use live API.
 */
export const STATIC_RESPONSES_ENABLED = true

const STATIC_RESPONSES: Record<string, StaticResponse> = {
  // === SUGGESTION CHIPS (3) ===
  // To populate: send each query, capture the final SSE message, paste here

  // === CAROUSEL CARDS (5) ===
  // To populate: send each query, capture the final SSE message, paste here
}
