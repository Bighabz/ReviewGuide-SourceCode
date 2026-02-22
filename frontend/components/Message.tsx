'use client'

import { User, Copy, Check, ArrowRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'
import { Message as MessageType, NextSuggestion } from './ChatContainer'
import { normalizeBlocks } from '@/lib/normalizeBlocks'
import { UIBlocks } from '@/components/blocks/BlockRegistry'
import { useState, useEffect } from 'react'
import { formatTimestamp, formatFullTimestamp, SUGGESTION_CLICK_PREFIX } from '@/lib/utils'

interface MessageProps {
  message: MessageType
}

export default function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)
  const [relativeTime, setRelativeTime] = useState(() => formatTimestamp(message.timestamp))

  // Update relative timestamp every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setRelativeTime(formatTimestamp(message.timestamp))
    }, 60000) // Update every minute

    return () => clearInterval(interval)
  }, [message.timestamp])

  const handleCopy = async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(message.content)
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = message.content
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        try {
          document.execCommand('copy')
        } finally {
          document.body.removeChild(textArea)
        }
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      id={`message-${message.id}`}
      className="w-full py-4 sm:py-5 px-3 sm:px-4"
    >
      <div id="message-container" className="mx-auto flex gap-3 sm:gap-4 items-start flex-row overflow-visible" style={{ maxWidth: '780px' }}>
        {/* Avatar - Only show for assistant */}
        {!isUser && (
          <div className="flex-shrink-0 mt-0.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-[var(--primary)] shadow-sm">
              <img
                src="/images/ezgif-7b66ba24abcfdab0.gif"
                alt="AI"
                className="w-4 h-4 rounded"
              />
            </div>
          </div>
        )}

        {/* Message Content */}
        <div className={`flex-1 min-w-0 ${isUser ? 'flex flex-col items-end' : 'text-left'}`}>
          {isUser ? (
            message.isSuggestionClick ? (
              // Suggestion click: show as subtle pill
              <div className="w-full flex justify-end">
                <div className="text-xs sm:text-sm py-2 px-4 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)]">
                  <span className="opacity-60">{SUGGESTION_CLICK_PREFIX}</span>{' '}
                  <span className="font-medium text-[var(--text)]">
                    {message.content.startsWith(SUGGESTION_CLICK_PREFIX)
                      ? message.content.slice(SUGGESTION_CLICK_PREFIX.length).trim()
                      : message.content}
                  </span>
                </div>
              </div>
            ) : (
              // Regular user message: editorial bubble
              <>
                <div className="relative group flex items-start justify-end max-w-full gap-2.5">
                  <div className="px-4 py-3 rounded-2xl rounded-tr-md bg-[var(--primary)] text-white shadow-card">
                    <p className="whitespace-pre-wrap text-[15px] leading-relaxed">
                      {message.content}
                    </p>
                  </div>

                  {/* User Avatar */}
                  <div className="flex-shrink-0 mt-0.5">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center bg-[var(--surface-hover)] text-[var(--text-muted)] border border-[var(--border)]">
                      <User size={14} strokeWidth={1.5} />
                    </div>
                  </div>
                </div>
                {/* Timestamp */}
                <div className="text-[10px] text-[var(--text-muted)] text-right mt-1.5 mr-10">
                  {relativeTime}
                </div>
              </>
            )
          ) : (
            <div className="w-full">
              {/* Status indicator — shown while tools are working */}
              {!message.content && message.isThinking && (
                <div className="flex items-center gap-2 py-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] animate-pulse" />
                  <span className="text-sm text-[var(--text-secondary)] font-medium tracking-tight">
                    {message.statusText || 'Thinking...'}
                  </span>
                </div>
              )}

              {/* 1. Render text content FIRST (brief summary) */}
              {message.content && (
                <div className="w-full">
                  <div className="prose prose-sm sm:prose-base max-w-none
                      text-[var(--text)]
                      prose-headings:font-serif prose-headings:tracking-tight prose-headings:text-[var(--text)]
                      prose-p:text-[var(--text)] prose-p:leading-relaxed prose-p:text-[15px]
                      prose-strong:text-[var(--text)] prose-strong:font-semibold
                      prose-li:text-[var(--text)] prose-li:marker:text-[var(--text-muted)]
                      prose-pre:bg-[var(--surface)] prose-pre:border prose-pre:border-[var(--border)] prose-pre:rounded-xl
                      prose-a:text-[var(--primary)] prose-a:no-underline hover:prose-a:underline"
                  >
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                </div>
              )}

              {/* 2. Render all UI blocks via registry-driven dispatcher */}
              <UIBlocks
                blocks={normalizeBlocks(message.ui_blocks ?? [])}
                itinerary={message.itinerary}
              />

              {/* 3. Render clarifier follow-up questions (structured slot-filling) */}
              {message.followups && typeof message.followups === 'object' && !Array.isArray(message.followups) && (
                <div className="w-full mt-5">
                  <div className="border border-[var(--border)] rounded-xl p-4 bg-[var(--surface)]">
                    {message.followups.intro && (
                      <p className="text-sm font-medium text-[var(--text)] mb-3">
                        {message.followups.intro}
                      </p>
                    )}
                    <div className="space-y-1.5">
                      {message.followups.questions && message.followups.questions.map((q: { slot: string; question: string }, idx: number) => (
                        <button
                          key={idx}
                          className="w-full text-left px-3.5 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--background)] hover:border-[var(--primary)] hover:bg-[var(--primary-light)] transition-all text-sm text-[var(--text)] flex items-center justify-between group"
                          onClick={() => {
                            const event = new CustomEvent('sendSuggestion', {
                              detail: { question: q.question }
                            })
                            window.dispatchEvent(event)
                          }}
                        >
                          <span>{q.question}</span>
                          <ArrowRight size={14} strokeWidth={1.5} className="opacity-0 group-hover:opacity-100 transition-opacity text-[var(--primary)]" />
                        </button>
                      ))}
                    </div>
                    {message.followups.closing && (
                      <p className="mt-3 text-xs italic text-[var(--text-muted)]">
                        {message.followups.closing}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Timestamp for assistant */}
              <div
                className="text-[10px] text-[var(--text-muted)] mt-2 ml-0.5"
                title={formatFullTimestamp(message.timestamp)}
              >
                {relativeTime}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
