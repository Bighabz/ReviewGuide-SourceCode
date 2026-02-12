"""User model"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Boolean

from app.core.database import Base


class User(Base):
    """User table"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    locale = Column(String(10), default="en", nullable=False)
    extended_search_enabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
