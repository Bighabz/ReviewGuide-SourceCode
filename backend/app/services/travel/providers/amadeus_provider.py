"""
Amadeus Travel Provider
Implements both hotel and flight search using Amadeus Self-Service APIs

API Documentation:
- Hotels: https://developers.amadeus.com/self-service/category/hotels
- Flights: https://developers.amadeus.com/self-service/category/flights

Features:
- Hotel search by city/destination
- Flight search (one-way and round-trip)
- OAuth2 authentication
- Rate limiting and error handling
"""
from app.core.centralized_logger import get_logger
import re
import json
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from amadeus import Client, ResponseError

from ..base import (
    HotelProvider, FlightProvider,
    HotelCard, FlightCard,
    TravelAPIError, RateLimitError
)
from ..registry import ProviderRegistry
from app.core.config import settings

logger = get_logger(__name__)

# ANSI color codes for yellow
YELLOW = '\033[93m'
RESET = '\033[0m'

def log_api_call(api_name: str, input_data: Dict[str, Any], output_data: Any = None, error: Exception = None):
    """Log Amadeus API calls with yellow color"""
    logger.info(f"{YELLOW}{'='*80}{RESET}")
    logger.info(f"{YELLOW}AMADEUS API: {api_name}{RESET}")
    logger.info(f"{YELLOW}{'='*80}{RESET}")

    # Log input
    logger.info(f"{YELLOW}INPUT:{RESET}")
    for key, value in input_data.items():
        logger.info(f"{YELLOW}  {key}: {value}{RESET}")

    # Log output or error
    if error:
        logger.info(f"{YELLOW}ERROR: {error}{RESET}")
    elif output_data is not None:
        logger.info(f"{YELLOW}OUTPUT:{RESET}")
        if hasattr(output_data, 'data'):
            data_len = len(output_data.data) if hasattr(output_data.data, '__len__') else 1
            logger.info(f"{YELLOW}  Results: {data_len} items{RESET}")
            if data_len > 0 and hasattr(output_data.data, '__getitem__'):
                logger.info(f"{YELLOW}  Sample: {json.dumps(output_data.data[0] if isinstance(output_data.data, list) else output_data.data, default=str)}{RESET}")
        else:
            logger.info(f"{YELLOW}  {output_data}{RESET}")

    logger.info(f"{YELLOW}{'='*80}{RESET}")


