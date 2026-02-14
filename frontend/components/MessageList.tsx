'use client'

import { useEffect, useRef } from 'react'
import { Message as MessageType } from './ChatContainer'
import Message from './Message'

interface MessageListProps {
  messages: MessageType[]
  isStreaming?: boolean
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const userScrolledUpRef = useRef(false)
  const prevMessageCountRef = useRef(messages.length)
  const isAutoScrollingRef = useRef(false)

  // Detect INTENTIONAL user scroll (wheel/touch), not programmatic scroll
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleUserScroll = () => {
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
      if (!isNearBottom) {
        userScrolledUpRef.current = true
      }
    }

    const handleScrollEnd = () => {
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
      if (isNearBottom && !isAutoScrollingRef.current) {
        userScrolledUpRef.current = false
      }
    }

    container.addEventListener('wheel', handleUserScroll, { passive: true })
    container.addEventListener('touchmove', handleUserScroll, { passive: true })
    container.addEventListener('scrollend', handleScrollEnd)

    return () => {
      container.removeEventListener('wheel', handleUserScroll)
      container.removeEventListener('touchmove', handleUserScroll)
      container.removeEventListener('scrollend', handleScrollEnd)
    }
  }, [])

  const scrollToBottom = () => {
    if (userScrolledUpRef.current) return
    isAutoScrollingRef.current = true
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    setTimeout(() => {
      isAutoScrollingRef.current = false
    }, 350)
  }

  // Scroll on new messages only
  useEffect(() => {
    const newCount = messages.length
    const isNewMessage = newCount > prevMessageCountRef.current
    prevMessageCountRef.current = newCount

    if (isNewMessage) {
      userScrolledUpRef.current = false
      scrollToBottom()
    }
  }, [messages.length])

  // Scroll when streaming completes
  useEffect(() => {
    if (!isStreaming) {
      scrollToBottom()
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
