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
    image: '/images/browse/travel.jpg',
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
    image: '/images/browse/electronics.jpg',
    icon: 'Laptop',
    queries: [
      'Most popular noise cancelling headphones',
      'Top-rated laptops for students 2026',
      'Samsung vs iPhone comparison',
      'Solid budget smartphones under $400',
    ],
  },
  {
    slug: 'home-appliances',
    name: 'Home Appliances',
    tagline: 'The machines that make your home work',
    image: '/images/browse/home-appliances.jpg',
    icon: 'Home',
    queries: [
      'Top robot vacuums for pet hair',
      'Highly rated washing machines for large families',
      'Dyson vs Shark cordless vacuums',
      'Great espresso machines under $500',
    ],
  },
  {
    slug: 'health-wellness',
    name: 'Health & Wellness',
    tagline: 'Gear and supplements backed by research',
    image: '/images/browse/health-wellness.jpg',
    icon: 'Heart',
    queries: [
      'Top-rated standing desks for back pain',
      'Most effective supplements for energy and focus',
      'Theragun vs Hypervolt massage gun',
      'Affordable fitness trackers under $100',
    ],
  },
  {
    slug: 'outdoor-fitness',
    name: 'Outdoor & Fitness',
    tagline: 'Built for the trail, the road & the gym',
    image: '/images/browse/outdoor-fitness.jpg',
    icon: 'Mountain',
    queries: [
      'Top hiking boots for beginners',
      'Highly rated running shoes for flat feet',
      'Garmin vs Apple Watch for fitness',
      'Great home treadmills under $1000',
    ],
  },
  {
    slug: 'fashion-style',
    name: 'Fashion & Style',
    tagline: 'Sneakers, watches & wardrobe essentials reviewed',
    image: '/images/browse/fashion-style.jpg',
    icon: 'Shirt',
    queries: [
      'Best white sneakers for everyday wear',
      'Affordable gold jewelry that won\'t tarnish',
      'Best streetwear brands in 2026',
      'Top-rated watches under $500',
    ],
  },
]
