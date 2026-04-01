# Phase 18: AI Image Generation - Research

**Researched:** 2026-03-31
**Domain:** AI image generation (Gemini Imagen 3 / nano-banana MCP), WebP optimization, batch prompt engineering
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| IMG-01 | Generate 15+ bold & colorful product category hero images (headphones, laptops, kitchen, travel, fitness, etc.) using consistent style prompt | Canonical style prompt defined; target directories identified; naming convention established |
| IMG-02 | Generate 8+ mosaic tile images (diverse products at varied angles) for landing page hero collage | Mosaic-specific aspect ratio (3:4 portrait) and composition guidelines established; target path: `/public/images/products/mosaic-*.webp` |
| IMG-03 | All generated images pre-optimized (WebP, <200KB each) and stored in public/images/ | Sharp `quality:75, effort:6` confirmed achievable; Node.js script pattern documented; all existing PNGs confirmed oversize (400KB–1.1MB) |
</phase_requirements>

---

## Summary

Phase 18 is a production task, not an engineering task. The primary deliverable is a set of committed static files — not code. The tool for generation is `mcp__nanobanana__gemini_generate_image` (Gemini Imagen 3 / nano-banana MCP). The tool for optimization is a Node.js script using the `sharp` module (already installed in the frontend at `^0.33.5`). No new dependencies are required.

The single highest risk is visual inconsistency across the image batch. Every image in the batch must share a locked style prefix so that when the MosaicHero component (Phase 19) arranges them in a grid, they read as a designed editorial system rather than a collage of unrelated AI outputs. The solution is a canonical style spec — a reusable text block that prepends every single prompt — combined with generating all images in one session (conversation continuity).

All existing PNGs in `public/images/products/` and `public/images/topics/` are 400KB–1.1MB. They all need WebP conversion. The `<200KB` requirement is achievable at `quality: 75` with `effort: 6` using sharp — this typically yields 60–80% reduction on photographic AI output.

**Primary recommendation:** Generate all images in one MCP session using a locked canonical style prefix, save as PNG to `public/images/`, then run a single Node.js sharp script to batch-convert all new PNGs to WebP in-place.

---

## Current Image Inventory

### What Exists (and must be assessed)

| Directory | Files | Format | Size Range | Status |
|-----------|-------|--------|-----------|--------|
| `public/images/products/` | 14 PNGs | PNG | 409KB–1.1MB | Oversize — need WebP conversion |
| `public/images/topics/` | 16 PNGs | PNG | 527KB–1.0MB | Oversize — need WebP conversion |
| `public/images/browse/` | 10 JPGs | JPEG | 32KB–108KB | Already compliant; editorial style does not match |
| `public/images/categories/` | 0 files | — | — | Empty |

### What Already Exists in products/ (carousel uses these)

These 5 are referenced directly by `ProductCarousel.tsx` SLIDES array:
- `headphones.png`, `laptop.png`, `shoes.png`, `smart-home.png`, `tokyo.png`

These 8 are fallback images for chat/travel cards:
- `fallback-car.png`, `fallback-default.png`, `fallback-fitness.png`, `fallback-flight.png`
- `fallback-headphones.png`, `fallback-hotel.png`, `fallback-kitchen.png`, `fallback-laptop.png`

### What Needs to Be Generated (Phase 18)

**IMG-01: Category hero images** (target: `public/images/categories/`)
15 images for the BRW-01 category hero backgrounds (Phase 20 uses these):

| Slug | Subject |
|------|---------|
| `cat-headphones.webp` | Over-ear headphones, studio environment |
| `cat-laptops.webp` | Laptop on designer desk |
| `cat-kitchen.webp` | Premium kitchen appliances |
| `cat-travel.webp` | Travel destination, luggage, maps |
| `cat-fitness.webp` | Fitness equipment, weights, resistance bands |
| `cat-smartphones.webp` | Smartphone, floating apps |
| `cat-gaming.webp` | Gaming setup, controller, RGB |
| `cat-home-decor.webp` | Interior design, decorative objects |
| `cat-beauty.webp` | Beauty and skincare products |
| `cat-outdoor.webp` | Outdoor gear, hiking, nature |
| `cat-fashion.webp` | Editorial fashion accessories |
| `cat-smart-home.webp` | Smart devices, connected home |
| `cat-audio.webp` | Speakers, vinyl, audio equipment |
| `cat-cameras.webp` | Camera, lens, photography gear |
| `cat-furniture.webp` | Modern furniture, living space |

