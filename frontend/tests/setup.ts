import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock fetch
global.fetch = vi.fn()

// Mock CSS variables
document.documentElement.style.setProperty('--gpt-background', '#ffffff')
document.documentElement.style.setProperty('--gpt-text', '#000000')
document.documentElement.style.setProperty('--gpt-text-secondary', '#666666')
document.documentElement.style.setProperty('--gpt-accent', '#3b82f6')

// Mock scrollIntoView (not available in JSDOM)
Element.prototype.scrollIntoView = vi.fn()
