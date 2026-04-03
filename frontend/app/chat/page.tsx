'use client'

import { useEffect, useState, useCallback, Suspense, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import CategorySidebar from '@/components/CategorySidebar'
import ChatContainer from '@/components/ChatContainer'
import ConversationSidebar from '@/components/ConversationSidebar'
import ErrorBoundary from '@/components/ErrorBoundary'
import { CHAT_CONFIG } from '@/lib/constants'

/** QAR-16: persist session ID to chat_all_session_ids so ConversationSidebar can list history */
function trackSessionId(sessionId: string) {
  try {
    const allIds: string[] = JSON.parse(localStorage.getItem('chat_all_session_ids') || '[]')
    if (!allIds.includes(sessionId)) {
      allIds.push(sessionId)
      localStorage.setItem('chat_all_session_ids', JSON.stringify(allIds))
    }
  } catch {
    // localStorage unavailable (SSR guard) — silently skip
  }
}

function ChatPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [conversationSidebarOpen, setConversationSidebarOpen] = useState(false)
  const [clearHistoryTrigger, setClearHistoryTrigger] = useState(0)
  const [showClearDialog, setShowClearDialog] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string>('')
  const [switchToSessionId, setSwitchToSessionId] = useState<string | undefined>(undefined)
  const [initialQuery, setInitialQuery] = useState<string | undefined>(undefined)

  // Track which query we've processed to avoid re-processing after router.replace
  const processedQueryRef = useRef<string | null>(null)

  useEffect(() => {
    // Check for query parameters (from sticky chat bar on browse page)
    const query = searchParams.get('q')
    const isNewSession = searchParams.get('new') === '1'

    console.log('[ChatPage] URL params:', { query, isNewSession, alreadyProcessed: processedQueryRef.current })

    // Only process if this is a new session request AND we haven't processed this exact query
    if (isNewSession && query && processedQueryRef.current !== query) {
      console.log('[ChatPage] Processing new session with query:', query)
      processedQueryRef.current = query

      // Start a fresh session with the query
      const newSessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0
        const v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
      })

      // Clear old session data
      localStorage.removeItem(CHAT_CONFIG.MESSAGES_STORAGE_KEY)
      localStorage.setItem(CHAT_CONFIG.SESSION_STORAGE_KEY, newSessionId)
      // QAR-16: persist so ConversationSidebar can list this session
      trackSessionId(newSessionId)

      setSwitchToSessionId(newSessionId)
      setCurrentSessionId(newSessionId)
      setInitialQuery(query)

      // QAR-16: put session ID in URL so back/forward navigation restores correct session.
      // Remove q/new params while keeping session param for history continuity.
      setTimeout(() => {
        router.replace(`/chat?session=${newSessionId}`, { scroll: false })
      }, 100)
    } else if (isNewSession && !query) {
      // New session without query - just start fresh
      processedQueryRef.current = null

      const newSessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0
        const v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
      })

      localStorage.removeItem(CHAT_CONFIG.MESSAGES_STORAGE_KEY)
      localStorage.setItem(CHAT_CONFIG.SESSION_STORAGE_KEY, newSessionId)
      // QAR-16: persist so ConversationSidebar can list this session
      trackSessionId(newSessionId)

      setSwitchToSessionId(newSessionId)
      setCurrentSessionId(newSessionId)
      setInitialQuery(undefined)

      // QAR-16: session ID in URL for history continuity
      setTimeout(() => {
        router.replace(`/chat?session=${newSessionId}`, { scroll: false })
      }, 100)
    } else if (!isNewSession && !query) {
      // Normal page load — check for session param or fall back to stored session
      const sessionParam = searchParams.get('session')
      const storedSessionId = sessionParam || localStorage.getItem(CHAT_CONFIG.SESSION_STORAGE_KEY)
      if (storedSessionId) {
        setCurrentSessionId(storedSessionId)
        // If session came from URL param, make sure it's stored locally
        if (sessionParam) {
          localStorage.setItem(CHAT_CONFIG.SESSION_STORAGE_KEY, sessionParam)
          trackSessionId(sessionParam)
        }
      }
    }
  }, [searchParams, router])

  const handleSessionChange = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId)
  }, [])

  const handleSelectConversation = useCallback((sessionId: string) => {
    setSwitchToSessionId(sessionId)
    setCurrentSessionId(sessionId)
    setInitialQuery(undefined) // Clear initial query when switching conversations
    // QAR-16: update URL so browser history entry reflects the selected session
    router.replace(`/chat?session=${sessionId}`, { scroll: false })
  }, [router])

  const handleNewConversation = useCallback(() => {
    // Generate new session ID
    const newSessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0
      const v = c === 'x' ? r : (r & 0x3 | 0x8)
      return v.toString(16)
    })
    localStorage.setItem(CHAT_CONFIG.SESSION_STORAGE_KEY, newSessionId)
    // QAR-16: persist so ConversationSidebar can list this session
    trackSessionId(newSessionId)
    setSwitchToSessionId(newSessionId)
    setCurrentSessionId(newSessionId)
    setInitialQuery(undefined)
    processedQueryRef.current = null // Reset for next potential URL param processing
    // Clear local messages
    localStorage.removeItem(CHAT_CONFIG.MESSAGES_STORAGE_KEY)
    // QAR-16: update URL so browser history entry reflects the new session
    router.replace(`/chat?session=${newSessionId}`, { scroll: false })
  }, [router])

  const handleClearHistory = () => {
    setShowClearDialog(true)
  }

  const confirmClearHistory = () => {
    setShowClearDialog(false)
    setClearHistoryTrigger(prev => prev + 1)
  }

  const cancelClearHistory = () => {
    setShowClearDialog(false)
  }

  const handleSearch = (query: string) => {
    // Start a new conversation with the search query
    handleNewConversation()
    setInitialQuery(query)
  }

  return (
    <div className="h-full flex flex-col overflow-clip bg-[var(--background)] text-[var(--text)]">

      {/* Content area below topbar */}
      <div className="flex-1 flex overflow-clip relative min-h-0">
        {/* Mobile category sidebar overlay */}
        {sidebarOpen && (
          <CategorySidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        )}

        {/* Full-width chat */}
        <main className="flex flex-1 flex-col overflow-clip min-h-0">
          <ErrorBoundary>
            <ChatContainer
              clearHistoryTrigger={clearHistoryTrigger}
              externalSessionId={switchToSessionId}
              onSessionChange={handleSessionChange}
              initialQuery={initialQuery}
            />
          </ErrorBoundary>
        </main>

        <ConversationSidebar
          isOpen={conversationSidebarOpen}
          onClose={() => setConversationSidebarOpen(false)}
          currentSessionId={currentSessionId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />
      </div>

      {/* Custom Clear History Dialog */}
      {showClearDialog && (
        <div
          className="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-4"
          style={{
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(4px)'
          }}
          onClick={cancelClearHistory}
        >
          <div
            className="rounded-2xl shadow-2xl max-w-md w-full p-5 sm:p-6 bg-[var(--background)] border border-[var(--border)]"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-base sm:text-lg font-semibold font-serif mb-2 text-[var(--text)]">
              Clear Chat History
            </h3>
            <p className="text-xs sm:text-sm mb-5 sm:mb-6 text-[var(--text-secondary)]">
              Are you sure you want to clear all chat history? This cannot be undone.
            </p>
            <div className="flex gap-2 sm:gap-3 justify-end">
              <button
                onClick={cancelClearHistory}
                className="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] hover:bg-[var(--surface-hover)] cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={confirmClearHistory}
                className="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] cursor-pointer border-none"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="h-dvh flex items-center justify-center bg-[var(--background)]">
        <div className="text-center text-[var(--text-secondary)]">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-current mb-2"></div>
          <p>Loading chat...</p>
        </div>
      </div>
    }>
      <ChatPageContent />
    </Suspense>
  )
}
