"""
Search Services Module
Modular search provider system
"""
from .base import SearchProvider, SearchResult
from .manager import search_manager

__all__ = [
    "SearchProvider",
    "SearchResult",
    "search_manager",
]
