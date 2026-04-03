/**
 * Phase 12 — NAV-01 (mobile tab bar) + NAV-05 (safe area)
 *
 * Tests for MobileTabBar component (frontend/components/MobileTabBar.tsx).
 *
 * Updated in Phase 22 to match current component:
 * - 3 Link tabs (Home, History, Saved) + 1 Settings button = 4 interactive elements
 * - Tabs use <Link> (renders as <a>), not <button>
 * - Active detection via data-active="true" attribute
 * - No "Ask" FAB / no Discover / no Compare / no Profile labels
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'

// Capture the router.push mock so individual tests can assert against it.
const mockPush = vi.fn()

let currentPathname = '/'

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => currentPathname,
  useSearchParams: () => new URLSearchParams(),
}))

import MobileTabBar from '@/components/MobileTabBar'

describe('MobileTabBar — tab count and labels (NAV-01)', () => {
  beforeEach(() => {
    currentPathname = '/'
    mockPush.mockClear()
  })

  it('renders exactly 4 interactive elements (3 link tabs + 1 settings button)', () => {
    render(<MobileTabBar />)
    // 3 tabs rendered as <Link> (role="link") + 1 Settings button (role="button")
    const links = screen.getAllByRole('link')
    const buttons = screen.getAllByRole('button')
    expect(links).toHaveLength(3)
    expect(buttons).toHaveLength(1)
  })

  it('renders Home label', () => {
    render(<MobileTabBar />)
    expect(screen.getByText('Home')).toBeTruthy()
  })

  it('renders History label', () => {
    render(<MobileTabBar />)
    expect(screen.getByText('History')).toBeTruthy()
  })

  it('renders Saved label', () => {
    render(<MobileTabBar />)
    expect(screen.getByText('Saved')).toBeTruthy()
  })

  it('renders Settings label', () => {
    render(<MobileTabBar />)
    expect(screen.getByText('Settings')).toBeTruthy()
  })
})

describe('MobileTabBar — History link navigation (NAV-01)', () => {
  beforeEach(() => {
    currentPathname = '/'
    mockPush.mockClear()
  })

  it('History link has href="/chat"', () => {
    render(<MobileTabBar />)
    // History tab is a Link (renders as <a>)
    const historyLink = screen.getByText('History').closest('a')
    expect(historyLink).toBeTruthy()
    const href = historyLink!.getAttribute('href') ?? ''
    expect(href).toBe('/chat')
  })

  it('Home link has href="/"', () => {
    render(<MobileTabBar />)
    const homeLink = screen.getByText('Home').closest('a')
    expect(homeLink).toBeTruthy()
    const href = homeLink!.getAttribute('href') ?? ''
    expect(href).toBe('/')
  })
})

describe('MobileTabBar — active tab highlighting (NAV-01)', () => {
  it('Home tab has active styling when pathname is /browse', () => {
    currentPathname = '/browse'
    render(<MobileTabBar />)
    const homeLink = screen.getByText('Home').closest('a')
    expect(homeLink).toBeTruthy()
    // Active tab uses data-active="true" or aria-current="page"
    const isActive =
      homeLink!.getAttribute('aria-current') === 'page' ||
      homeLink!.className.includes('active') ||
      homeLink!.className.includes('blue') ||
      homeLink!.getAttribute('data-active') === 'true'
    expect(isActive).toBe(true)
  })

  it('Home tab does NOT have active styling when pathname is /chat', () => {
    currentPathname = '/chat'
    render(<MobileTabBar />)
    const homeLink = screen.getByText('Home').closest('a')
    const isActive =
      homeLink!.getAttribute('aria-current') === 'page' ||
      homeLink!.getAttribute('data-active') === 'true'
    expect(isActive).toBe(false)
  })
})

describe('MobileTabBar — safe area padding (NAV-05)', () => {
  it('nav element has paddingBottom that includes env(safe-area-inset-bottom)', () => {
    render(<MobileTabBar />)
    // The root nav element should include env(safe-area-inset-bottom) in its inline style.
    const nav = document.querySelector('nav')
    expect(nav).toBeTruthy()
    const pb = nav!.style.paddingBottom
    expect(pb).toContain('env(safe-area-inset-bottom)')
  })
})

describe('MobileTabBar — keyboard hide behavior (NAV-01)', () => {
  let originalVisualViewport: VisualViewport | null

  beforeEach(() => {
    currentPathname = '/'
    originalVisualViewport = window.visualViewport
  })

  afterEach(() => {
    // Restore visualViewport after each test.
    Object.defineProperty(window, 'visualViewport', {
      value: originalVisualViewport,
      writable: true,
      configurable: true,
    })
  })

  it('tab bar is hidden when keyboard is open (viewport height < 75% of innerHeight)', () => {
    // Simulate keyboard open: visualViewport.height is less than 75% of window.innerHeight.
    const resizeListeners: Array<() => void> = []
    const mockViewport = {
      height: window.innerHeight * 0.5, // keyboard open: only 50% visible
      addEventListener: (_event: string, handler: () => void) => {
        resizeListeners.push(handler)
      },
      removeEventListener: vi.fn(),
    }
    Object.defineProperty(window, 'visualViewport', {
      value: mockViewport,
      writable: true,
      configurable: true,
    })

    const { container } = render(<MobileTabBar />)

    // Trigger the resize listener to simulate keyboard appearing.
    act(() => {
      resizeListeners.forEach((handler) => handler())
    })

    // The nav element should be hidden (display:none or aria-hidden or removed from DOM).
    const nav = container.querySelector('nav')
    if (nav) {
      const hidden =
        nav.style.display === 'none' ||
        nav.getAttribute('aria-hidden') === 'true' ||
        nav.getAttribute('data-keyboard-open') === 'true' ||
        nav.className.includes('hidden') ||
        nav.className.includes('translate-y')
      expect(hidden).toBe(true)
    } else {
      // Nav removed from DOM entirely — also valid.
      expect(nav).toBeNull()
    }
  })

  it('tab bar is visible when keyboard is closed (full viewport height)', () => {
    // Normal state: visualViewport.height close to innerHeight.
    const mockViewport = {
      height: window.innerHeight * 0.95,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }
    Object.defineProperty(window, 'visualViewport', {
      value: mockViewport,
      writable: true,
      configurable: true,
    })

    render(<MobileTabBar />)
    // Tab bar should be visible — tab labels should be in the document.
    expect(screen.getByText('Home')).toBeTruthy()
  })
})
