"""Conversation Message model for individual messages"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, BigInteger, Boolean
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy as sa

from app.core.database import Base


class ConversationMessage(Base):
    """Individual messages in conversations - persistent storage"""
    __tablename__ = "conversation_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # Auto-increment ID
    session_id = Column(String(255), nullable=False, index=True)  # UUID string like "0ac2b93d-180b-4d38-ab3f-56b5ad733dc9"
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)  # Plain text content for simple messages and backward compatibility
    message_metadata = Column(JSONB, nullable=True)  # All message metadata: followups, ui_blocks, next_suggestions, is_suggestion_click, citations, intent, status, etc.
    sequence_number = Column(Integer, nullable=False)  # Order of messages in conversation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<ConversationMessage {self.id} role={self.role}>"

    def to_dict(self):
        """Convert to dictionary format for conversation history"""
        base_dict = {
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

        # Spread all metadata fields into the response (generic approach)
        if self.message_metadata:
            base_dict["message_metadata"] = self.message_metadata

        return base_dict
