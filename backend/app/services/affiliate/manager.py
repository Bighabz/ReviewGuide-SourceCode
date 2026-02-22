"""
Affiliate Manager
Manages multiple affiliate providers and handles provider selection/fallback
"""
from app.core.centralized_logger import get_logger
from typing import List, Dict, Any, Optional
from app.services.affiliate.base import BaseAffiliateProvider, AffiliateProduct
from app.core.config import settings

logger = get_logger(__name__)


class MockAffiliateProvider(BaseAffiliateProvider):
    """Mock provider for testing without real API calls - generates realistic product data"""

    def get_provider_name(self) -> str:
        return "MockAffiliate"

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
    ) -> List[AffiliateProduct]:
        """Return realistic mock products based on query and filters"""
        logger.info(f"MockAffiliate: Searching for '{query}' (category={category}, budget=${max_price}, limit={limit})")

        # Determine base price range from category or max_price
        if max_price:
            # Generate products within budget
            base_price = max_price * 0.6  # Start at 60% of budget
            price_increment = (max_price * 0.4) / max(limit - 1, 1)  # Spread remaining 40%
        elif category == "laptop":
            base_price = 800
            price_increment = 100
        elif category == "phone" or category == "smartphone":
            base_price = 600
            price_increment = 80
        else:
            base_price = 100
            price_increment = 50

        # Generate realistic brand names based on category
        brands = self._get_realistic_brands(category)

        # Generate mock products
        products = []
        for i in range(min(limit, 6)):  # Return up to 6 products
            product_brand = brands[i % len(brands)]
            model_num = i + 1

            # Calculate price
            price = base_price + (i * price_increment)
            if max_price and price > max_price:
                price = max_price - (i * 10)  # Stay under budget

            # Generate realistic title
            title = self._generate_title(query, product_brand, model_num, category)

            products.append(
                AffiliateProduct(
                    product_id=f"mock_{category}_{i+1}",
                    title=title,
                    price=round(price, 2),
                    currency="USD",
                    affiliate_link=f"https://example.com/aff/{category}/{i+1}?ref=reviewguide",
                    merchant=f"{product_brand} Store",
                    image_url=f"https://via.placeholder.com/400x300?text={product_brand}+{category}",
                    rating=round(4.0 + (i * 0.15), 1),
                    review_count=150 + (i * 75),
                    condition="new",
                    availability=True,
                )
            )

        logger.info(f"MockAffiliate: Generated {len(products)} realistic products")
        return products

    def _get_realistic_brands(self, category: Optional[str]) -> List[str]:
        """Get realistic brand names for a category"""
        brand_map = {
            "laptop": ["Dell", "HP", "ASUS", "Lenovo", "Acer", "MSI"],
            "phone": ["Apple", "Samsung", "Google", "OnePlus", "Motorola", "Xiaomi"],
            "smartphone": ["Apple", "Samsung", "Google", "OnePlus", "Motorola", "Xiaomi"],
            "headphones": ["Sony", "Bose", "Apple", "Sennheiser", "JBL", "Audio-Technica"],
            "camera": ["Canon", "Nikon", "Sony", "Fujifilm", "Panasonic", "Olympus"],
        }
        return brand_map.get(category, ["BrandA", "BrandB", "BrandC", "BrandD", "BrandE", "BrandF"])

    def _generate_title(self, query: str, brand: str, model_num: int, category: Optional[str]) -> str:
        """Generate a realistic product title"""
        if category == "laptop":
            models = ["Pro", "Elite", "Aspire", "IdeaPad", "Pavilion", "VivoBook"]
            model = models[model_num % len(models)]
            return f"{brand} {model} 15.6\" Gaming Laptop - Intel i7, 16GB RAM, RTX 4050"
        elif category == "phone" or category == "smartphone":
            return f"{brand} Smartphone 5G - 128GB, 6.5\" Display, Triple Camera"
        else:
            return f"{brand} {query.title()} - Model {model_num}"

    async def generate_affiliate_link(
        self,
        product_id: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> str:
        """Return mock affiliate link"""
        return f"https://example.com/product/{product_id}?aff=123&tracking={tracking_id}"

    async def check_link_health(self, affiliate_link: str) -> bool:
        """Mock links are always healthy"""
        return True


class AffiliateManager:
    """
    Manages multiple affiliate network providers

    Features:
    - Provider registration and selection
    - Automatic fallback between providers
    - Unified interface for all affiliate operations
    - Provider health monitoring
    """

    def __init__(self):
        self.providers: Dict[str, BaseAffiliateProvider] = {}
        self.primary_provider: Optional[str] = None

        # Initialize providers based on configuration
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize affiliate providers via auto-discovery registry"""
        from app.services.affiliate.loader import setup_affiliate_providers

        logger.info("Initializing affiliate providers")

        # Check if we should use mock provider
        if settings.USE_MOCK_AFFILIATE:
            logger.info("Using mock affiliate provider (USE_MOCK_AFFILIATE=True)")
            mock_provider = MockAffiliateProvider()
            self.register_provider("mock", mock_provider)
            self.primary_provider = "mock"

        # Auto-discover, validate, and register all decorated providers
        setup_affiliate_providers(self)

        # Set primary to first real provider if not already set
        if not self.primary_provider:
            for name in self.providers:
                if name != "mock":
                    self.primary_provider = name
                    break

        # Fallback to mock if no providers configured
        if not self.providers:
            logger.warning(
                "No affiliate providers configured. Using mock provider as fallback."
            )
            mock_provider = MockAffiliateProvider()
            self.register_provider("mock", mock_provider)
            self.primary_provider = "mock"

        logger.info(
            f"Affiliate manager initialized with providers: {list(self.providers.keys())}"
        )
        logger.info(f"Primary provider: {self.primary_provider}")

    def register_provider(self, name: str, provider: BaseAffiliateProvider):
        """Register a new affiliate provider"""
        self.providers[name] = provider
        logger.info(f"Registered affiliate provider: {name}")

    def get_provider(self, name: Optional[str] = None) -> Optional[BaseAffiliateProvider]:
        """
        Get a specific provider or the primary provider

        Args:
            name: Provider name (optional, defaults to primary)

        Returns:
            Provider instance or None
        """
        if name:
            return self.providers.get(name)
        elif self.primary_provider:
            return self.providers.get(self.primary_provider)
        return None

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
        provider_name: Optional[str] = None,
    ) -> List[AffiliateProduct]:
        """
        Search for products across affiliate networks

        Args:
            query: Search query
            category: Optional category filter
            brand: Optional brand filter
            min_price: Minimum price
            max_price: Maximum price
            limit: Maximum results
            provider_name: Specific provider to use (optional)

        Returns:
            List of AffiliateProduct objects
        """
        # Get provider
        provider = self.get_provider(provider_name)

        if not provider:
            logger.error("No affiliate provider available")
            return []

        try:
            products = await provider.search_products(
                query=query,
                category=category,
                brand=brand,
                min_price=min_price,
                max_price=max_price,
                limit=limit,
            )

            logger.info(
                f"Found {len(products)} products via {provider.get_provider_name()}"
            )
            return products

        except Exception as e:
            logger.error(
                f"Error searching products with {provider.get_provider_name()}: {e}",
                exc_info=True,
            )

            # Try fallback providers
            return await self._search_with_fallback(
                query, category, brand, min_price, max_price, limit, provider_name
            )

    async def _search_with_fallback(
        self,
        query: str,
        category: Optional[str],
        brand: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        limit: int,
        failed_provider: Optional[str],
    ) -> List[AffiliateProduct]:
        """Try other providers if primary fails"""
        for name, provider in self.providers.items():
            # Skip the failed provider
            if name == failed_provider:
                continue

            try:
                logger.info(f"Trying fallback provider: {name}")
                products = await provider.search_products(
                    query=query,
                    category=category,
                    brand=brand,
                    min_price=min_price,
                    max_price=max_price,
                    limit=limit,
                )

                if products:
                    logger.info(f"Fallback successful with {name}")
                    return products

            except Exception as e:
                logger.warning(f"Fallback provider {name} also failed: {e}")
                continue

        logger.error("All affiliate providers failed")
        return []

    async def generate_affiliate_link(
        self,
        product_id: str,
        provider_name: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate affiliate link for a product

        Args:
            product_id: Product identifier
            provider_name: Which provider to use
            campaign_id: Campaign ID
            tracking_id: Tracking identifier (e.g., session_id)

        Returns:
            Affiliate link or None
        """
        provider = self.get_provider(provider_name)

        if not provider:
            logger.error(f"Provider '{provider_name}' not found")
            return None

        try:
            link = await provider.generate_affiliate_link(
                product_id=product_id,
                campaign_id=campaign_id,
                tracking_id=tracking_id,
            )
            return link

        except Exception as e:
            logger.error(
                f"Error generating affiliate link with {provider_name}: {e}",
                exc_info=True,
            )
            return None

    async def check_link_health(
        self, affiliate_link: str, provider_name: Optional[str] = None
    ) -> bool:
        """
        Check if an affiliate link is still valid

        Args:
            affiliate_link: The link to check
            provider_name: Optional provider name

        Returns:
            True if healthy, False otherwise
        """
        provider = self.get_provider(provider_name)

        if not provider:
            logger.warning("No provider specified for link health check")
            return False

        try:
            is_healthy = await provider.check_link_health(affiliate_link)
            return is_healthy

        except Exception as e:
            logger.error(f"Link health check failed: {e}")
            return False

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return list(self.providers.keys())

    async def search_amazon_products(
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
        Search for products specifically on Amazon with country code support

        This is a convenience method that:
        1. Uses the Amazon provider directly
        2. Supports country-specific domains and affiliate tags
        3. Falls back gracefully if Amazon provider is not available

        Args:
            query: Search query
            category: Optional category filter
            brand: Optional brand filter
            min_price: Minimum price
            max_price: Maximum price
            limit: Maximum results
            country_code: Country code for regional Amazon (US, UK, DE, etc.)

        Returns:
            List of AffiliateProduct objects with Amazon affiliate links
        """
        amazon_provider = self.providers.get("amazon")

        if not amazon_provider:
            logger.warning("Amazon provider not available")
            return []

        try:
            # Amazon provider has extended search_products with country_code
            from app.services.affiliate.providers.amazon_provider import AmazonAffiliateProvider
            if isinstance(amazon_provider, AmazonAffiliateProvider):
                products = await amazon_provider.search_products(
                    query=query,
                    category=category,
                    brand=brand,
                    min_price=min_price,
                    max_price=max_price,
                    limit=limit,
                    country_code=country_code,
                )
            else:
                # Fallback for base provider interface
                products = await amazon_provider.search_products(
                    query=query,
                    category=category,
                    brand=brand,
                    min_price=min_price,
                    max_price=max_price,
                    limit=limit,
                )

            logger.info(f"Amazon search found {len(products)} products for '{query}'")
            return products

        except Exception as e:
            logger.error(f"Error searching Amazon products: {e}", exc_info=True)
            return []

    def get_amazon_search_url(
        self,
        query: str,
        country_code: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get Amazon search URL for redirecting users

        Useful when you want to send users directly to Amazon search
        with your affiliate tag embedded.

        Args:
            query: Search query
            country_code: Country code for regional Amazon

        Returns:
            Amazon search URL with affiliate tag, or None if not available
        """
        amazon_provider = self.providers.get("amazon")

        from app.services.affiliate.providers.amazon_provider import AmazonAffiliateProvider
        if not amazon_provider or not isinstance(amazon_provider, AmazonAffiliateProvider):
            logger.warning("Amazon provider not available for search URL")
            return None

        return amazon_provider.get_search_url(query, country_code)


# Create global affiliate manager instance
affiliate_manager = AffiliateManager()

# Export
__all__ = ["affiliate_manager", "AffiliateManager", "AffiliateProduct"]
