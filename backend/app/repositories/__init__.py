"""
Repositories for data access layer
Implements Repository pattern for clean separation of data access logic
"""
from .conversation_repository import ConversationRepository

__all__ = ["ConversationRepository"]
