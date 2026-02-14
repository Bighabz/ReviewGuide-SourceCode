'use client'

import {
  Plane,
  Laptop,
  Home,
  Heart,
  Mountain,
  Shirt,
  User,
  X,
} from 'lucide-react'
import { useEffect, useState, useRef } from 'react'
import { categories } from '@/lib/categoryConfig'

const ICON_MAP: Record<string, any> = {
  Plane,
  Laptop,
  Home,
  Heart,
  Mountain,
  Shirt,
}

interface CategorySidebarProps {
  isOpen?: boolean
  onClose?: () => void
}

export default function CategorySidebar({ isOpen = true, onClose }: CategorySidebarProps) {
  const [activeSlug, setActiveSlug] = useState<string | null>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)

  // IntersectionObserver to highlight active category on scroll
  useEffect(() => {
    const sections = categories
      .map((cat) => document.getElementById(`category-${cat.slug}`))
      .filter(Boolean) as HTMLElement[]

    if (sections.length === 0) return

    observerRef.current = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const slug = entry.target.id.replace('category-', '')
            setActiveSlug(slug)
          }
        }
      },
      { rootMargin: '-20% 0px -60% 0px', threshold: 0 }
    )

    sections.forEach((section) => observerRef.current?.observe(section))

    return () => observerRef.current?.disconnect()
  }, [])

  const handleClick = (slug: string) => {
    document.getElementById(`category-${slug}`)?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    })
    if (onClose) onClose()
  }

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
              const Icon = ICON_MAP[category.icon] || Laptop
              const isActive = activeSlug === category.slug
              return (
                <button
                  key={category.slug}
                  onClick={() => handleClick(category.slug)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-left transition-all group ${
                    isActive
                      ? 'bg-[var(--primary-light)] text-[var(--text)] font-semibold'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]'
                  }`}
                >
                  <Icon
                    size={16}
                    strokeWidth={1.5}
                    className={`transition-colors ${
                      isActive
                        ? 'text-[var(--primary)]'
                        : 'text-[var(--text-muted)] group-hover:text-[var(--primary)]'
                    }`}
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
