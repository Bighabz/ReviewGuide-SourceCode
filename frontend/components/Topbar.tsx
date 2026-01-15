'use client'

import { Sun, Moon, Menu, Trash2 } from 'lucide-react'
import { useState, useEffect } from 'react'

interface TopbarProps {
  onMenuClick?: () => void
  onClearHistory?: () => void
}

export default function Topbar({ onMenuClick, onClearHistory }: TopbarProps) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  // Initialize theme from localStorage or default to 'light'
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    const initialTheme = savedTheme || 'light'
    setTheme(initialTheme)
    document.documentElement.setAttribute('data-theme', initialTheme)
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('theme', newTheme)
  }

  return (
    <div
      id="topbar"
      className="sticky top-0 z-50 h-16 px-3 sm:px-6 flex items-center justify-between gap-2"
      style={{
        background: 'var(--gpt-background)',
        borderBottom: '1px solid var(--gpt-border)',
        backdropFilter: 'blur(10px)'
      }}
    >
      {/* Mobile Menu Button - Hamburger icon */}
      <button
        id="mobile-browse-button"
        onClick={onMenuClick}
        className="lg:hidden p-1.5 sm:p-2 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{
          background: 'transparent',
          border: '1px solid var(--gpt-border)',
          color: 'var(--gpt-text)',
          cursor: 'pointer',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'var(--gpt-hover)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent'
        }}
        title="Browse categories"
      >
        <Menu size={16} className="sm:w-[18px] sm:h-[18px]" />
      </button>

      {/* Title */}
      <div className="flex-1 min-w-0 px-3 sm:px-0">
        <h1 className="text-xs sm:text-xl font-semibold truncate" style={{ color: 'var(--gpt-text)' }}>
          Review Guide AI
        </h1>
        <p className="text-xs truncate hidden sm:block" style={{ color: 'var(--gpt-text-secondary)' }}>
          AI Travel Planner & Product Recommendation Assistant
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-1.5 sm:gap-3 flex-shrink-0">
        {/* Clear History Button */}
        <button
          onClick={onClearHistory}
          className="p-2 rounded-lg flex items-center justify-center"
          style={{
            background: 'transparent',
            border: '1px solid var(--gpt-border)',
            color: 'var(--gpt-text)',
            cursor: 'pointer',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--gpt-hover)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent'
          }}
          title="Clear chat history"
        >
          <Trash2 size={18} />
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg flex items-center justify-center"
          style={{
            background: 'transparent',
            border: '1px solid var(--gpt-border)',
            color: 'var(--gpt-text)',
            cursor: 'pointer',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--gpt-hover)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent'
          }}
          title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>

        {/* Divider */}
        <div
          className="h-6 w-px hidden sm:block"
          style={{ background: 'var(--gpt-border)' }}
        />

        {/* Model Selector - Hidden */}
        <div id="model-selector" className="hidden md:flex items-center gap-2" style={{ display: 'none' }}>
          <label
            htmlFor="model-select"
            className="text-sm font-medium"
            style={{ color: 'var(--gpt-text-secondary)' }}
          >
            Model
          </label>
          <select
            id="model-select"
            className="px-3 py-1.5 rounded-lg text-sm"
            style={{
              background: 'var(--gpt-input-bg)',
              border: '1px solid var(--gpt-input-border)',
              color: 'var(--gpt-text)',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--gpt-accent)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--gpt-input-border)'
            }}
          >
            <option>OpenAI - gpt-4o-mini</option>
            <option>OpenAI - gpt-4o</option>
            <option>OpenAI - gpt-3.5-turbo</option>
          </select>
        </div>
      </div>
    </div>
  )
}
