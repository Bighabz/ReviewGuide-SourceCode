"""
Amazon Affiliate Provider
Supports both mock data (development) and real PA-API (production)
Automatically switches based on AMAZON_API_ENABLED configuration
"""
import json
import hashlib
import hmac
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
from app.core.centralized_logger import get_logger
from app.services.affiliate.base import BaseAffiliateProvider, AffiliateProduct
from app.core.config import settings

logger = get_logger(__name__)


# Category-aware product variations for mock data (specs/editions, NOT accessories)
CATEGORY_VARIATIONS = {
    "laptop": [
        "Intel i7, 16GB RAM, 512GB SSD",
        "AMD Ryzen 7, 32GB RAM, 1TB SSD",
        "Intel i9, 64GB RAM, 2TB SSD",
        "AMD Ryzen 9, 16GB RAM, 512GB SSD",
        "Intel i5, 8GB RAM, 256GB SSD",
    ],
    "computer": [
        "Intel i7, 32GB RAM, 1TB SSD Tower",
        "AMD Ryzen 9, 64GB RAM, 2TB NVMe",
        "Intel Xeon, 128GB ECC RAM, 4TB",
        "AMD Threadripper, 256GB RAM, 8TB",
        "Intel i9, 64GB RAM, 2TB SSD Workstation",
    ],
    "server": [
        "Dual Xeon, 256GB ECC, 8TB RAID",
        "AMD EPYC 64-Core, 512GB RAM",
        "Intel Xeon W, 128GB RAM, 4TB NVMe",
        "GPU Server - 4x RTX 4090, 256GB RAM",
        "Tower Server - 64GB RAM, 2TB SSD",
    ],
    "gpu": [
        "RTX 4090 24GB GDDR6X",
        "RTX 4080 Super 16GB",
        "RTX 3090 Ti 24GB",
        "AMD RX 7900 XTX 24GB",
        "RTX A6000 48GB Professional",
    ],
    "phone": [
        "128GB Midnight Black",
        "256GB Starlight Silver",
        "512GB Deep Purple",
        "128GB Blue Titanium",
        "256GB Natural Titanium",
    ],
    "headphones": [
        "Noise Cancelling - Black",
        "Wireless - Silver",
        "Over-Ear Studio - Midnight Blue",
        "Sport - Neon Green",
        "Premium - Rose Gold",
    ],
    "monitor": [
        '27" 4K IPS 144Hz',
        '32" QHD 165Hz Curved',
        '34" Ultrawide WQHD',
        '24" FHD 240Hz Gaming',
        '27" OLED 4K HDR',
    ],
    "keyboard": [
        "Mechanical RGB - Cherry MX Brown",
        "Wireless Low-Profile - White",
        "65% Compact - Hot-Swappable",
        "Full-Size Ergonomic - Split",
        "TKL Gaming - Linear Switches",
    ],
    "camera": [
        "Mirrorless 45MP Body Only",
        "Full Frame 30MP + 24-70mm Kit",
        "APS-C 26MP + 18-55mm Kit",
        "Mirrorless 61MP Professional",
        "Compact 20MP 24-200mm Zoom",
    ],
    "tablet": [
        '11" 256GB WiFi - Space Gray',
        '12.9" 512GB WiFi+Cellular',
        '10.9" 128GB WiFi - Blue',
        '11" 1TB WiFi - Silver',
        '12.9" 256GB WiFi - Starlight',
    ],
    "tv": [
        '65" OLED 4K Smart TV',
        '55" QLED 4K 120Hz',
        '75" Mini-LED 4K HDR',
        '50" LED 4K Smart TV',
        '77" OLED 4K Dolby Vision',
    ],
    "general": [
        "- Pro Edition",
        "- Standard Edition",
        "- Premium Model",
        "- Latest Generation",
        "- Deluxe Version",
    ],
}

# Base prices by category for realistic mock data
CATEGORY_BASE_PRICES = {
    "laptop": 899.99,
    "computer": 999.99,
    "server": 1999.99,
    "gpu": 799.99,
    "phone": 699.99,
    "headphones": 249.99,
    "monitor": 399.99,
    "keyboard": 129.99,
    "camera": 1299.99,
    "tablet": 499.99,
    "tv": 799.99,
    "general": 199.99,
}

