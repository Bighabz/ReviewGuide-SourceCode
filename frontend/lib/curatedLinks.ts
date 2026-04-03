export interface CuratedProduct {
  asin: string
  url: string
  name?: string // Product display name for EditorsPicks cards
}

export interface CuratedTopic {
  title: string
  description: string
  products: CuratedProduct[]
}

export type CuratedCategory = Record<string, CuratedTopic[]>

export const curatedLinks: CuratedCategory = {
  electronics: [
    {
      title: 'Best Noise-Cancelling Headphones',
      description:
        'Block out the world and focus — our top picks for immersive sound and all-day comfort.',
      products: [
        { asin: 'B0C3HCD34R', url: 'https://amzn.to/4cg2c2g', name: 'Sony WH-1000XM5' },
        { asin: 'B0CQXMXJC5', url: 'https://amzn.to/46sYSNy', name: 'Bose QC Ultra' },
        { asin: 'B0C8PR4W22', url: 'https://amzn.to/40hVQbz', name: 'Apple AirPods Max' },
        { asin: 'B0G64H1QX7', url: 'https://amzn.to/4qWWrtW', name: 'Sony WH-1000XM4' },
        { asin: 'B0CCZ26B5V', url: 'https://amzn.to/4kZCHVl', name: 'Bose QC45' },
      ],
    },
    {
      title: 'Top Laptops for Students in 2026',
      description:
        'Reliable machines that handle lectures, code, and everything in between without breaking the bank.',
      products: [
        { asin: 'B0DV5R3Y6B', url: 'https://amzn.to/4tSpXE1', name: 'MacBook Air M3' },
        { asin: 'B0DY1ZSZGQ', url: 'https://amzn.to/3OtNdIf', name: 'Dell XPS 13' },
        { asin: 'B0GL1GHKNK', url: 'https://amzn.to/40srrqS', name: 'HP Spectre x360' },
        { asin: 'B0GGRBPMLD', url: 'https://amzn.to/3ZTVpE2', name: 'Lenovo IdeaPad 5i' },
        { asin: 'B0DZDC3WW5', url: 'https://amzn.to/4kUxiPj', name: 'ASUS Vivobook 15' },
      ],
    },
    {
      title: 'Best Budget Smartphones Under $400',
      description:
        'Flagship-level cameras and performance at a fraction of the price.',
      products: [
        { asin: 'B0DM1RCBHR', url: 'https://amzn.to/40wHa8k', name: 'Google Pixel 8a' },
        { asin: 'B0FRG6XMSP', url: 'https://amzn.to/4baYypf', name: 'Samsung A55' },
        { asin: 'B0FRYBKRZP', url: 'https://amzn.to/4s7D16v', name: 'Motorola Edge 50' },
        { asin: 'B0FTG3Z4YT', url: 'https://amzn.to/4ucdsmS', name: 'OnePlus Nord 4' },
        { asin: 'B09SM24S8C', url: 'https://amzn.to/4aAkUjS', name: 'iPhone SE 3rd Gen' },
      ],
    },
    {
      title: 'Best Bluetooth Speakers',
      description:
        'From pool parties to park sessions — portable speakers that punch well above their size.',
      products: [
        { asin: 'B0CH9K2ZLF', url: 'https://amzn.to/40tnceG', name: 'JBL Charge 5' },
        { asin: 'B08X4YMTPM', url: 'https://amzn.to/4cW8fcm', name: 'Bose SoundLink Flex' },
        { asin: 'B0FMK5C52K', url: 'https://amzn.to/3OE2Rkf', name: 'Sony SRS-XB33' },
        { asin: 'B094LS37Z4', url: 'https://amzn.to/4aUTEeI', name: 'Anker Soundcore 3' },
        { asin: 'B0DVSR7QM5', url: 'https://amzn.to/46ZowJS', name: 'UE Hyperboom' },
        { asin: 'B01MTB55WH', url: 'https://amzn.to/4sflr0x', name: 'JBL Xtreme 2' },
      ],
    },
  ],
  'home-appliances': [
    {
      title: 'Best Robot Vacuums for Pet Hair',
      description:
        'Hands-free cleaning that keeps up with shedding season — tested on real pet households.',
      products: [
        { asin: 'B0DHCJ571Z', url: 'https://amzn.to/4kZU08C', name: 'iRobot Roomba j9+' },
        { asin: 'B0DWG3C3ZF', url: 'https://amzn.to/3ZYKrNt', name: 'Roborock S8 Pro' },
        { asin: 'B0FP2XWWSP', url: 'https://amzn.to/4cK6Jdq', name: 'Shark Matrix Plus' },
        { asin: 'B0FXGKW7ZK', url: 'https://amzn.to/4sxhxAv', name: 'Eufy X10 Pro Omni' },
        { asin: 'B07R295MLS', url: 'https://amzn.to/46qmUst', name: 'Roomba 694' },
      ],
    },
    {
      title: 'Best Compact Washing Machines',
      description:
        'Space-saving washers perfect for apartments, dorms, and small laundry rooms.',
      products: [
        { asin: 'B0DC6C34XF', url: 'https://amzn.to/4u2A4Gq' },
        { asin: 'B0DGKYJCGR', url: 'https://amzn.to/4kXfNxK' },
        { asin: 'B08B4L4CGG', url: 'https://amzn.to/4qRmimV' },
        { asin: 'B0DFDRL7Q7', url: 'https://amzn.to/4siBCKJ' },
        { asin: 'B09YLKMHLH', url: 'https://amzn.to/4sel4Dv' },
      ],
    },
    {
      title: 'Dyson vs Shark: Which Vacuum Wins?',
      description:
        'We compared suction power, build quality, and value — here are the standouts from both brands.',
      products: [
        { asin: 'B09YS9N7H2', url: 'https://amzn.to/4r3yGk3' },
        { asin: 'B0CT97D9R2', url: 'https://amzn.to/4s43SQQ' },
        { asin: 'B0C2J7R8PY', url: 'https://amzn.to/4aC3lQt' },
        { asin: 'B0FB59FN5M', url: 'https://amzn.to/46te6SN' },
        { asin: 'B07S652B12', url: 'https://amzn.to/4kZFii3' },
      ],
    },
    {
      title: 'Best Espresso Machines Under $500',
      description:
        'Cafe-quality espresso at home without the barista price tag.',
      products: [
        { asin: 'B09X3WGJ3R', url: 'https://amzn.to/46NZBZZ' },
        { asin: 'B0D53126XJ', url: 'https://amzn.to/4bgoDlV' },
        { asin: 'B0GHRJDNWV', url: 'https://amzn.to/4kVjGTL' },
        { asin: 'B0DP1WXVK8', url: 'https://amzn.to/4rxiqbW' },
        { asin: 'B0FHKWCR2S', url: 'https://amzn.to/4b8KI6O' },
      ],
    },
  ],
  'health-wellness': [
    {
      title: 'Best Standing Desks for Back Pain',
      description:
        'Ergonomic sit-stand desks that actually relieve lower back strain — tested by remote workers.',
      products: [
        { asin: 'B09RMD7R15', url: 'https://amzn.to/4rHjBWv', name: 'Flexispot E7 Pro' },
        { asin: 'B0FSS4M57Z', url: 'https://amzn.to/3ZTY3ts', name: 'Uplift V2 Commercial' },
        { asin: 'B0FJX2TWP3', url: 'https://amzn.to/3MTqx3r', name: 'Fully Jarvis Bamboo' },
        { asin: 'B0FPC7XF5D', url: 'https://amzn.to/3ZYlH84', name: 'Flexispot E5 Plus' },
        { asin: 'B0DQTTC37M', url: 'https://amzn.to/3MIFHsr', name: 'SHW Electric Desk' },
      ],
    },
    {
      title: 'Best Supplements for Energy and Focus',
      description:
        'Science-backed picks to sharpen your focus and sustain energy without the crash.',
      products: [
        { asin: 'B09ZBC7DNT', url: 'https://amzn.to/4aSaSto', name: 'Alpha Brain' },
        { asin: 'B0FSNYKYQ1', url: 'https://amzn.to/4u2BIrA', name: 'Thesis Clarity' },
        { asin: 'B0DF6YL2RD', url: 'https://amzn.to/3ZTq1FL', name: 'Mind Lab Pro' },
        { asin: 'B00J547PAA', url: 'https://amzn.to/4cgr1el', name: "Doctor's Best CoQ10" },
        { asin: 'B0DCGQJ1DX', url: 'https://amzn.to/4kXo0lz', name: 'Nootropics Depot CDP' },
      ],
    },
    {
      title: 'Theragun vs Hypervolt: Which Massage Gun Is Better?',
      description:
        'Head-to-head comparison of the two biggest names in percussion therapy.',
      products: [
        { asin: 'B0CDHLKJ2H', url: 'https://amzn.to/4kZ7fX1', name: 'Theragun Pro' },
        { asin: 'B0CDMX8QBZ', url: 'https://amzn.to/4l2yxMq', name: 'Theragun Prime' },
        { asin: 'B09JB64T9Z', url: 'https://amzn.to/4tXXqNg', name: 'Hypervolt 2 Pro' },
        { asin: 'B0CNS894RH', url: 'https://amzn.to/4qWfnsA', name: 'Hypervolt Go 2' },
        { asin: 'B0FKCJNHWB', url: 'https://amzn.to/4l0t7kX', name: 'Achedaway Pro' },
      ],
    },
    {
      title: 'Best Fitness Trackers Under $100',
      description:
        'Accurate heart rate, sleep tracking, and step counts without the smartwatch price.',
      products: [
        { asin: 'B0G2BR4MJ7', url: 'https://amzn.to/3ZXGdpy', name: 'Fitbit Inspire 3' },
        { asin: 'B0G8FBXBWD', url: 'https://amzn.to/4aRMcBb', name: 'Garmin vivosmart 5' },
        { asin: 'B0F9PHLR2D', url: 'https://amzn.to/4scnhiz', name: 'Samsung Galaxy Fit3' },
        { asin: 'B0F9PHLR2D', url: 'https://amzn.to/4tWNnb3', name: 'Xiaomi Smart Band 8' },
        { asin: 'B0GMGTRSJR', url: 'https://amzn.to/46u0M0j', name: 'Amazfit Band 7' },
      ],
    },
    {
      title: 'Top-Rated Supplements for Weight Loss',
      description:
        'Popular weight management supplements with strong customer reviews and transparent ingredients.',
      products: [
        { asin: 'B08HHQWBBZ', url: 'https://amzn.to/4baXYIa' },
        { asin: 'B0CD8PV49D', url: 'https://amzn.to/46OSVuD' },
        { asin: 'B0F9YL3BWJ', url: 'https://amzn.to/3OM6Yuw' },
        { asin: 'B07GNZNNFN', url: 'https://amzn.to/4s88HZr' },
        { asin: 'B0897F2PG3', url: 'https://amzn.to/3OBZXg0' },
        { asin: 'B0BKDM7JRG', url: 'https://amzn.to/4cPmL5G' },
      ],
    },
    {
      title: 'Best Supplements for Menopause Support',
      description:
        'Targeted formulas for hot flashes, mood balance, and overall well-being during menopause.',
      products: [
        { asin: 'B008KPZMS2', url: 'https://amzn.to/4sdlxpu' },
        { asin: 'B0DPXTNW68', url: 'https://amzn.to/46P16aj' },
        { asin: 'B089V9WXYL', url: 'https://amzn.to/46uZPVx' },
        { asin: 'B07N813336', url: 'https://amzn.to/4qY1JVW' },
        { asin: 'B0BKDM7JRG', url: 'https://amzn.to/4cPmL5G' },
      ],
    },
  ],
  'outdoor-fitness': [
    {
      title: 'Best Hiking Boots for Beginners',
      description:
        'Trail-ready boots with solid ankle support and waterproofing — no break-in period needed.',
      products: [
        { asin: 'B0G8J8KB4Y', url: 'https://amzn.to/4aIxo7G', name: 'Merrell Moab Speed' },
        { asin: 'B0CC8X9T96', url: 'https://amzn.to/4aU6jP2', name: 'Salomon X Ultra 4' },
        { asin: 'B089Y3KJ76', url: 'https://amzn.to/3MvKUUr', name: 'Columbia Redmond III' },
        { asin: 'B0987X1QZK', url: 'https://amzn.to/3OAEGDf', name: 'Keen Targhee III' },
        { asin: 'B0987XXZ75', url: 'https://amzn.to/3P2NBNS', name: 'HOKA Anacapa Low' },
      ],
    },
    {
      title: 'Best Shoes for Flat Feet',
      description:
        'Arch support meets all-day comfort — footwear that keeps flat feet pain-free.',
      products: [
        { asin: 'B08QFSC1P6', url: 'https://amzn.to/3P4MahS', name: 'Brooks Adrenaline GTS' },
        { asin: 'B0CZ7MGXT6', url: 'https://amzn.to/3MvLcdZ', name: 'New Balance 1540v3' },
        { asin: 'B0CNWRQ6Y1', url: 'https://amzn.to/4si597f', name: 'ASICS Gel-Kayano 30' },
        { asin: 'B08H2GWTQP', url: 'https://amzn.to/47ebcRY', name: 'Saucony Guide 16' },
        { asin: 'B09H3P9MXL', url: 'https://amzn.to/3ZYOMQL', name: 'Vionic Walker Classic' },
      ],
    },
    {
      title: 'Garmin vs Apple Watch for Fitness',
      description:
        'Which wearable tracks your workouts better? We break down GPS accuracy, battery life, and features.',
      products: [
        { asin: 'B092RCLKHN', url: 'https://amzn.to/46rIc94', name: 'Garmin Forerunner 265' },
        { asin: 'B0GL9R2637', url: 'https://amzn.to/4tXZNQ5', name: 'Garmin Fenix 8' },
        { asin: 'B0BW288CHV', url: 'https://amzn.to/4rFsj7D', name: 'Apple Watch Ultra 2' },
        { asin: 'B0FQF5BZ8Z', url: 'https://amzn.to/4l6ws1R', name: 'Apple Watch Series 10' },
        { asin: 'B0FQFW7M9H', url: 'https://amzn.to/4tWPfAB', name: 'Garmin Venu 3' },
      ],
    },
    {
      title: 'Best Home Treadmills Under $1,000',
      description:
        'Foldable, quiet, and gym-quality — treadmills that fit your home and your budget.',
      products: [
        { asin: 'B0F64RQ7CT', url: 'https://amzn.to/4aC70hb', name: 'NordicTrack T 6.5 S' },
        { asin: 'B0G8DVSVF4', url: 'https://amzn.to/4siFxXX', name: 'LifeFitness T3' },
        { asin: 'B0CZ9B8JSB', url: 'https://amzn.to/46pe8uP', name: 'Schwinn 810 Treadmill' },
        { asin: 'B0CR6WB19J', url: 'https://amzn.to/46VPrGw', name: 'ProForm Carbon T7' },
        { asin: 'B0FP2N8GTL', url: 'https://amzn.to/4qX2ZJ2', name: 'Sunny SF-T7603' },
      ],
    },
  ],
  'fashion-style': [
    {
      title: 'Best White Sneakers for Everyday Wear',
      description:
        'Clean, versatile kicks that pair with everything from jeans to chinos.',
      products: [
        { asin: 'B0CH9G62F5', url: 'https://amzn.to/3ZXKuJu' },
        { asin: 'B092Z1X1HD', url: 'https://amzn.to/476uRmL' },
        { asin: 'B0D7QJFH38', url: 'https://amzn.to/4cguOZg' },
        { asin: 'B093QJPCPB', url: 'https://amzn.to/4rE2h4J' },
        { asin: 'B000OCQ134', url: 'https://amzn.to/4qX1Hh0' },
      ],
    },
    {
      title: "Best Affordable Jewelry That Won't Tarnish",
      description:
        'Gold-plated and stainless steel pieces that look expensive and last for years.',
      products: [
        { asin: 'B0D7HMQ1BS', url: 'https://amzn.to/3MKtN1c' },
        { asin: 'B0FCY8GX7N', url: 'https://amzn.to/4rHcIo2' },
        { asin: 'B09QMJRRR1', url: 'https://amzn.to/46vziY9' },
        { asin: 'B0G2BYQ2BB', url: 'https://amzn.to/4l6BoUr' },
        { asin: 'B0BRS255G2', url: 'https://amzn.to/4aXQ2Jb' },
      ],
    },
    {
      title: 'Best Streetwear Brands in 2026',
      description:
        'Fresh drops and cult favorites — streetwear pieces that stand out without trying too hard.',
      products: [
        { asin: 'B0BGNZQHLR', url: 'https://amzn.to/3OyKi0U' },
        { asin: 'B0CQR5P1SM', url: 'https://amzn.to/3ZYtGly' },
        { asin: 'B0CY53RSRC', url: 'https://amzn.to/40wRNYM' },
        { asin: 'B0CYC5HXZS', url: 'https://amzn.to/4shzrHk' },
        { asin: 'B0DSC6ZXFG', url: 'https://amzn.to/4sezXWl' },
      ],
    },
    {
      title: 'Best Watches Under $500',
      description:
        'Automatic and quartz timepieces that punch way above their price point.',
      products: [
        { asin: 'B0FFTSCYCZ', url: 'https://amzn.to/4aN66gE' },
        { asin: 'B07D1ZK5VG', url: 'https://amzn.to/3N5VIsv' },
        { asin: 'B000820YBU', url: 'https://amzn.to/4qX2XAK' },
        { asin: 'B00FZE1AZU', url: 'https://amzn.to/4aXQTJN' },
        { asin: 'B09C1WSQFJ', url: 'https://amzn.to/4qU4Tdh' },
      ],
    },
  ],
  'smart-home': [
    {
      title: 'Best Alexa-Compatible Smart Home Gadgets',
      description:
        'Voice-controlled lights, locks, plugs, and more — everything works seamlessly with Alexa.',
      products: [
        { asin: 'B089DR29T6', url: 'https://amzn.to/4l2GelM' },
        { asin: 'B07KRY43KN', url: 'https://amzn.to/4r3IWsz' },
        { asin: 'B0BCR7M9KX', url: 'https://amzn.to/3OPqRRr' },
        { asin: 'B0D14WP9TB', url: 'https://amzn.to/46Y9EeO' },
        { asin: 'B0CHJBJLHN', url: 'https://amzn.to/4sg5N5d' },
        { asin: 'B0FY6YZDVN', url: 'https://amzn.to/4qTKyov' },
        { asin: 'B0C1ZFNNKV', url: 'https://amzn.to/3P2VD9u' },
      ],
    },
  ],
  'kids-toys': [
    {
      title: 'Hottest Toys of 2026',
      description:
        'The most-wanted toys this year — from creative kits to action figures kids are obsessed with.',
      products: [
        { asin: 'B0BL6DCNGR', url: 'https://amzn.to/4u2gfis' },
        { asin: 'B0FD44PTYN', url: 'https://amzn.to/4qX4iHM' },
        { asin: 'B0DB5K3JF4', url: 'https://amzn.to/4rzKtHH' },
        { asin: 'B0C9Q492PF', url: 'https://amzn.to/3ZXSWZk' },
        { asin: 'B0DT44TSM2', url: 'https://amzn.to/4cgFw1Y' },
        { asin: 'B0D9NQXCS1', url: 'https://amzn.to/4r3JVcf' },
        { asin: 'B0D2JGYX3F', url: 'https://amzn.to/4sdnEd0' },
        { asin: 'B07TT6664Z', url: 'https://amzn.to/3MwI5CB' },
      ],
    },
  ],
  baby: [
    {
      title: 'Baby Essentials Every New Parent Needs',
      description:
        'The gear that makes the first year easier — from strollers to monitors to feeding supplies.',
      products: [
        { asin: 'B0DSMHJ2FF', url: 'https://amzn.to/40y4ZfW' },
        { asin: 'B0FTSJQPWT', url: 'https://amzn.to/46pFVLM' },
        { asin: 'B0CCTTHXVN', url: 'https://amzn.to/4kTSBjM' },
        { asin: 'B0DR55SVHB', url: 'https://amzn.to/4kU8p68' },
        { asin: 'B0CGRB23YM', url: 'https://amzn.to/4cOOKT6' },
        { asin: 'B08769M234', url: 'https://amzn.to/4l08rtk' },
        { asin: 'B08N4W4CFC', url: 'https://amzn.to/4qTLWHL' },
      ],
    },
  ],
  'big-tall': [
    {
      title: 'Best Big & Tall Clothing for Men',
      description:
        'Well-fitted basics and outerwear designed for bigger frames — no more settling for ill-fitting clothes.',
      products: [
        { asin: 'B0BFDR1MR7', url: 'https://amzn.to/4cbMKnN' },
        { asin: 'B075ZZ7YGD', url: 'https://amzn.to/3MwIkO1' },
        { asin: 'B07T9DC8GS', url: 'https://amzn.to/401kjl9' },
        { asin: 'B0FBX6SK94', url: 'https://amzn.to/4bcefMY' },
        { asin: 'B0FB11TX35', url: 'https://amzn.to/4seDT9z' },
        { asin: 'B0C5NW3JXC', url: 'https://amzn.to/4aEwmLq' },
      ],
    },
  ],
}
