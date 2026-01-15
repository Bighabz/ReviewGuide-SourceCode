"""
Base Affiliate Provider Interface
Defines the contract for all affiliate network providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class AffiliateProduct:
    """Standardized affiliate product structure"""
    product_id: str
    title: str
    price: float
    currency: str
    affiliate_link: str
    merchant: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    condition: str = "new"
    shipping_cost: Optional[float] = None
    availability: bool = True
    source_url: Optional[str] = None


class BaseAffiliateProvider(ABC):
    """Base class for affiliate network providers"""

    @abstractmethod
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
    ) -> List[AffiliateProduct]:
        """
        Search for products in the affiliate network

        Args:
            query: Search query string
            category: Optional category filter
            brand: Optional brand filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Maximum number of results

        Returns:
            List of AffiliateProduct objects
        """
        pass

    @abstractmethod
    async def generate_affiliate_link(
        self,
        product_id: str,
        campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> str:
        """
        Generate affiliate tracking link for a product

        Args:
            product_id: Product identifier
            campaign_id: Campaign identifier for tracking
            tracking_id: Custom tracking identifier (e.g., session_id)

        Returns:
            Affiliate tracking URL
        """
        pass

    @abstractmethod
    async def check_link_health(self, affiliate_link: str) -> bool:
        """
        Check if an affiliate link is still valid and active

        Args:
            affiliate_link: The affiliate URL to check

        Returns:
            True if link is healthy, False otherwise
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the provider"""
        pass
