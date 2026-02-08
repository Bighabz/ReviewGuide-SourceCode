
export interface ProductItem {
    id: string;
    title: string;
    description: string;
    image: string;
    images: string[];
    price: number;
    originalPrice?: number;
    currency: string;
    rating: number;
    reviewCount: number;

    // Review Intelligence
    sourceCount: number;
    topSources: string[];
    sentiment: {
        positive: number;
        neutral: number;
        negative: number;
    };

    // Insights
    topPros: Array<{ title: string; count: number }>;
    topCons: Array<{ title: string; count: number }>;
    quotes: Array<{ text: string; author: string; source: string }>;

    // Metadata
    category: string;
    subcategory: string;
    tags: string[];
    bestFor: string;
    affiliateLink: string;
    merchant: string;
}

export interface CategoryData {
    id: string;
    title: string;
    description: string;
    heroGradient: string;
    stats: {
        totalReviews: number;
        totalSources: number;
        totalProducts: number;
    };
    rows: Array<{
        id: string;
        title: string;
        subtitle: string;
        items: ProductItem[];
    }>;
}

// Helpers to generate random data for prototyping
const SCORES = [4.5, 4.6, 4.7, 4.8, 4.9, 5.0];
const SOURCES = ['Reddit', 'Amazon', 'YouTube', 'Twitter', 'Forums', 'TechRadar'];

// Category-specific pros and cons
const CATEGORY_INSIGHTS: Record<string, { pros: string[], cons: string[] }> = {
    'Flights': {
        pros: ['Best price found', 'Direct flight available', 'Good departure times', 'Flexible cancellation'],
        cons: ['Limited baggage', 'No meal included', 'Long layover option']
    },
    'Hotels': {
        pros: ['Great location', 'Excellent amenities', 'Friendly staff', 'Clean rooms'],
        cons: ['Pricey parking', 'Busy during peak', 'Limited breakfast options']
    },
    'Destinations': {
        pros: ['Stunning views', 'Rich culture', 'Great food scene', 'Safe for tourists'],
        cons: ['Crowded in summer', 'Can be expensive', 'Language barrier']
    },
    'Games': {
        pros: ['Engaging storyline', 'Great graphics', 'High replay value', 'Active community'],
        cons: ['Steep learning curve', 'Requires beefy PC', 'Some bugs at launch']
    },
    'PCs': {
        pros: ['Powerful performance', 'Quiet cooling', 'Easy upgrades', 'Great build quality'],
        cons: ['Premium price', 'Bulky design', 'Loud under load']
    },
    'Smartphones': {
        pros: ['Amazing camera', 'All-day battery', 'Fast performance', 'Great display'],
        cons: ['Expensive', 'No headphone jack', 'Slow charging']
    },
    'Headphones': {
        pros: ['Great sound quality', 'Excellent noise canceling', 'Comfortable fit', 'Long battery life'],
        cons: ['Premium price', 'Bulky for travel', 'Touch controls finicky']
    },
    'Kitchen': {
        pros: ['Easy to use', 'Quick cooking', 'Easy cleanup', 'Versatile'],
        cons: ['Takes counter space', 'Learning curve', 'Loud operation']
    },
    'Sneakers': {
        pros: ['Super comfortable', 'Great style', 'Durable build', 'Good support'],
        cons: ['Runs small', 'Limited colors', 'Premium price']
    },
    'Equipment': {
        pros: ['Solid build', 'Smooth operation', 'Great for home use', 'Quiet'],
        cons: ['Expensive', 'Heavy', 'Requires space']
    },
    'Skincare': {
        pros: ['Visible results', 'Gentle formula', 'Dermatologist approved', 'Pleasant texture'],
        cons: ['Expensive', 'Takes time to work', 'Not for sensitive skin']
    },
    'Tools': {
        pros: ['Professional results', 'Fast drying', 'Multiple settings', 'Lightweight'],
        cons: ['Premium price', 'Loud', 'Gets hot']
    }
};

const DEFAULT_INSIGHTS = {
    pros: ['Great value', 'High quality', 'Well reviewed'],
    cons: ['Premium price', 'Limited availability']
};

// Deterministic hash function to generate consistent values from ID
const hashCode = (str: string): number => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash);
};

const getSeededValue = (id: string, min: number, max: number, seed: number = 0): number => {
    const hash = hashCode(id + seed.toString());
    return min + (hash % (max - min + 1));
};