**IMG-02: Mosaic tile images** (target: `public/images/products/mosaic-*.webp`)
8 portrait images at varied angles and compositions for the Phase 19 collage:

| Slug | Subject |
|------|---------|
| `mosaic-headphones.webp` | Headphones, floating in space, bold blue |
| `mosaic-laptop.webp` | Laptop from above, bold green |
| `mosaic-sneakers.webp` | Running shoes, dynamic angle, bold red |
| `mosaic-espresso.webp` | Espresso machine + cup, bold terracotta |
| `mosaic-smartwatch.webp` | Smartwatch, wrist shot, bold purple |
| `mosaic-camera.webp` | Camera body and lens, editorial gold |
| `mosaic-fitness-gear.webp` | Dumbbells and bands, energetic |
| `mosaic-speaker.webp` | Bluetooth speaker, bold teal |

---

## Standard Stack

### Core (No new dependencies needed)

| Tool | Version | Purpose | Status |
|------|---------|---------|--------|
| `mcp__nanobanana__gemini_generate_image` | — | Generate images via Gemini Imagen 3 | Available in environment |
| `mcp__nanobanana__set_aspect_ratio` | — | Set aspect ratio before generation | Required before each session |
| `sharp` | `^0.33.5` | PNG to WebP batch conversion | Already in `frontend/package.json` |
| Node.js | 22.16.0 | Run optimization script | Available |

### MCP Tool Parameters

**`mcp__nanobanana__set_aspect_ratio`** — must be called before generating:
- Valid ratios: `1:1`, `9:16`, `16:9`, `3:4`, `4:3`, `3:2`, `2:3`, `5:4`, `4:5`, `21:9`
- Use `3:4` for mosaic portrait tiles (vertical composition)
- Use `4:3` for category hero images (landscape, matches hero layout)
- Use `16:9` for wide panoramic destinations (travel category)

**`mcp__nanobanana__gemini_generate_image`** — generation parameters:
```
prompt: string (required) — full canonical prompt including style prefix
output_path: string — absolute path to save PNG file
use_image_history: boolean — set true after first image to maintain session consistency
```

**Model:** Default is `gemini-3.1-flash-image-preview` (nano-banana 2, fast). The `pro` model (`gemini-3-pro-image-preview`) produces higher fidelity at slower speed — use for final quality pass on hero images if needed.

### WebP Optimization (Sharp)

**Installation:** Already in `frontend/node_modules/sharp` — use via Node.js script at project root.

**Parameters for <200KB:**
```javascript
sharp(inputPng)
  .resize(1200, null, { withoutEnlargement: true })  // cap width at 1200px
  .webp({ quality: 75, effort: 6 })
  .toFile(outputWebp)
```

- `quality: 75` — perceptually excellent, ~60-75% smaller than source PNG
- `effort: 6` — maximum compression (slowest, but one-time batch)
- `resize(1200)` — category heroes need no more than 1200px wide; mosaic tiles capped at 800px

**Size target verification:** Existing PNGs are 400KB–1.1MB. At quality 75, expected WebP output: 80KB–180KB. Files near 1MB (tokyo.png, hiking-boots.png) may need `quality: 65` to guarantee sub-200KB.

---

## Architecture Patterns

### Directory Structure After Phase 18