@ProviderRegistry.register_hotel_provider("amadeus")
class AmadeusHotelProvider(HotelProvider):
    """
    Amadeus hotel provider implementation

    Usage:
        provider = AmadeusHotelProvider(
            api_key="your_amadeus_api_key",
            api_secret="your_amadeus_api_secret"
        )
    """

    def __init__(self, api_key: str, api_secret: str = "", **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_secret = api_secret
        self.client = Client(
            client_id=api_key,
            client_secret=api_secret
        )
        self.timeout = kwargs.get("timeout", 30)

    def get_provider_name(self) -> str:
        return "amadeus"

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
        Search for hotels using Amadeus Hotels API (2-step process)

        Step 1: Get hotel IDs in the city using /v1/reference-data/locations/hotels/by-city
        Step 2: Get offers for those hotels using /v3/shopping/hotel-offers

        Args:
            destination: City name or IATA city code (e.g., "Bangkok", "BKK")
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            rooms: Number of rooms
            **filters: Additional filters (amenities, price_max, rating_min, etc.)

        Returns:
            List of HotelCard objects
        """
        try:
            logger.info(f"Amadeus hotel search: {destination}, {check_in} to {check_out}")

            # Step 1: Get city code
            city_code = await self._get_city_code(destination)
            if not city_code:
                logger.warning(f"Could not find city code for: {destination}")
                return []

            # Step 2: Get hotel IDs in this city
            try:
                hotel_by_city_input = {"cityCode": city_code}
                log_api_call("Hotels by City", hotel_by_city_input)

                hotels_response = self.client.reference_data.locations.hotels.by_city.get(
                    cityCode=city_code
                )

                log_api_call("Hotels by City", hotel_by_city_input, output_data=hotels_response)

                if not hasattr(hotels_response, 'data') or not hotels_response.data:
                    logger.info(f"No hotels found in city: {city_code}")
                    return []

                # Get hotel IDs (limit to configured max for performance)
                hotel_ids = [hotel['hotelId'] for hotel in hotels_response.data[:settings.AMADEUS_MAX_HOTEL_RESULTS]]
                logger.info(f"Found {len(hotel_ids)} hotels in {city_code}")

            except ResponseError as error:
                log_api_call("Hotels by City", {"cityCode": city_code}, error=error)
                if error.response.status_code == 429:
                    raise RateLimitError("Amadeus API rate limit exceeded")
                logger.error(f"Failed to get hotels in city {city_code}: {error}")
                return []

            # Step 3: Get offers for these hotels
            try:
                # Build amenities filter if provided
                amenities = filters.get("amenities", [])

                hotel_offers_input = {
                    "hotelIds": ','.join(hotel_ids[:settings.AMADEUS_MAX_HOTELS_PER_REQUEST]),
                    "checkInDate": check_in.isoformat(),
                    "checkOutDate": check_out.isoformat(),
                    "adults": guests,
                    "roomQuantity": rooms,
                    "currency": "USD",
                    "paymentPolicy": "NONE",
                    "bestRateOnly": True
                }
                log_api_call("Hotel Offers Search", hotel_offers_input)

                offers_response = self.client.shopping.hotel_offers_search.get(
                    hotelIds=','.join(hotel_ids[:settings.AMADEUS_MAX_HOTELS_PER_REQUEST]),  # Use configured limit
                    checkInDate=check_in.isoformat(),
                    checkOutDate=check_out.isoformat(),
                    adults=guests,
                    roomQuantity=rooms,
                    currency='USD',
                    paymentPolicy='NONE',
                    bestRateOnly=True
                )

                log_api_call("Hotel Offers Search", hotel_offers_input, output_data=offers_response)

                if not hasattr(offers_response, 'data') or not offers_response.data:
                    logger.info(f"No offers available for hotels in {city_code}")
                    return []

                return self._parse_hotels(offers_response.data, destination, **filters)

            except ResponseError as error:
                log_api_call("Hotel Offers Search", hotel_offers_input, error=error)
                if error.response.status_code == 429:
                    raise RateLimitError("Amadeus API rate limit exceeded")
                logger.error(f"Failed to get hotel offers: {error}")
                if hasattr(error, 'response'):
                    logger.error(f"Status: {error.response.status_code}")
                return []

        except TravelAPIError:
            raise
        except Exception as e:
            logger.error(f"Amadeus hotel search error: {e}", exc_info=True)
            raise TravelAPIError(f"Failed to search hotels: {e}")

    async def _get_city_code(self, destination: str) -> Optional[str]:
        """
        Get IATA city code for a destination using Amadeus Location API

        Uses: GET /v1/reference-data/locations?subType=CITY&keyword={city_name}

        Args:
            destination: City name (e.g., "Tokyo", "Paris", "Berlin")

        Returns:
            IATA city code (e.g., "TYO", "PAR", "BER") or None
        """
        try:
            # Check if already a valid IATA code (3 letters)
            if len(destination) == 3 and destination.isalpha():
                return destination.upper()

            # Use Amadeus Location API with CITY subtype only
            input_params = {
                "keyword": destination,
                "subType": "CITY"
            }
            log_api_call("Location Search (City)", input_params)

            response = self.client.reference_data.locations.get(
                keyword=destination,
                subType="CITY"  # Only search for cities, not airports
            )

            log_api_call("Location Search (City)", input_params, output_data=response)

            if hasattr(response, 'data') and response.data:
                # Return first matching location's IATA code
                city_code = response.data[0].get('iataCode')
                if city_code:
                    logger.info(f"Found city code via Amadeus API: {destination} -> {city_code}")
                    return city_code

            # If no results, log and return None
            logger.warning(f"No IATA code found for destination: {destination}")
            return None

        except ResponseError as e:
            # Log detailed error but don't crash
            log_api_call("Location Search (City)", {"keyword": destination, "subType": "CITY"}, error=e)
            logger.error(f"Amadeus location API error for {destination}: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.body}")
            return None
        except Exception as e:
            log_api_call("Location Search (City)", {"keyword": destination, "subType": "CITY"}, error=e)
            logger.error(f"Unexpected error getting city code for {destination}: {e}", exc_info=True)
            return None

    def _parse_hotels(self, offers: List[Dict], destination: str, **filters) -> List[HotelCard]:
        """
        Parse Amadeus hotel offers into HotelCard objects

        Args:
            offers: List of hotel offers from Amadeus API
            destination: Destination city name
            **filters: Filtering criteria

        Returns:
            List of HotelCard objects
        """
        hotels = []
        price_max = filters.get("price_max")
        rating_min = filters.get("rating_min", 0)

        for offer in offers[:settings.AMADEUS_MAX_HOTELS_TO_RETURN]:  # Use configured limit
            try:
                hotel_data = offer.get('hotel', {})
                offer_data = offer.get('offers', [{}])[0]

                # Extract price
                price_data = offer_data.get('price', {})
                price_nightly = float(price_data.get('total', 0))
                currency = price_data.get('currency', 'USD')

                # Apply price filter
                if price_max and price_nightly > price_max:
                    continue

                # Extract rating (if available)
                rating = hotel_data.get('rating')
                if rating:
                    try:
                        rating = float(rating)
                    except:
                        rating = None

                # Apply rating filter
                if rating and rating < rating_min:
                    continue

                # Extract amenities
                amenities = hotel_data.get('amenities', [])

                # Extract address
                address = hotel_data.get('address', {})
                city = address.get('cityName', destination)

                # Build hotel card
                hotel = HotelCard(
                    provider="amadeus",
                    name=hotel_data.get('name', 'Unknown Hotel'),
                    city=city,
                    country=address.get('countryCode', ''),
                    neighborhood=address.get('stateCode', ''),
                    rating=rating,
                    price_nightly=price_nightly,
                    currency=currency,
                    amenities=amenities,
                    deeplink=self._build_hotel_deeplink(offer.get('id', '')),
                    thumbnail_url="",  # Amadeus doesn't provide images in basic API
                    description=hotel_data.get('description', {}).get('text', ''),
                    citations=[
                        f"https://www.amadeus.com/hotels/{offer.get('id', '')}"
                    ]
                )

                hotels.append(hotel)

            except Exception as e:
                logger.warning(f"Failed to parse hotel offer: {e}")
                continue

        logger.info(f"Parsed {len(hotels)} hotels from Amadeus")
        return hotels

    def _build_hotel_deeplink(self, hotel_id: str) -> str:
        """Build Amadeus hotel booking link"""
        return f"https://www.amadeus.com/hotels/{hotel_id}"

    async def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """Get detailed hotel information"""
        try:
            response = self.client.shopping.hotel_offer_search(hotel_id).get()
            if hasattr(response, 'data'):
                return response.data
            return {}
        except Exception as e:
            logger.error(f"Failed to get hotel details: {e}")
            return {}


@ProviderRegistry.register_flight_provider("amadeus")
class AmadeusFlightProvider(FlightProvider):
    """
    Amadeus flight provider implementation

    Usage:
        provider = AmadeusFlightProvider(
            api_key="your_amadeus_api_key",
            api_secret="your_amadeus_api_secret"
        )
    """

    def __init__(self, api_key: str, api_secret: str = "", **kwargs):
        super().__init__(api_key, **kwargs)
        self.api_secret = api_secret
        self.client = Client(
            client_id=api_key,
            client_secret=api_secret
        )
        self.timeout = kwargs.get("timeout", 30)

    def get_provider_name(self) -> str:
        return "amadeus"

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
        Search for flights using Amadeus Flight Offers Search API

        Args:
            origin: Origin airport code (e.g., "JFK", "LAX")
            destination: Destination airport code
            depart_date: Departure date
            return_date: Return date (None for one-way)
            passengers: Number of passengers
            cabin_class: economy, premium_economy, business, first
            **filters: max_stops, airlines, price_max, etc.

        Returns:
            List of FlightCard objects
        """
        try:
            logger.info(f"Amadeus flight search: {origin} -> {destination} on {depart_date}")

            # Map cabin class to Amadeus format
            cabin_map = {
                "economy": "ECONOMY",
                "premium_economy": "PREMIUM_ECONOMY",
                "business": "BUSINESS",
                "first": "FIRST"
            }
            amadeus_cabin = cabin_map.get(cabin_class.lower(), "ECONOMY")

            # Build search parameters
            search_params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": depart_date.isoformat(),
                "adults": passengers,
                "travelClass": amadeus_cabin,
                "currencyCode": "USD",
                "max": settings.AMADEUS_MAX_FLIGHT_RESULTS  # Use configured limit
            }

            # Add return date for round-trip
            if return_date:
                search_params["returnDate"] = return_date.isoformat()

            # Add filters
            if filters.get("max_stops") == 0:
                search_params["nonStop"] = True

            # Search flights
            try:
                log_api_call("Flight Offers Search", search_params)

                response = self.client.shopping.flight_offers_search.get(**search_params)

                log_api_call("Flight Offers Search", search_params, output_data=response)

                if not hasattr(response, 'data') or not response.data:
                    logger.info(f"No flights found for {origin} -> {destination}")
                    return []

                return self._parse_flights(response.data, **filters)

            except ResponseError as error:
                log_api_call("Flight Offers Search", search_params, error=error)
                if error.response.status_code == 429:
                    raise RateLimitError("Amadeus API rate limit exceeded")

                # Log detailed error info
                error_detail = ""
                if hasattr(error, 'response') and hasattr(error.response, 'body'):
                    error_detail = f" - Details: {error.response.body}"

                logger.error(f"Amadeus API error: {error}{error_detail}")
                raise TravelAPIError(f"Amadeus flight search failed: {error}")

        except Exception as e:
            logger.error(f"Amadeus flight search error: {e}", exc_info=True)
            raise TravelAPIError(f"Failed to search flights: {e}")

    def _parse_flights(self, offers: List[Dict], **filters) -> List[FlightCard]:
        """
        Parse Amadeus flight offers into FlightCard objects

        Args:
            offers: List of flight offers from Amadeus API
            **filters: Filtering criteria

        Returns:
            List of FlightCard objects
        """
        flights = []
        price_max = filters.get("price_max")
        max_stops = filters.get("max_stops")

        for offer in offers[:settings.AMADEUS_MAX_FLIGHT_RESULTS]:  # Use configured limit
            try:
                itineraries = offer.get("itineraries", [])
                if not itineraries:
                    continue

                # Get first itinerary (outbound)
                itinerary = itineraries[0]
                segments = itinerary.get("segments", [])
                if not segments:
                    continue

                # First and last segment
                first_segment = segments[0]
                last_segment = segments[-1]

                # Calculate stops
                stops = len(segments) - 1

                # Apply stops filter
                if max_stops is not None and stops > max_stops:
                    continue

                # Parse price
                price_data = offer.get("price", {})
                price = float(price_data.get("total", 0))

                # Apply price filter
                if price_max and price > price_max:
                    continue

                # Parse departure and arrival times
                depart_time = datetime.fromisoformat(
                    first_segment.get("departure", {}).get("at", "").replace("Z", "+00:00")
                )
                arrive_time = datetime.fromisoformat(
                    last_segment.get("arrival", {}).get("at", "").replace("Z", "+00:00")
                )

                # Parse duration
                duration_str = itinerary.get("duration", "PT0M")
                duration_minutes = self._parse_duration(duration_str)

                # Carrier info
                carrier_code = first_segment.get("carrierCode", "")
                flight_number = first_segment.get("number", "")

                # Build flight card
                flight = FlightCard(
                    provider="amadeus",
                    carrier=carrier_code,  # Could map to full airline name
                    carrier_code=carrier_code,
                    flight_number=f"{carrier_code}{flight_number}",
                    origin=first_segment.get("departure", {}).get("iataCode", ""),
                    origin_code=first_segment.get("departure", {}).get("iataCode", ""),
                    destination=last_segment.get("arrival", {}).get("iataCode", ""),
                    destination_code=last_segment.get("arrival", {}).get("iataCode", ""),
                    depart_time=depart_time,
                    arrive_time=arrive_time,
                    duration_minutes=duration_minutes,
                    stops=stops,
                    price=price,
                    currency=price_data.get("currency", "USD"),
                    cabin_class="economy",  # Parse from validatingAirlineCodes if needed
                    deeplink=self._build_flight_deeplink(offer.get("id")),
                    citations=[
                        f"https://www.amadeus.com/flights/{offer.get('id')}"
                    ]
                )

                flights.append(flight)

            except Exception as e:
                logger.warning(f"Failed to parse flight offer: {e}")
                continue

        logger.info(f"Parsed {len(flights)} flights from Amadeus")
        return flights

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration to minutes
        Example: PT8H30M -> 510 minutes

        Args:
            duration_str: ISO 8601 duration string

        Returns:
            Duration in minutes
        """
        try:
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration_str)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                return hours * 60 + minutes
        except Exception as e:
            logger.warning(f"Failed to parse duration {duration_str}: {e}")
        return 0

    def _build_flight_deeplink(self, offer_id: str) -> str:
        """Build Amadeus flight booking link"""
        return f"https://www.amadeus.com/flights/{offer_id}"

    async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Get detailed flight information"""
        try:
            response = self.client.shopping.flight_offers.pricing.post(
                flight_id
            )
            if hasattr(response, 'data'):
                return response.data
            return {}
        except Exception as e:
            logger.error(f"Failed to get flight details: {e}")
            return {}
