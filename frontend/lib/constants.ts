/**
 * Frontend Constants
 * Centralized configuration for UI strings, trending searches, and defaults
 */

// Trending searches shown on the welcome screen (legacy - text pills)
export const TRENDING_SEARCHES = [
  'Best Gaming Laptop',
  'iPhone 17 Rumors',
  'Paris Travel Deals',
  'Vacuum for Dog Hair',
  'Best Running Shoes',
] as const

// Trending products with images for product card display
export const TRENDING_PRODUCTS = [
  {
    id: 'tp1',
    title: 'Sony WH-1000XM5 Headphones',
    price: 348,
    image: 'https://m.media-amazon.com/images/I/61+btxzpfDL._AC_SL1500_.jpg',
    rating: 4.8,
    reviewCount: 12400,
    category: 'Electronics',
    searchQuery: 'Sony WH-1000XM5 review'
  },
  {
    id: 'tp2',
    title: 'Ninja Air Fryer XL',
    price: 119,
    image: 'https://m.media-amazon.com/images/I/71aMCOJKqiL._AC_SL1500_.jpg',
    rating: 4.7,
    reviewCount: 8500,
    category: 'Kitchen',
    searchQuery: 'Best air fryer 2025'
  },
  {
    id: 'tp3',
    title: 'Nanit Pro Baby Monitor',
    price: 299,
    image: 'https://m.media-amazon.com/images/I/61vGqvbKReL._AC_SL1500_.jpg',
    rating: 4.6,
    reviewCount: 4200,
    category: 'Baby',
    searchQuery: 'Best baby monitor review'
  },
  {
    id: 'tp4',
    title: 'iRobot Roomba j7+',
    price: 599,
    image: 'https://m.media-amazon.com/images/I/61HnJXyFX-L._AC_SL1500_.jpg',
    rating: 4.5,
    reviewCount: 6800,
    category: 'Cleaning',
    searchQuery: 'Best robot vacuum review'
  },
  {
    id: 'tp5',
    title: 'KONG Classic Dog Toy',
    price: 15,
    image: 'https://m.media-amazon.com/images/I/71Rtf+mtHOL._AC_SL1500_.jpg',
    rating: 4.9,
    reviewCount: 52000,
    category: 'Pet',
    searchQuery: 'Best dog toys for chewers'
  },
  {
    id: 'tp6',
    title: 'Instant Pot Duo 7-in-1',
    price: 89,
    image: 'https://m.media-amazon.com/images/I/71V1LrY3MSL._AC_SL1500_.jpg',
    rating: 4.7,
    reviewCount: 145000,
    category: 'Kitchen',
    searchQuery: 'Instant Pot review'
  },
] as const

// Chat configuration
export const CHAT_CONFIG = {
  MAX_MESSAGE_LENGTH: 2000,
  SESSION_STORAGE_KEY: 'chat_session_id',
  ALL_SESSIONS_KEY: 'chat_all_session_ids',  // Track all sessions for this browser
  USER_ID_STORAGE_KEY: 'chat_user_id',
  MESSAGES_STORAGE_KEY: 'chat_messages',
} as const

// SSE retry configuration
export const SSE_CONFIG = {
  MAX_RETRIES: 3,
  INITIAL_BACKOFF_MS: 1000,
  MAX_BACKOFF_MS: 10000,
  REQUEST_TIMEOUT_MS: 120000,
} as const

// UI text constants
export const UI_TEXT = {
  WELCOME_TITLE: 'Where should we begin?',
  TRENDING_LABEL: 'Trending Now',
  PLACEHOLDER_TEXT: 'Ask anything',
  LOADING_HISTORY: 'Loading chat history...',
  RECONNECTING: 'Reconnecting',
  ERROR_MESSAGE: 'Something went wrong. If this issue persists please try again.',
} as const

// Footer links
export const FOOTER_LINKS = [
  { label: 'About', href: '#' },
  { label: 'Privacy', href: '#' },
  { label: 'Affiliate Disclosure', href: '#', desktopOnly: true },
  { label: 'Contact', href: '#' },
] as const