const getSeededFromArray = <T>(arr: T[], id: string, seed: number = 0): T => {
    const hash = hashCode(id + seed.toString());
    return arr[hash % arr.length];
};

const getRandomSubset = (arr: any[], count: number) => arr.slice(0, count);

const createMockProduct = (id: string, title: string, price: number, category: string, sub: string, image: string): ProductItem => {
    const insights = CATEGORY_INSIGHTS[sub] || DEFAULT_INSIGHTS;
    return {
        id,
        title,
        description: `Experience the best in ${sub} with the ${title}. Analyzed from thousands of user reviews.`,
        image,
        images: [image, image, image],
        price,
        originalPrice: price * 1.2,
        currency: '$',
        rating: getSeededFromArray(SCORES, id, 1),
        reviewCount: getSeededValue(id, 500, 5500, 2),
        sourceCount: getSeededValue(id, 10, 50, 3),
        topSources: getRandomSubset(SOURCES, 3),
        sentiment: {
            positive: getSeededValue(id, 70, 95, 4),
            neutral: getSeededValue(id, 5, 15, 5),
            negative: getSeededValue(id, 0, 5, 6),
        },
        topPros: insights.pros.slice(0, 3).map((p, i) => ({ title: p, count: getSeededValue(id, 100, 500, 10 + i) })),
        topCons: insights.cons.slice(0, 2).map((c, i) => ({ title: c, count: getSeededValue(id, 20, 100, 20 + i) })),
        quotes: [
            { text: "Best purchase I've made all year, honestly.", author: "u/tech_guru", source: "Reddit" },
            { text: "Features are unmatched at this price point.", author: "ReviewerXYZ", source: "Amazon" }
        ],
        category,
        subcategory: sub,
        tags: ['Best Seller', 'Top Rated'],
        bestFor: sub,
        affiliateLink: '#',
        merchant: 'Amazon'
    };
};

