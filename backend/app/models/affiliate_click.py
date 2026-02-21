"""Affiliate click tracking model"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer

from app.core.database import Base


class AffiliateClick(Base):
    """Tracks affiliate link clicks for analytics"""
    __tablename__ = "affiliate_clicks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=True)
    provider = Column(String(100), nullable=False)
    product_name = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    url = Column(String(2048), nullable=False)
    clicked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AffiliateClick {self.provider} {self.product_name}>"
