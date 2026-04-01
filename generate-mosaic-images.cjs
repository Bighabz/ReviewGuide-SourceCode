#!/usr/bin/env node
/**
 * Generates 8 mosaic tile images using Gemini Imagen 4.0 API
 * Portrait 3:4 orientation for mosaic collage grid usage
 * All images use the canonical editorial style prefix for consistency
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const GEMINI_API_KEY = 'AIzaSyDJzuCRMF7ix8_r_pcqLAFsEBDwNJeCzzQ';
const OUTPUT_DIR = path.join(__dirname, 'frontend/public/images/products');

const STYLE_PREFIX = `Editorial product photography, bold and vibrant colors, ivory-white background (#FAFAF7), dramatic studio lighting with soft key light from camera-left at 45 degree angle, gentle fill light from right, sharp product focus with shallow depth of field, medium-format camera aesthetic, high contrast with lifted shadows, subtle film grain, no text overlays, no watermarks, no people, no UI elements, clean negative space, commercial photography quality, Monocle and Wirecutter editorial style, hyperrealistic`;

const IMAGES = [
  {
    filename: 'mosaic-headphones.png',
    subject: 'premium over-ear headphones levitating in space with subtle shadow beneath, bold cobalt blue (#1B4DFF) color accent, floating weightlessly, portrait orientation, generous white space around product'
  },
  {
    filename: 'mosaic-laptop.png',
    subject: 'premium laptop viewed from directly above at 90 degrees, screen showing colorful gradient, bold electric green (#10B981) color accent, flat lay composition, portrait orientation, generous white space'
  },
  {
    filename: 'mosaic-sneakers.png',
    subject: 'premium running shoes tilted at 25 degree dynamic angle showing sole detail, bold crimson red (#DC2626) color accent, energetic and dynamic feel, portrait orientation, generous white space'
  },
  {
    filename: 'mosaic-espresso.png',
    subject: 'premium espresso machine with a filled espresso cup in foreground, warm terracotta (#E85D3A) color accent, classic three-quarter product shot with slight tilt, portrait orientation, generous white space'
  },
  {
    filename: 'mosaic-smartwatch.png',
    subject: 'premium smartwatch face cropped tight showing display detail and crown button, deep violet (#7C3AED) color accent, dramatic close-up with extremely shallow depth of field, portrait orientation, generous white space'
  },
  {
    filename: 'mosaic-camera.png',
    subject: 'professional camera body with prime lens floating with subtle shadow beneath, warm gold (#D97706) color accent, levitating at slight angle showing lens glass elements, portrait orientation, generous white space'
  },
  {
    filename: 'mosaic-fitness-gear.png',
    subject: 'premium dumbbells and resistance bands arranged as overhead flat lay from 90 degrees, electric green (#10B981) color accent, energetic arrangement, portrait orientation, generous white space'
  },
  {
    filename: 'mosaic-speaker.png',
    subject: 'premium cylindrical bluetooth speaker with fabric mesh texture visible, bold teal (#0D9488) color accent, classic three-quarter product angle, portrait orientation, generous white space'
  }
];

function generateImage(prompt) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      instances: [{ prompt }],
      parameters: {
        aspectRatio: '3:4',
        sampleCount: 1
      }
    });

    const options = {
      hostname: 'generativelanguage.googleapis.com',
      path: `/v1beta/models/imagen-4.0-generate-001:predict?key=${GEMINI_API_KEY}`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      }
    };

    const req = https.request(options, (res) => {
      let responseData = '';
      res.on('data', (chunk) => { responseData += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(responseData);
          if (parsed.error) {
            reject(new Error('API error: ' + JSON.stringify(parsed.error)));
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
    req.write(body);
    req.end();
  });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log(`Generating ${IMAGES.length} mosaic tile images (3:4 portrait)...`);
  console.log(`Output directory: ${OUTPUT_DIR}`);
  console.log('');

  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  let successCount = 0;
  const errors = [];

  for (let i = 0; i < IMAGES.length; i++) {
    const { filename, subject } = IMAGES[i];
    const outputPath = path.join(OUTPUT_DIR, filename);

    // Skip if already exists and valid
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
      await sleep(600);
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
