/**
 * optimize-images.mjs
 *
 * Batch PNG-to-WebP conversion script using sharp.
 * Run from project root: node scripts/optimize-images.mjs
 *
 * Converts all PNG files in frontend/public/images/{categories,products,topics}
 * to WebP (quality 75, effort 6), resizes to max width per directory, and
 * deletes the source PNG. Any output still over 200KB is re-processed at
 * quality 60 with a warning.
 */

import { createRequire } from 'module'
import { readdirSync, statSync, existsSync, mkdirSync, unlinkSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const projectRoot = path.resolve(__dirname, '..')

// Load sharp from frontend's node_modules so script runs from project root
const require = createRequire(import.meta.url)
const sharp = require(path.join(projectRoot, 'frontend/node_modules/sharp'))

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const TARGET_DIRS = [
  {
    dir: path.join(projectRoot, 'frontend/public/images/products'),
    maxWidth: 800,
    label: 'products',
  },
  {
    dir: path.join(projectRoot, 'frontend/public/images/categories'),
    maxWidth: 1200,
    label: 'categories',
  },
  {
    dir: path.join(projectRoot, 'frontend/public/images/topics'),
    maxWidth: 800,
    label: 'topics',
  },
]

const MAX_FILE_SIZE = 200_000 // 200KB

// ---------------------------------------------------------------------------
// Conversion helpers
// ---------------------------------------------------------------------------

/**
 * Convert a single PNG to WebP with the given quality setting.
 * Returns the output file path.
 */
async function convertToWebP(inputPath, outputPath, maxWidth, quality = 75) {
  await sharp(inputPath)
    .resize(maxWidth, null, { withoutEnlargement: true })
    .webp({ quality, effort: 6 })
    .toFile(outputPath)
  return outputPath
}

/**
 * Process a single PNG file: convert → check size → re-encode if over limit.
 * Returns a summary object.
 */
async function processFile(inputPath, maxWidth) {
  const ext = path.extname(inputPath)
  if (ext.toLowerCase() !== '.png') return null

  const outputPath = inputPath.replace(/\.png$/i, '.webp')
  const inputSize = statSync(inputPath).size

  let quality = 75
  try {
    await convertToWebP(inputPath, outputPath, maxWidth, quality)
    let outputSize = statSync(outputPath).size

    if (outputSize >= MAX_FILE_SIZE) {
      console.warn(
        `  WARNING: ${path.basename(outputPath)} is ${(outputSize / 1024).toFixed(1)}KB after quality=${quality} — re-encoding at quality=60`
      )
      quality = 60
      await convertToWebP(inputPath, outputPath, maxWidth, quality)
      outputSize = statSync(outputPath).size
    }

    // Remove source PNG after successful conversion
    unlinkSync(inputPath)

    const pass = outputSize < MAX_FILE_SIZE
    return {
      file: path.basename(outputPath),
      inputKB: (inputSize / 1024).toFixed(1),
      outputKB: (outputSize / 1024).toFixed(1),
      quality,
      pass,
    }
  } catch (err) {
    console.error(`  ERROR processing ${path.basename(inputPath)}: ${err.message}`)
    return {
      file: path.basename(inputPath),
      inputKB: (inputSize / 1024).toFixed(1),
      outputKB: 'N/A',
      quality,
      pass: false,
      error: err.message,
    }
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  let totalConverted = 0
  let totalFailed = 0

  for (const { dir, maxWidth, label } of TARGET_DIRS) {
    console.log(`\n--- Processing: ${label} (maxWidth=${maxWidth}) ---`)

    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true })
      console.log(`  Created directory: ${dir}`)
    }

    const files = readdirSync(dir).filter(f => /\.png$/i.test(f))

    if (files.length === 0) {
      console.log('  No PNG files found — skipping.')
      continue
    }

    const results = []
    for (const file of files) {
      const inputPath = path.join(dir, file)
      console.log(`  Converting: ${file}`)
      const result = await processFile(inputPath, maxWidth)
      if (result) results.push(result)
    }

    // Print summary table for this directory
    console.log(`\n  Summary for ${label}:`)
    console.log('  ' + '-'.repeat(65))
    console.log(`  ${'File'.padEnd(35)} ${'In (KB)'.padStart(8)} ${'Out (KB)'.padStart(9)} ${'Status'.padStart(8)}`)
    console.log('  ' + '-'.repeat(65))
    for (const r of results) {
      const status = r.error ? 'ERROR' : r.pass ? 'PASS' : 'OVER LIMIT'
      console.log(
        `  ${r.file.padEnd(35)} ${String(r.inputKB).padStart(8)} ${String(r.outputKB).padStart(9)} ${status.padStart(8)}`
      )
      if (r.pass) totalConverted++
      else totalFailed++
    }
    console.log('  ' + '-'.repeat(65))
  }

  console.log(`\n=== Done: ${totalConverted} converted (under 200KB), ${totalFailed} failed/over-limit ===\n`)
  if (totalFailed > 0) {
    process.exit(1)
  }
}

main().catch(err => {
  console.error('Fatal error:', err)
  process.exit(1)
})