# Keywords for category detection
CATEGORY_KEYWORDS = {
    "laptop": ["laptop", "notebook", "macbook", "chromebook", "ultrabook"],
    "computer": ["computer", "desktop", "pc", "workstation", "llm", "llms", "ai server", "hosting"],
    "server": ["server", "rack", "nas", "hosting server"],
    "gpu": ["gpu", "graphics card", "video card", "rtx", "radeon"],
    "phone": ["phone", "iphone", "smartphone", "android", "galaxy", "pixel"],
    "headphones": ["headphone", "earphone", "earbud", "airpod", "earpiece", "headset"],
    "monitor": ["monitor", "display", "screen"],
    "keyboard": ["keyboard", "keeb", "mechanical keyboard"],
    "camera": ["camera", "dslr", "mirrorless", "camcorder"],
    "tablet": ["tablet", "ipad", "surface pro"],
    "tv": ["tv", "television", "smart tv", "oled tv"],
}


def _detect_category(query: str, category_hint: Optional[str] = None) -> str:
    """Detect product category from query keywords or category hint."""
    if category_hint:
        hint_lower = category_hint.lower()
        for cat in CATEGORY_KEYWORDS:
            if cat in hint_lower:
                return cat

    query_lower = query.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return cat

    return "general"


# PA-API hosts by country
PAAPI_HOSTS: Dict[str, str] = {
    "US": "webservices.amazon.com",
    "UK": "webservices.amazon.co.uk",
    "GB": "webservices.amazon.co.uk",
    "DE": "webservices.amazon.de",
    "FR": "webservices.amazon.fr",
    "ES": "webservices.amazon.es",
    "IT": "webservices.amazon.it",
    "JP": "webservices.amazon.co.jp",
    "CA": "webservices.amazon.ca",
    "AU": "webservices.amazon.com.au",
    "IN": "webservices.amazon.in",
    "BR": "webservices.amazon.com.br",
    "MX": "webservices.amazon.com.mx",
    "SG": "webservices.amazon.sg",
    "AE": "webservices.amazon.ae",
    "TR": "webservices.amazon.com.tr",
}

# AWS regions for PA-API signing
PAAPI_REGIONS: Dict[str, str] = {
    "US": "us-east-1",
    "UK": "eu-west-1",
    "GB": "eu-west-1",
    "DE": "eu-west-1",
    "FR": "eu-west-1",
    "ES": "eu-west-1",
    "IT": "eu-west-1",
    "JP": "us-west-2",
    "CA": "us-east-1",
    "AU": "us-west-2",
    "IN": "eu-west-1",
    "BR": "us-east-1",
    "MX": "us-east-1",
    "SG": "us-west-2",
    "AE": "eu-west-1",
    "TR": "eu-west-1",
}


# Amazon domain mapping by country code
AMAZON_DOMAINS: Dict[str, str] = {
    "US": "amazon.com",
    "UK": "amazon.co.uk",
    "GB": "amazon.co.uk",
    "DE": "amazon.de",
    "FR": "amazon.fr",
    "ES": "amazon.es",
    "IT": "amazon.it",
    "JP": "amazon.co.jp",
    "CA": "amazon.ca",
    "AU": "amazon.com.au",
    "IN": "amazon.in",
    "BR": "amazon.com.br",
    "MX": "amazon.com.mx",
    "NL": "amazon.nl",
    "SE": "amazon.se",
    "PL": "amazon.pl",
    "SG": "amazon.sg",
    "AE": "amazon.ae",
    "SA": "amazon.sa",
    "TR": "amazon.com.tr",
}


def parse_associate_tags(tags_string: str) -> Dict[str, str]:
    """
    Parse AMAZON_ASSOCIATE_TAGS from config into a dictionary

    Format: "US:tag-20,UK:tag-21,DE:tag-21"
    Returns: {"US": "tag-20", "UK": "tag-21", "DE": "tag-21"}
    """
    tags = {}
    if not tags_string:
        return tags

    for pair in tags_string.split(","):
        pair = pair.strip()
        if ":" in pair:
            country, tag = pair.split(":", 1)
            country = country.strip().upper()
            tag = tag.strip()
            if country and tag:
                tags[country] = tag

    return tags


