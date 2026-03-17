export interface TrendingTopic {
  id: string
  title: string
  subtitle: string
  query: string
  icon: string      // Lucide icon name
  iconBg: string    // pastel background hex
  iconColor: string // icon stroke hex
}

export const trendingTopics: TrendingTopic[] = [
  {
    id: 'headphones-2026',
    title: 'Best Headphones 2026',
    subtitle: 'Noise-cancelling picks at every price',
    query: 'Best noise-cancelling headphones 2026',
    icon: 'Headphones',
    iconBg: '#EFF6FF',
    iconColor: '#3B82F6',
  },
  {
    id: 'tokyo-travel',
    title: 'Tokyo Travel Guide',
    subtitle: 'Flights, stays and hidden gems',
    query: 'Tokyo travel guide flights hotels hidden gems',
    icon: 'Plane',
    iconBg: '#FFF7ED',
    iconColor: '#F97316',
  },
  {
    id: 'laptops-students',
    title: 'Top Laptops for Students',
    subtitle: 'Performance meets portability',
    query: 'Best laptops for students 2026',
    icon: 'Laptop2',
    iconBg: '#F0FDF4',
    iconColor: '#22C55E',
  },
  {
    id: 'robot-vacuums',
    title: 'Best Robot Vacuums',
    subtitle: 'Hands-free cleaning, tested',
    query: 'Best robot vacuums for pet hair',
    icon: 'Bot',
    iconBg: '#FDF4FF',
    iconColor: '#A855F7',
  },
  {
    id: 'running-shoes',
    title: 'Running Shoes Ranked',
    subtitle: 'From trail to treadmill',
    query: 'Best running shoes trail treadmill 2026',
    icon: 'Footprints',
    iconBg: '#FEF2F2',
    iconColor: '#EF4444',
  },
  {
    id: 'smart-home-starter',
    title: 'Smart Home Starter Kit',
    subtitle: 'Automate your home under $200',
    query: 'Smart home starter kit under 200 dollars',
    icon: 'Speaker',
    iconBg: '#ECFDF5',
    iconColor: '#10B981',
  },
]
