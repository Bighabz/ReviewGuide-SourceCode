'use client'

import { useState, useEffect, useRef } from 'react'
import { Message as MessageType } from './ChatContainer'
import Message from './Message'

interface MessageListProps {
  messages: MessageType[]
  isStreaming?: boolean
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const [userScrolledUp, setUserScrolledUp] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const prevMessageCountRef = useRef(messages.length)

  // Detect user scroll intent
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleScroll = () => {
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
      setUserScrolledUp(!isNearBottom)
    }

    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [])

  // Auto-scroll only for new messages (not updates to existing ones like follow-up suggestions)
  useEffect(() => {
    const newCount = messages.length
    const isNewMessage = newCount > prevMessageCountRef.current
    prevMessageCountRef.current = newCount

    if (isNewMessage) {
      setUserScrolledUp(false)
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    } else if (!userScrolledUp) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, userScrolledUp])

  // When streaming completes, scroll only if user hasn't scrolled up
  useEffect(() => {
    if (!isStreaming && !userScrolledUp) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [isStreaming])

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto p-3 sm:p-6">
      <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
