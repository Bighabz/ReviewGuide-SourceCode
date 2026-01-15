'use client'

import { useState, useEffect, useRef } from 'react'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import ErrorBanner from './ErrorBanner'
import { streamChat, fetchConversationHistory } from '@/lib/chatApi'
import { SUGGESTION_CLICK_PREFIX } from '@/lib/utils'
import { TRENDING_SEARCHES, UI_TEXT, CHAT_CONFIG } from '@/lib/constants'

export interface FollowupQuestion {
  slot: string
  question: string
}

export interface StructuredFollowups {
  intro: string
  questions: FollowupQuestion[]
  closing: string
}

export interface NextSuggestion {
  id: string
  question: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  ui_blocks?: any[]
  itinerary?: any[]  // Travel itinerary data
  followups?: string[] | StructuredFollowups  // Follow-up questions (legacy array or new structured format)
  next_suggestions?: NextSuggestion[]  // Follow-up questions from next_step_suggestion tool
  isSuggestionClick?: boolean  // True when message was triggered by clicking a suggestion button
}

interface ChatContainerProps {
  clearHistoryTrigger?: number
}

export default function ChatContainer({ clearHistoryTrigger }: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [userId, setUserId] = useState<number | null>(null)  // Track user_id for persistence
  const [error, setError] = useState<string>('')
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)

  // Error state for ChatGPT-style error banner
  const [showErrorBanner, setShowErrorBanner] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [pendingUserMessage, setPendingUserMessage] = useState<string>('')
  const [isRetrying, setIsRetrying] = useState(false)

  // Reconnecting state for SSE connection drops
  const [isReconnecting, setIsReconnecting] = useState(false)
  const [reconnectAttempt, setReconnectAttempt] = useState(0)

  // Track which message ID is currently being updated (can change if create_new_message is sent)
  const currentMessageIdRef = useRef<string>('')

  // Load from localStorage on mount and fetch from database if needed
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const storedSessionId = localStorage.getItem(CHAT_CONFIG.SESSION_STORAGE_KEY)
        const storedUserId = localStorage.getItem(CHAT_CONFIG.USER_ID_STORAGE_KEY)
        const storedMessages = localStorage.getItem(CHAT_CONFIG.MESSAGES_STORAGE_KEY)

        // Load user ID if available
        if (storedUserId) {
          const parsedUserId = parseInt(storedUserId, 10)
          if (!isNaN(parsedUserId)) {
            setUserId(parsedUserId)
          }
        }

        // Validate and set session ID
        if (storedSessionId) {
          const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
          if (uuidPattern.test(storedSessionId)) {
            setSessionId(storedSessionId)
          } else {
            localStorage.removeItem(CHAT_CONFIG.SESSION_STORAGE_KEY)
          }
        }

        // PRIORITY 1: Load from localStorage if available
        if (storedMessages) {
          try {
            const parsed = JSON.parse(storedMessages)
            const messagesWithDates = parsed.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp)
            }))
            setMessages(messagesWithDates)
            console.log('✅ Loaded conversation history from localStorage:', messagesWithDates.length, 'messages')
          } catch (e) {
            console.error('Failed to parse stored messages:', e)
          }
        }
        // PRIORITY 2: Fallback to database if localStorage is empty but we have a session ID
        else if (storedSessionId) {
          const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
          if (uuidPattern.test(storedSessionId)) {
            console.log('📥 No messages in localStorage, fetching from database for session:', storedSessionId)
            try {
              const response = await fetchConversationHistory(storedSessionId)
              if (response.success && response.messages && response.messages.length > 0) {
                console.log('✅ Fetched', response.messages.length, 'messages from database')

                // Convert database messages to frontend format
                const messagesWithDates = response.messages.map((msg: any, index: number) => {
                  const baseMessage = {
                    id: (Date.now() + index).toString(),
                    role: msg.role,
                    content: msg.content,
                    timestamp: new Date(msg.created_at || Date.now()),
                  }

                  // Spread ALL metadata fields from message_metadata (generic approach)
                  // This automatically includes: followups, ui_blocks, next_suggestions, is_suggestion_click, citations, intent, status, etc.
                  if (msg.message_metadata) {
                    return {
                      ...baseMessage,
                      ...msg.message_metadata,  // Spread all metadata fields
                    }
                  }

                  return baseMessage
                })

                setMessages(messagesWithDates)
                console.log('✅ Loaded conversation history from database')
              } else {
                console.log('ℹ️ No messages found in database for this session')
              }
            } catch (e) {
              console.error('❌ Failed to fetch conversation history from database:', e)
            }
          }
        }
      } catch (error) {
        console.error('Error loading history:', error)
      } finally {
        setIsLoadingHistory(false)
      }
    }

    loadHistory()
  }, [])

  // Persist session ID to localStorage whenever it changes
  useEffect(() => {
    if (sessionId && !isLoadingHistory) {
      localStorage.setItem(CHAT_CONFIG.SESSION_STORAGE_KEY, sessionId)
    }
  }, [sessionId, isLoadingHistory])

  // Persist user_id to localStorage whenever it changes
  useEffect(() => {
    if (userId !== null && !isLoadingHistory) {
      localStorage.setItem(CHAT_CONFIG.USER_ID_STORAGE_KEY, userId.toString())
    }
  }, [userId, isLoadingHistory])

  // Persist messages to localStorage whenever they change
  // Don't persist if there's an error banner showing (wait for user to retry or send new message)
  useEffect(() => {
    if (messages.length > 0 && !isLoadingHistory && !showErrorBanner) {
      localStorage.setItem(CHAT_CONFIG.MESSAGES_STORAGE_KEY, JSON.stringify(messages))
    }
  }, [messages, isLoadingHistory, showErrorBanner])

  // Ref to store sendMessage function for use in event listener
  const sendMessageRef = useRef<(message: string) => void>(() => {})

  // Shared function to handle streaming with error management
  const handleStream = async (messageToSend: string, isSuggestion: boolean = false) => {
    setIsStreaming(true)
    setError('')
    setShowErrorBanner(false)
    setPendingUserMessage(messageToSend)

    // Generate session ID if not exists
    let currentSessionId = sessionId
    if (!currentSessionId) {
      currentSessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0
        const v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
      })
      setSessionId(currentSessionId)
    }

    // Create assistant message placeholder
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, assistantMessage])
    currentMessageIdRef.current = assistantMessageId

    // Stream response from API
    await streamChat({
      message: messageToSend,
      sessionId: currentSessionId,
      userId: userId || undefined,
      onToken: (token, isPlaceholder) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === currentMessageIdRef.current
              ? {
                  ...msg,
                  content: isPlaceholder ? token : msg.content + token
                }
              : msg
          )
        )
      },
      onClear: () => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === currentMessageIdRef.current
              ? { ...msg, content: '' }
              : msg
          )
        )
      },
      onComplete: (data) => {
        if (data.user_id && data.user_id !== userId) {
          setUserId(data.user_id)
        }

        if (data.create_new_message) {
          const originalMessageId = currentMessageIdRef.current

          if (data.itinerary) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === originalMessageId
                  ? { ...msg, itinerary: data.itinerary }
                  : msg
              )
            )
          }

          const followupMessageId = (Date.now() + 2).toString()
          const followupMessage: Message = {
            id: followupMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
          }

          setMessages((prev) => [...prev, followupMessage])
          currentMessageIdRef.current = followupMessageId
        } else if (data.ui_blocks || data.itinerary || data.followups || data.next_suggestions) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === currentMessageIdRef.current
                ? {
                    ...msg,
                    ...(data.ui_blocks && data.ui_blocks.length > 0 ? { ui_blocks: data.ui_blocks } : {}),
                    ...(data.itinerary ? { itinerary: data.itinerary } : {}),
                    ...(data.followups ? { followups: data.followups } : {}),
                    ...(data.next_suggestions && data.next_suggestions.length > 0 ? { next_suggestions: data.next_suggestions } : {})
                  }
                : msg
            )
          )
        }
        setIsStreaming(false)
        setPendingUserMessage('')
        setIsRetrying(false)
        setIsReconnecting(false)
      },
      onError: (errorMsg) => {
        console.error('Stream error:', errorMsg)

        // Remove the empty assistant message
        setMessages((prev) => prev.filter(msg => msg.id !== assistantMessageId))

        // Show error banner
        setShowErrorBanner(true)
        setErrorMessage(UI_TEXT.ERROR_MESSAGE)
        setError(errorMsg)
        setIsStreaming(false)
        setIsRetrying(false)
        setIsReconnecting(false)
      },
      onReconnecting: (attempt, maxRetries) => {
        setIsReconnecting(true)
        setReconnectAttempt(attempt)
        console.log(`Reconnecting... attempt ${attempt}/${maxRetries}`)
      },
      onReconnected: () => {
        setIsReconnecting(false)
        setReconnectAttempt(0)
      },
    })
  }

  // Handle retry button click
  const handleRetry = async () => {
    if (!pendingUserMessage || isStreaming) return

    setIsRetrying(true)
    setShowErrorBanner(false)

    // Re-stream with the pending message (don't add user message again - it's already in the array)
    await handleStream(pendingUserMessage, false)
  }

  // Handle suggestion click from next_suggestions buttons
  const handleSuggestionClick = async (question: string) => {
    if (isStreaming) return

    // Prefix so backend knows this is a user accepting a bot suggestion
    const messageToSend = `${SUGGESTION_CLICK_PREFIX} ${question}`

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageToSend,
      timestamp: new Date(),
      isSuggestionClick: true,  // Mark as suggestion click for different visual treatment
    }

    setMessages((prev) => [...prev, userMessage])

    // Use shared streaming function
    await handleStream(messageToSend, true)
  }

  // Listen for sendSuggestion events from Message component
  useEffect(() => {
    const handleSendSuggestion = (event: CustomEvent<{ question: string }>) => {
      handleSuggestionClick(event.detail.question)
    }

    window.addEventListener('sendSuggestion', handleSendSuggestion as EventListener)
    return () => {
      window.removeEventListener('sendSuggestion', handleSendSuggestion as EventListener)
    }
  }, [isStreaming, sessionId, userId])

  const handleSendMessage = async () => {
    if (!input.trim() || isStreaming) return

    // Clear error banner when sending new message
    setShowErrorBanner(false)
    setPendingUserMessage('')

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const messageToSend = input
    setInput('')

    // Use shared streaming function
    await handleStream(messageToSend, false)
  }

  // Clear history when trigger changes
  useEffect(() => {
    if (clearHistoryTrigger && clearHistoryTrigger > 0) {
      setMessages([])
      setSessionId('')
      // Only clear session_id and messages, KEEP user_id for reuse
      localStorage.removeItem('chat_session_id')
      localStorage.removeItem(CHAT_CONFIG.MESSAGES_STORAGE_KEY)
      // DO NOT remove 'chat_user_id' - keep it so same user is reused
      console.log('Cleared chat history, keeping user_id:', userId)
    }
  }, [clearHistoryTrigger, userId])

  // Show loading indicator while loading history
  if (isLoadingHistory) {
    return (
      <div className="flex-1 flex items-center justify-center" style={{ background: 'var(--gpt-background)' }}>
        <div className="text-center" style={{ color: 'var(--gpt-text-secondary)' }}>
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-current mb-2"></div>
          <p>{UI_TEXT.LOADING_HISTORY}</p>
        </div>
      </div>
    )
  }

  return (
    <div id="chat-container" className="flex-1 flex flex-col overflow-hidden" style={{ background: 'var(--gpt-background)' }}>
      {/* Search Bar (when no messages) */}
      {messages.length === 0 && (
        <div id="welcome-screen" className="flex-1 flex items-center justify-center p-3 sm:p-8">
          <div id="welcome-container" className="w-full px-2 sm:px-0" style={{ maxWidth: '780px' }}>
            <div className="text-center mb-6 sm:mb-12">
              <h2 className="text-xl sm:text-3xl font-semibold mb-3" style={{ color: 'var(--gpt-text)' }}>
                {UI_TEXT.WELCOME_TITLE}
              </h2>
            </div>
            <ChatInput
              value={input}
              onChange={setInput}
              onSend={handleSendMessage}
              disabled={isStreaming}
              placeholder={UI_TEXT.PLACEHOLDER_TEXT}
            />

            {/* Hot Searches Section */}
            <div id="hot-searches" className="mt-4 sm:mt-6">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs sm:text-sm font-medium" style={{ color: 'var(--gpt-text-secondary)' }}>
                  🔥 {UI_TEXT.TRENDING_LABEL}
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 sm:gap-2 justify-center sm:justify-start">
                {TRENDING_SEARCHES.map((search) => (
                  <button
                    key={search}
                    onClick={async () => {
                      if (isStreaming) return

                      const userMessage: Message = {
                        id: Date.now().toString(),
                        role: 'user',
                        content: search,
                        timestamp: new Date(),
                      }

                      setMessages((prev) => [...prev, userMessage])

                      // Use shared streaming function
                      await handleStream(search, false)
                    }}
                    disabled={isStreaming}
                    className="px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm transition-all whitespace-nowrap"
                    style={{
                      background: 'var(--gpt-accent-light)',
                      border: '1px solid var(--gpt-accent)',
                      color: 'var(--gpt-accent)',
                      cursor: isStreaming ? 'not-allowed' : 'pointer',
                      fontWeight: 500,
                      opacity: isStreaming ? 0.5 : 1,
                    }}
                    onMouseEnter={(e) => {
                      if (!isStreaming) {
                        e.currentTarget.style.background = 'var(--gpt-accent)'
                        e.currentTarget.style.color = '#ffffff'
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isStreaming) {
                        e.currentTarget.style.background = 'var(--gpt-accent-light)'
                        e.currentTarget.style.color = 'var(--gpt-accent)'
                      }
                    }}
                  >
                    {search}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.length > 0 && (
        <>
          <MessageList messages={messages} />

          {/* Reconnecting indicator */}
          {isReconnecting && (
            <div
              className="flex items-center justify-center gap-2 py-2 px-4 mx-auto mb-2"
              style={{
                background: 'var(--gpt-surface, #f3f4f6)',
                borderRadius: '9999px',
                maxWidth: 'fit-content',
              }}
            >
              <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" style={{ color: 'var(--gpt-accent)' }} />
              <span className="text-sm" style={{ color: 'var(--gpt-text-secondary)' }}>
                {UI_TEXT.RECONNECTING}{reconnectAttempt > 0 ? ` (attempt ${reconnectAttempt}/3)` : '...'}
              </span>
            </div>
          )}

          {/* Error Banner - shown after last message */}
          {showErrorBanner && (
            <ErrorBanner
              message={errorMessage}
              onRetry={handleRetry}
            />
          )}

          <div
            id="chat-input-wrapper"
            className="sticky bottom-0 p-3 sm:p-4 z-40"
            style={{
              borderTop: '1px solid var(--gpt-border)',
              background: 'var(--gpt-background)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <div id="chat-input-container" className="mx-auto px-2 sm:px-0" style={{ maxWidth: '780px' }}>
              <ChatInput
                value={input}
                onChange={setInput}
                onSend={handleSendMessage}
                disabled={isStreaming}
                placeholder={UI_TEXT.PLACEHOLDER_TEXT}
              />

              {/* Ultra-minimal footer */}
              <div id="footer" className="mt-3 sm:mt-4 text-center">
                {/* Footer links */}
                <div className="text-[10px] sm:text-xs mb-2" style={{ color: 'var(--gpt-text-muted)', opacity: 0.6 }}>
                  <a href="#" className="hover:underline" style={{ color: 'inherit' }}>About</a>
                  <span className="mx-1 sm:mx-2">·</span>
                  <a href="#" className="hover:underline" style={{ color: 'inherit' }}>Privacy</a>
                  <span className="mx-1 sm:mx-2">·</span>
                  <span className="hidden sm:inline">
                    <a href="#" className="hover:underline" style={{ color: 'inherit' }}>Affiliate Disclosure</a>
                    <span className="mx-2">·</span>
                  </span>
                  <a href="#" className="hover:underline" style={{ color: 'inherit' }}>Contact</a>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
