'use client'

import { usePathname, useRouter } from 'next/navigation'
import { ArrowLeft, User, ArrowUpRight } from 'lucide-react'
import { useChatStatus } from '@/lib/chatStatusContext'

export default function MobileHeader() {
  const pathname = usePathname()
  const router = useRouter()
  const { isStreaming, statusText, sessionTitle } = useChatStatus()

  const isChatRoute = pathname?.startsWith('/chat')
  const isResultsRoute = pathname?.startsWith('/results')
  const showChatHeader = isChatRoute || isResultsRoute

  return (
    <header
      className="fixed top-0 left-0 right-0 z-[100] flex items-center h-14 px-6"
      data-mobile-header
      style={{
        background: showChatHeader ? 'var(--surface)' : 'var(--background)',
        borderBottom: '1px solid var(--border)',
        backdropFilter: 'blur(20px) saturate(1.1)',
        WebkitBackdropFilter: 'blur(20px) saturate(1.1)',
      }}
    >
      {showChatHeader ? (
        <>
          {/* Back arrow — goes to /chat from results, or / from chat */}
          <button
            onClick={() => router.push(isResultsRoute ? '/chat' : '/')}
            className="flex items-center justify-center w-8 h-8 rounded-lg -ml-1 focus-ring"
            style={{ color: 'var(--text)' }}
            aria-label={isResultsRoute ? 'Back to Chat' : 'Back to Discover'}
          >
            <ArrowLeft size={20} strokeWidth={1.5} />
          </button>

          {/* Dynamic title + status */}
          <div className="flex-1 px-2 min-w-0">
            <div
              className="text-sm font-semibold truncate"
              style={{ color: 'var(--text)' }}
            >
              {sessionTitle || 'New Research'}
            </div>
            <div
              className="text-[11px] truncate"
              style={{ color: 'var(--text-muted)' }}
            >
              {isStreaming ? (statusText || 'Researching...') : 'Researching'}
            </div>
          </div>

          {/* Share button — hidden on /results */}
          {!isResultsRoute && (
            <button
              className="flex items-center justify-center w-8 h-8 rounded-lg focus-ring"
              style={{ color: 'var(--text-secondary)' }}
              aria-label="Share"
            >
              <ArrowUpRight size={18} strokeWidth={1.5} />
            </button>
          )}

          {/* Spacer to keep title balanced when share button hidden */}
          {isResultsRoute && (
            <div className="w-8 h-8" />
          )}
        </>
      ) : (
        <>
          {/* Logo — serif italic per Figma */}
          <a
            href="/"
            className="flex items-center shrink-0 font-serif italic focus-ring"
            style={{ fontSize: '22px', color: 'var(--text)' }}
          >
            ReviewGuide
          </a>

          {/* Spacer */}
          <div className="flex-1" />

          {/* User avatar — filled gradient circle per Figma */}
          <button
            className="flex w-8 h-8 rounded-full items-center justify-center transition-all focus-ring"
            style={{
              background: 'linear-gradient(135deg, var(--primary), #6366f1)',
              color: 'white',
            }}
            aria-label="User menu"
          >
            <User size={14} strokeWidth={2} />
          </button>
        </>
      )}
    </header>
  )
}
