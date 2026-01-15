"""
Search Provider Registry
Auto-discovery and registration system
"""
from app.core.centralized_logger import get_logger
from typing import Dict, Type, Optional, Any
from .base import SearchProvider

logger = get_logger(__name__)


class SearchProviderRegistry:
    """Registry for search providers"""

    _providers: Dict[str, Type[SearchProvider]] = {}

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a search provider

        Usage:
            @SearchProviderRegistry.register("perplexity")
            class PerplexityProvider(SearchProvider):
                pass
        """
        def decorator(provider_class: Type[SearchProvider]):
            cls._providers[name] = provider_class
            logger.debug(f"Registered search provider: {name}")
            return provider_class
        return decorator

    @classmethod
    def get_provider(cls, name: str) -> Optional[Type[SearchProvider]]:
        """Get provider class by name"""
        return cls._providers.get(name)

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider names"""
        return list(cls._providers.keys())

    @classmethod
    def create_provider(cls, name: str, config: Dict[str, Any]) -> Optional[SearchProvider]:
        """
        Create provider instance from configuration

        Args:
            name: Provider name
            config: Provider configuration

        Returns:
            Provider instance or None
        """
        provider_class = cls.get_provider(name)
        if not provider_class:
            logger.warning(f"Search provider '{name}' not found")
            return None

        try:
            api_key = config.get("api_key")
            if not api_key:
                logger.warning(f"Search provider '{name}' missing api_key")
                return None

            # Remove api_key from config to avoid passing it twice
            config_without_key = {k: v for k, v in config.items() if k != "api_key"}

            instance = provider_class(api_key=api_key, **config_without_key)
            logger.info(f"Created search provider: {name}")
            return instance

        except Exception as e:
            logger.error(f"Failed to create search provider '{name}': {e}")
            return None
