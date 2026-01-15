'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import CategorySidebar from '@/components/CategorySidebar'
import ChatContainer from '@/components/ChatContainer'
import Topbar from '@/components/Topbar'
import ErrorBoundary from '@/components/ErrorBoundary'

export default function ChatPage() {
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [clearHistoryTrigger, setClearHistoryTrigger] = useState(0)
  const [showClearDialog, setShowClearDialog] = useState(false)

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/')
    }
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

  return (
    <div className="h-screen flex overflow-hidden">
      <CategorySidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar
          onMenuClick={() => setSidebarOpen(true)}
          onClearHistory={handleClearHistory}
        />
        <ErrorBoundary>
          <ChatContainer clearHistoryTrigger={clearHistoryTrigger} />
        </ErrorBoundary>
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
            className="rounded-2xl shadow-2xl max-w-md w-full p-5 sm:p-6"
            style={{
              background: 'var(--gpt-background)',
              border: '1px solid var(--gpt-border)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              className="text-base sm:text-lg font-semibold mb-2"
              style={{ color: 'var(--gpt-text)' }}
            >
              Clear Chat History
            </h3>
            <p
              className="text-xs sm:text-sm mb-5 sm:mb-6"
              style={{ color: 'var(--gpt-text-secondary)' }}
            >
              Are you sure you want to clear all chat history? This cannot be undone.
            </p>
            <div className="flex gap-2 sm:gap-3 justify-end">
              <button
                onClick={cancelClearHistory}
                className="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all"
                style={{
                  background: 'var(--gpt-hover)',
                  border: '1px solid var(--gpt-border)',
                  color: 'var(--gpt-text)',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'var(--gpt-input-bg)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'var(--gpt-hover)'
                }}
              >
                Cancel
              </button>
              <button
                onClick={confirmClearHistory}
                className="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all"
                style={{
                  background: 'var(--gpt-accent)',
                  border: 'none',
                  color: '#ffffff',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'var(--gpt-accent-hover)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'var(--gpt-accent)'
                }}
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
