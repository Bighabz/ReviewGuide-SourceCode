"""
Mock Travel Providers
For testing and development until real APIs are integrated
"""
from app.core.centralized_logger import get_logger
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from ..base import (
    HotelProvider,
    FlightProvider,
    HotelCard,
    FlightCard,
    TravelAPIError
)
from ..registry import ProviderRegistry

logger = get_logger(__name__)


@ProviderRegistry.register_hotel_provider("mock")
class MockHotelProvider(HotelProvider):
    """
    Mock hotel provider for testing
    Returns realistic-looking mock data
    """

    def get_provider_name(self) -> str:
        return "mock_hotels"

    async def search_hotels(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int = 2,
        rooms: int = 1,
        **filters
    ) -> List[HotelCard]:
        """Return mock hotel data"""

        logger.info(f"Mock Hotel Provider: Searching hotels in {destination}")

        # Mock hotel data
        mock_hotels = [
            HotelCard(
                provider="mock_hotels",
                name=f"Grand {destination} Hotel",
                city=destination,
                country="Country",
                neighborhood="City Center",
                price_nightly=120.0,
                currency="USD",
                rating=4.5,
                rating_count=1250,
                thumbnail_url="https://via.placeholder.com/300x200?text=Grand+Hotel",
                amenities=["WiFi", "Pool", "Gym", "Restaurant", "Bar"],
                distance_to_center="0.5 km",
                cancellation_policy="Free cancellation until 24h before check-in",
                deeplink=f"https://example.com/hotels/grand-{destination.lower()}",
                citations=["https://tripadvisor.com", "https://booking.com"]
            ),
            HotelCard(
                provider="mock_hotels",
                name=f"{destination} Boutique Inn",
                city=destination,
                country="Country",
                neighborhood="Historic District",
                price_nightly=95.0,
                currency="USD",
                rating=4.3,
                rating_count=850,
                thumbnail_url="https://via.placeholder.com/300x200?text=Boutique+Inn",
                amenities=["WiFi", "Breakfast", "Terrace"],
                distance_to_center="1.2 km",
                cancellation_policy="Free cancellation until 48h before check-in",
                deeplink=f"https://example.com/hotels/boutique-{destination.lower()}",
                citations=["https://tripadvisor.com"]
            ),
            HotelCard(
                provider="mock_hotels",
                name=f"Luxury {destination} Resort",
                city=destination,
                country="Country",
                neighborhood="Beachfront",
                price_nightly=250.0,
                currency="USD",
                rating=4.8,
                rating_count=2100,
                thumbnail_url="https://via.placeholder.com/300x200?text=Luxury+Resort",
                amenities=["WiFi", "Pool", "Spa", "Beach Access", "Restaurant", "Bar", "Gym", "Room Service"],
                distance_to_center="5.0 km",
                cancellation_policy="Free cancellation until 7 days before check-in",
                deeplink=f"https://example.com/hotels/luxury-{destination.lower()}",
                citations=["https://tripadvisor.com", "https://booking.com", "https://expedia.com"]
            ),
            HotelCard(
                provider="mock_hotels",
                name=f"Budget {destination} Hostel",
                city=destination,
                country="Country",
                neighborhood="Downtown",
                price_nightly=35.0,
                currency="USD",
                rating=4.0,
                rating_count=450,
                thumbnail_url="https://via.placeholder.com/300x200?text=Budget+Hostel",
                amenities=["WiFi", "Kitchen", "Lounge"],
                distance_to_center="0.8 km",
                cancellation_policy="No refund",
                deeplink=f"https://example.com/hotels/budget-{destination.lower()}",
                citations=["https://hostelworld.com"]
            ),
            HotelCard(
                provider="mock_hotels",
                name=f"{destination} Business Hotel",
                city=destination,
                country="Country",
                neighborhood="Business District",
                price_nightly=150.0,
                currency="USD",
                rating=4.4,
                rating_count=980,
                thumbnail_url="https://via.placeholder.com/300x200?text=Business+Hotel",
                amenities=["WiFi", "Meeting Rooms", "Restaurant", "Gym", "Airport Shuttle"],
                distance_to_center="3.0 km",
                cancellation_policy="Free cancellation until 24h before check-in",
                deeplink=f"https://example.com/hotels/business-{destination.lower()}",
                citations=["https://booking.com"]
            ),
        ]

        # Apply filters if provided
        price_max = filters.get("price_max")
        if price_max:
            mock_hotels = [h for h in mock_hotels if h.price_nightly <= price_max]

        rating_min = filters.get("rating_min")
        if rating_min:
            mock_hotels = [h for h in mock_hotels if h.rating and h.rating >= rating_min]

        return mock_hotels

    async def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """Return mock hotel details"""
        return {
            "hotel_id": hotel_id,
            "description": "A wonderful hotel with great amenities",
            "photos": [],
            "reviews": []
        }


