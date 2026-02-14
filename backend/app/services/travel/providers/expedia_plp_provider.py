"""
Expedia PLP (Product Listing Page) Provider

Generates Expedia search result page URLs with affiliate links.
This provider returns PLP search links instead of individual hotel/flight cards,
ensuring users see multiple options within the affiliate-eligible flow.

Link Format:
- Hotels: https://www.expedia.com/Hotel-Search?destination=<SEARCH_TERM>&partnerId=1101l413711
- Flights: https://www.expedia.com/Flights-Search?trip=oneway&leg1=from:[ORIGIN],to:[DESTINATION],departure:[DATE]TANYT&passengers=adults:1&options=cabinclass:economy&mode=search&partnerId=1101l413711
"""
from app.core.centralized_logger import get_logger
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from urllib.parse import quote_plus
from ..base import HotelProvider, FlightProvider, HotelCard, FlightCard
from ..registry import ProviderRegistry

logger = get_logger(__name__)

# Expedia Partner ID for affiliate tracking
EXPEDIA_PARTNER_ID = "1101l413711"


class ExpediaPLPLinkGenerator:
    """
    Generates Expedia PLP (Product Listing Page) search URLs with affiliate tracking.
    """

    @staticmethod
    def generate_hotel_search_url(
        destination: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        guests: int = 2,
        rooms: int = 1
    ) -> str:
        """
        Generate Expedia hotel search PLP URL.

        Format: https://www.expedia.com/Hotel-Search?destination=<SEARCH_TERM>&partnerId=1101l413711

        Args:
            destination: City or hotel name to search
            check_in: Check-in date (optional)
            check_out: Check-out date (optional)
            guests: Number of guests
            rooms: Number of rooms

        Returns:
            Expedia hotel search URL with affiliate partner ID
        """
        # URL encode the destination
        encoded_destination = quote_plus(destination)

        # Build base URL
        base_url = f"https://www.expedia.com/Hotel-Search?destination={encoded_destination}"

        # Add dates if provided
        if check_in:
            base_url += f"&startDate={check_in.strftime('%Y-%m-%d')}"
        if check_out:
            base_url += f"&endDate={check_out.strftime('%Y-%m-%d')}"

        # Add guests and rooms
        if guests:
            base_url += f"&adults={guests}"
        if rooms:
            base_url += f"&rooms={rooms}"

        # Add affiliate partner ID
        base_url += f"&partnerId={EXPEDIA_PARTNER_ID}"

        return base_url

    @staticmethod
    def generate_flight_search_url(
        origin: str,
        destination: str,
        departure_date: Optional[date] = None,
        return_date: Optional[date] = None,
        passengers: int = 1,
        cabin_class: str = "economy"
    ) -> str:
        """
        Generate Expedia flight search PLP URL.

        Format (one-way):
        https://www.expedia.com/Flights-Search?trip=oneway&leg1=from:[ORIGIN],to:[DESTINATION],departure:[DATE]TANYT&passengers=adults:1&options=cabinclass:economy&mode=search&partnerId=1101l413711

        Format (round-trip):
        https://www.expedia.com/Flights-Search?trip=roundtrip&leg1=from:[ORIGIN],to:[DESTINATION],departure:[DATE]TANYT&leg2=from:[DESTINATION],to:[ORIGIN],departure:[RETURN_DATE]TANYT&passengers=adults:1&options=cabinclass:economy&mode=search&partnerId=1101l413711

        Args:
            origin: Origin city or airport code
            destination: Destination city or airport code
            departure_date: Departure date (uses today + 10 days if not provided)
            return_date: Return date (None for one-way)
            passengers: Number of passengers
            cabin_class: Cabin class (economy, premium_economy, business, first)

        Returns:
            Expedia flight search URL with affiliate partner ID
        """
        # URL encode origin and destination
        encoded_origin = quote_plus(origin)
        encoded_destination = quote_plus(destination)

        # Use today + 10 days if departure date not provided
        if not departure_date:
            departure_date = date.today() + timedelta(days=10)

        departure_str = departure_date.strftime('%Y-%m-%d')

        # Map cabin class to Expedia format
        cabin_map = {
            "economy": "economy",
            "premium_economy": "premiumeconomy",
            "business": "business",
            "first": "first"
        }
        expedia_cabin = cabin_map.get(cabin_class.lower(), "economy")

        # Determine trip type
        if return_date:
            trip_type = "roundtrip"
            return_str = return_date.strftime('%Y-%m-%d')
            legs = (
                f"leg1=from:{encoded_origin},to:{encoded_destination},departure:{departure_str}TANYT"
                f"&leg2=from:{encoded_destination},to:{encoded_origin},departure:{return_str}TANYT"
            )
        else:
            trip_type = "oneway"
            legs = f"leg1=from:{encoded_origin},to:{encoded_destination},departure:{departure_str}TANYT"

        # Build full URL
        url = (
            f"https://www.expedia.com/Flights-Search?"
            f"trip={trip_type}&{legs}"
            f"&passengers=adults:{passengers}"
            f"&options=cabinclass:{expedia_cabin}"
            f"&mode=search"
            f"&partnerId={EXPEDIA_PARTNER_ID}"
        )

        return url


    @staticmethod
    def generate_car_rental_search_url(
        location: str,
        pickup_date: Optional[date] = None,
        dropoff_date: Optional[date] = None,
        pickup_time: str = "1000AM",
        dropoff_time: str = "1000AM"
    ) -> str:
        """
        Generate Expedia car rental search PLP URL.

        Format:
        https://www.expedia.com/carsearch?locn=<LOCATION>&date1=MM/DD/YYYY&time1=1000AM&date2=MM/DD/YYYY&time2=1000AM&partnerId=...

        Args:
            location: Pickup city or location
            pickup_date: Pickup date (uses today + 30 days if not provided)
            dropoff_date: Drop-off date (uses pickup + 5 days if not provided)
            pickup_time: Pickup time in Expedia format (default 10:00 AM)
            dropoff_time: Drop-off time in Expedia format (default 10:00 AM)

        Returns:
            Expedia car rental search URL with affiliate partner ID
        """
        encoded_location = quote_plus(location)

        if not pickup_date:
            pickup_date = date.today() + timedelta(days=30)
        if not dropoff_date:
            dropoff_date = pickup_date + timedelta(days=5)

        pickup_str = pickup_date.strftime('%m/%d/%Y')
        dropoff_str = dropoff_date.strftime('%m/%d/%Y')

        url = (
            f"https://www.expedia.com/carsearch?"
            f"locn={encoded_location}"
            f"&date1={pickup_str}&time1={pickup_time}"
            f"&date2={dropoff_str}&time2={dropoff_time}"
            f"&partnerId={EXPEDIA_PARTNER_ID}"
        )

        return url


