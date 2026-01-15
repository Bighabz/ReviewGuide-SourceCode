'use client'

import { Send } from 'lucide-react'
import { useRef, useEffect } from 'react'

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  disabled?: boolean
  placeholder?: string
}

export default function ChatInput({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = 'Type your message...',
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const adjustHeight = () => {
    const textarea = textareaRef.current
    if (textarea) {
      // Calculate line height (approximately 24px per line with padding)
      const lineHeight = 24
      const maxRows = 10
      const maxHeight = lineHeight * maxRows

      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, maxHeight) + 'px'
    }
  }

  useEffect(() => {
    adjustHeight()
  }, [value])

  return (
    <div className="w-full">
      <div className="relative flex items-center">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => {
            onChange(e.target.value)
            adjustHeight()
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="w-full resize-none rounded-2xl px-4 py-3 pr-10 focus:outline-none disabled:cursor-not-allowed scrollbar-hide text-sm sm:text-base"
          style={{
            minHeight: '52px',
            maxHeight: '240px',
            overflowY: 'auto',
            background: 'var(--gpt-input-bg)',
            border: '1px solid var(--gpt-input-border)',
            color: 'var(--gpt-text)',
            boxShadow: 'var(--gpt-shadow-sm)',
            transition: 'border-color var(--gpt-transition), box-shadow var(--gpt-transition)'
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'var(--gpt-accent)'
            e.currentTarget.style.boxShadow = '0 0 0 3px var(--gpt-accent-light)'
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'var(--gpt-input-border)'
            e.currentTarget.style.boxShadow = 'var(--gpt-shadow-sm)'
          }}
        />
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          data-send-button
          className="btn-small absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center justify-center rounded-md w-[30px] h-[30px] sm:w-auto sm:h-auto sm:p-2 disabled:cursor-not-allowed disabled:opacity-30"
          style={{
            background: disabled || !value.trim() ? 'var(--gpt-text-muted)' : 'var(--gpt-accent)',
            color: 'white',
            transition: 'all var(--gpt-transition)'
          }}
          onMouseEnter={(e) => {
            if (!disabled && value.trim()) {
              e.currentTarget.style.background = 'var(--gpt-accent-hover)'
              e.currentTarget.style.transform = 'translateY(-50%) scale(1.05)'
            }
          }}
          onMouseLeave={(e) => {
            if (!disabled && value.trim()) {
              e.currentTarget.style.background = 'var(--gpt-accent)'
              e.currentTarget.style.transform = 'translateY(-50%) scale(1)'
            }
          }}
        >
          <Send size={16} className="sm:w-[18px] sm:h-[18px]" />
        </button>
      </div>
      {/* Hint text - Hidden on mobile */}
      <div className="hidden sm:flex items-center justify-center gap-2 mt-2" style={{ color: 'var(--gpt-text-muted)', fontSize: '12px' }}>
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M7 4v4l2 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        <span>Press <kbd className="px-1.5 py-0.5 rounded" style={{ background: 'var(--gpt-hover)', border: '1px solid var(--gpt-border)', fontSize: '11px' }}>Shift</kbd> + <kbd className="px-1.5 py-0.5 rounded" style={{ background: 'var(--gpt-hover)', border: '1px solid var(--gpt-border)', fontSize: '11px' }}>Enter</kbd> for new line</span>
      </div>
    </div>
  )
}