```
frontend/public/images/
├── products/               # Existing + new carousel/fallback images (all WebP)
│   ├── headphones.webp     # Converted from headphones.png
│   ├── laptop.webp
│   ├── shoes.webp
│   ├── smart-home.webp
│   ├── tokyo.webp
│   ├── fallback-*.webp     # 8 fallback images
│   ├── mosaic-headphones.webp   # NEW: IMG-02 mosaic tiles
│   ├── mosaic-laptop.webp
│   ├── mosaic-sneakers.webp
│   ├── mosaic-espresso.webp
│   ├── mosaic-smartwatch.webp
│   ├── mosaic-camera.webp
│   ├── mosaic-fitness-gear.webp
│   └── mosaic-speaker.webp
├── categories/             # NEW: IMG-01 category heroes
│   ├── cat-headphones.webp
│   ├── cat-laptops.webp
│   ├── cat-kitchen.webp
│   ├── cat-travel.webp
│   ├── cat-fitness.webp
│   ├── cat-smartphones.webp
│   ├── cat-gaming.webp
│   ├── cat-home-decor.webp
│   ├── cat-beauty.webp
│   ├── cat-outdoor.webp
│   ├── cat-fashion.webp
│   ├── cat-smart-home.webp
│   ├── cat-audio.webp
│   ├── cat-cameras.webp
│   └── cat-furniture.webp
├── topics/                 # Existing (converted to WebP)
│   └── *.webp
└── browse/                 # Keep as-is (already <200KB as JPEG)
```

### Pattern 1: Canonical Style Prefix (Style Spec)

Every prompt prepends this exact style spec block. It must never vary across the batch:

```
STYLE PREFIX (lock this across all generations):
"Editorial product photography, bold and vibrant colors, ivory/cream white background
(#FAFAF7), dramatic studio lighting with soft key light from camera-left at 45°,
shallow depth of field, sharp product focus, medium-format camera aesthetic,
high contrast with lifted shadows, no text overlays, no watermarks, no people,
no props except the product, clean negative space, commercial photography quality,
Monocle magazine editorial style"
```

Then append subject-specific detail:
```
"[STYLE_PREFIX], [SUBJECT DESCRIPTION], [COLOR ACCENT], [COMPOSITION DETAIL]"
```

Example full prompt for headphones category hero:
```
"Editorial product photography, bold and vibrant colors, ivory/cream white background
(#FAFAF7), dramatic studio lighting with soft key light from camera-left at 45°,
shallow depth of field, sharp product focus, medium-format camera aesthetic,
high contrast with lifted shadows, no text overlays, no watermarks, no people,
clean negative space, commercial photography quality, Monocle magazine editorial style,
premium over-ear noise-cancelling headphones floating at a 15-degree tilt, bold cobalt
blue color accent, minimalist composition with generous negative space below"
```

### Pattern 2: Per-Category Color Accents

Each category image should inject a distinct bold accent from the design token palette. This creates visual variety while maintaining style cohesion:

| Category | Accent Color | CSS Token Equivalent |
|----------|-------------|---------------------|
| Headphones, Audio | Cobalt blue `#1B4DFF` | `--primary` |
| Travel | Golden amber `#F59E0B` | `--accent-amber` |
| Kitchen, Food | Terracotta `#E85D3A` | `--accent-terracotta` |
| Fitness, Outdoor | Electric green `#10B981` | `--accent-green` |
| Gaming, Tech | Deep violet `#7C3AED` | `--accent-violet` |
| Beauty, Fashion | Dusty rose `#EC4899` | `--accent-rose` |
| Smart Home | Teal `#0D9488` | `--accent-teal` |
| Cameras | Warm gold `#D97706` | `--accent-gold` |

### Pattern 3: Mosaic Tile Composition Variants

Mosaic tiles need visual variety in composition to avoid a grid of identical angles. Rotate through these compositional modes:

1. **Floating** — Product levitating in space, slight shadow beneath
2. **Top-down** — Flat lay from directly above at 90°
3. **Three-quarter angle** — Classic 3/4 product shot, slight tilt
4. **Dramatic close-up** — Cropped tight on distinctive feature, shallow DOF
5. **Dynamic angle** — Rotated 15–30 degrees, energetic feel

Use each mode 1–2 times across the 8 mosaic tiles for maximum visual variation.

### Pattern 4: Batch Session Workflow

```
1. Call set_aspect_ratio("4:3") for category heroes
2. Generate first category image (headphones) — full prompt with style prefix
3. Generate remaining 14 category images using use_image_history: true
   — Only change the subject and accent color in each prompt
   — Keep the entire style prefix identical

4. Call set_aspect_ratio("3:4") for mosaic tiles
5. Generate first mosaic image — full prompt with style prefix
6. Generate remaining 7 mosaic tiles using use_image_history: true

7. Verify visual consistency — view all images side-by-side before committing

8. Run WebP optimization script on all new PNGs
9. Commit WebP files, delete intermediate PNGs
```

