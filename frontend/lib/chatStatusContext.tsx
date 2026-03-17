'use client'

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

interface ChatStatusState {
  isStreaming: boolean
  statusText: string
  sessionTitle: string
  setIsStreaming: (v: boolean) => void
  setStatusText: (v: string) => void
  setSessionTitle: (v: string) => void
}

const defaultState: ChatStatusState = {
  isStreaming: false,
  statusText: '',
  sessionTitle: 'New Research',
  setIsStreaming: () => {},
  setStatusText: () => {},
  setSessionTitle: () => {},
}

const ChatStatusContext = createContext<ChatStatusState>(defaultState)

export function ChatStatusProvider({ children }: { children: ReactNode }) {
  const [isStreaming, setIsStreaming] = useState(false)
  const [statusText, setStatusText] = useState('')
  const [sessionTitle, setSessionTitle] = useState('New Research')

  // Memoize setters to avoid unnecessary re-renders
  const stableSetIsStreaming = useCallback((v: boolean) => setIsStreaming(v), [])
  const stableSetStatusText = useCallback((v: string) => setStatusText(v), [])
  const stableSetSessionTitle = useCallback((v: string) => setSessionTitle(v), [])

  return (
    <ChatStatusContext.Provider value={{
      isStreaming,
      statusText,
      sessionTitle,
      setIsStreaming: stableSetIsStreaming,
      setStatusText: stableSetStatusText,
      setSessionTitle: stableSetSessionTitle,
    }}>
      {children}
    </ChatStatusContext.Provider>
  )
}

export const useChatStatus = () => useContext(ChatStatusContext)
