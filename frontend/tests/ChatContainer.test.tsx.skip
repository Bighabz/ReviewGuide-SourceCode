import { describe, it, expect, vi, beforeEach, Mock } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import ChatContainer from '@/components/ChatContainer'
import * as chatApi from '@/lib/chatApi'
import { TRENDING_SEARCHES, UI_TEXT, CHAT_CONFIG } from '@/lib/constants'

// Mock the chatApi module
vi.mock('@/lib/chatApi', () => ({
  streamChat: vi.fn(),
  fetchConversationHistory: vi.fn(),
}))

describe('ChatContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset localStorage mock
    ;(localStorage.getItem as Mock).mockReturnValue(null)
    // Default mock for fetchConversationHistory
    ;(chatApi.fetchConversationHistory as Mock).mockResolvedValue({
      success: true,
      messages: [],
    })
  })

  it('renders welcome screen when no messages', async () => {
    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByText(UI_TEXT.WELCOME_TITLE)).toBeInTheDocument()
    })
  })

  it('renders trending searches on welcome screen', async () => {
    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByText(TRENDING_SEARCHES[0])).toBeInTheDocument()
      expect(screen.getByText(TRENDING_SEARCHES[1])).toBeInTheDocument()
      expect(screen.getByText(TRENDING_SEARCHES[2])).toBeInTheDocument()
    })
  })

  it('shows loading state while fetching history', async () => {
    // Make fetchConversationHistory hang
    ;(chatApi.fetchConversationHistory as Mock).mockImplementation(
      () => new Promise(() => {})
    )
    ;(localStorage.getItem as Mock).mockImplementation((key: string) => {
      if (key === CHAT_CONFIG.SESSION_STORAGE_KEY) return '12345678-1234-1234-1234-123456789012'
      return null
    })

    render(<ChatContainer />)

    expect(screen.getByText(UI_TEXT.LOADING_HISTORY)).toBeInTheDocument()
  })

  it('sends message and receives streaming response', async () => {
    let capturedCallbacks: any = {}
    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      capturedCallbacks = params
      // Simulate streaming tokens
      params.onToken('Hello')
      params.onToken(' world!')
      params.onComplete({ user_id: 1 })
      return Promise.resolve()
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(chatApi.streamChat).toHaveBeenCalled()
    })
  })

  it('handles ui_blocks in streaming response', async () => {
    const mockUiBlocks = [
      {
        block_type: 'product_cards',
        products: [
          { name: 'Test Product', price: '$99.99', rating: 4.5 },
        ],
      },
    ]

    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      params.onToken('Here are some products:')
      params.onComplete({
        user_id: 1,
        ui_blocks: mockUiBlocks,
      })
      return Promise.resolve()
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)
    fireEvent.change(input, { target: { value: 'Show me products' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(chatApi.streamChat).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Show me products',
        })
      )
    })
  })

  it('handles next_suggestions in streaming response', async () => {
    const mockSuggestions = [
      { id: '1', question: 'Tell me more about laptops' },
      { id: '2', question: 'Compare with other brands' },
    ]

    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      params.onToken('Here is the info.')
      params.onComplete({
        user_id: 1,
        next_suggestions: mockSuggestions,
      })
      return Promise.resolve()
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)
    fireEvent.change(input, { target: { value: 'Best laptops' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(chatApi.streamChat).toHaveBeenCalled()
    })
  })

  it('shows error banner on stream error', async () => {
    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      params.onError('Network error')
      return Promise.resolve()
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong/)).toBeInTheDocument()
    })
  })

  it('clears content when onClear is called', async () => {
    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      params.onToken('Initial content')
      params.onClear()
      params.onToken('New content')
      params.onComplete({ user_id: 1 })
      return Promise.resolve()
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)
    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(chatApi.streamChat).toHaveBeenCalled()
    })
  })

  it('clears history when clearHistoryTrigger changes', async () => {
    const { rerender } = render(<ChatContainer clearHistoryTrigger={0} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)).toBeInTheDocument()
    })

    // Send a message first
    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      params.onToken('Response')
      params.onComplete({ user_id: 1 })
      return Promise.resolve()
    })

    const input = screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(chatApi.streamChat).toHaveBeenCalled()
    })

    // Trigger clear
    rerender(<ChatContainer clearHistoryTrigger={1} />)

    await waitFor(() => {
      expect(screen.getByText(UI_TEXT.WELCOME_TITLE)).toBeInTheDocument()
    })
  })

  it('loads messages from localStorage on mount', async () => {
    const storedMessages = [
      {
        id: '1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date().toISOString(),
      },
      {
        id: '2',
        role: 'assistant',
        content: 'Hi there!',
        timestamp: new Date().toISOString(),
      },
    ]

    ;(localStorage.getItem as Mock).mockImplementation((key: string) => {
      if (key === CHAT_CONFIG.MESSAGES_STORAGE_KEY) return JSON.stringify(storedMessages)
      if (key === CHAT_CONFIG.SESSION_STORAGE_KEY) return '12345678-1234-1234-1234-123456789012'
      return null
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument()
      expect(screen.getByText('Hi there!')).toBeInTheDocument()
    })
  })

  it('fetches history from database when localStorage is empty', async () => {
    ;(localStorage.getItem as Mock).mockImplementation((key: string) => {
      if (key === CHAT_CONFIG.SESSION_STORAGE_KEY) return '12345678-1234-1234-1234-123456789012'
      return null
    })

    ;(chatApi.fetchConversationHistory as Mock).mockResolvedValue({
      success: true,
      messages: [
        { role: 'user', content: 'DB message', created_at: new Date().toISOString() },
        { role: 'assistant', content: 'DB response', created_at: new Date().toISOString() },
      ],
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(chatApi.fetchConversationHistory).toHaveBeenCalledWith(
        '12345678-1234-1234-1234-123456789012'
      )
    })
  })

  it('handles create_new_message for itinerary responses', async () => {
    const mockItinerary = {
      destination: 'Paris',
      days: [{ day: 1, activities: ['Eiffel Tower'] }],
    }

    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      params.onToken('Planning your trip...')
      params.onComplete({
        user_id: 1,
        create_new_message: true,
        itinerary: mockItinerary,
      })
      return Promise.resolve()
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)
    fireEvent.change(input, { target: { value: 'Plan Paris trip' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(chatApi.streamChat).toHaveBeenCalled()
    })
  })

  it('handles trending search button click', async () => {
    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      params.onToken('Here are the best gaming laptops...')
      params.onComplete({ user_id: 1 })
      return Promise.resolve()
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByText(TRENDING_SEARCHES[0])).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(TRENDING_SEARCHES[0]))

    await waitFor(() => {
      expect(chatApi.streamChat).toHaveBeenCalledWith(
        expect.objectContaining({
          message: TRENDING_SEARCHES[0],
        })
      )
    })
  })

  it('shows reconnecting indicator when SSE connection is retrying', async () => {
    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      // Simulate reconnecting callback
      params.onReconnecting(1, 3)
      // Don't call onComplete yet - keep it in reconnecting state
      return new Promise(() => {}) // Never resolves
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)
    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText(/Reconnecting/)).toBeInTheDocument()
    })
  })

  it('hides reconnecting indicator when connection is restored', async () => {
    ;(chatApi.streamChat as Mock).mockImplementation((params) => {
      params.onReconnecting(1, 3)
      // Simulate successful reconnection
      setTimeout(() => {
        params.onReconnected()
        params.onToken('Response after reconnect')
        params.onComplete({ user_id: 1 })
      }, 10)
      return Promise.resolve()
    })

    render(<ChatContainer />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(UI_TEXT.PLACEHOLDER_TEXT)
    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    // Wait for reconnection to complete
    await waitFor(() => {
      expect(screen.queryByText(/Reconnecting/)).not.toBeInTheDocument()
    }, { timeout: 1000 })
  })
})