### Pattern 5: WebP Batch Conversion Script

```javascript
// scripts/optimize-images.mjs
import sharp from 'sharp'
import { readdir, unlink } from 'fs/promises'
import path from 'path'

const DIRS = [
  'frontend/public/images/products',
  'frontend/public/images/categories',
  'frontend/public/images/topics',
]

const MAX_WIDTH = { products: 800, categories: 1200, topics: 800 }

for (const dir of DIRS) {
  const folder = path.basename(dir)
  const maxW = MAX_WIDTH[folder] ?? 1000
  const files = await readdir(dir)
  const pngs = files.filter(f => f.endsWith('.png'))

  for (const file of pngs) {
    const inPath = path.join(dir, file)
    const outPath = path.join(dir, file.replace('.png', '.webp'))
    await sharp(inPath)
      .resize(maxW, null, { withoutEnlargement: true })
      .webp({ quality: 75, effort: 6 })
      .toFile(outPath)
    console.log(`${file} -> ${path.basename(outPath)}`)
    await unlink(inPath)  // remove source PNG after successful conversion
  }
}
```

Run from project root:
```bash
node scripts/optimize-images.mjs
```

**Note on existing component references:** `ProductCarousel.tsx` currently references `/images/products/headphones.png` etc. After converting PNGs to WebP, update the SLIDES array image paths to `.webp`. This is a 5-line change in `ProductCarousel.tsx` covered in Phase 20, but the WebP files must exist before that component update.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image optimization | Custom compression loop | `sharp` (already installed) | libvips handles gamma-correct resizing, color space conversion, optimal WebP encoding — hand-rolled solutions miss edge cases |
| Style consistency | "Try to remember" | Locked style prefix string in task | One variation in wording produces visually different outputs; drift is invisible until you see images side-by-side |
| Image generation API | Python openai client | `mcp__nanobanana__gemini_generate_image` | MCP tool saves directly to disk; no auth setup; no intermediate base64 decoding |

**Key insight:** The style prefix is the engineering artifact here, not code. Every minute spent writing the prefix precisely is worth 10 minutes of regenerating inconsistent images.

---

## Common Pitfalls

### Pitfall 1: Generating in Multiple Sessions Without Anchoring
**What goes wrong:** Images from session 1 have warm lighting; session 2 images have cooler tones. Side-by-side in the mosaic, this looks inconsistent and amateur.
**Why it happens:** Gemini doesn't preserve "memory" of previous images unless `use_image_history: true` is set and you stay in the same session.
**How to avoid:** Generate ALL images in one continuous session. Set `use_image_history: true` from image 2 onward. If you must resume, regenerate a few overlap images using the first batch as `reference_images`.
**Warning signs:** Images have subtly different background tones (some cream, some stark white, some off-white).

### Pitfall 2: Forgetting set_aspect_ratio Before Generation
**What goes wrong:** Images default to 1:1 square. Category hero images in a landscape slot look cropped or letter-boxed.
**Why it happens:** The MCP tool requires `set_aspect_ratio` to be called first; it doesn't error, it silently uses the last set ratio.
**How to avoid:** Call `set_aspect_ratio("4:3")` before the category hero batch, then `set_aspect_ratio("3:4")` before the mosaic batch. Document the current ratio at the top of each task.

### Pitfall 3: PNG Files Committed Without WebP Conversion
**What goes wrong:** 14 PNGs at 400KB–1.1MB each = 8–12MB added to the repo; every page load downloads them uncached.
**Why it happens:** Generation saves PNG; optimization is a separate step that gets skipped under time pressure.
**How to avoid:** The optimization script MUST run before the commit. The task sequence is: generate → verify visuals → optimize → commit. Never commit raw generated PNGs as final.

