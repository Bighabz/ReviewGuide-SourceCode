"""
Base interfaces for travel providers
Define abstract classes that all hotel and flight providers must implement
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date


# Data Models
class TravelCard(BaseModel):
    """Base class for travel-related cards"""
    provider: str
    deeplink: str
    citations: List[str] = []


class HotelCard(TravelCard):
    """Standardized hotel card format"""
    name: str
    neighborhood: Optional[str] = None
    city: str
    country: str
    price_nightly: float
    currency: str = "USD"
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    amenities: List[str] = []
    distance_to_center: Optional[str] = None
    cancellation_policy: Optional[str] = None


class FlightCard(TravelCard):
    """Standardized flight card format"""
    carrier: str
    carrier_code: str
    flight_number: str
    origin: str
    origin_code: str
    destination: str
    destination_code: str
    depart_time: datetime
    arrive_time: datetime
    duration_minutes: int
    stops: int
    price: float
    currency: str = "USD"
    cabin_class: str = "economy"
    baggage_allowance: Optional[str] = None


# Abstract Provider Interfaces
class HotelProvider(ABC):
    """
    Abstract base class for hotel providers
    Implement this interface for: Booking.com, Expedia, Hotels.com, etc.
    """

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def search_hotels(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int = 2,
        rooms: int = 1,
        **filters
    ) -> List[HotelCard]:
        """
        Search for hotels

        Args:
            destination: City or destination name
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            rooms: Number of rooms
            **filters: Additional filters (price_min, price_max, rating_min, amenities, etc.)

        Returns:
            List of HotelCard objects

        Raises:
            TravelAPIError: If the API call fails
        """
        pass

    @abstractmethod
    async def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific hotel"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'booking', 'expedia')"""
        pass


class FlightProvider(ABC):
    """
    Abstract base class for flight providers
    Implement this interface for: Skyscanner, Amadeus, Kiwi.com, etc.
    """

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        return_date: Optional[date] = None,
        passengers: int = 1,
        cabin_class: str = "economy",
        **filters
    ) -> List[FlightCard]:
        """
        Search for flights

        Args:
            origin: Origin airport code or city
            destination: Destination airport code or city
            depart_date: Departure date
            return_date: Return date (None for one-way)
            passengers: Number of passengers
            cabin_class: Cabin class (economy, premium_economy, business, first)
            **filters: Additional filters (max_stops, airlines, price_max, etc.)

        Returns:
            List of FlightCard objects

        Raises:
            TravelAPIError: If the API call fails
        """
        pass

    @abstractmethod
    async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific flight"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'skyscanner', 'amadeus')"""
        pass


# Custom Exceptions
class TravelAPIError(Exception):
    """Base exception for travel API errors"""
    pass


class ProviderNotAvailableError(TravelAPIError):
    """Raised when a provider is not configured or available"""
    pass


class RateLimitError(TravelAPIError):
    """Raised when rate limit is exceeded"""
    pass


class InvalidSearchError(TravelAPIError):
    """Raised when search parameters are invalid"""
    pass
