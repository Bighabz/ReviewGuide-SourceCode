'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronLeft, ChevronRight, Star, ArrowRight } from 'lucide-react'

interface ProductSlide {
  id: string
  tag: string
  tagColor: string
  title: string
  subtitle: string
  score: string
  scoreLabel: string
  price?: string
  query: string
  image: string
  gradient: string
  iconColor: string
}

const SLIDES: ProductSlide[] = [
  {
    id: 'headphones',
    tag: 'TOP PICK',
    tagColor: '#92400E',
    title: 'Best Headphones 2026',
    subtitle: 'Sony WH-1000XM6 leads for noise cancellation',
    score: '4.7',
    scoreLabel: 'Expert Score',
    price: '$348',
    query: 'Best noise-cancelling headphones 2026',
    image: '/images/products/headphones.webp',
    gradient: 'linear-gradient(135deg, #DBEAFE 0%, #93C5FD 50%, #60A5FA 100%)',
    iconColor: '#2563EB',
  },
  {
    id: 'tokyo',
    tag: 'TRENDING',
    tagColor: '#9A3412',
    title: 'Tokyo Travel Guide',
    subtitle: '7-day itinerary with flights, stays & hidden gems',
    score: '4.9',
    scoreLabel: 'Traveler Rating',
    query: 'Tokyo travel guide flights hotels hidden gems',
    image: '/images/products/tokyo.webp',
    gradient: 'linear-gradient(135deg, #FEF3C7 0%, #FDE68A 50%, #FBBF24 100%)',
    iconColor: '#D97706',
  },
  {
    id: 'laptops',
    tag: 'BEST VALUE',
    tagColor: '#166534',
    title: 'Laptops for Students',
    subtitle: 'M4 MacBook Air vs ThinkPad X1 — expert verdict',
    score: '4.6',
    scoreLabel: 'Expert Score',
    price: '$999',
    query: 'Best laptops for students 2026',
    image: '/images/products/laptop.webp',
    gradient: 'linear-gradient(135deg, #D1FAE5 0%, #6EE7B7 50%, #34D399 100%)',
    iconColor: '#059669',
  },
  {
    id: 'vacuums',
    tag: 'EDITOR PICK',
    tagColor: '#6B21A8',
    title: 'Robot Vacuums Ranked',
    subtitle: 'Roborock S8 MaxV Ultra dominates pet hair tests',
    score: '4.6',
    scoreLabel: 'Expert Score',
    price: '$649',
    query: 'Best robot vacuums for pet hair',
    image: '/images/products/vacuum.webp',
    gradient: 'linear-gradient(135deg, #F3E8FF 0%, #D8B4FE 50%, #C084FC 100%)',
    iconColor: '#7C3AED',
  },
  {
    id: 'running',
    tag: 'NEW',
    tagColor: '#991B1B',
    title: 'Running Shoes Ranked',
    subtitle: 'Nike Vaporfly 4 vs Adidas Adizero Pro 4',
    score: '4.5',
    scoreLabel: 'Expert Score',
    price: '$260',
    query: 'Best running shoes trail treadmill 2026',
    image: '/images/products/shoes.webp',
    gradient: 'linear-gradient(135deg, #FFE4E6 0%, #FDA4AF 50%, #FB7185 100%)',
    iconColor: '#E11D48',
  },
]

const AUTO_INTERVAL = 4000

