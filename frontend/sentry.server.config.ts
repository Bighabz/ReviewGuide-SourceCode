/**
 * Sentry server-side config (Next.js server + edge runtime).
 *
 * Added 2026-04-21. Uses the non-public SENTRY_DSN for server-side errors,
 * falling back to NEXT_PUBLIC_SENTRY_DSN if only the public one is set.
 */
import * as Sentry from '@sentry/nextjs'

const DSN = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN

if (DSN) {
  Sentry.init({
    dsn: DSN,
    environment: process.env.VERCEL_ENV || process.env.NODE_ENV || 'development',
    tracesSampleRate: 0.1,
  })
}
