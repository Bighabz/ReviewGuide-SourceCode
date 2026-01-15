"""Session model"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer

from app.core.database import Base


class Session(Base):
    """Session table for tracking user sessions"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    country_code = Column(String(2), nullable=True, index=True)  # ISO 3166-1 alpha-2 country code
    meta = Column(JSON, default=dict)  # Additional metadata (user agent, IP, etc.)

    def __repr__(self):
        return f"<Session {self.id} for User {self.user_id}>"