def generate_amazon_affiliate_link(
    asin: str,
    country_code: str = "US",
    associate_tag: Optional[str] = None,
) -> str:
    """
    Generate Amazon affiliate link for a product

    Args:
        asin: Amazon Standard Identification Number (e.g., "B09NQNGDGB")
        country_code: ISO country code (e.g., "US", "UK", "DE")
        associate_tag: Optional override for associate tag

    Returns:
        Affiliate link like: https://www.amazon.com/dp/B09NQNGDGB?tag=yoursite-20
    """
    # Normalize country code
    country_code = country_code.upper() if country_code else settings.AMAZON_DEFAULT_COUNTRY

    # Get domain for country
    domain = AMAZON_DOMAINS.get(country_code, AMAZON_DOMAINS.get("US", "amazon.com"))

    # Get associate tag for country
    if associate_tag:
        tag = associate_tag
    else:
        # Try country-specific tag first
        country_tags = parse_associate_tags(settings.AMAZON_ASSOCIATE_TAGS)
        tag = country_tags.get(country_code)

        # Fallback to default tag
        if not tag:
            tag = settings.AMAZON_ASSOCIATE_TAG

    # Build affiliate URL
    if tag:
        return f"https://www.{domain}/dp/{asin}?tag={tag}"
    else:
        # Return direct link if no tag configured
        return f"https://www.{domain}/dp/{asin}"


