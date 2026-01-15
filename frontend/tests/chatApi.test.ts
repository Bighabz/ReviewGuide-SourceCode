import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { streamChat, login, checkHealth } from '@/lib/chatApi'

// Mock ReadableStream for SSE testing
function createMockReadableStream(chunks: string[]) {
  let index = 0
  const encoder = new TextEncoder()

  return {
    getReader: () => ({
      read: async () => {
        if (index < chunks.length) {
          const chunk = chunks[index++]
          return { done: false, value: encoder.encode(chunk) }
        }
        return { done: true, value: undefined }
      },
    }),
  }
}

describe('chatApi', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  describe('streamChat', () => {
    it('calls onToken for each token received', async () => {
      const onToken = vi.fn()
      const onComplete = vi.fn()
      const onError = vi.fn()

      const mockStream = createMockReadableStream([
        'data: {"token":"Hello"}\n',
        'data: {"token":" world"}\n',
        'data: {"done":true,"status":"completed"}\n',
      ])

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      })

      const promise = streamChat({
        message: 'test',
        onToken,
        onComplete,
        onError,
      })

      await vi.runAllTimersAsync()
      await promise

      expect(onToken).toHaveBeenCalledWith('Hello', undefined)
      expect(onToken).toHaveBeenCalledWith(' world', undefined)
      expect(onComplete).toHaveBeenCalledWith(expect.objectContaining({
        status: 'completed',
      }))
      expect(onError).not.toHaveBeenCalled()
    })

    it('calls onError on 4xx response without retry', async () => {
      const onToken = vi.fn()
      const onComplete = vi.fn()
      const onError = vi.fn()

      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
      })

      const promise = streamChat({
        message: 'test',
        onToken,
        onComplete,
        onError,
      })

      await vi.runAllTimersAsync()
      await promise

      expect(onError).toHaveBeenCalledWith('Request failed: 400')
      expect(fetch).toHaveBeenCalledTimes(1) // No retry
    })

    it('retries on network error with exponential backoff', async () => {
      const onToken = vi.fn()
      const onComplete = vi.fn()
      const onError = vi.fn()

      // First call fails with network error, second succeeds
      let callCount = 0
      global.fetch = vi.fn().mockImplementation(async () => {
        callCount++
        if (callCount === 1) {
          throw new TypeError('Failed to fetch')
        }
        return {
          ok: true,
          body: createMockReadableStream([
            'data: {"done":true,"status":"completed"}\n',
          ]),
        }
      })

      const promise = streamChat({
        message: 'test',
        onToken,
        onComplete,
        onError,
      })

      // Allow retries to happen
      await vi.runAllTimersAsync()
      await promise

      expect(fetch).toHaveBeenCalledTimes(2) // Initial + 1 retry
      expect(onComplete).toHaveBeenCalled()
      expect(onError).not.toHaveBeenCalled()
    })

    it('calls onError after max retries exceeded', async () => {
      const onToken = vi.fn()
      const onComplete = vi.fn()
      const onError = vi.fn()

      // All calls fail with network error
      global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))

      const promise = streamChat({
        message: 'test',
        onToken,
        onComplete,
        onError,
      })

      await vi.runAllTimersAsync()
      await promise

      expect(fetch).toHaveBeenCalledTimes(3) // MAX_RETRIES = 3
      expect(onError).toHaveBeenCalledWith('Failed to fetch')
    })

    it('calls onClear when clear flag is received', async () => {
      const onToken = vi.fn()
      const onComplete = vi.fn()
      const onError = vi.fn()
      const onClear = vi.fn()

      const mockStream = createMockReadableStream([
        'data: {"clear":true}\n',
        'data: {"done":true}\n',
      ])

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      })

      const promise = streamChat({
        message: 'test',
        onToken,
        onComplete,
        onError,
        onClear,
      })

      await vi.runAllTimersAsync()
      await promise

      expect(onClear).toHaveBeenCalled()
    })

    it('handles ui_blocks in intermediate chunks', async () => {
      const onToken = vi.fn()
      const onComplete = vi.fn()
      const onError = vi.fn()

      const uiBlocks = [{ type: 'product', data: { name: 'Test Product' } }]

      const mockStream = createMockReadableStream([
        `data: ${JSON.stringify({ ui_blocks: uiBlocks })}\n`,
        'data: {"done":true}\n',
      ])

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      })

      const promise = streamChat({
        message: 'test',
        onToken,
        onComplete,
        onError,
      })

      await vi.runAllTimersAsync()
      await promise

      expect(onComplete).toHaveBeenCalledWith(expect.objectContaining({
        ui_blocks: uiBlocks,
      }))
    })

    it('handles error in SSE data', async () => {
      const onToken = vi.fn()
      const onComplete = vi.fn()
      const onError = vi.fn()

      const mockStream = createMockReadableStream([
        'data: {"error":"Server error occurred"}\n',
      ])

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      })

      const promise = streamChat({
        message: 'test',
        onToken,
        onComplete,
        onError,
      })

      await vi.runAllTimersAsync()
      await promise

      expect(onError).toHaveBeenCalledWith('Server error occurred')
    })
  })

  describe('login', () => {
    it('returns access token on successful login', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ access_token: 'test-token' }),
      })

      const result = await login('admin', 'password')

      expect(result.access_token).toBe('test-token')
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ username: 'admin', password: 'password' }),
        })
      )
    })

    it('throws error on failed login', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ detail: 'Invalid credentials' }),
      })

      await expect(login('admin', 'wrong')).rejects.toThrow('Invalid credentials')
    })
  })

  describe('checkHealth', () => {
    it('returns health status', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok' }),
      })

      const result = await checkHealth()

      expect(result.status).toBe('ok')
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/health'))
    })
  })
})
