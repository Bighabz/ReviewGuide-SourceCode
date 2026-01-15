"""
Base Search Provider Interface
Abstract class that all search providers must implement
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SearchResult(BaseModel):
    """Standardized search result format"""
    url: str
    title: str
    snippet: str
    source_rank: int
    freshness: str = "recent"
    authority_score: int = 5


class SearchProvider(ABC):
    """
    Abstract base class for search providers
    Implement this for: Perplexity, Tavily, Bing, SerpAPI, etc.
    """

    def __init__(self, api_key: str, **config):
        self.api_key = api_key
        self.config = config

    @abstractmethod
    async def search(
        self,
        query: str,
        intent: Optional[str] = None,
        max_results: int = 10,
        include_history: bool = False,
        **filters
    ) -> List[SearchResult]:
        """
        Perform search

        Args:
            query: Search query
            intent: Intent type (product, travel, general, etc.)
            max_results: Maximum number of results
            include_history: If True, provider should include conversation history for context
            **filters: Provider-specific filters (e.g., conversation_history when include_history=True)

        Returns:
            List of SearchResult objects
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name"""
        pass


class SearchProviderError(Exception):
    """Base exception for search provider errors"""
    pass