### Pitfall 4: Using the Wrong Output Directory
**What goes wrong:** Category images land in `products/` instead of `categories/`; Phase 20 code that looks for `/images/categories/cat-headphones.webp` finds nothing.
**Why it happens:** MCP tool's `output_path` parameter defaults to `~/Documents/nanobanana_generated/`. The exact absolute path must be specified.
**How to avoid:** Always specify `output_path` as an absolute path: `/c/Users/habib/downloads/reviewguide-sourcecode/frontend/public/images/categories/cat-headphones.png`. Create the target directory first.

### Pitfall 5: Mosaic Tiles All at Same Composition Angle
**What goes wrong:** All 8 mosaic tiles look visually identical in composition — same angle, same framing. The grid looks like a filmstrip, not a dynamic collage.
**Why it happens:** The style prefix alone controls lighting/color; composition must be varied explicitly per prompt.
**How to avoid:** Rotate through the 5 composition modes (floating, top-down, three-quarter, close-up, dynamic) explicitly in each mosaic tile's subject-specific portion of the prompt.

### Pitfall 6: Optimized WebP Still Over 200KB
**What goes wrong:** A few images (especially complex scenes like tokyo/travel) remain 200–300KB at quality 75.
**Why it happens:** Highly detailed photographic images compress less efficiently.
**How to avoid:** After optimization, run a size check. For files still over 200KB, re-run sharp with `quality: 60` or reduce `maxWidth` to 900px. The visual difference at this size is negligible for background use.

### Pitfall 7: Deleting PNGs Before Verifying WebP Quality
**What goes wrong:** WebP conversion ran with wrong parameters (e.g., quality 30 instead of 75); visuals are degraded; original PNGs are gone.
**Why it happens:** The optimization script deletes source PNGs after conversion.
**How to avoid:** Run the script with `dryRun: true` first (log paths without deleting). View several output WebPs before enabling the delete step. Keep originals in a temp location until committed files are verified.

---

## Code Examples

### Full Canonical Style Prefix (use verbatim)

```
Editorial product photography, bold and vibrant colors, ivory-white background (#FAFAF7),
dramatic studio lighting with soft key light from camera-left at 45° angle, gentle fill
light from right, sharp product focus with shallow depth of field, medium-format camera
aesthetic, high contrast with lifted shadows, subtle film grain, no text overlays,
no watermarks, no people, no UI elements, clean negative space, commercial photography
quality, Monocle and Wirecutter editorial style, hyperrealistic
```

### Category Hero Prompt Formula

```
[STYLE_PREFIX], [PRODUCT_TYPE] in [COLOR_ACCENT] color scheme, [COMPOSITION],
[UNIQUE_DETAIL], landscape orientation, wide negative space for text overlay
```

Example — cameras:
```
Editorial product photography, bold and vibrant colors, ivory-white background (#FAFAF7),
dramatic studio lighting with soft key light from camera-left at 45° angle, gentle fill
light from right, sharp product focus with shallow depth of field, medium-format camera
aesthetic, high contrast with lifted shadows, subtle film grain, no text overlays,
no watermarks, no people, clean negative space, commercial photography quality,
Monocle and Wirecutter editorial style, hyperrealistic,
professional DSLR camera body with telephoto lens in warm gold color scheme,
three-quarter angle view, lens cap removed showing glass elements,
wide negative space on left side for text overlay
```

### Mosaic Tile Prompt Formula

```
[STYLE_PREFIX], [PRODUCT_TYPE] in [COLOR_ACCENT] color scheme, [COMPOSITION_MODE],
portrait orientation, no background text, generous white space
```

Example — sneakers mosaic tile:
```
Editorial product photography, bold and vibrant colors, ivory-white background (#FAFAF7),
dramatic studio lighting with soft key light from camera-left at 45° angle, gentle fill
light from right, sharp product focus with shallow depth of field, medium-format camera
aesthetic, high contrast with lifted shadows, subtle film grain, no text overlays,
no watermarks, no people, clean negative space, commercial photography quality,
Monocle and Wirecutter editorial style, hyperrealistic,
premium running shoes in bold crimson red color scheme, dynamic angle tilted 20 degrees,
floating with subtle shadow beneath, portrait orientation, sole detail visible
```

