#!/usr/bin/env node
/**
 * Generates 15 category hero images using Gemini Imagen 4.0 API
 * All images use the canonical editorial style prefix for consistency
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const GEMINI_API_KEY = 'AIzaSyDJzuCRMF7ix8_r_pcqLAFsEBDwNJeCzzQ';
const OUTPUT_DIR = path.join(__dirname, 'frontend/public/images/categories');

const STYLE_PREFIX = `Editorial product photography, bold and vibrant colors, ivory-white background (#FAFAF7), dramatic studio lighting with soft key light from camera-left at 45 degree angle, gentle fill light from right, sharp product focus with shallow depth of field, medium-format camera aesthetic, high contrast with lifted shadows, subtle film grain, no text overlays, no watermarks, no people, no UI elements, clean negative space, commercial photography quality, Monocle and Wirecutter editorial style, hyperrealistic`;

const IMAGES = [
  {
    filename: 'cat-headphones.png',
    subject: 'premium over-ear noise-cancelling headphones in cobalt blue (#1B4DFF) color scheme, three-quarter angle view tilted 15 degrees, bold dramatic presence, wide negative space on left for text overlay, landscape orientation'
  },
  {
    filename: 'cat-laptops.png',
    subject: 'sleek premium laptop open at 120 degrees on a minimal desk surface, cool cobalt blue (#1B4DFF) accent lighting, overhead three-quarter angle, landscape orientation, wide negative space on right for text overlay'
  },
  {
    filename: 'cat-kitchen.png',
    subject: 'premium kitchen stand mixer and espresso machine arrangement, warm terracotta (#E85D3A) color accent, three-quarter view, landscape orientation, wide negative space on left for text overlay'
  },
  {
    filename: 'cat-travel.png',
    subject: 'premium hardshell suitcase and leather passport holder, golden amber (#F59E0B) color accent, three-quarter angle, landscape orientation, wide negative space on right for text overlay'
  },
  {
    filename: 'cat-fitness.png',
    subject: 'premium adjustable dumbbells and resistance bands, electric green (#10B981) color accent, dynamic low angle view, landscape orientation, wide negative space on left for text overlay'
  },
  {
    filename: 'cat-smartphones.png',
    subject: 'flagship smartphone standing upright with colorful screen display, deep violet (#7C3AED) color accent reflecting on surface, three-quarter angle, landscape orientation, wide negative space on right for text overlay'
  },
  {
    filename: 'cat-gaming.png',
    subject: 'premium gaming controller and mechanical keyboard, deep violet (#7C3AED) accent with subtle RGB glow, three-quarter angle, landscape orientation, wide negative space on left for text overlay'
  },
  {
    filename: 'cat-home-decor.png',
    subject: 'sculptural ceramic vase and designer table lamp, teal (#0D9488) color accent, three-quarter view, landscape orientation, wide negative space on right for text overlay'
  },
  {
    filename: 'cat-beauty.png',
    subject: 'luxury skincare bottles and cosmetic containers in elegant arrangement, dusty rose (#EC4899) color accent, overhead flat lay angle, landscape orientation, wide negative space on left for text overlay'
  },
  {
    filename: 'cat-outdoor.png',
    subject: 'premium hiking backpack and trekking poles, electric green (#10B981) color accent, three-quarter angle, landscape orientation, wide negative space on right for text overlay'
  },
  {
    filename: 'cat-fashion.png',
    subject: 'designer sunglasses and premium leather belt on minimal surface, dusty rose (#EC4899) color accent, overhead three-quarter angle, landscape orientation, wide negative space on left for text overlay'
  },
  {
    filename: 'cat-smart-home.png',
    subject: 'smart speaker and connected home hub devices, teal (#0D9488) color accent with subtle glow, three-quarter angle, landscape orientation, wide negative space on right for text overlay'
  },
  {
    filename: 'cat-audio.png',
    subject: 'premium bookshelf speakers and vinyl turntable, cobalt blue (#1B4DFF) color accent, three-quarter angle, landscape orientation, wide negative space on left for text overlay'
  },
  {
    filename: 'cat-cameras.png',
    subject: 'professional DSLR camera body with telephoto lens, warm gold (#D97706) color accent, three-quarter angle showing glass lens elements, landscape orientation, wide negative space on right for text overlay'
  },
  {
    filename: 'cat-furniture.png',
    subject: 'designer lounge chair and modern side table, teal (#0D9488) color accent, three-quarter angle in minimal room setting, landscape orientation, wide negative space on left for text overlay'
  }
];

function generateImage(prompt) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      instances: [{ prompt }],
      parameters: {
        sampleCount: 1,
        aspectRatio: '4:3'
      }
    });

    const options = {
      hostname: 'generativelanguage.googleapis.com',
      path: `/v1beta/models/imagen-4.0-generate-001:predict?key=${GEMINI_API_KEY}`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    };

    let responseData = '';
    const req = https.request(options, (res) => {
      res.on('data', (chunk) => { responseData += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(responseData);
          if (parsed.error) {
            reject(new Error(`API Error ${parsed.error.code}: ${parsed.error.message}`));
          } else {
            const predictions = parsed.predictions || [];
            if (predictions.length > 0 && predictions[0].bytesBase64Encoded) {
              resolve(predictions[0].bytesBase64Encoded);
            } else {
              reject(new Error('No image data in response: ' + JSON.stringify(parsed).substring(0, 200)));
            }
          }
        } catch (e) {
          reject(new Error('Parse error: ' + responseData.substring(0, 200)));
        }
      });
    });

    req.on('error', (e) => reject(e));
    req.write(data);
    req.end();
  });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log(`Generating ${IMAGES.length} category hero images...`);
  console.log(`Output directory: ${OUTPUT_DIR}`);
  console.log('');

  // Ensure output directory exists
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  let successCount = 0;
  const errors = [];

  for (let i = 0; i < IMAGES.length; i++) {
    const { filename, subject } = IMAGES[i];
    const outputPath = path.join(OUTPUT_DIR, filename);

    // Skip if already exists
    if (fs.existsSync(outputPath)) {
      const stats = fs.statSync(outputPath);
      if (stats.size > 10000) {
        console.log(`[${i+1}/${IMAGES.length}] SKIP (exists) ${filename}`);
        successCount++;
        continue;
      }
    }

    const fullPrompt = `${STYLE_PREFIX}, ${subject}`;
    console.log(`[${i+1}/${IMAGES.length}] Generating ${filename}...`);

    try {
      const imageBase64 = await generateImage(fullPrompt);
      const imageBuffer = Buffer.from(imageBase64, 'base64');
      fs.writeFileSync(outputPath, imageBuffer);
      const sizeKB = Math.round(imageBuffer.length / 1024);
      console.log(`  -> Saved ${filename} (${sizeKB} KB)`);
      successCount++;
    } catch (err) {
      console.error(`  -> ERROR generating ${filename}: ${err.message}`);
      errors.push({ filename, error: err.message });
    }

    // Small delay between requests to avoid rate limiting
    if (i < IMAGES.length - 1) {
      await sleep(500);
    }
  }

  console.log('');
  console.log(`=== DONE: ${successCount}/${IMAGES.length} images generated ===`);
  if (errors.length > 0) {
    console.log('Errors:');
    errors.forEach(e => console.log(`  - ${e.filename}: ${e.error}`));
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
