# backend/app/models/api_usage_log.py
"""API Usage Log model for cost tracking."""

from sqlalchemy import Column, String, Integer, SmallInteger, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class APIUsageLog(Base):
    """Tracks API call costs and outcomes."""

    __tablename__ = "api_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    api_name = Column(String(50), nullable=False)
    tier = Column(SmallInteger, nullable=False)
    cost_cents = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
