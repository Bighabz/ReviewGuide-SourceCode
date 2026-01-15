"""Affiliate Link model"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, Integer

from app.core.database import Base


class AffiliateLink(Base):
    """Affiliate Link table for mapping products to merchant links"""
    __tablename__ = "affiliate_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_key = Column(String(255), nullable=False, index=True)  # Normalized product identifier
    product_id = Column(String(255), nullable=False)  # Provider's product ID
    title = Column(String(500), nullable=False)  # Product title
    deeplink = Column(Text, nullable=False)  # Full affiliate URL with tracking
    merchant_name = Column(String(255), nullable=False)  # Merchant name (e.g., "eBay", "Amazon")
    price = Column(Float, nullable=True)  # Product price
    currency = Column(String(10), default="USD", nullable=False)  # Currency code
    image_url = Column(Text, nullable=True)  # Product image URL
    rating = Column(Float, nullable=True)  # Product rating (0-5)
    review_count = Column(Integer, nullable=True)  # Number of reviews
    healthy = Column(Boolean, default=True, nullable=False)  # Link health status
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AffiliateLink {self.entity_key}: {self.title}>"
