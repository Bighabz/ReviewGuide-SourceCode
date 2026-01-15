'use client'

import ReactMarkdown from 'react-markdown'

interface ProductRecommendationsProps {
  content: string
}

export default function ProductRecommendations({ content }: ProductRecommendationsProps) {
  return (
    <div className="rounded-lg border p-6 my-6" style={{ background: 'var(--gpt-assistant-message)', borderColor: 'var(--gpt-border)' }}>
      <div className="prose prose-sm max-w-none" style={{ color: 'var(--gpt-text)' }}>
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  )
}
