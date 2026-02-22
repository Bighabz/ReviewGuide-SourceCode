"""
Booking.com PLP (Product Listing Page) Provider

Generates Booking.com search result page URLs with affiliate links.
Only active when BOOKING_AFFILIATE_ID environment variable is set.
"""
from app.core.centralized_logger import get_logger
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus
from ..base import HotelProvider, HotelCard
from ..registry import ProviderRegistry
from app.core.config import settings

logger = get_logger(__name__)


class BookingPLPLinkGenerator:
    """Generates Booking.com PLP search URLs with affiliate tracking."""

    @staticmethod
    def generate_hotel_search_url(
        destination: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        guests: int = 2,
        rooms: int = 1,
    ) -> str:
        """
        Generate Booking.com hotel search PLP URL.

        Format: https://www.booking.com/searchresults.html?ss={dest}&checkin={date}&checkout={date}&group_adults={n}&aid={AFFILIATE_ID}
        """
        encoded_dest = quote_plus(destination)
        base_url = f"https://www.booking.com/searchresults.html?ss={encoded_dest}"

        if check_in:
            base_url += f"&checkin={check_in.strftime('%Y-%m-%d')}"
        if check_out:
            base_url += f"&checkout={check_out.strftime('%Y-%m-%d')}"

        base_url += f"&group_adults={guests}&no_rooms={rooms}"

        affiliate_id = settings.BOOKING_AFFILIATE_ID
        if affiliate_id:
            base_url += f"&aid={affiliate_id}"

        return base_url


@ProviderRegistry.register_hotel_provider("booking_plp")
class BookingPLPHotelProvider(HotelProvider):
    """
    Booking.com PLP Hotel Provider

    Returns a single HotelCard with a Booking.com PLP search link.
    Only instantiated when BOOKING_AFFILIATE_ID is configured.
    """

    def __init__(self, api_key: str = "plp_provider", **kwargs):
        super().__init__(api_key, **kwargs)
        self.link_generator = BookingPLPLinkGenerator()

    def get_provider_name(self) -> str:
        return "booking_plp"

    async def search_hotels(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int = 2,
        rooms: int = 1,
        **filters,
    ) -> List[HotelCard]:
        """Generate Booking.com hotel search PLP link."""
        logger.info(f"[BookingPLP] Generating hotel search link for: {destination}")

        search_url = self.link_generator.generate_hotel_search_url(
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            rooms=rooms,
        )

        logger.info(f"[BookingPLP] Generated hotel search URL: {search_url}")

        return [
            HotelCard(
                provider="booking_plp",
                name=f"Hotels in {destination}",
                city=destination,
                country="",
                neighborhood=None,
                price_nightly=0,
                currency="USD",
                rating=None,
                rating_count=None,
                thumbnail_url=None,
                amenities=[],
                distance_to_center=None,
                cancellation_policy=None,
                deeplink=search_url,
                citations=[search_url],
            )
        ]

    async def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        return {}