@ProviderRegistry.register_flight_provider("mock")
class MockFlightProvider(FlightProvider):
    """
    Mock flight provider for testing
    Returns realistic-looking mock data
    """

    def get_provider_name(self) -> str:
        return "mock_flights"

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
        """Return mock flight data"""

        logger.info(f"Mock Flight Provider: Searching flights from {origin} to {destination}")

        # Mock flight data
        base_depart = datetime.combine(depart_date, datetime.min.time()).replace(hour=8, minute=0)

        mock_flights = [
            FlightCard(
                provider="mock_flights",
                carrier="United Airlines",
                carrier_code="UA",
                flight_number="UA123",
                origin=origin,
                origin_code="XXX",
                destination=destination,
                destination_code="YYY",
                depart_time=base_depart,
                arrive_time=base_depart + timedelta(hours=5, minutes=30),
                duration_minutes=330,
                stops=0,
                price=450.0,
                currency="USD",
                cabin_class=cabin_class,
                baggage_allowance="1 checked bag",
                deeplink=f"https://example.com/flights/ua123",
                citations=["https://united.com", "https://kayak.com"]
            ),
            FlightCard(
                provider="mock_flights",
                carrier="Delta Air Lines",
                carrier_code="DL",
                flight_number="DL456",
                origin=origin,
                origin_code="XXX",
                destination=destination,
                destination_code="YYY",
                depart_time=base_depart + timedelta(hours=3),
                arrive_time=base_depart + timedelta(hours=9, minutes=15),
                duration_minutes=375,
                stops=1,
                price=380.0,
                currency="USD",
                cabin_class=cabin_class,
                baggage_allowance="1 carry-on",
                deeplink=f"https://example.com/flights/dl456",
                citations=["https://delta.com", "https://kayak.com"]
            ),
            FlightCard(
                provider="mock_flights",
                carrier="American Airlines",
                carrier_code="AA",
                flight_number="AA789",
                origin=origin,
                origin_code="XXX",
                destination=destination,
                destination_code="YYY",
                depart_time=base_depart + timedelta(hours=6),
                arrive_time=base_depart + timedelta(hours=11, minutes=45),
                duration_minutes=345,
                stops=0,
                price=520.0,
                currency="USD",
                cabin_class=cabin_class,
                baggage_allowance="2 checked bags",
                deeplink=f"https://example.com/flights/aa789",
                citations=["https://aa.com", "https://expedia.com"]
            ),
            FlightCard(
                provider="mock_flights",
                carrier="Budget Airways",
                carrier_code="BA",
                flight_number="BA001",
                origin=origin,
                origin_code="XXX",
                destination=destination,
                destination_code="YYY",
                depart_time=base_depart + timedelta(hours=10),
                arrive_time=base_depart + timedelta(hours=17, minutes=30),
                duration_minutes=450,
                stops=2,
                price=280.0,
                currency="USD",
                cabin_class=cabin_class,
                baggage_allowance="Carry-on only",
                deeplink=f"https://example.com/flights/ba001",
                citations=["https://kayak.com"]
            ),
        ]

        # Apply filters
        max_stops = filters.get("max_stops")
        if max_stops is not None:
            mock_flights = [f for f in mock_flights if f.stops <= max_stops]

        price_max = filters.get("price_max")
        if price_max:
            mock_flights = [f for f in mock_flights if f.price <= price_max]

        return mock_flights

    async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Return mock flight details"""
        return {
            "flight_id": flight_id,
            "aircraft_type": "Boeing 737",
            "seat_map": [],
            "amenities": ["WiFi", "In-flight Entertainment"]
        }
