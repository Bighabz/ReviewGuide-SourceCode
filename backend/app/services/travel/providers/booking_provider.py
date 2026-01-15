"""
Booking.com Hotel Provider
Implements hotel search using Booking.com API via RapidAPI

API Documentation:
- RapidAPI Booking: https://rapidapi.com/apidojo/api/booking
- Official Booking.com API: https://developers.booking.com

Features:
- Hotel search by destination
- Real-time availability and pricing
- Affiliate link generation
- Rate limiting and caching
"""
from app.core.centralized_logger import get_logger
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import httpx
from ..base import HotelProvider, HotelCard, TravelAPIError, RateLimitError
from ..registry import ProviderRegistry
from app.core.config import settings

logger = get_logger(__name__)


@ProviderRegistry.register_hotel_provider("booking")
class BookingHotelProvider(HotelProvider):
    """
    Booking.com hotel provider implementation via RapidAPI

    Usage:
        provider = BookingHotelProvider(
            api_key="your_rapidapi_key",
            affiliate_id="your_booking_affiliate_id"
        )
    """

    def __init__(self, api_key: str, affiliate_id: str = "", **kwargs):
        super().__init__(api_key, **kwargs)
        self.affiliate_id = affiliate_id
        self.base_url = "https://booking-com.p.rapidapi.com/v1"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
        }
        self.timeout = kwargs.get("timeout", 30)

    def get_provider_name(self) -> str:
        return "booking"

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
        Search for hotels on Booking.com

        Args:
            destination: City name or destination
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            rooms: Number of rooms
            **filters: price_min, price_max, rating_min, etc.

        Returns:
            List of HotelCard objects
        """
        try:
            logger.info(f"Searching Booking.com: {destination}, {check_in} to {check_out}")

            # Step 1: Search for destination to get dest_id
            dest_id = await self._search_destination(destination)
            if not dest_id:
                logger.warning(f"Could not find destination: {destination}")
                return []

            # Step 2: Search hotels
            hotels = await self._search_hotels_by_dest_id(
                dest_id=dest_id,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                rooms=rooms,
                **filters
            )

            logger.info(f"Found {len(hotels)} hotels on Booking.com")
            return hotels

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Booking.com API rate limit exceeded")
            raise TravelAPIError(f"Booking.com API error: {e}")
        except Exception as e:
            logger.error(f"Booking.com search error: {e}", exc_info=True)
            raise TravelAPIError(f"Booking.com search failed: {e}")

    async def _search_destination(self, destination: str) -> Optional[str]:
        """Search for destination and get dest_id"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/hotels/locations",
                    headers=self.headers,
                    params={
                        "name": destination,
                        "locale": "en-us"
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Return first destination ID (usually the city)
                if data and len(data) > 0:
                    return data[0].get("dest_id")

                return None

        except Exception as e:
            logger.error(f"Destination search error: {e}")
            return None

    async def _search_hotels_by_dest_id(
        self,
        dest_id: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **filters
    ) -> List[HotelCard]:
        """Search hotels by destination ID"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "dest_id": dest_id,
                    "dest_type": "city",
                    "checkin_date": check_in.strftime("%Y-%m-%d"),
                    "checkout_date": check_out.strftime("%Y-%m-%d"),
                    "adults_number": guests,
                    "room_number": rooms,
                    "locale": "en-us",
                    "currency": "USD",
                    "order_by": "popularity",
                    "units": "metric",
                }

                # Add filters
                if "price_max" in filters:
                    params["price_filter_currencycode"] = "USD"

                response = await client.get(
                    f"{self.base_url}/hotels/search",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                return self._parse_hotels(data)

        except Exception as e:
            logger.error(f"Hotel search by dest_id error: {e}")
            raise

    async def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """Get detailed hotel information"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/hotels/data",
                    headers=self.headers,
                    params={
                        "hotel_id": hotel_id,
                        "locale": "en-us"
                    }
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get hotel details error: {e}")
            return {}

    def _parse_hotels(self, api_response: Dict[str, Any]) -> List[HotelCard]:
        """Parse Booking.com API response into HotelCard objects"""
        hotels = []

        try:
            results = api_response.get("result", [])

            for hotel_data in results[:settings.BOOKING_MAX_RESULTS]:  # Use configured limit
                try:
                    hotel = HotelCard(
                        provider="booking",
                        name=hotel_data.get("hotel_name", "Unknown Hotel"),
                        city=hotel_data.get("city", ""),
                        country=hotel_data.get("country_trans", ""),
                        neighborhood=hotel_data.get("district"),
                        price_nightly=float(hotel_data.get("min_total_price", 0)),
                        currency=hotel_data.get("currencycode", "USD"),
                        rating=float(hotel_data.get("review_score", 0)) if hotel_data.get("review_score") else None,
                        rating_count=int(hotel_data.get("review_nr", 0)) if hotel_data.get("review_nr") else None,
                        thumbnail_url=hotel_data.get("max_photo_url") or hotel_data.get("main_photo_url"),
                        amenities=self._extract_amenities(hotel_data),
                        distance_to_center=hotel_data.get("distance", ""),
                        cancellation_policy=self._get_cancellation_policy(hotel_data),
                        deeplink=self._build_deeplink(hotel_data.get("hotel_id")),
                        citations=[self._build_deeplink(hotel_data.get("hotel_id"))]
                    )
                    hotels.append(hotel)

                except Exception as e:
                    logger.warning(f"Failed to parse hotel: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to parse hotels response: {e}")

        return hotels

    def _extract_amenities(self, hotel_data: Dict[str, Any]) -> List[str]:
        """Extract amenities from hotel data"""
        amenities = []

        # Common Booking.com amenities
        if hotel_data.get("has_free_parking"):
            amenities.append("Free Parking")
        if hotel_data.get("has_swimming_pool"):
            amenities.append("Swimming Pool")
        if hotel_data.get("is_free_cancellable"):
            amenities.append("Free Cancellation")

        # Get from facilities if available
        facilities = hotel_data.get("hotel_facilities", "")
        if facilities:
            amenities.extend(facilities.split(",")[:5])  # Limit to 5

        return amenities[:5]  # Max 5 amenities

    def _get_cancellation_policy(self, hotel_data: Dict[str, Any]) -> Optional[str]:
        """Extract cancellation policy"""
        if hotel_data.get("is_free_cancellable"):
            return "Free cancellation"
        return "Check hotel policy"

    def _build_deeplink(self, hotel_id: str) -> str:
        """Build affiliate deep link"""
        if self.affiliate_id:
            return f"https://www.booking.com/hotel/{hotel_id}.html?aid={self.affiliate_id}"
        return f"https://www.booking.com/hotel/{hotel_id}.html"
