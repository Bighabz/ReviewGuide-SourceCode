'use client'

import { usePathname, useRouter } from 'next/navigation'
import UnifiedTopbar from './UnifiedTopbar'
import MobileHeader from './MobileHeader'
import MobileTabBar from './MobileTabBar'
import Footer from './Footer'
import { ChatStatusProvider } from '@/lib/chatStatusContext'

const EXCLUDED_PREFIXES = ['/admin', '/privacy', '/terms', '/affiliate-disclosure', '/login']

interface NavLayoutProps {
  children: React.ReactNode
}

export default function NavLayout({ children }: NavLayoutProps) {
  const pathname = usePathname()
  const router = useRouter()

  const isExcluded = EXCLUDED_PREFIXES.some((prefix) => pathname?.startsWith(prefix))

  if (isExcluded) {
    // Excluded routes render children with no layout chrome.
    // Each excluded route manages its own topbar (or none).
    return <>{children}</>
  }

  const handleSearch = (query: string) => {
    router.push(`/chat?q=${encodeURIComponent(query)}&new=1`)
  }

  const handleNewChat = () => {
    router.push('/chat?new=1')
  }

  const handleHistory = () => {
    router.push('/chat')
  }

  return (
    <ChatStatusProvider>
      <div className="flex flex-col h-dvh">
        {/* Desktop: UnifiedTopbar (hidden on mobile) */}
        <div className="hidden md:block">
          <UnifiedTopbar
            onSearch={handleSearch}
            onNewChat={handleNewChat}
            onHistoryClick={handleHistory}
          />
        </div>

        {/* Mobile: MobileHeader (hidden on desktop) */}
        <div className="block md:hidden">
          <MobileHeader />
        </div>

        {/* Content area — padded bottom on mobile for 64px tab bar + safe area.
            overflow-y-auto added 2026-04-21 to fix desktop overflow at ≤1200px-tall viewports:
            without it, content taller than (viewport - topbar - footer) overflowed main and
            rendered behind the footer. Chat page's inner h-full overflow-hidden prevents
            double-scroll; homepage/browse use main's scroll. */}
        <main className="flex-1 min-h-0 overflow-y-auto pb-[calc(64px+env(safe-area-inset-bottom))] md:pb-0">
          {children}
        </main>

        {/* Desktop: Footer (hidden on mobile) */}
        <div className="hidden md:block">
          <Footer />
        </div>

        {/* Mobile: MobileTabBar (hidden on desktop) */}
        <div className="block md:hidden">
          <MobileTabBar />
        </div>
      </div>
    </ChatStatusProvider>
  )
}
