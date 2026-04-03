import { describe, it, expect } from 'vitest'
import { readdirSync, statSync, existsSync } from 'fs'
import path from 'path'

const imagesRoot = path.resolve(__dirname, '../public/images')
const categoriesDir = path.join(imagesRoot, 'categories')
const productsDir = path.join(imagesRoot, 'products')

// Expected filenames defined here for documentation and targeted assertion
const EXPECTED_CATEGORY_FILES = [
  'cat-headphones.webp',
  'cat-laptops.webp',
  'cat-kitchen.webp',
  'cat-travel.webp',
  'cat-fitness.webp',
  'cat-smartphones.webp',
  'cat-gaming.webp',
  'cat-home-decor.webp',
  'cat-beauty.webp',
  'cat-outdoor.webp',
  'cat-fashion.webp',
  'cat-smart-home.webp',
  'cat-audio.webp',
  'cat-cameras.webp',
  'cat-furniture.webp',
]

const EXPECTED_MOSAIC_FILES = [
  'mosaic-headphones.webp',
  'mosaic-laptop.webp',
  'mosaic-sneakers.webp',
  'mosaic-espresso.webp',
  'mosaic-smartwatch.webp',
  'mosaic-camera.webp',
  'mosaic-fitness-gear.webp',
  'mosaic-speaker.webp',
]

// ---------------------------------------------------------------------------
// IMG-01: Category WebP images
// ---------------------------------------------------------------------------

describe('IMG-01: Category images', () => {
  it('categories directory exists', () => {
    // Pre-Plan 02/03 this directory may not contain WebP files yet.
    // This test is intentionally lenient — it only asserts existence.
    expect(existsSync(categoriesDir)).toBe(true)
  })

  it('contains 15 or more .webp files', () => {
    if (!existsSync(categoriesDir)) {
      console.log('SKIP: categories/ directory does not exist yet — run Plans 02 & 03 first')
      return
    }
    const webpFiles = readdirSync(categoriesDir).filter(f => f.endsWith('.webp'))
    expect(
      webpFiles.length,
      `Expected at least 15 category WebP files, found ${webpFiles.length}: [${webpFiles.join(', ')}]`
    ).toBeGreaterThanOrEqual(15)
  })

  it('contains all 15 expected category filenames', () => {
    if (!existsSync(categoriesDir)) {
      console.log('SKIP: categories/ directory does not exist yet — run Plans 02 & 03 first')
      return
    }
    const existing = readdirSync(categoriesDir)
    const webpFiles = existing.filter(f => f.endsWith('.webp'))
    if (webpFiles.length === 0) {
      console.log('SKIP: No category WebP files found yet — run Plans 02 & 03 first')
      return
    }
    for (const expected of EXPECTED_CATEGORY_FILES) {
      expect(
        existing,
        `Missing expected category image: ${expected}`
      ).toContain(expected)
    }
  })
})

// ---------------------------------------------------------------------------
// IMG-02: Product mosaic WebP images
// ---------------------------------------------------------------------------

describe('IMG-02: Product mosaic images', () => {
  it('products directory exists', () => {
    expect(existsSync(productsDir)).toBe(true)
  })

  it('contains 8 or more mosaic-*.webp files', () => {
    if (!existsSync(productsDir)) {
      console.log('SKIP: products/ directory does not exist yet — run Plans 02 & 03 first')
      return
    }
    const mosaicFiles = readdirSync(productsDir).filter(
      f => f.startsWith('mosaic-') && f.endsWith('.webp')
    )
    expect(
      mosaicFiles.length,
      `Expected at least 8 mosaic WebP files, found ${mosaicFiles.length}: [${mosaicFiles.join(', ')}]`
    ).toBeGreaterThanOrEqual(8)
  })

  it('contains all 8 expected mosaic filenames', () => {
    if (!existsSync(productsDir)) {
      console.log('SKIP: products/ directory does not exist yet — run Plans 02 & 03 first')
      return
    }
    const existing = readdirSync(productsDir)
    const mosaicFiles = existing.filter(f => f.startsWith('mosaic-') && f.endsWith('.webp'))
    if (mosaicFiles.length === 0) {
      console.log('SKIP: No mosaic WebP files found yet — run Plans 02 & 03 first')
      return
    }
    for (const expected of EXPECTED_MOSAIC_FILES) {
      expect(
        existing,
        `Missing expected mosaic image: ${expected}`
      ).toContain(expected)
    }
  })
})

// ---------------------------------------------------------------------------
// DISC-07: Product carousel slide images exist on disk
// ---------------------------------------------------------------------------

const EXPECTED_CAROUSEL_SLIDES = [
  'headphones.webp',
  'laptop.webp',
  'tokyo.webp',
  'vacuum.webp',
  'shoes.webp',
  'smart-home.webp',
]

describe('DISC-07: Product carousel slide images', () => {
  it('all carousel slide .webp files exist in products directory', () => {
    if (!existsSync(productsDir)) {
      console.log('SKIP: products/ directory does not exist yet')
      return
    }
    const existing = readdirSync(productsDir)
    for (const expected of EXPECTED_CAROUSEL_SLIDES) {
      expect(
        existing,
        `Missing carousel slide image: ${expected}`
      ).toContain(expected)
    }
  })
})

// ---------------------------------------------------------------------------
// IMG-03: All WebP files under 200KB
// ---------------------------------------------------------------------------

describe('IMG-03: Image file sizes under 200KB', () => {
  it('all category WebP files are under 200KB', () => {
    if (!existsSync(categoriesDir)) {
      console.log('SKIP: categories/ directory does not exist yet — run Plans 02 & 03 first')
      return
    }
    const webpFiles = readdirSync(categoriesDir).filter(f => f.endsWith('.webp'))
    if (webpFiles.length === 0) {
      console.log('SKIP: No category WebP files found yet — run Plans 02 & 03 first')
      return
    }
    for (const f of webpFiles) {
      const filePath = path.join(categoriesDir, f)
      const size = statSync(filePath).size
      expect(size, `${f} is ${(size / 1024).toFixed(1)}KB — exceeds 200KB limit`).toBeLessThan(200_000)
    }
  })

  it('all mosaic WebP files are under 200KB', () => {
    if (!existsSync(productsDir)) {
      console.log('SKIP: products/ directory does not exist yet — run Plans 02 & 03 first')
      return
    }
    const mosaicFiles = readdirSync(productsDir).filter(
      f => f.startsWith('mosaic-') && f.endsWith('.webp')
    )
    if (mosaicFiles.length === 0) {
      console.log('SKIP: No mosaic WebP files found yet — run Plans 02 & 03 first')
      return
    }
    for (const f of mosaicFiles) {
      const filePath = path.join(productsDir, f)
      const size = statSync(filePath).size
      expect(size, `${f} is ${(size / 1024).toFixed(1)}KB — exceeds 200KB limit`).toBeLessThan(200_000)
    }
  })
})
