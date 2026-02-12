'use client'

import {
  Compass,
  Plane,
  Laptop,
  Sparkles,
  Home,
  Gamepad2,
  Shirt,
  Dumbbell,
  User,
  X,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

const categories = [
  { id: 'home', name: 'Discover', icon: Compass, isHome: true },
  { id: 'travel', name: 'Travel', icon: Plane },
  { id: 'electronics', name: 'Electronics', icon: Laptop },
  { id: 'gaming', name: 'Gaming', icon: Gamepad2 },
  { id: 'home-garden', name: 'Kitchen', icon: Home },
  { id: 'fashion', name: 'Fashion', icon: Shirt },
  { id: 'sports', name: 'Sports', icon: Dumbbell },
  { id: 'beauty', name: 'Beauty', icon: Sparkles },
]

interface CategorySidebarProps {
  isOpen?: boolean
  onClose?: () => void
}

export default function CategorySidebar({ isOpen = true, onClose }: CategorySidebarProps) {
  const router = useRouter()
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    setTheme(savedTheme || 'light')

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
          const newTheme = document.documentElement.getAttribute('data-theme') as 'light' | 'dark' | null
          if (newTheme) setTheme(newTheme)
        }
      })
    })

    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => observer.disconnect()
  }, [])

  const logoSrc = theme === 'dark'
    ? '/images/1815e5dc-c4db-4248-9aeb-0a815fd87a4b.png'
    : '/images/8f4c1971-a5b0-474e-9fb1-698e76324f0b.png'

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          fixed lg:relative inset-y-0 left-0 z-[60]
          w-56 lg:w-52 flex flex-col h-screen lg:h-full
          transform transition-transform duration-300 ease-out
          lg:transform-none border-r border-[var(--border)]
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        style={{ background: 'var(--surface)' }}
      >
        {/* Close button (mobile) */}
        <button
          onClick={onClose}
          className="lg:hidden absolute top-3 right-3 p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] z-[70]"
        >
          <X size={16} strokeWidth={1.5} />
        </button>

        {/* Categories */}
        <div className="flex-1 overflow-y-auto px-3 py-5">
          <div className="text-[10px] font-semibold uppercase tracking-widest text-[var(--text-muted)] px-3 mb-3">
            Categories
          </div>
          <nav className="space-y-0.5">
            {categories.map((category) => {
              const Icon = category.icon
              return (
                <button
                  key={category.id}
                  onClick={() => {
                    const path = category.id === 'home' ? '/browse' : `/browse/${category.id}`
                    router.push(path)
                    if (onClose) onClose()
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-left text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-all group"
                >
                  <Icon
                    size={16}
                    strokeWidth={1.5}
                    className="text-[var(--text-muted)] group-hover:text-[var(--primary)] transition-colors"
                  />
                  <span className="text-sm font-medium">{category.name}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Footer */}
        <div className="border-t border-[var(--border)] p-3">
          <div className="flex items-center gap-2.5 px-2 py-2">
            <div className="w-7 h-7 rounded-full bg-[var(--surface-hover)] flex items-center justify-center">
              <User size={13} strokeWidth={1.5} className="text-[var(--text-muted)]" />
            </div>
            <div>
              <p className="text-sm text-[var(--text-secondary)]">Guest</p>
              <p className="text-[10px] text-[var(--text-muted)]">Active</p>
            </div>
          </div>
          <div className="mt-2 pt-2 border-t border-[var(--border)]">
            <p className="text-[10px] text-[var(--text-muted)] leading-relaxed px-2">
              ReviewGuide.ai earns commissions via affiliate links.
            </p>
          </div>
        </div>
      </div>
    </>
  )
}
