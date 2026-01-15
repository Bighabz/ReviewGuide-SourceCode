'use client'

import {
  ShoppingCart,
  Plane,
  Laptop,
  Sparkles,
  Home,
  Gamepad2,
  Book,
  Coffee,
  Shirt,
  Heart,
  User,
  X,
} from 'lucide-react'
import Image from 'next/image'
import { useRef, useEffect, useState } from 'react'

const categories = [
  { id: 'shopping', name: 'Shopping', icon: ShoppingCart },
  { id: 'travel', name: 'Travel', icon: Plane },
  { id: 'electronics', name: 'Electronics', icon: Laptop },
  { id: 'beauty', name: 'Beauty', icon: Sparkles },
  { id: 'home', name: 'Home', icon: Home },
  { id: 'gaming', name: 'Gaming', icon: Gamepad2 },
  { id: 'books', name: 'Books', icon: Book },
  { id: 'food', name: 'Food', icon: Coffee },
  { id: 'fashion', name: 'Fashion', icon: Shirt },
  { id: 'health', name: 'Health', icon: Heart },
]

interface CategorySidebarProps {
  isOpen?: boolean
  onClose?: () => void
}

export default function CategorySidebar({ isOpen = true, onClose }: CategorySidebarProps) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    // Get initial theme
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    const initialTheme = savedTheme || 'light'
    setTheme(initialTheme)

    // Listen for theme changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
          const newTheme = document.documentElement.getAttribute('data-theme') as 'light' | 'dark' | null
          if (newTheme) {
            setTheme(newTheme)
          }
        }
      })
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    })

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
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar - Slim and lighter design */}
      <div
        id="category-sidebar"
        className={`
          fixed lg:static inset-y-0 left-0 z-[60]
          w-64 lg:w-56 flex flex-col h-screen
          transform transition-transform duration-300 ease-in-out
          lg:transform-none
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        style={{ background: 'var(--gpt-sidebar)', borderRight: '1px solid rgba(0,0,0,0.06)' }}
      >
        {/* Close button for mobile - Top right corner */}
        <button
          onClick={onClose}
          className="lg:hidden absolute top-1 right-1 p-1 rounded-full z-[70] hover:bg-opacity-20 transition-colors flex items-center justify-center"
          style={{
            background: 'transparent',
            color: 'var(--gpt-text)',
            cursor: 'pointer',
          }}
        >
          <X size={18} strokeWidth={2} />
        </button>

        {/* Top Section with Logo - Smaller and lighter */}
        <div className="border-b" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
          <div className="w-full flex items-center justify-center" style={{ height: '120px', padding: '16px' }}>
            <Image
              src={logoSrc}
              alt="Review Guide AI"
              width={160}
              height={96}
              priority
              style={{
                width: 'auto',
                height: 'auto',
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                opacity: 0.9
              }}
            />
          </div>
        </div>

      {/* Categories - Lighter, smaller icons and text */}
      <div id="category-list" className="flex-1 overflow-y-auto px-2 py-3">
        <nav id="category-nav" className="space-y-0.5">
          {categories.map((category) => {
            const Icon = category.icon
            return (
              <button
                id={`category-${category.id}`}
                key={category.id}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg group text-left"
                style={{
                  color: 'var(--gpt-text-secondary)',
                  background: 'transparent',
                  cursor: 'pointer',
                  transition: 'all var(--gpt-transition)',
                  opacity: 0.75
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(0,0,0,0.03)'
                  e.currentTarget.style.opacity = '1'
                  const icon = e.currentTarget.querySelector('svg')
                  if (icon) {
                    ;(icon as SVGSVGElement).style.color = 'var(--gpt-accent)'
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.opacity = '0.75'
                  const icon = e.currentTarget.querySelector('svg')
                  if (icon) {
                    ;(icon as SVGSVGElement).style.color = 'var(--gpt-text-secondary)'
                  }
                }}
              >
                <Icon size={16} style={{ color: 'var(--gpt-text-secondary)', transition: 'color var(--gpt-transition)', opacity: 0.6 }} />
                <span className="text-sm font-normal">{category.name}</span>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Footer - Lighter styling */}
      <div className="border-t" style={{ borderColor: 'rgba(0,0,0,0.06)', background: 'var(--gpt-sidebar)' }}>
        <div className="p-3">
          <div className="flex items-center gap-2 px-2 py-1.5">
            <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.04)' }}>
              <User size={13} style={{ color: 'var(--gpt-text-secondary)', opacity: 0.6 }} />
            </div>
            <div>
              <p className="text-sm font-normal" style={{ color: 'var(--gpt-text-secondary)', opacity: 0.8 }}>Guest User</p>
              <p className="text-xs" style={{ color: 'var(--gpt-text-muted)', opacity: 0.6 }}>Active</p>
            </div>
          </div>
        </div>

        {/* Affiliate disclaimer */}
        <div className="px-3 pb-3 pt-2 border-t" style={{ borderColor: 'rgba(0,0,0,0.04)' }}>
          <p className="text-xs leading-relaxed px-2" style={{ color: 'var(--gpt-text-muted)', opacity: 0.4 }}>
            <strong>Disclosure:</strong> ReviewGuide.ai earns commissions when you buy through our affiliate links. This does not affect the products we recommend.
          </p>
        </div>
      </div>
      </div>
    </>
  )
}
