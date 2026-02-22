'use client'

import { useState, useEffect, useRef } from 'react'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import ErrorBanner from './ErrorBanner'
import BlockSkeleton from './BlockSkeleton'
import { streamChat, fetchConversationHistory } from '@/lib/chatApi'
import { SUGGESTION_CLICK_PREFIX } from '@/lib/utils'
import { TRENDING_SEARCHES, UI_TEXT, CHAT_CONFIG } from '@/lib/constants'
import { saveRecentSearch } from '@/lib/recentSearches'
import { useStreamReducer } from '@/hooks/useStreamReducer'
import { TOOL_BLOCK_MAP, BLOCK_SKELETON_CONFIG } from '@/lib/skeletonMap'
import type { SkeletonBlockType } from '@/components/BlockSkeleton'

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
  isThinking?: boolean  // True while waiting for real tokens (status updates hidden)
  statusText?: string   // Current tool status text (e.g., "Checking reviews...")
}

interface ChatContainerProps {
  clearHistoryTrigger?: number
  externalSessionId?: string  // Allow parent to set session ID
  onSessionChange?: (sessionId: string) => void  // Notify parent of session changes
  initialQuery?: string  // Initial query from URL params (for sticky chat bar)
}

export default function ChatContainer({ clearHistoryTrigger, externalSessionId, onSessionChange, initialQuery }: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const { streamState, dispatch: dispatchStream, isStreaming } = useStreamReducer()
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

  // RFC §2.2: skeleton block type shown while a tool is running but before the artifact arrives
  const [pendingSkeleton, setPendingSkeleton] = useState<SkeletonBlockType | null>(null)

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

  // Track processed queries and sessions to avoid duplicate processing
  const initialQueryProcessedRef = useRef<string | null>(null)
  const lastExternalSessionIdRef = useRef<string | null>(null)

  // Single unified effect to handle initial query from URL params (sticky chat bar)
  // This runs when we have BOTH an externalSessionId AND initialQuery (new session with query)
  useEffect(() => {
    if (initialQuery && !isLoadingHistory && !isStreaming && initialQueryProcessedRef.current !== initialQuery && externalSessionId) {
      initialQueryProcessedRef.current = initialQuery

      // Add user message
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: initialQuery,
        timestamp: new Date(),
      }
      setMessages([userMessage])

      // Set session ID and trigger stream with explicit session ID
      setSessionId(externalSessionId)
      localStorage.setItem(CHAT_CONFIG.SESSION_STORAGE_KEY, externalSessionId)

      // Pass session ID directly since state update is async
      handleStream(initialQuery, false, externalSessionId)
    }
  }, [initialQuery, isLoadingHistory, isStreaming, externalSessionId])

  // Handle external session ID changes (from conversation sidebar - switching sessions WITHOUT a query)
  useEffect(() => {
    // Only handle session switches that DON'T have an initialQuery (those are handled above)
    if (externalSessionId && externalSessionId !== lastExternalSessionIdRef.current && !initialQuery) {
      lastExternalSessionIdRef.current = externalSessionId

      const switchToSession = async () => {
        setIsLoadingHistory(true)
        setMessages([])

        try {
          const response = await fetchConversationHistory(externalSessionId)
          if (response.success && response.messages && response.messages.length > 0) {
            const messagesWithDates = response.messages.map((msg: any, index: number) => {
              const baseMessage = {
                id: (Date.now() + index).toString(),
                role: msg.role,
                content: msg.content,
                timestamp: new Date(msg.created_at || Date.now()),
              }

              if (msg.message_metadata) {
                return {
                  ...baseMessage,
                  ...msg.message_metadata,
                }
              }

              return baseMessage
            })

            setMessages(messagesWithDates)
            console.log(`Switched to session ${externalSessionId} with ${messagesWithDates.length} messages`)
          }
        } catch (error) {
          console.error('Failed to load session:', error)
        }

        setSessionId(externalSessionId)
        localStorage.setItem(CHAT_CONFIG.SESSION_STORAGE_KEY, externalSessionId)
        localStorage.setItem(CHAT_CONFIG.MESSAGES_STORAGE_KEY, JSON.stringify([]))
        setIsLoadingHistory(false)
      }

      switchToSession()
    }

    // Update ref for sessions WITH initialQuery too (to track we've seen this session)
    if (externalSessionId && externalSessionId !== lastExternalSessionIdRef.current) {
      lastExternalSessionIdRef.current = externalSessionId
    }
  }, [externalSessionId, initialQuery])

  // Persist session ID to localStorage whenever it changes
  useEffect(() => {
    if (sessionId && !isLoadingHistory) {
      localStorage.setItem(CHAT_CONFIG.SESSION_STORAGE_KEY, sessionId)
      // Notify parent of session change
      if (onSessionChange) {
        onSessionChange(sessionId)
      }
    }
  }, [sessionId, isLoadingHistory, onSessionChange])

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

  // Ref to always hold the latest handleSuggestionClick (avoids stale closure in event listener)
  const handleSuggestionClickRef = useRef<(question: string) => void>(() => { })

  // Shared function to handle streaming with error management
  // overrideSessionId allows passing session ID directly when state hasn't updated yet
  const handleStream = async (messageToSend: string, isSuggestion: boolean = false, overrideSessionId?: string) => {
    dispatchStream({ type: 'RESET' })
    dispatchStream({ type: 'SEND_MESSAGE' })
    setError('')
    setShowErrorBanner(false)
    setPendingUserMessage(messageToSend)

    // Use override if provided (for cases where state hasn't updated yet), otherwise fall back to state
    let currentSessionId = overrideSessionId || sessionId
    if (!currentSessionId) {
      currentSessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0
        const v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
      })
      setSessionId(currentSessionId)

      // Track this session in the all_sessions list for conversation history
      const allSessionsJson = localStorage.getItem('chat_all_session_ids')
      const allSessions: string[] = allSessionsJson ? JSON.parse(allSessionsJson) : []
      if (!allSessions.includes(currentSessionId)) {
        allSessions.push(currentSessionId)
        localStorage.setItem('chat_all_session_ids', JSON.stringify(allSessions))
      }
    }

    // Create assistant message placeholder with thinking state
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isThinking: true,  // Show "Thinking..." immediately until first real token
    }

    setMessages((prev) => [...prev, assistantMessage])
    currentMessageIdRef.current = assistantMessageId

    // Stream response from API
    await streamChat({
      message: messageToSend,
      sessionId: currentSessionId,
      userId: userId || undefined,
      // RFC §1.8: dispatch stream-reducer actions by named SSE event type.
      // The legacy onToken/onClear/onComplete/onError callbacks still run for
      // the actual UI updates — this layer only drives the FSM state machine.
      // RFC §2.2: also manages pendingSkeleton based on tool names in status text.
      onEvent: ({ eventType, data }) => {
        switch (eventType) {
          case 'status': {
            dispatchStream({ type: 'RECEIVE_STATUS', text: '' })
            // RFC §2.2: parse status text for known tool names → show skeleton
            const text = (data as any).text || (data as any).status_update || ''
            const normalizedText = text.toLowerCase().replace(/_/g, ' ')
            const toolMatch = Object.keys(TOOL_BLOCK_MAP).find(
              (tool) => normalizedText.includes(tool.replace(/_/g, ' '))
            )
            if (toolMatch) {
              setPendingSkeleton(TOOL_BLOCK_MAP[toolMatch])
            }
            break
          }
          case 'content':
            dispatchStream({ type: 'RECEIVE_CONTENT', token: '' })
            break
          case 'artifact':
            dispatchStream({ type: 'RECEIVE_ARTIFACT', blocks: [] })
            // RFC §2.2: real blocks have arrived — clear the skeleton
            setPendingSkeleton(null)
            break
          // 'done' and 'error' are dispatched inside onComplete / onError below
          default:
            break
        }
      },
      onToken: (token, isPlaceholder) => {
        if (isPlaceholder) {
          dispatchStream({ type: 'RECEIVE_STATUS', text: token })
        } else {
          dispatchStream({ type: 'RECEIVE_CONTENT', token })
        }
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === currentMessageIdRef.current
              ? isPlaceholder
                ? { ...msg, isThinking: true, statusText: token }  // Show status text while working
                : { ...msg, content: msg.content + token, isThinking: false, statusText: undefined }
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
        } else if (data.ui_blocks || data.itinerary || data.followups) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === currentMessageIdRef.current
                ? {
                  ...msg,
                  ...(data.ui_blocks && data.ui_blocks.length > 0 ? { ui_blocks: data.ui_blocks } : {}),
                  ...(data.itinerary ? { itinerary: data.itinerary } : {}),
                  ...(data.followups ? { followups: data.followups } : {}),
                }
                : msg
            )
          )
        }
        // Only dispatch RECEIVE_DONE for the actual terminal 'done' event.
        // Intermediate artifact events also call onComplete (to attach ui_blocks /
        // itinerary to the message) but must NOT move the FSM to finalized, because
        // the backend stream is still open.  session_id is present only on the real
        // done payload, so it's a reliable sentinel.
        if (data.session_id) {
          dispatchStream({ type: 'RECEIVE_DONE', data: data as any })
        }

        // Save to recent searches if product results were shown
        if (data.ui_blocks && pendingUserMessage) {
          const productBlock = data.ui_blocks.find(
            (b: any) => b.type === 'product_cards' || b.type === 'ebay_products' || b.type === 'amazon_products'
          )
          if (productBlock) {
            const items = productBlock.data?.items || productBlock.items || productBlock.data || []
            saveRecentSearch({
              query: pendingUserMessage,
              productNames: (Array.isArray(items) ? items : []).slice(0, 3).map((i: any) => i.title || i.name || '').filter(Boolean),
              category: productBlock.category || '',
              timestamp: Date.now(),
            })
          }
        }

        setPendingUserMessage('')
        setIsRetrying(false)
        setIsReconnecting(false)
        // RFC §2.2: stream finished — ensure skeleton is cleared
        setPendingSkeleton(null)
      },
      onError: (errorMsg) => {
        console.error('Stream error:', errorMsg)

        // Remove the empty assistant message
        setMessages((prev) => prev.filter(msg => msg.id !== assistantMessageId))

        // Show error banner with actual error for diagnosis
        setShowErrorBanner(true)
        setErrorMessage(`${UI_TEXT.ERROR_MESSAGE}\n\nDetails: ${errorMsg}`)
        setError(errorMsg)
        dispatchStream({ type: 'RECEIVE_ERROR', error: { message: errorMsg } })
        setIsRetrying(false)
        setIsReconnecting(false)
        // RFC §2.2: stream errored — clear skeleton
        setPendingSkeleton(null)
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

  // Keep ref in sync with the latest handleSuggestionClick
  useEffect(() => {
    handleSuggestionClickRef.current = handleSuggestionClick
  })

  // Listen for sendSuggestion events from Message component
  // Uses a ref so the listener never goes stale — no need to re-register on dependency changes
  useEffect(() => {
    const handleSendSuggestion = (event: CustomEvent<{ question: string }>) => {
      handleSuggestionClickRef.current(event.detail.question)
    }

    window.addEventListener('sendSuggestion', handleSendSuggestion as EventListener)
    return () => {
      window.removeEventListener('sendSuggestion', handleSendSuggestion as EventListener)
    }
  }, [])

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
      <div className="flex-1 flex items-center justify-center" style={{ background: 'var(--background)' }}>
        <div className="text-center" style={{ color: 'var(--text-secondary)' }}>
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-current mb-2"></div>
          <p>{UI_TEXT.LOADING_HISTORY}</p>
        </div>
      </div>
    )
  }

  return (
    <div id="chat-container" className="flex-1 flex flex-col overflow-hidden relative" style={{ background: 'var(--background)' }}>
      {/* Welcome Screen (no messages) */}
      {messages.length === 0 && (
        <div id="welcome-screen" className="flex-1 overflow-y-auto">
          <div className="flex flex-col items-center justify-center px-4 lg:pr-28 pt-14 sm:pt-16 pb-10 sm:pb-16">
              <img
                src="/images/ezgif-7b66ba24abcfdab0.gif"
                alt="ReviewGuide.Ai"
                className="h-32 sm:h-44 md:h-56 w-auto mb-4"
              />
              <h1 className="font-serif text-2xl sm:text-3xl md:text-4xl text-center text-[var(--text)] leading-tight tracking-tight">
                Smart shopping,{' '}
                <span className="italic text-[var(--primary)]">simplified.</span>
              </h1>
              <p className="text-sm sm:text-base text-[var(--text-secondary)] text-center mt-3 max-w-md">
                AI-powered product reviews, travel planning, and price comparison — all in one conversation.
              </p>

              <div className="w-full max-w-xl mx-auto mt-8">
                <ChatInput
                  value={input}
                  onChange={setInput}
                  onSend={handleSendMessage}
                  disabled={isStreaming}
                  placeholder="Ask anything — best headphones, Tokyo trip, laptop deals..."
                />
              </div>

              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {['Best wireless earbuds under $100', 'Plan a 5-day trip to Tokyo', 'Compare MacBook Air vs Pro'].map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInput(suggestion)
                    }}
                    className="px-4 py-2 rounded-full text-sm border border-[var(--border)] text-[var(--text-secondary)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] hover:text-[var(--text)] hover:border-[var(--border-strong)] transition-all"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.length > 0 && (
        <>
          <MessageList messages={messages} isStreaming={isStreaming} />

          {/* RFC §2.2: Block skeleton — shown while a tool is running, before artifact arrives */}
          {pendingSkeleton && isStreaming && (
            <div
              id="block-skeleton-container"
              className="mx-auto px-4 pb-2"
              style={{ maxWidth: '780px' }}
            >
              <BlockSkeleton
                blockType={pendingSkeleton}
                count={BLOCK_SKELETON_CONFIG[pendingSkeleton].count}
                layout={BLOCK_SKELETON_CONFIG[pendingSkeleton].layout}
              />
            </div>
          )}

          {/* Reconnecting indicator */}
          {isReconnecting && (
            <div
              className="flex items-center justify-center gap-2 py-2 px-4 mx-auto mb-2 rounded-full"
              style={{
                background: 'var(--surface)',
                maxWidth: 'fit-content',
              }}
            >
              <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" style={{ color: 'var(--primary)' }} />
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
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

          {/* Interrupted Banner - stream closed without terminal event (distinct from errored) */}
          {streamState === 'interrupted' && !showErrorBanner && (
            <div
              className="flex items-center gap-3 py-3 px-4 mx-4 mb-2 rounded-lg"
              style={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                color: 'var(--text-secondary)',
              }}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ flexShrink: 0, color: '#E85D3A' }}
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span className="text-sm">
                Response may be incomplete — the stream was interrupted.
              </span>
            </div>
          )}

          <div
            id="chat-input-wrapper"
            className="sticky bottom-0 p-3 sm:p-4 z-40"
            style={{
              borderTop: '1px solid var(--border)',
              background: 'var(--surface)',
              backdropFilter: 'blur(12px)'
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

              {/* Minimal footer */}
              <div id="footer" className="mt-3 sm:mt-4 text-center">
                <div className="text-[10px] sm:text-xs mb-2 text-[var(--text-muted)] opacity-80">
                  ReviewGuide.ai may earn from qualifying purchases. AI results should be verified.
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
