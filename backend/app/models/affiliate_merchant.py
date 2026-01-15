"""Affiliate Merchant model"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, Integer
import enum

from app.core.database import Base


class MerchantStatus(str, enum.Enum):
    """Merchant status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class AffiliateMerchant(Base):
    """Affiliate Merchant table"""
    __tablename__ = "affiliate_merchants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # e.g., "eBay"
    network = Column(String(100), nullable=False)  # e.g., "eBay Partner Network"
    deeplink_template = Column(Text, nullable=False)  # URL template with placeholders
    status = Column(SQLEnum(MerchantStatus), default=MerchantStatus.ACTIVE, nullable=False)
    last_health_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AffiliateMerchant {self.name} - {self.network}>"
