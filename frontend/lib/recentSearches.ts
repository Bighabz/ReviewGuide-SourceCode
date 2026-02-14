import { MAX_RECENT_SEARCHES } from './categoryConfig'

const STORAGE_KEY = 'reviewguide_recent_searches'

export interface RecentSearch {
  query: string
  productNames: string[]
  category: string
  timestamp: number
}

export function saveRecentSearch(search: RecentSearch): void {
  try {
    const existing = getRecentSearches()

    // Dedupe by query (case-insensitive)
    const filtered = existing.filter(
      (s) => s.query.toLowerCase() !== search.query.toLowerCase()
    )

    // Prepend new search and cap
    const updated = [search, ...filtered].slice(0, MAX_RECENT_SEARCHES)

    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  } catch {
    // localStorage unavailable (SSR, private browsing)
  }
}

export function getRecentSearches(): RecentSearch[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []

    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []

    // Basic validation
    return parsed.filter(
      (s: any) =>
        typeof s.query === 'string' &&
        Array.isArray(s.productNames) &&
        typeof s.timestamp === 'number'
    )
  } catch {
    return []
  }
}

export function clearRecentSearches(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // localStorage unavailable
  }
}