class AmazonAffiliateProvider(BaseAffiliateProvider):
    """
    Amazon Affiliate Provider

    Supports two modes:
    1. Mock mode (AMAZON_API_ENABLED=false): Uses local JSON file with real ASINs
    2. Real mode (AMAZON_API_ENABLED=true): Uses Amazon PA-API (requires credentials)

    Both modes generate working affiliate links using the same format.
    """

    def __init__(
        self,
        country_code: str = None,
        associate_tag: str = None,
    ):
        """
        Initialize Amazon affiliate provider

        Args:
            country_code: Default country code for this provider instance
            associate_tag: Optional override for associate tag
        """
        self.country_code = country_code or settings.AMAZON_DEFAULT_COUNTRY
        self.associate_tag = associate_tag or settings.AMAZON_ASSOCIATE_TAG
        self.api_enabled = settings.AMAZON_API_ENABLED

        # Load mock data
        self._mock_data = None
        self._load_mock_data()

        logger.info(
            f"Amazon provider initialized: "
            f"api_enabled={self.api_enabled}, "
            f"country={self.country_code}, "
            f"tag={self.associate_tag}"
        )

    def _load_mock_data(self):
        """Load mock product data from JSON file"""
        try:
            mock_file = Path(__file__).parent.parent.parent.parent.parent / "data" / "mock_amazon_products.json"
            if mock_file.exists():
                with open(mock_file, "r") as f:
                    self._mock_data = json.load(f)
                logger.info(f"Loaded {len(self._mock_data.get('products', []))} mock Amazon products")
            else:
                logger.warning(f"Mock Amazon products file not found: {mock_file}")
                self._mock_data = {"products": [], "categories": {}}
        except Exception as e:
            logger.error(f"Failed to load mock Amazon data: {e}")
            self._mock_data = {"products": [], "categories": {}}

    def get_provider_name(self) -> str:
        """Return provider name"""
        return "Amazon"

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
        country_code: Optional[str] = None,
    ) -> List[AffiliateProduct]:
        """
        Search for products on Amazon

        In mock mode: Searches local JSON file
        In real mode: Calls Amazon PA-API (placeholder)
        """
        effective_country = country_code or self.country_code

        logger.info(
            f"Amazon search: query='{query}', category={category}, "
            f"country={effective_country}, limit={limit}"
        )

        if self.api_enabled:
            return await self._search_real_api(
                query, category, brand, min_price, max_price, limit, effective_country
            )
        else:
            return await self._search_mock_data(
                query, category, brand, min_price, max_price, limit, effective_country
            )

    async def _search_mock_data(
        self,
        query: str,
        category: Optional[str],
        brand: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        limit: int,
        country_code: str,
    ) -> List[AffiliateProduct]:
        """Return mock products for development - generates category-aware products"""
        import random
        import hashlib

        # Generate deterministic but different prices/ratings based on query
        query_hash = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
        random.seed(query_hash)

        # Detect category for realistic variations
        detected_category = _detect_category(query, category)
        variations = CATEGORY_VARIATIONS.get(detected_category, CATEGORY_VARIATIONS["general"])
        base_price = CATEGORY_BASE_PRICES.get(detected_category, 199.99)

        ratings = [4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9]

        results = []
        for i in range(min(limit, 5)):
            # Deterministic price variance: +/- 30% from base
            price_offset = ((query_hash + i * 13) % 60 - 30) / 100.0
            price = round(base_price * (1.0 + price_offset), 2)
            rating_idx = (query_hash + i * 3) % len(ratings)
            review_count = 100 + ((query_hash + i * 7) % 9900)

            asin = f"MOCK{query_hash % 1000000:06d}{i}"
            affiliate_link = generate_amazon_affiliate_link(
                asin=asin,
                country_code=country_code,
                associate_tag=self.associate_tag,
            )

            # First result = exact query, rest = query + spec variation
            if i == 0:
                title = query
            else:
                variation = variations[i % len(variations)]
                title = f"{query} - {variation}"

            results.append(AffiliateProduct(
                product_id=asin,
                title=title,
                price=price,
                currency="USD",
                affiliate_link=affiliate_link,
                merchant="Amazon",
                image_url=f"https://placehold.co/400x400/fef3c7/f59e0b?text={query.replace(' ', '+')}",
                rating=ratings[rating_idx],
                review_count=review_count,
                condition="new",
                availability=True,
                source_url=affiliate_link,
            ))

        logger.info(f"Amazon mock: generated {len(results)} {detected_category} products for '{query}'")
        return results

    async def _search_real_api(
        self,
        query: str,
        category: Optional[str],
        brand: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        limit: int,
        country_code: str,
    ) -> List[AffiliateProduct]:
        """
        Search products using Amazon PA-API 5.0

        Uses AWS Signature Version 4 for authentication.
        Reference: https://webservices.amazon.com/paapi5/documentation/
        """
        # Validate credentials
        if not settings.AMAZON_ACCESS_KEY or not settings.AMAZON_SECRET_KEY:
            logger.error("Amazon PA-API credentials not configured. Set AMAZON_ACCESS_KEY and AMAZON_SECRET_KEY in .env")
            return await self._search_mock_data(query, category, brand, min_price, max_price, limit, country_code)

        # Get country-specific tag
        country_tags = parse_associate_tags(settings.AMAZON_ASSOCIATE_TAGS)
        partner_tag = country_tags.get(country_code.upper()) or self.associate_tag

        if not partner_tag:
            logger.error("No Amazon Associate tag configured for country: " + country_code)
            return []

        # Build request
        host = PAAPI_HOSTS.get(country_code.upper(), PAAPI_HOSTS["US"])
        region = PAAPI_REGIONS.get(country_code.upper(), PAAPI_REGIONS["US"])
        path = "/paapi5/searchitems"

        # Map category to Amazon SearchIndex
        search_index = self._map_category_to_search_index(category)

        # Build request payload
        payload = {
            "PartnerTag": partner_tag,
            "PartnerType": "Associates",
            "Keywords": query,
            "SearchIndex": search_index,
            "ItemCount": min(limit, 10),  # PA-API max is 10
            "Resources": [
                "Images.Primary.Large",
                "ItemInfo.Title",
                "ItemInfo.Features",
                "ItemInfo.ProductInfo",
                "Offers.Listings.Price",
                "Offers.Listings.DeliveryInfo.IsPrimeEligible",
                "CustomerReviews.Count",
                "CustomerReviews.StarRating",
            ]
        }

        # Add optional filters
        if brand:
            payload["Brand"] = brand
        if min_price is not None or max_price is not None:
            payload["MinPrice"] = int(min_price * 100) if min_price else None
            payload["MaxPrice"] = int(max_price * 100) if max_price else None
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

        try:
            # Sign and send request
            response_data = await self._send_paapi_request(host, region, path, payload)

            if not response_data:
                logger.warning("Empty response from PA-API, falling back to mock data")
                return await self._search_mock_data(query, category, brand, min_price, max_price, limit, country_code)

            # Parse response
            return self._parse_paapi_response(response_data, country_code)

        except Exception as e:
            logger.error(f"PA-API request failed: {e}", exc_info=True)
            # Fallback to mock data on error
            return await self._search_mock_data(query, category, brand, min_price, max_price, limit, country_code)

    async def _send_paapi_request(
        self,
        host: str,
        region: str,
        path: str,
        payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Send signed request to Amazon PA-API using AWS Signature Version 4
        """
        # Request parameters
        service = "ProductAdvertisingAPI"
        target = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"
        content_type = "application/json; charset=UTF-8"

        # Timestamp
        t = datetime.datetime.utcnow()
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        # Prepare payload
        payload_json = json.dumps(payload)

        # Create canonical request
        canonical_uri = path
        canonical_querystring = ""
        canonical_headers = (
            f"content-encoding:amz-1.0\n"
            f"content-type:{content_type}\n"
            f"host:{host}\n"
            f"x-amz-date:{amz_date}\n"
            f"x-amz-target:{target}\n"
        )
        signed_headers = "content-encoding;content-type;host;x-amz-date;x-amz-target"
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        canonical_request = (
            f"POST\n"
            f"{canonical_uri}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )

        # Create string to sign
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
        string_to_sign = (
            f"{algorithm}\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        # Calculate signature
        def sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        k_date = sign(f"AWS4{settings.AMAZON_SECRET_KEY}".encode("utf-8"), date_stamp)
        k_region = sign(k_date, region)
        k_service = sign(k_region, service)
        k_signing = sign(k_service, "aws4_request")
        signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # Build authorization header
        authorization_header = (
            f"{algorithm} "
            f"Credential={settings.AMAZON_ACCESS_KEY}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        # Send request
        headers = {
            "Content-Type": content_type,
            "Content-Encoding": "amz-1.0",
            "Host": host,
            "X-Amz-Date": amz_date,
            "X-Amz-Target": target,
            "Authorization": authorization_header,
        }

        url = f"https://{host}{path}"
        logger.info(f"PA-API request to {url} with keywords: {payload.get('Keywords')}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, content=payload_json)

            if response.status_code == 200:
                return response.json()
            else:
                error_body = response.text
                logger.error(f"PA-API error {response.status_code}: {error_body}")
                return None

    def _map_category_to_search_index(self, category: Optional[str]) -> str:
        """Map category to Amazon SearchIndex"""
        if not category:
            return "All"

        category_mapping = {
            "electronics": "Electronics",
            "computers": "Computers",
            "books": "Books",
            "clothing": "Fashion",
            "fashion": "Fashion",
            "home": "HomeAndKitchen",
            "kitchen": "HomeAndKitchen",
            "garden": "GardenAndOutdoor",
            "outdoor": "GardenAndOutdoor",
            "sports": "SportsAndOutdoors",
            "toys": "ToysAndGames",
            "games": "VideoGames",
            "beauty": "Beauty",
            "health": "HealthPersonalCare",
            "baby": "Baby",
            "pet": "PetSupplies",
            "automotive": "Automotive",
            "tools": "ToolsAndHomeImprovement",
            "office": "OfficeProducts",
            "luggage": "Luggage",
            "travel": "Luggage",
        }

        return category_mapping.get(category.lower(), "All")

    def _parse_paapi_response(
        self,
        response_data: Dict[str, Any],
        country_code: str,
    ) -> List[AffiliateProduct]:
        """Parse PA-API SearchItems response into AffiliateProduct list"""
        results = []

        search_result = response_data.get("SearchResult", {})
        items = search_result.get("Items", [])

        logger.info(f"PA-API returned {len(items)} items")

        for item in items:
            try:
                asin = item.get("ASIN", "")

                # Get title
                item_info = item.get("ItemInfo", {})
                title_info = item_info.get("Title", {})
                title = title_info.get("DisplayValue", "Unknown Product")

                # Get image
                images = item.get("Images", {})
                primary_image = images.get("Primary", {})
                large_image = primary_image.get("Large", {})
                image_url = large_image.get("URL", "")

                # Get price
                offers = item.get("Offers", {})
                listings = offers.get("Listings", [])
                price = 0.0
                currency = "USD"
                if listings:
                    price_info = listings[0].get("Price", {})
                    price = price_info.get("Amount", 0.0)
                    currency = price_info.get("Currency", "USD")

                # Get reviews
                customer_reviews = item.get("CustomerReviews", {})
                rating = customer_reviews.get("StarRating", {}).get("Value")
                review_count = customer_reviews.get("Count")

                # Generate affiliate link
                affiliate_link = generate_amazon_affiliate_link(
                    asin=asin,
                    country_code=country_code,
                    associate_tag=self.associate_tag,
                )

                results.append(AffiliateProduct(
                    product_id=asin,
                    title=title,
                    price=price,
                    currency=currency,
                    affiliate_link=affiliate_link,
                    merchant="Amazon",
                    image_url=image_url,
                    rating=float(rating) if rating else None,
                    review_count=int(review_count) if review_count else None,
                    condition="new",
                    availability=True,
                    source_url=affiliate_link,
                ))

            except Exception as e:
                logger.warning(f"Failed to parse PA-API item: {e}")
                continue

        logger.info(f"PA-API: parsed {len(results)} products")
        return results

    async def generate_affiliate_link(
        self,
        product_id: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> str:
        """
        Generate Amazon affiliate link for a product

        Args:
            product_id: ASIN (Amazon Standard Identification Number)
            campaign_id: Not used for Amazon (tag is used instead)
            tracking_id: Optional sub-tracking ID (appended to tag)
            country_code: Country code for regional Amazon domain

        Returns:
            Amazon affiliate link
        """
        effective_country = country_code or self.country_code

        # Build affiliate link
        link = generate_amazon_affiliate_link(
            asin=product_id,
            country_code=effective_country,
            associate_tag=self.associate_tag,
        )

        # Add sub-tracking if provided (Amazon supports subtag parameter)
        if tracking_id:
            separator = "&" if "?" in link else "?"
            link = f"{link}{separator}ascsubtag={tracking_id}"

        logger.debug(f"Generated Amazon affiliate link: {link}")
        return link

    async def check_link_health(self, affiliate_link: str) -> bool:
        """
        Check if an Amazon affiliate link is still valid

        For Amazon, we mainly check if the ASIN exists.
        Note: Amazon pages always return 200, even for invalid ASINs.
        """
        # Extract ASIN from URL
        import re
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', affiliate_link)

        if not asin_match:
            logger.warning(f"Could not extract ASIN from link: {affiliate_link}")
            return False

        # For now, assume links with valid ASIN format are healthy
        # Full validation would require checking product availability via PA-API
        return True

    def get_product_url(self, asin: str, country_code: Optional[str] = None) -> str:
        """Get direct Amazon product URL (without affiliate tracking)"""
        effective_country = country_code or self.country_code
        domain = AMAZON_DOMAINS.get(effective_country.upper(), "amazon.com")
        return f"https://www.{domain}/dp/{asin}"

    def get_search_url(
        self,
        query: str,
        country_code: Optional[str] = None,
        include_tag: bool = True,
    ) -> str:
        """
        Get Amazon search URL for a query

        Useful for redirecting users to Amazon search with affiliate tag.

        Args:
            query: Search query
            country_code: Country code for regional Amazon domain
            include_tag: Whether to include affiliate tag

        Returns:
            Amazon search URL
        """
        effective_country = country_code or self.country_code
        domain = AMAZON_DOMAINS.get(effective_country.upper(), "amazon.com")

        # URL encode the query
        from urllib.parse import quote_plus
        encoded_query = quote_plus(query)

        base_url = f"https://www.{domain}/s?k={encoded_query}"

        if include_tag:
            country_tags = parse_associate_tags(settings.AMAZON_ASSOCIATE_TAGS)
            tag = country_tags.get(effective_country.upper()) or self.associate_tag
            if tag:
                base_url = f"{base_url}&tag={tag}"

        return base_url


# Export
__all__ = [
    "AmazonAffiliateProvider",
    "generate_amazon_affiliate_link",
    "AMAZON_DOMAINS",
]
