"""
Search Manager
Handles search provider with fallback
"""
from app.core.centralized_logger import get_logger
from typing import List, Optional
from .base import SearchProvider, SearchResult, SearchProviderError

logger = get_logger(__name__)


class SearchManager:
    """Manages search provider"""

    def __init__(self):
        self.provider: Optional[SearchProvider] = None

    def set_provider(self, provider: SearchProvider) -> None:
        """Set the active search provider"""
        self.provider = provider
        logger.info(f"Search provider set to: {provider.get_provider_name()}")

    async def search(
        self,
        query: str,
        intent: Optional[str] = None,
        max_results: int = 10,
        **filters
    ) -> List[SearchResult]:
        """
        Perform search using configured provider

        Args:
            query: Search query
            intent: Intent type
            max_results: Max results to return
            **filters: Additional filters (conversation_history can be passed here)

        Returns:
            List of SearchResult objects
        """
        if not self.provider:
            logger.error("No search provider configured")
            return []

        try:
            results = await self.provider.search(
                query=query,
                intent=intent,
                max_results=max_results,
                **filters
            )
            return results

        except SearchProviderError as e:
            logger.error(f"Search provider error: {e}")
            return []

        except Exception as e:
            logger.error(f"Unexpected search error: {e}")
            return []

    def get_provider_name(self) -> Optional[str]:
        """Get current provider name"""
        if self.provider:
            return self.provider.get_provider_name()
        return None


# Global instance
search_manager = SearchManager()