// --- TRAVEL DATA ---
const flightDeals = [
    createMockProduct('f1', 'NYC to Tokyo Roundtrip', 850, 'Travel', 'Flights', 'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=600&h=400&fit=crop'),
    createMockProduct('f2', 'LAX to London Direct', 620, 'Travel', 'Flights', 'https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=600&h=400&fit=crop'),
    createMockProduct('f3', 'Miami to Cancun Weekend', 180, 'Travel', 'Flights', 'https://images.unsplash.com/photo-1464037866556-6812c9d1c72e?w=600&h=400&fit=crop'),
    createMockProduct('f4', 'Chicago to Paris', 450, 'Travel', 'Flights', 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=600&h=400&fit=crop'),
];

const hotelDeals = [
    createMockProduct('h1', 'Ritz Carlton Tokyo', 450, 'Travel', 'Hotels', 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=600&h=400&fit=crop'),
    createMockProduct('h2', 'Marina Bay Sands', 800, 'Travel', 'Hotels', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop'),
    createMockProduct('h3', 'Four Seasons Maui', 1200, 'Travel', 'Hotels', 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600&h=400&fit=crop'),
];

const destinations = [
    createMockProduct('d1', 'Bali, Indonesia', 1200, 'Travel', 'Destinations', 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=600&h=400&fit=crop'),
    createMockProduct('d2', 'Santorini, Greece', 1500, 'Travel', 'Destinations', 'https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=600&h=400&fit=crop'),
];

// --- GAMING DATA ---
const games = [
    createMockProduct('g1', 'Elden Ring', 59, 'Gaming', 'Games', 'https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=600&h=400&fit=crop'),
    createMockProduct('g2', 'God of War Ragnarok', 69, 'Gaming', 'Games', 'https://images.unsplash.com/photo-1493711662062-fa541f7f3d24?w=600&h=400&fit=crop'),
    createMockProduct('g3', 'Cyberpunk 2077', 29, 'Gaming', 'Games', 'https://images.unsplash.com/photo-1511512578047-dfb367046420?w=600&h=400&fit=crop'),
];

const gamingPCs = [
    createMockProduct('pc1', 'Alienware Aurora R13', 2499, 'Gaming', 'PCs', 'https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=600&h=400&fit=crop'),
    createMockProduct('pc2', 'Corsair One i300', 3200, 'Gaming', 'PCs', 'https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=600&h=400&fit=crop'),
];

// --- ELECTRONICS ---
const phones = [
    createMockProduct('ph2', 'Samsung Galaxy S24 Ultra', 1299, 'Electronics', 'Smartphones', 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=600&h=400&fit=crop'),
    createMockProduct('ph3', 'Google Pixel 8 Pro', 999, 'Electronics', 'Smartphones', 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600&h=400&fit=crop'),
    createMockProduct('ph4', 'OnePlus 12', 799, 'Electronics', 'Smartphones', 'https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=600&h=400&fit=crop'),
    createMockProduct('ph5', 'iPhone 15 Pro', 999, 'Electronics', 'Smartphones', 'https://images.unsplash.com/photo-1591337676887-a217a6970a8a?w=600&h=400&fit=crop'),
];

const headphones = [
    createMockProduct('hp1', 'Sony WH-1000XM5', 348, 'Electronics', 'Headphones', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=400&fit=crop'),
    createMockProduct('hp2', 'Bose QuietComfort Ultra', 429, 'Electronics', 'Headphones', 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600&h=400&fit=crop'),
    createMockProduct('hp4', 'AirPods Max', 549, 'Electronics', 'Headphones', 'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600&h=400&fit=crop'),
    createMockProduct('hp5', 'Sennheiser Momentum 4', 349, 'Electronics', 'Headphones', 'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=600&h=400&fit=crop'),
];

const tablets = [
    createMockProduct('t2', 'iPad Pro 12.9"', 1099, 'Electronics', 'Tablets', 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600&h=400&fit=crop'),
    createMockProduct('t3', 'Samsung Galaxy Tab S9 Ultra', 1199, 'Electronics', 'Tablets', 'https://images.unsplash.com/photo-1561154464-82e9adf32764?w=600&h=400&fit=crop'),
];

const laptops = [
    createMockProduct('l2', 'MacBook Pro 16"', 2499, 'Electronics', 'Laptops', 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&h=400&fit=crop'),
    createMockProduct('l3', 'Dell XPS 15', 1799, 'Electronics', 'Laptops', 'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=600&h=400&fit=crop'),
    createMockProduct('l4', 'ThinkPad X1 Carbon', 1649, 'Electronics', 'Laptops', 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&h=400&fit=crop'),
];

// --- HOME & GARDEN ---
const kitchen = [
    createMockProduct('k1', 'Ninja Air Fryer Max XL', 119, 'Home', 'Kitchen', 'https://images.unsplash.com/photo-1626509653291-18d9a934b9db?w=600&h=400&fit=crop'),
    createMockProduct('k2', 'KitchenAid Artisan Mixer', 399, 'Home', 'Kitchen', 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=600&h=400&fit=crop'),
    createMockProduct('k3', 'Instant Pot Duo 7-in-1', 89, 'Home', 'Kitchen', 'https://images.unsplash.com/photo-1544233726-9f1d2b27be8b?w=600&h=400&fit=crop'),
    createMockProduct('k4', 'Breville Barista Express', 699, 'Home', 'Kitchen', 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&h=400&fit=crop'),
    createMockProduct('k5', 'Vitamix E310', 349, 'Home', 'Kitchen', 'https://images.unsplash.com/photo-1622480916113-9000ac49b79d?w=600&h=400&fit=crop'),
];

// --- FASHION ---
const sneakers = [
    createMockProduct('s1', 'Nike Air Jordan 1 Retro', 180, 'Fashion', 'Sneakers', 'https://images.unsplash.com/photo-1552346154-21d32810aba3?w=600&h=400&fit=crop'),
    createMockProduct('s2', 'Adidas Ultraboost 23', 190, 'Fashion', 'Sneakers', 'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=600&h=400&fit=crop'),
    createMockProduct('s3', 'New Balance 990v6', 199, 'Fashion', 'Sneakers', 'https://images.unsplash.com/photo-1539185441755-769473a23570?w=600&h=400&fit=crop'),
    createMockProduct('s4', 'Nike Air Max 90', 130, 'Fashion', 'Sneakers', 'https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?w=600&h=400&fit=crop'),
];

// --- SPORTS ---
const gym = [
    createMockProduct('sp1', 'Peloton Bike+', 2495, 'Sports', 'Equipment', 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=600&h=400&fit=crop'),
    createMockProduct('sp2', 'Bowflex SelectTech 552', 429, 'Sports', 'Equipment', 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=600&h=400&fit=crop'),
    createMockProduct('sp3', 'NordicTrack Commercial 1750', 1799, 'Sports', 'Equipment', 'https://images.unsplash.com/photo-1576678927484-cc907957088c?w=600&h=400&fit=crop'),
    createMockProduct('sp4', 'Theragun Pro', 599, 'Sports', 'Equipment', 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=600&h=400&fit=crop'),
];

// --- BEAUTY ---
const skincare = [
    createMockProduct('b1', 'La Mer Moisturizing Cream', 350, 'Beauty', 'Skincare', 'https://images.unsplash.com/photo-1570194065650-d99fb4b38b17?w=600&h=400&fit=crop'),
    createMockProduct('b2', 'Dyson Supersonic Hair Dryer', 429, 'Beauty', 'Tools', 'https://images.unsplash.com/photo-1522338140262-f46f5913618a?w=600&h=400&fit=crop'),
    createMockProduct('b3', 'SK-II Facial Treatment Essence', 185, 'Beauty', 'Skincare', 'https://images.unsplash.com/photo-1571781926291-c477ebfd024b?w=600&h=400&fit=crop'),
    createMockProduct('b4', 'Dyson Airwrap Complete', 599, 'Beauty', 'Tools', 'https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=600&h=400&fit=crop'),
];

// --- BABY & KIDS ---
const babyProducts = [
    createMockProduct('baby1', 'Graco Pack n Play', 179, 'Baby', 'Gear', 'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=600&h=400&fit=crop'),
    createMockProduct('baby2', 'Baby Brezza Formula Pro', 199, 'Baby', 'Feeding', 'https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=600&h=400&fit=crop'),
    createMockProduct('baby3', 'Hatch Rest 2nd Gen', 69, 'Baby', 'Sleep', 'https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=600&h=400&fit=crop'),
    createMockProduct('baby4', 'UPPAbaby Vista V2', 979, 'Baby', 'Strollers', 'https://images.unsplash.com/photo-1590864558584-77d5a5d2ebe8?w=600&h=400&fit=crop'),
    createMockProduct('baby5', 'Nanit Pro Camera', 299, 'Baby', 'Monitors', 'https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?w=600&h=400&fit=crop'),
];

// --- PET SUPPLIES ---
const petProducts = [
    createMockProduct('pet1', 'KONG Classic Dog Toy', 15, 'Pet', 'Toys', 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=600&h=400&fit=crop'),
    createMockProduct('pet2', 'Furminator Deshedding Tool', 32, 'Pet', 'Grooming', 'https://images.unsplash.com/photo-1516734212186-a967f81ad0d7?w=600&h=400&fit=crop'),
    createMockProduct('pet3', 'PetSafe Smart Feeder', 89, 'Pet', 'Feeding', 'https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=600&h=400&fit=crop'),
    createMockProduct('pet4', 'Outward Hound Fun Feeder', 18, 'Pet', 'Toys', 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=600&h=400&fit=crop'),
    createMockProduct('pet5', 'Catit Flower Fountain', 35, 'Pet', 'Water', 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&h=400&fit=crop'),
];

// --- CLEANING SUPPLIES ---
const cleaningProducts = [
    createMockProduct('clean1', 'Dyson V15 Detect', 749, 'Cleaning', 'Vacuums', 'https://images.unsplash.com/photo-1558317374-067fb5f30001?w=600&h=400&fit=crop'),
    createMockProduct('clean2', 'iRobot Roomba j7+', 599, 'Cleaning', 'Robot Vacuums', 'https://images.unsplash.com/photo-1603618090561-412154b4bd1b?w=600&h=400&fit=crop'),
    createMockProduct('clean3', 'Bissell CrossWave', 299, 'Cleaning', 'Wet/Dry', 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=600&h=400&fit=crop'),
    createMockProduct('clean4', 'Shark Steam Mop', 89, 'Cleaning', 'Mops', 'https://images.unsplash.com/photo-1628177142898-93e36e4e3a50?w=600&h=400&fit=crop'),
    createMockProduct('clean5', 'Tineco Floor One S5', 449, 'Cleaning', 'Smart Mops', 'https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?w=600&h=400&fit=crop'),
];

// Exporting Category Data Maps
export const CATEGORIES: Record<string, CategoryData> = {
    travel: {
        id: 'travel',
        title: 'Travel',
        description: 'Find the best gear, backed by real travelers',
        heroGradient: 'linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%)',
        stats: {
            totalReviews: 2400000,
            totalSources: 156,
            totalProducts: 12847,
        },
        rows: [
            { id: 'flights', title: '✈️ Flight Deals', subtitle: 'Best prices from 47 airlines', items: flightDeals },
            { id: 'hotels', title: '🏨 Top Hotels', subtitle: 'Highest rated on TripAdvisor & Booking', items: hotelDeals },
            { id: 'destinations', title: '🗺️ Trending Destinations', subtitle: 'Where everyone is going', items: destinations },
        ]
    },
    gaming: {
        id: 'gaming',
        title: 'Gaming',
        description: 'Unbiased reviews for hardcore gamers',
        heroGradient: 'linear-gradient(135deg, #7C3AED 0%, #C026D3 100%)',
        stats: { totalReviews: 5600000, totalSources: 89, totalProducts: 4500 },
        rows: [
            { id: 'games', title: '🎮 Hot Games', subtitle: 'Trending on Steam & Reddit', items: games },
            { id: 'pcs', title: '🖥️ Gaming PCs', subtitle: 'Performance beasts', items: gamingPCs },
        ]
    },
    electronics: {
        id: 'electronics',
        title: 'Electronics',
        description: 'Tech reviews you can trust',
        heroGradient: 'linear-gradient(135deg, #2563EB 0%, #06B6D4 100%)',
        stats: { totalReviews: 8900000, totalSources: 342, totalProducts: 23100 },
        rows: [
            { id: 'phones', title: '📱 Top Smartphones', subtitle: 'Latest flagships reviewed', items: phones },
            { id: 'headphones', title: '🎧 Best Headphones', subtitle: 'Audiophile approved', items: headphones },
            { id: 'laptops', title: '💻 Laptops', subtitle: 'Top picks for work & play', items: laptops },
            { id: 'tablets', title: '📱 Tablets', subtitle: 'Best portable productivity', items: tablets },
        ]
    },
    'home-garden': {
        id: 'home-garden',
        title: 'Kitchen',
        description: 'Make your kitchen smarter, not harder',
        heroGradient: 'linear-gradient(135deg, #F59E0B 0%, #EF4444 100%)',
        stats: { totalReviews: 3400000, totalSources: 120, totalProducts: 8900 },
        rows: [
            { id: 'kitchen', title: '🍳 Kitchen Essentials', subtitle: 'Chef recommended', items: kitchen },
        ]
    },
    fashion: {
        id: 'fashion',
        title: 'Fashion',
        description: 'Style trends and quality checks',
        heroGradient: 'linear-gradient(135deg, #DB2777 0%, #F472B6 100%)',
        stats: { totalReviews: 4100000, totalSources: 98, totalProducts: 15600 },
        rows: [
            { id: 'sneakers', title: '👟 Sneaker drops', subtitle: 'Hype and comfort', items: sneakers },
        ]
    },
    sports: {
        id: 'sports',
        title: 'Sports & Outdoors',
        description: 'Gear for your next adventure',
        heroGradient: 'linear-gradient(135deg, #EA580C 0%, #F97316 100%)',
        stats: { totalReviews: 1200000, totalSources: 67, totalProducts: 6700 },
        rows: [
            { id: 'gym', title: '💪 Home Gym', subtitle: 'Build muscle at home', items: gym },
        ]
    },
    beauty: {
        id: 'beauty',
        title: 'Beauty',
        description: 'Real results, no filters',
        heroGradient: 'linear-gradient(135deg, #E11D48 0%, #FDA4AF 100%)',
        stats: { totalReviews: 6700000, totalSources: 230, totalProducts: 9800 },
        rows: [
            { id: 'skincare', title: '✨ Skincare', subtitle: 'Dermatologist verified picks', items: skincare },
        ]
    }
};

// Balanced trending mix: 1 from each major category
const trendingMix = [
    hotelDeals[0],       // Ritz Carlton Tokyo (Travel)
    headphones[0],       // Sony WH-1000XM5
    laptops[0],          // Dell XPS 15
    kitchen[0],          // Ninja Air Fryer
    sneakers[0],         // Nike Air Jordan 1
    games[0],            // Elden Ring
    skincare[1],         // Dyson Supersonic
    cleaningProducts[0], // Dyson V15 Detect
];

export const HOME_ROWS = [
    { id: 'baby', title: '👶 Baby & Kids Essentials', subtitle: 'Parent-approved picks', items: babyProducts },
    { id: 'pet', title: '🐾 Pet Favorites', subtitle: 'Fur baby tested', items: petProducts },
    { id: 'cleaning', title: '🧹 Cleaning Must-Haves', subtitle: 'Top rated vacuums & more', items: cleaningProducts },
    { id: 'kitchen', title: '🍳 Kitchen Upgrades', subtitle: 'Viral on TikTok', items: kitchen },
];
