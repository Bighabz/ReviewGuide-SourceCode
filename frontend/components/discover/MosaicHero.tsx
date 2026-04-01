'use client'

// Tiles arranged in symmetric pairs fanning out from center.
// Inner pairs are larger (closer feel), outer pairs smaller (depth).
// Center is deliberately empty — that's where the headline text sits.
const MOSAIC_TILES = [
  // Inner pair — flanking the headline, larger
  { src: '/images/products/mosaic-headphones.webp',  alt: 'Headphones',  rotate: '-8deg',  x: '-200px', y: '15px',   z: 4, size: 200, eager: true  },
  { src: '/images/products/mosaic-laptop.webp',      alt: 'Laptop',      rotate: '6deg',   x: '200px',  y: '-10px',  z: 4, size: 200, eager: false },
  // Middle pair
  { src: '/images/products/mosaic-sneakers.webp',    alt: 'Sneakers',    rotate: '-4deg',  x: '340px',  y: '30px',   z: 3, size: 180, eager: false },
  { src: '/images/products/mosaic-espresso.webp',    alt: 'Coffee',      rotate: '7deg',   x: '-340px', y: '-15px',  z: 3, size: 180, eager: false },
  // Outer pair — smaller, receding
  { src: '/images/products/mosaic-smartwatch.webp',  alt: 'Smartwatch',  rotate: '-6deg',  x: '470px',  y: '5px',    z: 2, size: 160, eager: false },
  { src: '/images/products/mosaic-camera.webp',      alt: 'Camera',      rotate: '4deg',   x: '-470px', y: '20px',   z: 2, size: 160, eager: false },
  // Far outer pair — smallest, peeking at edges
  { src: '/images/products/mosaic-fitness-gear.webp',alt: 'Fitness',     rotate: '-5deg',  x: '590px',  y: '-10px',  z: 1, size: 140, eager: false },
  { src: '/images/products/mosaic-speaker.webp',     alt: 'Speaker',     rotate: '6deg',   x: '-590px', y: '12px',   z: 1, size: 140, eager: false },
]

export default function MosaicHero() {
  return (
    <div
      className="relative w-full"
      style={{ height: 'clamp(200px, 28vw, 280px)', overflow: 'visible' }}
      aria-hidden="true"
    >
      {MOSAIC_TILES.map((tile, index) => (
        <div
          key={tile.src}
          className={`absolute top-1/2 left-1/2 rounded-2xl overflow-hidden shadow-lg${index >= 4 ? ' hidden sm:block' : ''}`}
          style={{
            width: `${tile.size}px`,
            height: `${tile.size}px`,
            transform: `translate(calc(-50% + ${tile.x}), calc(-50% + ${tile.y})) rotate(${tile.rotate})`,
            zIndex: tile.z,
            willChange: 'transform',
            border: '1px solid rgba(255,255,255,0.15)',
          }}
        >
          <img
            src={tile.src}
            alt={tile.alt}
            width={tile.size}
            height={tile.size}
            loading={tile.eager ? 'eager' : 'lazy'}
            fetchPriority={tile.eager ? 'high' : 'auto'}
            className="w-full h-full object-cover"
            style={{ display: 'block' }}
          />
        </div>
      ))}
    </div>
  )
}
