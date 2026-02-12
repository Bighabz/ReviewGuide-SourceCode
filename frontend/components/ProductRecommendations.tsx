'use client'

import ReactMarkdown from 'react-markdown'

interface ProductRecommendationsProps {
  content: string
}

export default function ProductRecommendations({ content }: ProductRecommendationsProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 my-6 shadow-card">
      <div className="prose prose-sm max-w-none text-[var(--text)]">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  )
}
