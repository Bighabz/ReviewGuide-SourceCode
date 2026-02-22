"""
Affiliate Provider Registry - Plugin System
Automatically discovers and registers affiliate providers based on decorators.
No code changes needed to add/remove providers.
"""
from app.core.centralized_logger import get_logger
from typing import Dict, List, Type, Optional

from .base import BaseAffiliateProvider

logger = get_logger(__name__)


class AffiliateProviderRegistry:
    """
    Registry for affiliate providers.
    Providers self-register using the @register decorator.
    """

    _providers: Dict[str, dict] = {}

    @classmethod
    def register(
        cls,
        name: str,
        required_env_vars: Optional[List[str]] = None,
        optional_env_vars: Optional[List[str]] = None,
    ):
        """
        Decorator to register an affiliate provider class.

        Usage:
            @AffiliateProviderRegistry.register("ebay", required_env_vars=[], optional_env_vars=["EBAY_APP_ID"])
            class EbayAffiliateProvider(BaseAffiliateProvider):
                pass
        """
        def decorator(provider_class: Type[BaseAffiliateProvider]):
            cls._providers[name] = {
                "class": provider_class,
                "required_env_vars": required_env_vars or [],
                "optional_env_vars": optional_env_vars or [],
            }
            logger.debug(f"Registered affiliate provider class: {name}")
            return provider_class
        return decorator

    @classmethod
    def get_provider_class(cls, name: str) -> Optional[Type[BaseAffiliateProvider]]:
        """Get affiliate provider class by name"""
        entry = cls._providers.get(name)
        return entry["class"] if entry else None

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered affiliate provider names"""
        return list(cls._providers.keys())

    @classmethod
    def list_provider_info(cls) -> Dict[str, dict]:
        """List all registered providers with their env var requirements"""
        return {
            name: {
                "required_env_vars": info["required_env_vars"],
                "optional_env_vars": info["optional_env_vars"],
            }
            for name, info in cls._providers.items()
        }
