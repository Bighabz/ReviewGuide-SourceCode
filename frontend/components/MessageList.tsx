'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { Message as MessageType } from './ChatContainer'
import Message from './Message'
import { ChevronDown } from 'lucide-react'

interface MessageListProps {
  messages: MessageType[]
  isStreaming?: boolean
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const userScrolledUpRef = useRef(false)
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

    container.addEventListener('wheel', handleUserScroll, { passive: true })
    container.addEventListener('touchmove', handleUserScroll, { passive: true })
    container.addEventListener('scrollend', checkScrollPosition)

    return () => {
      container.removeEventListener('wheel', handleUserScroll)
      container.removeEventListener('touchmove', handleUserScroll)
      container.removeEventListener('scrollend', checkScrollPosition)
    }
  }, [isStreaming])

  // Hide jump button when streaming ends
  useEffect(() => {
    if (!isStreaming) {
      setShowJumpButton(false)
    }
  }, [isStreaming])

  // Scroll to top of the latest AI message when a new message arrives
  useEffect(() => {
    const newCount = messages.length
    const isNewMessage = newCount > prevMessageCountRef.current
    prevMessageCountRef.current = newCount

    if (isNewMessage) {
      userScrolledUpRef.current = false
      setShowJumpButton(false)

      // Find the newest AI message
      const newestAi = [...messages].reverse().find(m => m.role === 'assistant')
      if (newestAi && newestAi.id !== lastAiMessageIdRef.current) {
        lastAiMessageIdRef.current = newestAi.id
        // Scroll to the top of the new AI message
        requestAnimationFrame(() => {
          const el = document.getElementById(`message-${newestAi.id}`)
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        })
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

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto p-3 sm:p-6 relative">
      <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
      </div>

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
