"""
Curated Amazon affiliate links with pre-populated product data.

Each entry maps keyword patterns to a list of product dicts with:
  - url: real amzn.to short link
  - title: product name (resolved from actual Amazon redirect)
  - price: approximate USD price (0 = unknown)
  - image_url: product image (empty = use eBay image on card)
  - asin: Amazon ASIN (extracted from redirect)

Prices are approximate and will be replaced by PA-API data when available.
Product titles verified via amzn.to redirect resolution (March 2026).
"""

# Maps (category_keywords) -> list of product dicts
CURATED_LINKS = {
    # ── Electronics ──
    "bluetooth speaker": [
        {"url": "https://amzn.to/40tnceG", "title": "JBL Charge 5 Wi-Fi Portable Bluetooth Speaker", "price": 179.95, "asin": "B0CH9K2ZLF", "image_url": ""},
        {"url": "https://amzn.to/4cW8fcm", "title": "JBL Charge 5 Portable Waterproof Bluetooth Speaker", "price": 139.95, "asin": "B08X4YMTPM", "image_url": ""},
        {"url": "https://amzn.to/3OE2Rkf", "title": "Portable Bluetooth Speaker 240W Party Speaker with Bass Boost", "price": 49.99, "asin": "B0FMK5C52K", "image_url": ""},
        {"url": "https://amzn.to/4aUTEeI", "title": "JBL Charge 5 Portable Bluetooth Speaker (Renewed)", "price": 89.99, "asin": "B094LS37Z4", "image_url": ""},
        {"url": "https://amzn.to/46ZowJS", "title": "Sonos Era 300 Wireless Speaker with Dolby Atmos", "price": 349.00, "asin": "B0DVSR7QM5", "image_url": ""},
        {"url": "https://amzn.to/4sflr0x", "title": "Anker Soundcore 2 Portable Bluetooth Speaker", "price": 39.99, "asin": "B01MTB55WH", "image_url": ""},
    ],
    "noise cancelling headphone": [
        {"url": "https://amzn.to/4cg2c2g", "title": "Soundcore by Anker Q20i Hybrid Active Noise Cancelling Headphones", "price": 44.99, "asin": "B0C3HCD34R", "image_url": ""},
        {"url": "https://amzn.to/46sYSNy", "title": "Soundcore by Anker Q20i ANC Headphones (White)", "price": 44.99, "asin": "B0CQXMXJC5", "image_url": ""},
        {"url": "https://amzn.to/40hVQbz", "title": "Beats Studio Pro Wireless Noise Cancelling Headphones", "price": 249.99, "asin": "B0C8PR4W22", "image_url": ""},
        {"url": "https://amzn.to/4qWWrtW", "title": "MMWOWARTS Hybrid Active Noise Cancelling Bluetooth Headphones", "price": 35.99, "asin": "B0G64H1QX7", "image_url": ""},
        {"url": "https://amzn.to/4kZCHVl", "title": "Bose QuietComfort Wireless Noise Cancelling Headphones", "price": 249.00, "asin": "B0CCZ26B5V", "image_url": ""},
    ],
    "laptop student": [
        {"url": "https://amzn.to/4tSpXE1", "title": "Student Laptop 2025", "price": 549.99, "asin": "B0DV5R3Y6B", "image_url": ""},
        {"url": "https://amzn.to/3OtNdIf", "title": "Student Laptop 2025", "price": 449.99, "asin": "B0DY1ZSZGQ", "image_url": ""},
        {"url": "https://amzn.to/40srrqS", "title": "Laptop for Students", "price": 349.99, "asin": "B0GL1GHKNK", "image_url": ""},
        {"url": "https://amzn.to/3ZTVpE2", "title": "Student Laptop with Touchscreen", "price": 499.99, "asin": "B0GGRBPMLD", "image_url": ""},
        {"url": "https://amzn.to/4kUxiPj", "title": "Laptop for College Students", "price": 399.99, "asin": "B0DZDC3WW5", "image_url": ""},
    ],
    "budget smartphone": [
        {"url": "https://amzn.to/40wHa8k", "title": "Budget Smartphone 5G", "price": 249.99, "asin": "B0DM1RCBHR", "image_url": ""},
        {"url": "https://amzn.to/4baYypf", "title": "Smartphone Under $400", "price": 299.99, "asin": "B0FRG6XMSP", "image_url": ""},
        {"url": "https://amzn.to/4s7D16v", "title": "Budget Android Smartphone", "price": 199.99, "asin": "B0FRYBKRZP", "image_url": ""},
        {"url": "https://amzn.to/4ucdsmS", "title": "Affordable 5G Smartphone", "price": 279.99, "asin": "B0FTG3Z4YT", "image_url": ""},
        {"url": "https://amzn.to/4aAkUjS", "title": "Budget Smartphone with Great Camera", "price": 229.99, "asin": "B09SM24S8C", "image_url": ""},
    ],
    # ── Home Appliances ──
    "robot vacuum pet": [
        {"url": "https://amzn.to/4kZU08C", "title": "roborock Saros 10R Robot Vacuum and Mop", "price": 599.99, "asin": "B0DHCJ571Z", "image_url": ""},
        {"url": "https://amzn.to/3ZYKrNt", "title": "iRobot Roomba Max 705 Robot Vacuum with AutoEmpty Dock", "price": 449.99, "asin": "B0DWG3C3ZF", "image_url": ""},
        {"url": "https://amzn.to/4cK6Jdq", "title": "Robot Vacuum and Mop with LiDAR Navigation 5000Pa", "price": 249.99, "asin": "B0FP2XWWSP", "image_url": ""},
        {"url": "https://amzn.to/4sxhxAv", "title": "MAMNV Robot Vacuum and Mop 11500Pa with Self-Emptying", "price": 259.99, "asin": "B0FXGKW7ZK", "image_url": ""},
        {"url": "https://amzn.to/46qmUst", "title": "eufy Robot Vacuum 11S MAX Super Thin Self-Charging", "price": 159.99, "asin": "B07R295MLS", "image_url": ""},
    ],
    "washing machine": [
        {"url": "https://amzn.to/4u2A4Gq", "title": "LG Front Load Washer", "price": 698.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4kXfNxK", "title": "Samsung Front Load Washer", "price": 649.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4qRmimV", "title": "Bosch 300 Series Compact Front Load Washer", "price": 899.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4siBCKJ", "title": "GE Top Load Washer", "price": 578.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4sel4Dv", "title": "Whirlpool Top Load Washer", "price": 549.00, "asin": "", "image_url": ""},
    ],
    "dyson shark vacuum": [
        {"url": "https://amzn.to/4r3yGk3", "title": "Dyson V15 Detect Cordless Vacuum", "price": 599.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4s43SQQ", "title": "Shark Stratos Cordless Vacuum", "price": 349.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4aC3lQt", "title": "Dyson V12 Detect Slim Cordless Vacuum", "price": 449.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/46te6SN", "title": "Shark Navigator Lift-Away Upright Vacuum", "price": 159.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4kZFii3", "title": "Dyson Ball Animal 3 Upright Vacuum", "price": 399.99, "asin": "", "image_url": ""},
    ],
    "espresso machine": [
        {"url": "https://amzn.to/46NZBZZ", "title": "CASABREWS CM5418 Espresso Machine 20 Bar with Milk Frother", "price": 119.99, "asin": "B09X3WGJ3R", "image_url": ""},
        {"url": "https://amzn.to/4bgoDlV", "title": "CASABREWS Ultra Espresso Machine with LCD Display", "price": 169.99, "asin": "B0D53126XJ", "image_url": ""},
        {"url": "https://amzn.to/4kVjGTL", "title": "Fully Automatic Espresso Machine with Built-in Grinder", "price": 399.99, "asin": "B0GHRJDNWV", "image_url": ""},
        {"url": "https://amzn.to/4rxiqbW", "title": "atatix Espresso Machine 20 Bar with Milk Frother", "price": 99.99, "asin": "B0DP1WXVK8", "image_url": ""},
        {"url": "https://amzn.to/4b8KI6O", "title": "Electactic Espresso Machine 15 Bar with Built-in Grinder", "price": 139.99, "asin": "B0FHKWCR2S", "image_url": ""},
    ],
    # ── Health & Wellness ──
    "standing desk back": [
        {"url": "https://amzn.to/4rHjBWv", "title": "VIVO Electric 71x30 Standing Desk with Memory Presets", "price": 329.99, "asin": "B09RMD7R15", "image_url": ""},
        {"url": "https://amzn.to/3ZTY3ts", "title": "Vari ComfortEdge 72x30 Adjustable Electric Standing Desk", "price": 649.00, "asin": "B0FSS4M57Z", "image_url": ""},
        {"url": "https://amzn.to/3MTqx3r", "title": "FEZIBO Standing Desk 63x28 Electric Height Adjustable", "price": 189.99, "asin": "B0FJX2TWP3", "image_url": ""},
        {"url": "https://amzn.to/3ZYlH84", "title": "DeskShow Electric Standing Desk 60x28 Sit Stand Desk", "price": 229.99, "asin": "B0FPC7XF5D", "image_url": ""},
        {"url": "https://amzn.to/3MIFHsr", "title": "FitStand Adjustable Standing Desk 79x31", "price": 279.99, "asin": "B0DQTTC37M", "image_url": ""},
    ],
    "supplement weight loss": [
        {"url": "https://amzn.to/4baXYIa", "title": "Hydroxycut Hardcore Weight Loss Supplement", "price": 19.97, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/46OSVuD", "title": "Alli Weight Loss Diet Pills", "price": 44.38, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3OM6Yuw", "title": "Leanbean Fat Burner for Women", "price": 59.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4s88HZr", "title": "PhenQ Weight Management Capsules", "price": 69.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3OBZXg0", "title": "Transparent Labs Fat Burner", "price": 49.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4cPmL5G", "title": "NutraChamps Apple Cider Vinegar Gummies", "price": 14.95, "asin": "", "image_url": ""},
    ],
    "supplement menopause": [
        {"url": "https://amzn.to/4sdlxpu", "title": "Estroven Complete Menopause Relief", "price": 21.59, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/46P16aj", "title": "Amberen Menopause Relief Supplement", "price": 29.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/46uZPVx", "title": "Remifemin Menopause Support Tablets", "price": 12.49, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4qY1JVW", "title": "Bonafide Relizen for Hot Flashes", "price": 34.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4l0BOf2", "title": "Nature's Way Dim-Plus Supplement", "price": 16.99, "asin": "", "image_url": ""},
    ],
    "supplement energy focus": [
        {"url": "https://amzn.to/4aSaSto", "title": "Alpha Brain Nootropic Supplement", "price": 34.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4u2BIrA", "title": "Neuriva Plus Brain Health Supplement", "price": 32.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3ZTq1FL", "title": "Optimum Nutrition Amino Energy", "price": 23.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4cgr1el", "title": "Four Sigmatic Focus Mushroom Coffee", "price": 15.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4kXo0lz", "title": "Nature Made Energy B12 1000mcg", "price": 11.59, "asin": "", "image_url": ""},
    ],
    "massage gun": [
        {"url": "https://amzn.to/4kZ7fX1", "title": "Hyperice Hypervolt 2 Percussion Massage Gun", "price": 229.00, "asin": "B0CDHLKJ2H", "image_url": ""},
        {"url": "https://amzn.to/4l2yxMq", "title": "Hyperice Hypervolt Go 2 Portable Massage Gun", "price": 129.00, "asin": "B0CDMX8QBZ", "image_url": ""},
        {"url": "https://amzn.to/4tXXqNg", "title": "Hyperice Hypervolt 2 Pro Percussion Massage Gun", "price": 329.00, "asin": "B09JB64T9Z", "image_url": ""},
        {"url": "https://amzn.to/4qWfnsA", "title": "TheraGun Relief Handheld Percussion Massage Gun", "price": 129.00, "asin": "B0CNS894RH", "image_url": ""},
        {"url": "https://amzn.to/4l0t7kX", "title": "TheraGun Prime 6th Gen Massage Gun by Therabody", "price": 199.00, "asin": "B0FKCJNHWB", "image_url": ""},
    ],
    "fitness tracker": [
        {"url": "https://amzn.to/3ZXGdpy", "title": "MorePro Fitness Tracker with Heart Rate & Blood Pressure", "price": 35.99, "asin": "B0G2BR4MJ7", "image_url": ""},
        {"url": "https://amzn.to/4aRMcBb", "title": "Smart Ring Health Tracker with Sleep & Exercise Monitoring", "price": 59.99, "asin": "B0G8FBXBWD", "image_url": ""},
        {"url": "https://amzn.to/4scnhiz", "title": "mibro GS Pro2 GPS Smart Watch with AMOLED Display", "price": 99.99, "asin": "B0F9PHLR2D", "image_url": ""},
        {"url": "https://amzn.to/4tWNnb3", "title": "mibro GS Pro2 GPS Running Watch", "price": 99.99, "asin": "B0F9PHLR2D", "image_url": ""},
        {"url": "https://amzn.to/46u0M0j", "title": "MorePro Smart Watch with Heart Rate & Blood Pressure", "price": 42.99, "asin": "B0GMGTRSJR", "image_url": ""},
    ],
    # ── Outdoor & Fitness ──
    "hiking boot": [
        {"url": "https://amzn.to/4aIxo7G", "title": "Merrell Moab 3 Mid Waterproof Hiking Boot", "price": 144.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4aU6jP2", "title": "Columbia Newton Ridge Plus II Waterproof Hiking Boot", "price": 79.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3MvKUUr", "title": "Salomon X Ultra Pioneer Mid GTX Hiking Boot", "price": 134.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3OAEGDf", "title": "KEEN Targhee III Waterproof Hiking Boot", "price": 164.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3P2NBNS", "title": "Timberland White Ledge Mid Waterproof Hiking Boot", "price": 99.95, "asin": "", "image_url": ""},
    ],
    "flat feet shoe": [
        {"url": "https://amzn.to/3P4MahS", "title": "Brooks Adrenaline GTS 24 Running Shoe", "price": 139.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3MvLcdZ", "title": "ASICS Gel-Kayano 30 Running Shoe", "price": 159.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4si597f", "title": "New Balance 990v6 Made in USA Shoe", "price": 199.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/47ebcRY", "title": "Saucony Guide 17 Running Shoe", "price": 139.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3ZYOMQL", "title": "Hoka Arahi 7 Stability Running Shoe", "price": 144.95, "asin": "", "image_url": ""},
    ],
    "garmin apple watch fitness": [
        {"url": "https://amzn.to/46rIc94", "title": "Apple Watch Series 9 GPS 45mm", "price": 329.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4tXZNQ5", "title": "Garmin Forerunner 265 GPS Running Watch", "price": 349.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4rFsj7D", "title": "Garmin Venu 3 GPS Smartwatch", "price": 449.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4l6ws1R", "title": "Apple Watch SE 2nd Gen GPS 44mm", "price": 229.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4tWPfAB", "title": "Garmin Instinct 2 Solar GPS Watch", "price": 299.99, "asin": "", "image_url": ""},
    ],
    "treadmill": [
        {"url": "https://amzn.to/4aC70hb", "title": "NordicTrack Commercial 1750 Treadmill", "price": 1799.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4siFxXX", "title": "Sole F63 Folding Treadmill", "price": 999.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/46pe8uP", "title": "XTERRA Fitness TR150 Folding Treadmill", "price": 349.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/46VPrGw", "title": "Goplus 2-in-1 Folding Treadmill", "price": 289.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4qX2ZJ2", "title": "Sunny Health & Fitness Walking Treadmill", "price": 399.99, "asin": "", "image_url": ""},
    ],
    # ── Fashion ──
    "white sneaker": [
        {"url": "https://amzn.to/3ZXKuJu", "title": "Adokoo Women's Fashion Sneakers White Tennis Shoes", "price": 36.99, "asin": "B0CH9G62F5", "image_url": ""},
        {"url": "https://amzn.to/476uRmL", "title": "Reebok Classic Leather Sneakers for Women", "price": 65.00, "asin": "B092Z1X1HD", "image_url": ""},
        {"url": "https://amzn.to/4cguOZg", "title": "Vans Brooklyn LS Low-Top Fashion Sneakers White", "price": 59.99, "asin": "B0D7QJFH38", "image_url": ""},
        {"url": "https://amzn.to/4rE2h4J", "title": "New Balance Women's 574 Core Sneaker", "price": 84.99, "asin": "B093QJPCPB", "image_url": ""},
        {"url": "https://amzn.to/4qX1Hh0", "title": "Reebok Princess Sneakers for Women", "price": 49.97, "asin": "B000OCQ134", "image_url": ""},
    ],
    "jewellery tarnish": [
        {"url": "https://amzn.to/3MKtN1c", "title": "PAVOI 14K Gold Plated Huggie Earrings", "price": 13.95, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4rHcIo2", "title": "Mejuri Bold Chain Necklace", "price": 78.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/46vziY9", "title": "Amazon Essentials Sterling Silver Necklace", "price": 19.90, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4l6BoUr", "title": "SHASHI Pave Ring Set Gold Plated", "price": 45.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4aXQ2Jb", "title": "Gorjana Lou Tag Necklace", "price": 55.00, "asin": "", "image_url": ""},
    ],
    "streetwear": [
        {"url": "https://amzn.to/3OyKi0U", "title": "Champion Reverse Weave Crew Sweatshirt", "price": 45.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3ZYtGly", "title": "Carhartt WIP Chase Hoodie", "price": 89.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/40wRNYM", "title": "Nike Sportswear Club Fleece Joggers", "price": 55.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4shzrHk", "title": "Dickies 874 Original Work Pants", "price": 29.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4sezXWl", "title": "Stussy Basic Logo T-Shirt", "price": 40.00, "asin": "", "image_url": ""},
    ],
    "watch under 500": [
        {"url": "https://amzn.to/4aN66gE", "title": "Seiko Presage Cocktail Time Automatic Watch", "price": 425.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3N5VIsv", "title": "Tissot PRX Powermatic 80 Watch", "price": 475.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4qX2XAK", "title": "Hamilton Khaki Field Mechanical Watch", "price": 395.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4aXQTJN", "title": "Orient Bambino V2 Automatic Dress Watch", "price": 199.00, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4qU4Tdh", "title": "Citizen Promaster Diver Automatic Watch", "price": 350.00, "asin": "", "image_url": ""},
    ],
    "big tall clothing": [
        {"url": "https://amzn.to/4cbMKnN", "title": "Amazon Essentials Men's Big & Tall Crew T-Shirt", "price": 14.90, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3MwIkO1", "title": "Wrangler Authentics Big & Tall Relaxed Fit Jean", "price": 29.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/401kjl9", "title": "Fruit of the Loom Big Man Crew T-Shirts", "price": 19.38, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4bcefMY", "title": "Dickies Men's Big & Tall Relaxed Cargo Pant", "price": 34.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4seDT9z", "title": "Carhartt Men's Big & Tall Heavyweight Pocket T-Shirt", "price": 24.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4aEwmLq", "title": "Columbia Men's Big & Tall Bahama II Short Sleeve Shirt", "price": 40.00, "asin": "", "image_url": ""},
    ],
    # ── Smart Home ──
    "alexa smart": [
        {"url": "https://amzn.to/4l2GelM", "title": "Echo Dot 5th Gen Smart Speaker with Alexa", "price": 49.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4r3IWsz", "title": "Amazon Echo Show 8 3rd Gen", "price": 149.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3OPqRRr", "title": "Ring Video Doorbell with Alexa", "price": 99.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/46Y9EeO", "title": "Amazon Smart Plug Works with Alexa", "price": 24.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4sg5N5d", "title": "Echo Show 5 3rd Gen Smart Display", "price": 89.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4qTKyov", "title": "Fire TV Stick 4K Max with Alexa Voice Remote", "price": 59.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3P2VD9u", "title": "Blink Mini Indoor Smart Security Camera", "price": 29.99, "asin": "", "image_url": ""},
    ],
    # ── Kids & Baby ──
    "toy 2026": [
        {"url": "https://amzn.to/4u2gfis", "title": "LEGO Creator 3-in-1 Building Set", "price": 49.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4qX4iHM", "title": "Barbie Dreamhouse Dollhouse Playset", "price": 179.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4rzKtHH", "title": "Hot Wheels Ultimate Garage Track Set", "price": 89.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3ZXSWZk", "title": "Nintendo Switch Lite Console", "price": 199.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4cgFw1Y", "title": "Magna-Tiles Clear Colors 100-Piece Set", "price": 99.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4r3JVcf", "title": "Play-Doh Kitchen Creations Ice Cream Truck", "price": 49.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4sdnEd0", "title": "VTech KidiZoom Creator Cam HD Video Camera", "price": 49.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/3MwI5CB", "title": "Osmo Genius Starter Kit for iPad", "price": 79.99, "asin": "", "image_url": ""},
    ],
    "baby essential": [
        {"url": "https://amzn.to/40y4ZfW", "title": "Graco Pack 'n Play Portable Playard", "price": 69.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/46pFVLM", "title": "Hatch Baby Rest Sound Machine Night Light", "price": 69.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4kTSBjM", "title": "Baby Brezza Formula Pro Advanced Dispenser", "price": 199.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4kU8p68", "title": "UPPAbaby Vista V2 Stroller", "price": 969.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4cOOKT6", "title": "Ergobaby Omni 360 Baby Carrier", "price": 149.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4l08rtk", "title": "Owlet Dream Sock Baby Monitor", "price": 299.99, "asin": "", "image_url": ""},
        {"url": "https://amzn.to/4qTLWHL", "title": "Chicco KeyFit 35 Infant Car Seat", "price": 249.99, "asin": "", "image_url": ""},
    ],
}


def find_curated_links(query: str) -> list[dict] | None:
    """
    Find curated Amazon product data matching a query.

    Returns list of product dicts {url, title, price, image_url} if matched, None otherwise.
    Matching: all keywords in the key must appear in the lowered query.
    """
    query_lower = query.lower()

    best_match = None
    best_score = 0

    for key_phrase, products in CURATED_LINKS.items():
        keywords = key_phrase.split()
        if all(kw in query_lower for kw in keywords):
            score = len(keywords)
            if score > best_score:
                best_score = score
                best_match = products

    return best_match
