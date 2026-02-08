'use client'

import { Sun, Moon, Menu, Trash2, History, Plus } from 'lucide-react'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'

interface TopbarProps {
  onMenuClick?: () => void
  onClearHistory?: () => void
  onHistoryClick?: () => void
  onNewChat?: () => void
}

export default function Topbar({ onMenuClick, onClearHistory, onHistoryClick, onNewChat }: TopbarProps) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  // Initialize theme from localStorage or default to 'light' (Amazon-style clean theme)
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
      className="sticky top-0 z-50 h-16 w-full flex items-center justify-between px-4 sm:px-6 gap-4 bg-[var(--gpt-glass-bg)] border-b border-[var(--gpt-glass-border)] backdrop-blur-md supports-[backdrop-filter]:bg-[var(--gpt-glass-bg)]"
    >
      {/* Mobile Menu Button - Hamburger icon */}
      <button
        id="mobile-browse-button"
        onClick={onMenuClick}
        className="lg:hidden p-2 rounded-lg hover:bg-[var(--gpt-hover)] transition-colors text-[var(--gpt-text-secondary)]"
        title="Browse categories"
      >
        <Menu size={20} />
      </button>

      {/* Brand / Title - Click to go Home/Browse */}
      <Link href="/browse" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
        {/* Animated Logo */}
        <img
          src="/images/ezgif-7b66ba24abcfdab0.gif"
          alt="ReviewGuide.ai Logo"
          className="w-10 h-10 rounded-lg object-contain"
        />

        <div className="flex flex-col">
          <h1 className="text-base sm:text-lg font-bold text-[var(--gpt-text)] leading-tight">
            ReviewGuide.ai
          </h1>
          <span className="text-[10px] sm:text-xs font-medium text-[var(--gpt-text-secondary)] tracking-wide uppercase">
            Smart Shopping Assistant
          </span>
        </div>
      </Link>

      {/* Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Browse Link */}
        <Link href="/browse" className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg text-[var(--gpt-text-secondary)] hover:bg-[var(--gpt-hover)] hover:text-[var(--gpt-text)] transition-all font-medium text-sm">
          Browse
        </Link>

        {/* New Chat Button - Prominent */}
        <button
          onClick={onNewChat}
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--gpt-accent)] text-white hover:bg-[var(--gpt-accent-hover)] transition-all shadow-[var(--gpt-shadow-sm)] hover:shadow-[var(--gpt-shadow-md)] active:scale-95"
          title="Start new chat"
        >
          <Plus size={16} strokeWidth={2.5} />
          <span className="text-sm font-semibold">New Chat</span>
        </button>

        {/* Mobile New Chat (Icon Only) */}
        <button
          onClick={onNewChat}
          className="sm:hidden p-2 rounded-lg bg-[var(--gpt-accent)] text-white shadow-sm active:scale-95"
          title="Start new chat"
        >
          <Plus size={20} />
        </button>

        <div className="w-px h-6 bg-[var(--gpt-border)] mx-1 hidden sm:block" />

        {/* History Button */}
        <button
          onClick={onHistoryClick}
          className="p-2 rounded-lg text-[var(--gpt-text-secondary)] hover:text-[var(--gpt-text)] hover:bg-[var(--gpt-hover)] transition-colors"
          title="Chat history"
        >
          <History size={20} strokeWidth={2} />
        </button>

        {/* Clear History Button */}
        <button
          onClick={onClearHistory}
          className="p-2 rounded-lg text-[var(--gpt-text-secondary)] hover:text-red-500 hover:bg-red-50 transition-colors"
          title="Clear chat history"
        >
          <Trash2 size={20} strokeWidth={2} />
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-[var(--gpt-text-secondary)] hover:text-[var(--gpt-text)] hover:bg-[var(--gpt-hover)] transition-colors"
          title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
        >
          <motion.div
            initial={false}
            animate={{ rotate: theme === 'dark' ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
          </motion.div>
        </button>

        {/* User Avatar Dropdown Placeholder */}
        <div className="ml-1 hidden sm:block">
          <button className="w-8 h-8 rounded-full bg-[var(--gpt-accent-light)] border border-[var(--gpt-border)] flex items-center justify-center text-[var(--gpt-accent)] hover:ring-2 ring-[var(--gpt-accent)] ring-opacity-50 transition-all">
            <span className="font-bold text-xs">Guest</span>
          </button>
        </div>
      </div>
    </div>
  )
}