### WebP Optimization Script (verified sharp API)

```javascript
// Source: sharp.pixelplumbing.com/api-output
import sharp from 'sharp'

await sharp('input.png')
  .resize(1200, null, { withoutEnlargement: true })
  .webp({ quality: 75, effort: 6 })
  .toFile('output.webp')
```

### Verify File Sizes After Optimization (Node.js)

```javascript
import { stat, readdir } from 'fs/promises'
import path from 'path'

const dir = 'frontend/public/images/categories'
const files = (await readdir(dir)).filter(f => f.endsWith('.webp'))
for (const f of files) {
  const { size } = await stat(path.join(dir, f))
  const kb = (size / 1024).toFixed(1)
  const flag = size > 200_000 ? ' OVER LIMIT' : ''
  console.log(`${kb}KB  ${f}${flag}`)
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| DALL-E 3 (`dall-e-3` model) | `gpt-image-1` / Gemini Imagen 3 | DALL-E 3 retired March 4, 2026 | Cannot use DALL-E 3 at all |
| Generate at runtime | Pre-generate + commit as static files | Best practice, always | Zero LLM latency on page load |
| PNG static assets | WebP static assets | Browser support normalized ~2021 | 60-80% smaller file sizes |
| Gemini 2.5 Flash Image | Gemini 3.1 Flash Image (nano-banana 2) | February 26, 2026 | 4K support, better text rendering |

**Deprecated/outdated:**
- DALL-E 3 (`dall-e-3`): Retired March 4, 2026 — do not use
- PNG as final delivery format: All new images must be WebP
- The `topics/` directory PNGs: All 400KB–1MB, need WebP conversion as part of this phase

---

## Open Questions

1. **Whether existing `topics/` PNGs need to remain as PNG (component references)**
   - What we know: No component currently references `topics/` by filename (grep found zero references to `topics/` in TSX files)
   - What's unclear: Are they referenced by dynamic slug-matching code that's not visible in static grep?
   - Recommendation: Check `browse/[category]/page.tsx` and CategoryHero data files before converting. If no references, convert to WebP; if dynamic slug references exist, keep PNGs as source and add WebP alongside.

2. **`browse/` JPEG files compatibility with new editorial style**
   - What we know: 10 JPEGs in `browse/` are already <200KB but use a different visual style (stock photography look)
   - What's unclear: Phase 20 (BRW-01) needs category hero background images — will it use `categories/` or `browse/`?
   - Recommendation: Generate the `categories/` images as specified; leave `browse/` untouched. Phase 20 planner decides which to use.

3. **nano-banana MCP output_path absolute path format on Windows**
   - What we know: The MCP tool accepts an `output_path` parameter
   - What's unclear: Whether it accepts Windows-style `C:\...` or Unix-style `/c/Users/...` paths
   - Recommendation: Use forward-slash Unix format `/c/Users/habib/downloads/reviewguide-sourcecode/frontend/public/images/...` — this is consistent with the shell environment (bash on Windows).

---

## Validation Architecture

`nyquist_validation` is enabled. Phase 18 is a file-production phase (no application code changes), so traditional unit tests do not apply. The validation is file-system based.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest (existing, `frontend/package.json`) |
| Config file | `frontend/vite.config.ts` (inferred) / `package.json` scripts |
| Quick run command | `cd frontend && npm run test:run -- tests/imageAssets.test.ts` |
| Full suite command | `cd frontend && npm run test:run` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| IMG-01 | 15+ WebP files exist in `public/images/categories/` | filesystem assertion | `cd frontend && npm run test:run -- tests/imageAssets.test.ts` | Wave 0 |
| IMG-02 | 8+ WebP files named `mosaic-*.webp` exist in `public/images/products/` | filesystem assertion | `cd frontend && npm run test:run -- tests/imageAssets.test.ts` | Wave 0 |
| IMG-03 | All WebP files in `public/images/categories/` and `products/mosaic-*` are under 200KB | filesystem assertion | `cd frontend && npm run test:run -- tests/imageAssets.test.ts` | Wave 0 |

### Wave 0 Gaps

- [ ] `frontend/tests/imageAssets.test.ts` — covers IMG-01, IMG-02, IMG-03

**Scaffold:**
```typescript
// frontend/tests/imageAssets.test.ts
import { describe, it, expect } from 'vitest'
import { readdirSync, statSync } from 'fs'
import path from 'path'