export default function ProductCarousel() {
  const router = useRouter()
  const [current, setCurrent] = useState(0)
  const [isHovered, setIsHovered] = useState(false)
  const [touchStart, setTouchStart] = useState<number | null>(null)
  const [direction, setDirection] = useState<'left' | 'right'>('right')
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const goTo = useCallback((idx: number, dir?: 'left' | 'right') => {
    setDirection(dir || (idx > current ? 'right' : 'left'))
    setCurrent(idx)
  }, [current])

  const next = useCallback(() => {
    setDirection('right')
    setCurrent(prev => (prev + 1) % SLIDES.length)
  }, [])

  const prev = useCallback(() => {
    setDirection('left')
    setCurrent(prev => (prev - 1 + SLIDES.length) % SLIDES.length)
  }, [])

  // Auto-rotate
  useEffect(() => {
    if (isHovered) return
    timerRef.current = setInterval(next, AUTO_INTERVAL)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [next, isHovered])

  // Touch swipe
  const handleTouchStart = (e: React.TouchEvent) => setTouchStart(e.touches[0].clientX)
  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStart === null) return
    const diff = touchStart - e.changedTouches[0].clientX
    if (Math.abs(diff) > 50) diff > 0 ? next() : prev()
    setTouchStart(null)
  }

  const slide = SLIDES[current]

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p style={{
          textTransform: 'uppercase',
          fontSize: '11px',
          fontWeight: 600,
          color: 'var(--text-muted)',
          letterSpacing: '1.5px',
        }}>
          Recommended For You
        </p>
        {/* Desktop arrows */}
        <div className="hidden sm:flex gap-1">
          <button
            onClick={prev}
            className="w-7 h-7 rounded-full flex items-center justify-center transition-colors"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}
            aria-label="Previous"
          >
            <ChevronLeft size={14} />
          </button>
          <button
            onClick={next}
            className="w-7 h-7 rounded-full flex items-center justify-center transition-colors"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}
            aria-label="Next"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* Card */}
      <div
        className="relative overflow-hidden rounded-2xl cursor-pointer group"
        style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          boxShadow: 'var(--shadow-md)',
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onClick={() => router.push(`/chat?q=${encodeURIComponent(slide.query)}&new=1`)}
      >
        {/* Hero image area */}
        <div
          className="relative overflow-hidden transition-all duration-700"
          style={{ background: slide.gradient, height: '160px' }}
        >
          {/* Product image */}
          <img
            src={slide.image}
            alt={slide.title}
            className="absolute inset-0 w-full h-full object-cover opacity-90 transition-transform duration-500 group-hover:scale-105"
            loading="eager"
          />

          {/* Gradient overlay for text readability */}
          <div className="absolute inset-0" style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.3) 0%, transparent 60%)' }} />

          {/* Tag badge */}
          <div className="absolute top-3 left-3 z-10">
            <span className="px-2 py-0.5 rounded-md text-[9px] font-bold tracking-wider text-white"
              style={{ background: slide.tagColor }}>
              {slide.tag}
            </span>
          </div>

          {/* Score badge */}
          <div className="absolute top-3 right-3 z-10 flex items-center gap-1 px-2 py-1 rounded-lg backdrop-blur-sm"
            style={{ background: 'rgba(255,255,255,0.85)' }}>
            <Star size={10} fill={slide.iconColor} color={slide.iconColor} />
            <span className="text-xs font-bold" style={{ color: slide.iconColor }}>{slide.score}</span>
          </div>
        </div>

        {/* Info area */}
        <div className="px-4 py-2.5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="text-[15px] font-semibold truncate" style={{ color: 'var(--text)' }}>
                {slide.title}
              </h3>
              <p className="text-xs mt-0.5 line-clamp-1" style={{ color: 'var(--text-secondary)' }}>
                {slide.subtitle}
              </p>
            </div>
            {slide.price && (
              <span className="text-sm font-bold flex-shrink-0" style={{ color: 'var(--text)' }}>
                {slide.price}
              </span>
            )}
          </div>

          {/* CTA row */}
          <div className="flex items-center justify-between mt-2.5">
            <span className="text-[10px] font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              {slide.scoreLabel}
            </span>
            <span className="flex items-center gap-1 text-xs font-semibold transition-colors group-hover:gap-2"
              style={{ color: 'var(--primary)' }}>
              Research <ArrowRight size={12} className="transition-transform group-hover:translate-x-0.5" />
            </span>
          </div>
        </div>
      </div>

      {/* Dot indicators */}
      <div className="flex justify-center gap-1.5 mt-3">
        {SLIDES.map((s, i) => (
          <button
            key={s.id}
            onClick={(e) => { e.stopPropagation(); goTo(i) }}
            className="transition-all duration-300 rounded-full"
            style={{
              width: i === current ? '20px' : '6px',
              height: '6px',
              background: i === current ? 'var(--primary)' : 'var(--border-strong, #D4D1CC)',
            }}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  )
}
