/**
 * Frontend Constants
 * Centralized configuration for UI strings, trending searches, and defaults
 */

// Trending searches shown on the welcome screen
export const TRENDING_SEARCHES = [
  'Best Gaming Laptop',
  'iPhone 17 Rumors',
  'Paris Travel Deals',
  'Vacuum for Dog Hair',
  'Best Running Shoes',
] as const

// Chat configuration
export const CHAT_CONFIG = {
  MAX_MESSAGE_LENGTH: 2000,
  SESSION_STORAGE_KEY: 'chat_session_id',
  USER_ID_STORAGE_KEY: 'chat_user_id',
  MESSAGES_STORAGE_KEY: 'chat_messages',
} as const

// SSE retry configuration
export const SSE_CONFIG = {
  MAX_RETRIES: 3,
  INITIAL_BACKOFF_MS: 1000,
  MAX_BACKOFF_MS: 10000,
  REQUEST_TIMEOUT_MS: 120000,
} as const

// UI text constants
export const UI_TEXT = {
  WELCOME_TITLE: 'Where should we begin?',
  TRENDING_LABEL: 'Trending Now',
  PLACEHOLDER_TEXT: 'Ask anything',
  LOADING_HISTORY: 'Loading chat history...',
  RECONNECTING: 'Reconnecting',
  ERROR_MESSAGE: 'Something went wrong. If this issue persists please try again.',
} as const

// Footer links
export const FOOTER_LINKS = [
  { label: 'About', href: '#' },
  { label: 'Privacy', href: '#' },
  { label: 'Affiliate Disclosure', href: '#', desktopOnly: true },
  { label: 'Contact', href: '#' },
] as const
