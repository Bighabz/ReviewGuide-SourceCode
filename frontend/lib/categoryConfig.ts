export const MAX_RECENT_SEARCHES = 8

export interface BrowseCategory {
  slug: string
  name: string
  tagline: string
  image: string
  icon: string // lucide-react icon name
  queries: string[]
}

export const categories: BrowseCategory[] = [
  {
    slug: 'travel',
    name: 'Travel',
    tagline: 'Flights, hotels & destinations worth the trip',
    image: '/images/categories/cat-travel.webp',
    icon: 'Plane',
    queries: [
      'Top all-inclusive resorts in the Caribbean',
      'When to book flights to Japan for cheap',
      'Airbnb vs hotels for family vacations',
      'Great travel backpacks under $100',
    ],
  },
  {
    slug: 'electronics',
    name: 'Electronics',
    tagline: 'Researched, rated & ready to buy',
    image: '/images/categories/cat-laptops.webp',
    icon: 'Laptop',
    queries: [
      'Best noise-cancelling headphones',
      'Top laptops for students in 2026',
      'Best budget smartphones under $400',
      'Best Bluetooth speakers',
    ],
  },
  {
    slug: 'home-appliances',
    name: 'Home Appliances',
    tagline: 'The machines that make your home work',
    image: '/images/categories/cat-kitchen.webp',
    icon: 'Home',
    queries: [
      'Best robot vacuums for pet hair',
      'Best compact washing machines',
      'Dyson vs Shark: which vacuum wins?',
      'Best espresso machines under $500',
    ],
  },
  {
    slug: 'health-wellness',
    name: 'Health & Wellness',
    tagline: 'Gear and supplements backed by research',
    image: '/images/categories/cat-fitness.webp',
    icon: 'Heart',
    queries: [
      'Best standing desks for back pain',
      'Best supplements for energy and focus',
      'Theragun vs Hypervolt: which massage gun is better?',
      'Best fitness trackers under $100',
    ],
  },
  {
    slug: 'outdoor-fitness',
    name: 'Outdoor & Fitness',
    tagline: 'Built for the trail, the road & the gym',
    image: '/images/categories/cat-outdoor.webp',
    icon: 'Mountain',
    queries: [
      'Best hiking boots for beginners',
      'Best shoes for flat feet',
      'Garmin vs Apple Watch for fitness',
      'Best home treadmills under $1,000',
    ],
  },
  {
    slug: 'fashion-style',
    name: 'Fashion & Style',
    tagline: 'Sneakers, watches & wardrobe essentials reviewed',
    image: '/images/categories/cat-fashion.webp',
    icon: 'Shirt',
    queries: [
      'Best white sneakers for everyday wear',
      'Best affordable jewelry that won\'t tarnish',
      'Best streetwear brands in 2026',
      'Best watches under $500',
    ],
  },
  {
    slug: 'smart-home',
    name: 'Smart Home',
    tagline: 'Voice assistants, smart displays & connected living',
    image: '/images/categories/cat-smart-home.webp',
    icon: 'Speaker',
    queries: [
      'Best Alexa-compatible smart home gadgets',
      'Best smart plugs and switches',
      'Best smart doorbell cameras',
      'Best smart lighting systems',
    ],
  },
  {
    slug: 'kids-toys',
    name: 'Kids & Toys',
    tagline: 'Top-rated picks for every age and stage',
    image: '/images/categories/cat-gaming.webp',
    icon: 'Gamepad2',
    queries: [
      'Hottest toys of 2026',
      'Best educational toys for toddlers',
      'Best STEM toys for kids',
      'Best outdoor toys for summer',
    ],
  },
  {
    slug: 'baby',
    name: 'Baby',
    tagline: 'Essentials and gear for new parents',
    image: '/images/categories/cat-home-decor.webp',
    icon: 'Baby',
    queries: [
      'Baby essentials every new parent needs',
      'Best baby monitors',
      'Best strollers for city living',
      'Best baby car seats in 2026',
    ],
  },
  {
    slug: 'big-tall',
    name: 'Big & Tall',
    tagline: 'Clothing and gear that actually fits',
    image: '/images/categories/cat-fashion.webp',
    icon: 'PersonStanding',
    queries: [
      'Best big & tall clothing for men',
      'Best big & tall dress shirts',
      'Best jeans for big and tall guys',
      'Best activewear for larger builds',
    ],
  },
]
