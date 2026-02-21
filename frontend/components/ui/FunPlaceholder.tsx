'use client'

/**
 * FunPlaceholder — playful CSS animations shown while product images load or on error.
 * Each product gets a deterministic animation based on its ID so cards don't all match.
 * Pure CSS animations, no JS timers.
 */

interface FunPlaceholderProps {
  productId: string
  className?: string
}

// Simple deterministic hash from string → number
function hashId(id: string): number {
  let h = 0
  for (let i = 0; i < id.length; i++) {
    h = ((h << 5) - h + id.charCodeAt(i)) | 0
  }
  return Math.abs(h)
}

const ANIMATIONS = [
  // 0: Dancing cat
  {
    svg: (
      <svg viewBox="0 0 64 64" width="48" height="48" className="animate-bounce-gentle">
        <text x="14" y="48" fontSize="40">🐱</text>
      </svg>
    ),
    label: 'Finding purrfect products...',
  },
  // 1: Bike with spinning wheels
  {
    svg: (
      <svg viewBox="0 0 64 64" width="48" height="48" className="animate-ride">
        <text x="8" y="48" fontSize="40">🚲</text>
      </svg>
    ),
    label: 'Pedaling to fetch this one...',
  },
  // 2: Blender mixing
  {
    svg: (
      <svg viewBox="0 0 64 64" width="48" height="48" className="animate-shake">
        <text x="14" y="48" fontSize="40">🍹</text>
      </svg>
    ),
    label: 'Mixing up something good...',
  },
  // 3: Shopping bag with sparkles
  {
    svg: (
      <svg viewBox="0 0 64 64" width="48" height="48" className="animate-pulse-soft">
        <text x="8" y="48" fontSize="40">🛍️</text>
      </svg>
    ),
    label: 'Unwrapping this deal...',
  },
  // 4: Coffee cup steaming
  {
    svg: (
      <svg viewBox="0 0 64 64" width="48" height="48" className="animate-steam">
        <text x="14" y="48" fontSize="40">☕</text>
      </svg>
    ),
    label: 'Brewing up results...',
  },
  // 5: Rocket launching
  {
    svg: (
      <svg viewBox="0 0 64 64" width="48" height="48" className="animate-launch">
        <text x="14" y="48" fontSize="40">🚀</text>
      </svg>
    ),
    label: 'Launching image load...',
  },
]

export default function FunPlaceholder({ productId, className = '' }: FunPlaceholderProps) {
  const idx = hashId(productId) % ANIMATIONS.length
  const anim = ANIMATIONS[idx]

  return (
    <div className={`flex flex-col items-center justify-center gap-2 bg-[var(--surface)] ${className}`}>
      <style jsx global>{`
        @keyframes bounce-gentle {
          0%, 100% { transform: translateY(0) rotate(-3deg); }
          50% { transform: translateY(-8px) rotate(3deg); }
        }
        @keyframes ride {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(6px); }
        }
        @keyframes shake {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(-5deg); }
          75% { transform: rotate(5deg); }
        }
        @keyframes pulse-soft {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.08); opacity: 0.85; }
        }
        @keyframes steam {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        @keyframes launch {
          0% { transform: translateY(0); opacity: 1; }
          60% { transform: translateY(-10px); opacity: 0.9; }
          100% { transform: translateY(0); opacity: 1; }
        }
        .animate-bounce-gentle { animation: bounce-gentle 1.2s ease-in-out infinite; }
        .animate-ride { animation: ride 1s ease-in-out infinite; }
        .animate-shake { animation: shake 0.6s ease-in-out infinite; }
        .animate-pulse-soft { animation: pulse-soft 1.5s ease-in-out infinite; }
        .animate-steam { animation: steam 1.3s ease-in-out infinite; }
        .animate-launch { animation: launch 1.8s ease-in-out infinite; }
      `}</style>
      {anim.svg}
      <span className="text-xs text-[var(--text-muted)] font-medium">{anim.label}</span>
    </div>
  )
}
