import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for RG smoke tests.
 *
 * Added 2026-04-21. To run:
 *   cd frontend && npx playwright test tests/e2e/smoke.spec.ts
 *   BASE_URL=https://staging.reviewguide.ai npx playwright test ...
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  use: {
    baseURL: process.env.BASE_URL || 'https://www.reviewguide.ai',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'chromium-mobile',
      use: { ...devices['iPhone 14 Pro'] },
    },
  ],
})