@ProviderRegistry.register_hotel_provider("expedia_plp")
class ExpediaPLPHotelProvider(HotelProvider):
    """
    Expedia PLP Hotel Provider

    Returns a single HotelCard with a PLP search link instead of individual hotel results.
    This ensures users see multiple options on Expedia's search results page.
    """

    def __init__(self, api_key: str = "plp_provider", **kwargs):
        super().__init__(api_key, **kwargs)
        self.link_generator = ExpediaPLPLinkGenerator()

    def get_provider_name(self) -> str:
        return "expedia_plp"

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
        Generate Expedia hotel search PLP link.

        Returns a single HotelCard containing the PLP search URL.
        """
        logger.info(f"[ExpediaPLP] Generating hotel search link for: {destination}")

        # Generate the PLP search URL
        search_url = self.link_generator.generate_hotel_search_url(
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            rooms=rooms
        )

        logger.info(f"[ExpediaPLP] Generated hotel search URL: {search_url}")

        # Return a single HotelCard with the search link
        return [HotelCard(
            provider="expedia_plp",
            name=f"Hotels in {destination}",
            city=destination,
            country="",  # Not needed for PLP
            neighborhood=None,
            price_nightly=0,  # Price shown on Expedia
            currency="USD",
            rating=None,
            rating_count=None,
            thumbnail_url=None,
            amenities=[],
            distance_to_center=None,
            cancellation_policy=None,
            deeplink=search_url,
            citations=[search_url]
        )]

    async def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """Not applicable for PLP provider"""
        return {}


@ProviderRegistry.register_flight_provider("expedia_plp")
class ExpediaPLPFlightProvider(FlightProvider):
    """
    Expedia PLP Flight Provider

    Returns a single FlightCard with a PLP search link instead of individual flight results.
    This ensures users see multiple options on Expedia's search results page.
    """

    def __init__(self, api_key: str = "plp_provider", **kwargs):
        super().__init__(api_key, **kwargs)
        self.link_generator = ExpediaPLPLinkGenerator()

    def get_provider_name(self) -> str:
        return "expedia_plp"

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
        Generate Expedia flight search PLP link.

        Returns a single FlightCard containing the PLP search URL.
        """
        logger.info(f"[ExpediaPLP] Generating flight search link: {origin} -> {destination}")

        # Generate the PLP search URL
        search_url = self.link_generator.generate_flight_search_url(
            origin=origin,
            destination=destination,
            departure_date=depart_date,
            return_date=return_date,
            passengers=passengers,
            cabin_class=cabin_class
        )

        logger.info(f"[ExpediaPLP] Generated flight search URL: {search_url}")

        # Create placeholder datetime for the FlightCard
        depart_datetime = datetime.combine(depart_date, datetime.min.time()) if depart_date else datetime.now()
        arrive_datetime = depart_datetime  # Placeholder

        # Return a single FlightCard with the search link
        return [FlightCard(
            provider="expedia_plp",
            carrier="Multiple Airlines",
            carrier_code="",
            flight_number="",
            origin=origin,
            origin_code=origin if len(origin) == 3 else "",
            destination=destination,
            destination_code=destination if len(destination) == 3 else "",
            depart_time=depart_datetime,
            arrive_time=arrive_datetime,
            duration_minutes=0,  # Shown on Expedia
            stops=0,
            price=0,  # Price shown on Expedia
            currency="USD",
            cabin_class=cabin_class,
            baggage_allowance=None,
            deeplink=search_url,
            citations=[search_url]
        )]

    async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Not applicable for PLP provider"""
        return {}
