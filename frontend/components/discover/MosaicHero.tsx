'use client'

const MOSAIC_TILES = [
  { src: '/images/products/mosaic-headphones.webp',  alt: 'Headphones',  rotate: '-7deg', x: '-22px', y: '8px',   z: 1, eager: true  },
  { src: '/images/products/mosaic-laptop.webp',      alt: 'Laptop',      rotate: '4deg',  x: '18px',  y: '-12px', z: 3, eager: false },
  { src: '/images/products/mosaic-sneakers.webp',    alt: 'Sneakers',    rotate: '-3deg', x: '60px',  y: '18px',  z: 2, eager: false },
  { src: '/images/products/mosaic-espresso.webp',    alt: 'Coffee',      rotate: '6deg',  x: '-60px', y: '-6px',  z: 2, eager: false },
  { src: '/images/products/mosaic-smartwatch.webp',  alt: 'Smartwatch',  rotate: '-5deg', x: '110px', y: '4px',   z: 1, eager: false },
  { src: '/images/products/mosaic-camera.webp',      alt: 'Camera',      rotate: '3deg',  x: '-110px', y: '14px', z: 2, eager: false },
  { src: '/images/products/mosaic-fitness-gear.webp',alt: 'Fitness',     rotate: '-4deg', x: '160px', y: '-8px',  z: 1, eager: false },
  { src: '/images/products/mosaic-speaker.webp',     alt: 'Speaker',     rotate: '5deg',  x: '-160px', y: '6px',  z: 2, eager: false },
]

export default function MosaicHero() {
  return (
    <div
      className="relative w-full"
      style={{ height: 'clamp(200px, 30vw, 320px)', overflow: 'visible' }}
      aria-hidden="true"
    >
      {MOSAIC_TILES.map((tile, index) => (
        <div
          key={tile.src}
          className={`absolute top-1/2 left-1/2 rounded-xl overflow-hidden shadow-md${index >= 4 ? ' hidden sm:block' : ''}`}
          style={{
            width: '140px',
            height: '140px',
            transform: `translate(calc(-50% + ${tile.x}), calc(-50% + ${tile.y})) rotate(${tile.rotate})`,
            zIndex: tile.z,
            willChange: 'transform',
          }}
        >
          <img
            src={tile.src}
            alt={tile.alt}
            width={140}
            height={140}
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