// Featured Deals Categories
export const DEAL_CATEGORIES = [
  { id: 'electronics', label: 'Electronics' },
  { id: 'home', label: 'Home & Kitchen' },
  { id: 'travel', label: 'Travel' },
  { id: 'health', label: 'Health' },
] as const

// Mock Data for Featured Deals
export const FEATURED_DEALS = {
  electronics: [
    {
      id: 'e1',
      title: 'Sony WH-1000XM5 Wireless Noise Canceling Headphones',
      image: 'https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?auto=format&fit=crop&w=500&q=80',
      rating: 4.8,
      review_count: 1240,
      price: 348.00,
      original_price: 399.99,
      description: 'Industry-leading noise cancellation, 30-hour battery life, and crystal clear hands-free calling.',
      affiliate_link: '#',
      merchant: 'Amazon'
    },
    {
      id: 'e2',
      title: 'Dell XPS 15 Laptop 2024',
      image: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca4?auto=format&fit=crop&w=500&q=80',
      rating: 4.9,
      review_count: 856,
      price: 1299.00,
      original_price: 1499.00,
      description: 'Stunning 15.6" OLED display, Intel Core Ultra 7, 32GB RAM, 1TB SSD.',
      affiliate_link: '#',
      merchant: 'Dell'
    },
    {
      id: 'e3',
      title: 'Samsung 55-Inch Class QLED 4K Smart TV',
      image: 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=500&q=80',
      rating: 4.6,
      review_count: 342,
      price: 697.99,
      original_price: 899.99,
      description: 'Quantum Processor Lite with 4K Upscaling, Object Tracking Sound Lite, and Dual LED.',
      affiliate_link: '#',
      merchant: 'Best Buy'
    },
    {
      id: 'e4',
      title: 'Anker Scosche Rhythm+ 2.0 Heart Rate Monitor',
      image: 'https://images.unsplash.com/photo-1557858310-9052820906f7?auto=format&fit=crop&w=500&q=80',
      rating: 4.5,
      review_count: 120,
      price: 79.99,
      original_price: 99.99,
      description: 'Armband heart rate monitor with dual-mode ANT+ and Bluetooth Smart connectivity.',
      affiliate_link: '#',
      merchant: 'Amazon'
    }
  ],
  home: [
    {
      id: 'h1',
      title: 'Ninja AF101 Air Fryer that Crisps, Roasts, Reheats',
      image: 'https://images.unsplash.com/photo-1626162987518-bf4ae8129759?auto=format&fit=crop&w=500&q=80',
      rating: 4.8,
      review_count: 3200,
      price: 89.95,
      original_price: 129.99,
      description: '4-quart capacity, high gloss finish, and dishwasher safe parts.',
      affiliate_link: '#',
      merchant: 'Amazon'
    },
    {
      id: 'h2',
      title: 'Dyson V15 Detect Cordless Vacuum Cleaner',
      image: 'https://images.unsplash.com/photo-1558317374-a3594743e46e?auto=format&fit=crop&w=500&q=80',
      rating: 4.7,
      review_count: 980,
      price: 649.99,
      original_price: 749.99,
      description: 'Most powerful, intelligent cordless vacuum. Laser reveals microscopic dust.',
      affiliate_link: '#',
      merchant: 'Dyson'
    },
    {
      id: 'h3',
      title: 'KitchenAid Artisan Series 5-Quart Stand Mixer',
      image: 'https://images.unsplash.com/photo-1594385208974-2e75f8d7bb48?auto=format&fit=crop&w=500&q=80',
      rating: 4.9,
      review_count: 5400,
      price: 379.99,
      original_price: 449.99,
      description: '10 speeds to thoroughly mix, knead and whip ingredients quickly and easily.',
      affiliate_link: '#',
      merchant: 'KitchenAid'
    },
    {
      id: 'h4',
      title: 'Nespresso VertuoPlus Coffee and Espresso Machine',
      image: 'https://images.unsplash.com/photo-1517080315802-140dd7c49eec?auto=format&fit=crop&w=500&q=80',
      rating: 4.6,
      review_count: 2100,
      price: 149.00,
      original_price: 199.00,
      description: 'Single-serve coffee maker with Centrifusion technology for gentle brewing.',
      affiliate_link: '#',
      merchant: 'Amazon'
    }
  ],
  travel: [
    {
      id: 't1',
      title: 'Samsonite Omni PC Hardside Expandable Luggage',
      image: 'https://images.unsplash.com/photo-1565026057447-bc076b97ce53?auto=format&fit=crop&w=500&q=80',
      rating: 4.5,
      review_count: 4500,
      price: 129.00,
      original_price: 189.99,
      description: 'Micro-diamond polycarbonate texture is extremely scratch-resistant.',
      affiliate_link: '#',
      merchant: 'Samsonite'
    },
    {
      id: 't2',
      title: 'Sony Alpha a7 IV Full-frame Mirrorless Camera',
      image: 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=500&q=80',
      rating: 4.9,
      review_count: 320,
      price: 2498.00,
      original_price: 2698.00,
      description: '33MP full-frame Exmor R CMOS sensor, 8x more powerful BIONZ XR processor.',
      affiliate_link: '#',
      merchant: 'B&H Photo'
    },
    {
      id: 't3',
      title: 'Bose QuietComfort 45 Bluetooth Wireless Headset',
      image: 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=500&q=80',
      rating: 4.7,
      review_count: 5600,
      price: 279.00,
      original_price: 329.00,
      description: 'Iconic quiet, comfort, and sound. High-fidelity audio with adjustable EQ.',
      affiliate_link: '#',
      merchant: 'Amazon'
    },
    {
      id: 't4',
      title: 'Kindle Paperwhite (16 GB) - Now with 6.8" Screen',
      image: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=500&q=80',
      rating: 4.8,
      review_count: 8900,
      price: 139.99,
      original_price: 149.99,
      description: 'Adjustable warm light, up to 10 weeks of battery life, and 20% faster page turns.',
      affiliate_link: '#',
      merchant: 'Amazon'
    }
  ],
  health: [
    {
      id: 'he1',
      title: 'Fitbit Charge 6 Fitness Tracker with Google apps',
      image: 'https://images.unsplash.com/photo-1576243345690-4e4b79b63288?auto=format&fit=crop&w=500&q=80',
      rating: 4.3,
      review_count: 560,
      price: 139.95,
      original_price: 159.95,
      description: 'Heart rate on equipment, turn-by-turn directions, and YouTube Music controls.',
      affiliate_link: '#',
      merchant: 'Amazon'
    },
    {
      id: 'he2',
      title: 'Theragun Prime - Percussive Therapy Massage Gun',
      image: 'https://images.unsplash.com/photo-1598424268688-2cb3a32f919d?auto=format&fit=crop&w=500&q=80',
      rating: 4.8,
      review_count: 1200,
      price: 249.00,
      original_price: 299.00,
      description: 'Quiet, powerful deep muscle treatment. 5 speeds and app complete control.',
      affiliate_link: '#',
      merchant: 'Therabody'
    },
    {
      id: 'he3',
      title: 'Philips Sonicare 4100 Power Toothbrush',
      image: 'https://images.unsplash.com/photo-1559676756-32d699ae8b1b?auto=format&fit=crop&w=500&q=80',
      rating: 4.6,
      review_count: 4500,
      price: 39.96,
      original_price: 49.96,
      description: 'Removes up to 7x more plaque than a manual toothbrush. Pressure sensor.',
      affiliate_link: '#',
      merchant: 'Amazon'
    },
    {
      id: 'he4',
      title: 'Withings Body+ - Digital Wi-Fi Smart Scale',
      image: 'https://images.unsplash.com/photo-1576403328828-d3f3f0cf3d9c?auto=format&fit=crop&w=500&q=80',
      rating: 4.5,
      review_count: 3400,
      price: 89.95,
      original_price: 99.95,
      description: 'Full body composition analysis: weight, body fat, water percentage, muscle & bone mass.',
      affiliate_link: '#',
      merchant: 'Withings'
    }
  ]
} as const