const ROOT = path.resolve(__dirname, '../public/images')

describe('IMG-01: Category hero images', () => {
  it('has 15 or more WebP files in categories/', () => {
    const files = readdirSync(path.join(ROOT, 'categories'))
      .filter(f => f.endsWith('.webp'))
    expect(files.length).toBeGreaterThanOrEqual(15)
  })
})

describe('IMG-02: Mosaic tile images', () => {
  it('has 8 or more mosaic-*.webp files in products/', () => {
    const files = readdirSync(path.join(ROOT, 'products'))
      .filter(f => f.startsWith('mosaic-') && f.endsWith('.webp'))
    expect(files.length).toBeGreaterThanOrEqual(8)
  })
})

describe('IMG-03: All WebP files under 200KB', () => {
  it('all files in categories/ are under 200KB', () => {
    const dir = path.join(ROOT, 'categories')
    const files = readdirSync(dir).filter(f => f.endsWith('.webp'))
    for (const f of files) {
      const { size } = statSync(path.join(dir, f))
      expect(size, `${f} is ${(size/1024).toFixed(1)}KB`).toBeLessThan(200_000)
    }
  })

  it('all mosaic tiles in products/ are under 200KB', () => {
    const dir = path.join(ROOT, 'products')
    const files = readdirSync(dir)
      .filter(f => f.startsWith('mosaic-') && f.endsWith('.webp'))
    for (const f of files) {
      const { size } = statSync(path.join(dir, f))
      expect(size, `${f} is ${(size/1024).toFixed(1)}KB`).toBeLessThan(200_000)
    }
  })
})
```

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `frontend/public/images/` directory listing with file sizes
- Direct codebase inspection: `frontend/components/discover/ProductCarousel.tsx` — confirmed image paths and loading attributes
- Direct codebase inspection: `frontend/package.json` — confirmed `sharp@^0.33.5` installed
- `mcp__nanobanana__gemini_generate_image` tool — available in environment (confirmed from prompt)
- Sharp official docs: [sharp.pixelplumbing.com/api-output](https://sharp.pixelplumbing.com/api-output/) — WebP quality/effort parameters verified

### Secondary (MEDIUM confidence)
- NanoBanana MCP GitHub: [github.com/YCSE/nanobanana-mcp](https://github.com/YCSE/nanobanana-mcp) — tool parameters, available models, output path behavior
- Google AI docs: [ai.google.dev/gemini-api/docs/image-generation](https://ai.google.dev/gemini-api/docs/image-generation) — Gemini Imagen 3 models, aspect ratio support
- Style Spec + Anchor Image Workflow: [rephrase-it.com](https://rephrase-it.com/blog/consistent-style-across-ai-image-generators-the-style-spec-a) — style consistency methodology

### Tertiary (LOW confidence)
- Product photography prompt keywords: [photoroom.com/blog/image-prompting](https://www.photoroom.com/blog/image-prompting) — "bold", "vibrant", "editorial" keyword effectiveness
- Batch generation workflow: [mindstudio.ai/blog/batch-ai-image-generation-hundreds-visuals-minutes](https://www.mindstudio.ai/blog/batch-ai-image-generation-hundreds-visuals-minutes) — base template pattern

---

## Metadata

**Confidence breakdown:**
- Standard stack (MCP tools, sharp): HIGH — tools confirmed available in environment, sharp version verified in package.json
- Generation workflow (session consistency): MEDIUM — use_image_history behavior inferred from docs; validate on first 2–3 images before full batch
- Style prompt structure: MEDIUM — prompt engineering methodology verified from multiple sources; actual visual output must be validated against 3-image test batch
- WebP optimization parameters: HIGH — sharp API verified from official docs; size estimates based on typical PNG-to-WebP compression ratios for photographic content
- File naming convention: HIGH — derived from existing project patterns and Phase 20 requirements

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (MCP tool availability stable; sharp API stable; Gemini models may update)
