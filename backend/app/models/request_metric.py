"""Request metric model for RFC §4.2 QoS dashboards"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class RequestMetric(Base):
    """Stores per-request QoS data for dashboard metrics (RFC §4.2)"""
    __tablename__ = "request_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(255), nullable=True)
    intent = Column(String(50), nullable=True)
    total_duration_ms = Column(Integer, nullable=True)
    completeness = Column(String(20), default="full")
    tool_durations = Column(JSONB, default=dict)
    provider_errors = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<RequestMetric request_id={self.request_id} intent={self.intent} duration={self.total_duration_ms}ms>"
