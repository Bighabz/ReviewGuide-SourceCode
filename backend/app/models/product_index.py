"""Product Index model"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.core.database import Base


class ProductIndex(Base):
    """Product Index table for storing normalized product entities"""
    __tablename__ = "product_index"

    entity_key = Column(String(255), primary_key=True)  # Canonical product identifier
    title = Column(String(500), nullable=False)  # Normalized product title
    brand = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    attrs = Column(JSONB, default=dict)  # Product attributes (specs, features)
    source_urls = Column(JSONB, default=list)  # List of source URLs for citations
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ProductIndex {self.entity_key}: {self.title}>"
