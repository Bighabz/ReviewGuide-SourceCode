"""Airport Cache Model"""
from sqlalchemy import Column, String, DateTime, Index
from datetime import datetime
from app.core.database import Base


class AirportCache(Base):
    """Cache table for city name -> airport code lookups"""

    __tablename__ = "airport_cache"

    city_name = Column(String(255), primary_key=True)  # Lowercase city name
    airport_code = Column(String(10), nullable=False)  # IATA code (e.g., "JFK")
    airport_name = Column(String(500), nullable=True)  # Full airport name
    country_code = Column(String(10), nullable=True)  # Country code (e.g., "US")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_airport_cache_airport_code', 'airport_code'),
    )

    def __repr__(self):
        return f"<AirportCache(city='{self.city_name}', code='{self.airport_code}')>"
