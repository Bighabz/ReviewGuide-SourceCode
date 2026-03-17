'use client'

import { usePathname, useRouter } from 'next/navigation'
import { ArrowLeft, User } from 'lucide-react'
import { useState, useEffect } from 'react'

export default function MobileHeader() {
  const pathname = usePathname()
  const router = useRouter()
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  const isChatRoute = pathname?.startsWith('/chat')

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    setTheme(savedTheme || 'light')
  }, [])

  return (
    <header
      className="fixed top-0 left-0 right-0 z-[100] flex items-center h-12 px-4"
      style={{
        background: 'var(--background)',
        borderBottom: '1px solid var(--border)',
      }}
    >
      {isChatRoute ? (
        <>
          {/* Back arrow for chat routes */}
          <button
            onClick={() => router.push('/browse')}
            className="flex items-center justify-center w-8 h-8 rounded-lg -ml-1"
            style={{ color: 'var(--text)' }}
            aria-label="Back to Discover"
          >
            <ArrowLeft size={20} strokeWidth={1.5} />
          </button>

          {/* Conversation title — centered */}
          <span
            className="flex-1 text-center text-sm font-medium truncate px-2"
            style={{ color: 'var(--text)' }}
          >
            Research Session
          </span>

          {/* Spacer to balance the back button */}
          <div className="w-8" />
        </>
      ) : (
        <>
          {/* Logo */}
          <a href="/browse" className="flex items-center shrink-0">
            <img
              src={
                theme === 'dark'
                  ? '/images/1815e5dc-c4db-4248-9aeb-0a815fd87a4b.png'
                  : '/images/8f4c1971-a5b0-474e-9fb1-698e76324f0b.png'
              }
              alt="ReviewGuide.Ai"
              className="h-9 w-auto object-contain"
            />
          </a>

          {/* Spacer */}
          <div className="flex-1" />

          {/* User avatar */}
          <button
            className="flex w-8 h-8 rounded-full items-center justify-center border transition-all"
            style={{
              background: 'var(--surface)',
              borderColor: 'var(--border)',
              color: 'var(--text-muted)',
            }}
            aria-label="User menu"
          >
            <User size={14} strokeWidth={1.5} />
          </button>
        </>
      )}
    </header>
  )
}
