'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { Message as MessageType } from './ChatContainer'
import Message from './Message'
import { ChevronDown } from 'lucide-react'

// QAR-14: sentinel-based auto-scroll (replaces interval+rAF polling)
// scrollIntoView works reliably on iOS Safari; interval polling can fight
// with touch events and cause erratic scroll behaviour during streaming.

interface MessageListProps {
  messages: MessageType[]
  isStreaming?: boolean
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  // QAR-14: sentinel div ref — scrolled into view instead of imperative scrollTop manipulation
  const bottomRef = useRef<HTMLDivElement>(null)
  const userScrolledUpRef = useRef(false)
  const isTouchingRef = useRef(false)
  const prevMessageCountRef = useRef(messages.length)
  const lastAiMessageIdRef = useRef<string | null>(null)
  const [showJumpButton, setShowJumpButton] = useState(false)

  // Find the last AI message id
  const lastAiMessage = [...messages].reverse().find(m => m.role === 'assistant')
  const lastAiId = lastAiMessage?.id ?? null

  // Detect intentional user scroll (wheel/touch), not programmatic
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const checkScrollPosition = () => {
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
      if (isNearBottom) {
        userScrolledUpRef.current = false
        setShowJumpButton(false)
      }
    }

    const handleUserScroll = () => {
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
      if (!isNearBottom) {
        userScrolledUpRef.current = true
        if (isStreaming) {
          setShowJumpButton(true)
        }
      } else {
        userScrolledUpRef.current = false
        setShowJumpButton(false)
      }
    }

    const handleTouchStart = () => { isTouchingRef.current = true }
    const handleTouchEnd = () => {
      isTouchingRef.current = false
      // After touch ends, check if user scrolled away from bottom
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
      if (!isNearBottom) {
        userScrolledUpRef.current = true
        if (isStreaming) setShowJumpButton(true)
      }
    }

    container.addEventListener('wheel', handleUserScroll, { passive: true })
    container.addEventListener('touchmove', handleUserScroll, { passive: true })
    container.addEventListener('touchstart', handleTouchStart, { passive: true })
    container.addEventListener('touchend', handleTouchEnd, { passive: true })
    container.addEventListener('scrollend', checkScrollPosition)

    return () => {
      container.removeEventListener('wheel', handleUserScroll)
      container.removeEventListener('touchmove', handleUserScroll)
      container.removeEventListener('touchstart', handleTouchStart)
      container.removeEventListener('touchend', handleTouchEnd)
      container.removeEventListener('scrollend', checkScrollPosition)
    }
  }, [isStreaming])

  // Hide jump button when streaming ends
  useEffect(() => {
    if (!isStreaming) {
      setShowJumpButton(false)
    }
  }, [isStreaming])

  // Track new message arrivals — reset scroll lock so auto-scroll resumes
  useEffect(() => {
    const newCount = messages.length
    const isNewMessage = newCount > prevMessageCountRef.current
    prevMessageCountRef.current = newCount

    if (isNewMessage) {
      userScrolledUpRef.current = false
      setShowJumpButton(false)

      const newestAi = [...messages].reverse().find(m => m.role === 'assistant')
      if (newestAi && newestAi.id !== lastAiMessageIdRef.current) {
        lastAiMessageIdRef.current = newestAi.id
      }
    }
  }, [messages.length])

  const handleJumpToLatest = useCallback(() => {
    if (!lastAiId) return
    userScrolledUpRef.current = false
    setShowJumpButton(false)
    const el = document.getElementById(`message-${lastAiId}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [lastAiId])

  // Single unified auto-scroll: uses sentinel div on every message change.
  // Fires for both new message arrival AND streaming token updates.
  // Throttled to max once per 400ms to prevent scroll-fighting.
  const lastScrollTimeRef = useRef(0)
  useEffect(() => {
    if (userScrolledUpRef.current || isTouchingRef.current) return
    const now = Date.now()
    if (now - lastScrollTimeRef.current < 400) return
    lastScrollTimeRef.current = now
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isStreaming])

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto p-3 pt-16 md:pt-6 sm:px-6 sm:pb-6 relative"
      style={{
        overflowAnchor: 'none',
        // QAR-14: iOS Safari momentum scroll + overscroll containment
        WebkitOverflowScrolling: 'touch',
        overscrollBehaviorY: 'contain',
      }}
    >
      <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
        {messages.map((message, idx) => (
          <Message
            key={message.id}
            message={message}
            isLast={idx === messages.length - 1}
          />
        ))}
      </div>

      {/* QAR-14: sentinel div — scrolled into view during streaming instead of polling scrollTop */}
      <div ref={bottomRef} aria-hidden="true" />

      {/* Floating "Jump to latest" button */}
      {showJumpButton && (
        <button
          onClick={handleJumpToLatest}
          className="fixed bottom-28 left-1/2 -translate-x-1/2 z-30 flex items-center gap-1.5 px-4 py-2 rounded-full bg-[var(--surface-elevated)] border border-[var(--border)] shadow-card text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text)] hover:shadow-card-hover transition-all"
        >
          <ChevronDown size={16} />
          Jump to latest
        </button>
      )}
    </div>
  )
}
