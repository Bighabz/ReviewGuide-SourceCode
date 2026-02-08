'use client'

import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface Tab {
    id: string
    label: string
}

interface CategoryTabsProps {
    tabs: readonly Tab[]
    activeTab: string
    onTabChange: (id: string) => void
    className?: string
}

export function CategoryTabs({ tabs, activeTab, onTabChange, className }: CategoryTabsProps) {
    return (
        <div className={cn("flex space-x-1 overflow-x-auto scrollbar-hide pb-2", className)}>
            {tabs.map((tab) => {
                const isActive = activeTab === tab.id
                return (
                    <button
                        key={tab.id}
                        onClick={() => onTabChange(tab.id)}
                        className={cn(
                            "relative px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap rounded-lg outline-none focus-visible:ring-2",
                            isActive
                                ? "text-[var(--gpt-accent)]"
                                : "text-[var(--gpt-text-secondary)] hover:text-[var(--gpt-text)] hover:bg-[var(--gpt-hover)]"
                        )}
                    >
                        {/* Tab Label */}
                        <span className="relative z-10">{tab.label}</span>

                        {/* Sliding Background/Indicator */}
                        {isActive && (
                            <motion.div
                                layoutId="activeTab"
                                className="absolute inset-x-0 bottom-0 h-0.5 bg-[var(--gpt-accent)] rounded-full"
                                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                            />
                        )}

                        {/* Alternative: Sliding Background Pill style (optional, if preferred)
            {isActive && (
              <motion.div
                layoutId="activeTabBg"
                className="absolute inset-0 bg-[var(--gpt-accent-light)] rounded-lg"
                initial={false}
                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
              />
            )} 
            */}
                    </button>
                )
            })}
        </div>
    )
}
