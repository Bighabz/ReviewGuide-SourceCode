'use client'

import { useState, useEffect, useRef, useCallback, RefCallback } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { Home, MessageSquare, Bookmark, Settings, Sun, Moon } from 'lucide-react'

const ACCENT_COLORS = [
  { id: 'indigo', label: 'Default', color: '#3B82F6' },
  { id: 'ocean', label: 'Ocean', color: '#0EA5E9' },
  { id: 'sunset', label: 'Sunset', color: '#F97316' },
  { id: 'neon', label: 'Neon', color: '#A855F7' },
  { id: 'forest', label: 'Forest', color: '#10B981' },
  { id: 'berry', label: 'Berry', color: '#E11D48' },
] as const

const TABS = [
  { label: 'Home', icon: Home, href: '/' },
  { label: 'History', icon: MessageSquare, href: '/chat' },
  { label: 'Saved', icon: Bookmark, href: '/saved' },
] as const

export default function MobileTabBar() {
  const pathname = usePathname()
  const [keyboardOpen, setKeyboardOpen] = useState(false)
  const [showSettingsPopover, setShowSettingsPopover] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [accent, setAccent] = useState<string>('indigo')
  const settingsRef = useRef<HTMLDivElement>(null)

  // Apply env(safe-area-inset-bottom) via DOM ref to bypass React style normalization.
  // Use calc(0px + env(...)) so jsdom's CSS parser preserves the value during tests,
  // while real browsers still respect the env() function.
  const navRefCallback: RefCallback<HTMLElement> = useCallback((node) => {
    if (node) {
      node.style.paddingBottom = 'calc(0px + env(safe-area-inset-bottom))'
    }
  }, [])

  // Read theme/accent from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    const savedAccent = localStorage.getItem('accent') || 'indigo'
    setTheme(savedTheme || 'light')
    setAccent(savedAccent)
  }, [])

  // Keyboard detection via visualViewport API
  useEffect(() => {
    if (typeof window === 'undefined' || !window.visualViewport) return
    const vv = window.visualViewport

    const handleResize = () => {
      const keyboardThreshold = window.innerHeight * 0.75
      setKeyboardOpen(vv.height < keyboardThreshold)
    }

    vv.addEventListener('resize', handleResize)
    return () => vv.removeEventListener('resize', handleResize)
  }, [])

  // Close popover on click outside
  useEffect(() => {
    if (!showSettingsPopover) return

    const handleClickOutside = (e: MouseEvent) => {
      if (
        settingsRef.current &&
        !settingsRef.current.contains(e.target as Node)
      ) {
        setShowSettingsPopover(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showSettingsPopover])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('theme', newTheme)
  }

  const changeAccent = (newAccent: string) => {
    setAccent(newAccent)
    if (newAccent === 'indigo') {
      document.documentElement.removeAttribute('data-accent')
    } else {
      document.documentElement.setAttribute('data-accent', newAccent)
    }
    localStorage.setItem('accent', newAccent)
    setShowSettingsPopover(false)
  }

  return (
    <motion.nav
      ref={navRefCallback}
      animate={{ y: keyboardOpen ? '100%' : 0 }}
      transition={{ duration: 0.15, ease: 'easeInOut' }}
      className="fixed bottom-0 left-0 right-0 z-[200]"
      data-keyboard-open={keyboardOpen ? 'true' : 'false'}
      style={{
        background: 'var(--surface-elevated)',
        borderTop: '1px solid var(--border, #E8E6E1)',
        boxShadow: '0 -4px 16px rgba(0,0,0,0.04)',
      }}
    >
      <div className="flex items-center justify-around h-14 px-2">
        {TABS.map((tab) => {
          const isActive =
            tab.href === '/'
              ? pathname === '/' || pathname?.startsWith('/browse')
              : pathname?.startsWith(tab.href)
          const Icon = tab.icon

          return (
            <Link
              key={tab.label}
              href={tab.href}
              className="flex flex-col items-center gap-0.5 min-w-[56px] py-1 transition-colors focus-ring"
              aria-label={tab.label}
              aria-current={isActive ? 'page' : undefined}
              data-active={isActive ? 'true' : undefined}
              style={{ color: isActive ? 'var(--primary)' : 'var(--text-muted)' }}
            >
              <Icon size={22} strokeWidth={isActive ? 2 : 1.5} />
              <span
                style={{
                  fontSize: '10px',
                  fontFamily: 'var(--font-dm-sans, system-ui)',
                  fontWeight: 500,
                }}
              >
                {tab.label}
              </span>
            </Link>
          )
        })}

        {/* Settings icon — theme toggle and accent picker */}
        <div ref={settingsRef} className="relative">
          <button
            className="flex flex-col items-center gap-0.5 min-w-[56px] py-1 transition-colors focus-ring"
            aria-label="Settings"
            onClick={() => setShowSettingsPopover((prev) => !prev)}
            style={{ color: showSettingsPopover ? 'var(--primary)' : 'var(--text-muted)' }}
          >
            <Settings size={22} strokeWidth={showSettingsPopover ? 2 : 1.5} />
            <span
              style={{
                fontSize: '10px',
                fontFamily: 'var(--font-dm-sans, system-ui)',
                fontWeight: 500,
              }}
            >
              Settings
            </span>
          </button>

          <AnimatePresence>
            {showSettingsPopover && (
              <motion.div
                initial={{ opacity: 0, y: 6, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 6, scale: 0.96 }}
                transition={{ duration: 0.15 }}
                className="absolute bottom-full right-0 mb-2 p-3 rounded-xl border z-[300]"
                style={{
                  background: 'var(--surface-elevated)',
                  borderColor: 'var(--border, #E8E6E1)',
                  boxShadow: 'var(--shadow-lg)',
                  minWidth: '140px',
                }}
              >
                {/* Theme toggle */}
                <button
                  onClick={toggleTheme}
                  className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg hover:bg-[var(--surface-hover)] transition-colors mb-2"
                  style={{ color: 'var(--text)' }}
                >
                  {theme === 'light' ? (
                    <Moon size={16} strokeWidth={1.5} />
                  ) : (
                    <Sun size={16} strokeWidth={1.5} />
                  )}
                  <span style={{ fontSize: '13px', fontWeight: 500 }}>
                    {theme === 'light' ? 'Dark mode' : 'Light mode'}
                  </span>
                </button>

                {/* Accent color picker */}
                <div
                  className="text-[10px] font-semibold mb-2 uppercase tracking-widest"
                  style={{ color: 'var(--text-muted)' }}
                >
                  Accent
                </div>
                <div className="flex gap-2">
                  {ACCENT_COLORS.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => changeAccent(c.id)}
                      className={`w-6 h-6 rounded-full transition-transform hover:scale-110 ${
                        accent === c.id ? 'ring-2 ring-offset-1 scale-110' : ''
                      }`}
                      style={{ backgroundColor: c.color }}
                      title={c.label}
                      aria-label={`Set ${c.label} accent`}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.nav>
  )
}
