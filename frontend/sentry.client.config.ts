/**
 * Sentry client-side config (browser).
 *
 * Added 2026-04-21 as part of the stabilization sprint.
 * Requires:
 *   npm i @sentry/nextjs
 *   Set NEXT_PUBLIC_SENTRY_DSN in Vercel env vars (production + preview).
 *
 * If DSN is empty, Sentry.init is a no-op — safe for local dev.
 */
import * as Sentry from '@sentry/nextjs'

const DSN = process.env.NEXT_PUBLIC_SENTRY_DSN

if (DSN) {
  Sentry.init({
    dsn: DSN,
    environment: process.env.NEXT_PUBLIC_VERCEL_ENV || 'development',
    // Capture 10% of transactions for performance monitoring.
    tracesSampleRate: 0.1,
    // Session replays disabled by default to save quota.
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0.1,
    // Drop known-benign browser noise before sending.
    beforeSend(event, hint) {
      const msg = (hint?.originalException as Error | undefined)?.message || ''
      // Browser extension / third-party noise — don't use our quota on these.
      if (/ResizeObserver loop limit exceeded/i.test(msg)) return null
      if (/chrome-extension:/i.test(msg)) return null
      return event
    },
  })
}
