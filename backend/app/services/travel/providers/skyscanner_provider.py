"""
Skyscanner Flight Provider
Implements flight search using Skyscanner API via RapidAPI

API Documentation:
- RapidAPI Skyscanner: https://rapidapi.com/skyscanner/api/skyscanner-flight-search
- Official Skyscanner API: https://skyscanner.github.io/slate/

Features:
- Flight search (one-way and round-trip)
- Real-time pricing and availability
- Multi-carrier support
- Direct booking links
"""
from app.core.centralized_logger import get_logger
import asyncio
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import httpx
from ..base import FlightProvider, FlightCard, TravelAPIError, RateLimitError
from ..registry import ProviderRegistry
from app.core.config import settings

logger = get_logger(__name__)


@ProviderRegistry.register_flight_provider("skyscanner")
class SkyscannerFlightProvider(FlightProvider):
    """
    Skyscanner flight provider implementation via RapidAPI

    Usage:
        provider = SkyscannerFlightProvider(
            api_key="your_rapidapi_key"
        )
    """

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = "https://skyscanner-api.p.rapidapi.com/v3"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "skyscanner-api.p.rapidapi.com",
            "Content-Type": "application/json"
        }
        self.timeout = kwargs.get("timeout", 30)
        self.market = kwargs.get("market", "US")
        self.locale = kwargs.get("locale", "en-US")
        self.currency = kwargs.get("currency", "USD")

    def get_provider_name(self) -> str:
        return "skyscanner"

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
        Search for flights on Skyscanner

        Args:
            origin: Origin airport code (e.g., "JFK", "LAX") or city
            destination: Destination airport code or city
            depart_date: Departure date
            return_date: Return date (None for one-way)
            passengers: Number of passengers
            cabin_class: economy, premium_economy, business, first
            **filters: max_stops, airlines, price_max, etc.

        Returns:
            List of FlightCard objects
        """
        try:
            logger.info(f"Searching Skyscanner: {origin} -> {destination}, {depart_date}")

            # Create search
            search_id = await self._create_search(
                origin=origin,
                destination=destination,
                depart_date=depart_date,
                return_date=return_date,
                passengers=passengers,
                cabin_class=cabin_class
            )

            if not search_id:
                logger.warning("Failed to create Skyscanner search")
                return []

            # Poll for results
            flights = await self._poll_search_results(search_id, **filters)

            logger.info(f"Found {len(flights)} flights on Skyscanner")
            return flights

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Skyscanner API rate limit exceeded")
            raise TravelAPIError(f"Skyscanner API error: {e}")
        except Exception as e:
            logger.error(f"Skyscanner search error: {e}", exc_info=True)
            raise TravelAPIError(f"Skyscanner search failed: {e}")

    async def _create_search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        return_date: Optional[date],
        passengers: int,
        cabin_class: str
    ) -> Optional[str]:
        """Create a flight search and return session ID"""
        try:
            # Resolve origin and destination to IATA codes if needed
            origin_code = await self._resolve_airport(origin)
            dest_code = await self._resolve_airport(destination)

            if not origin_code or not dest_code:
                logger.error(f"Failed to resolve airports: {origin}, {destination}")
                return None

            # Build search payload
            payload = {
                "query": {
                    "market": self.market,
                    "locale": self.locale,
                    "currency": self.currency,
                    "queryLegs": [
                        {
                            "originPlaceId": {"iata": origin_code},
                            "destinationPlaceId": {"iata": dest_code},
                            "date": {
                                "year": depart_date.year,
                                "month": depart_date.month,
                                "day": depart_date.day
                            }
                        }
                    ],
                    "cabinClass": cabin_class.upper(),
                    "adults": passengers,
                    "childrenAges": []
                }
            }

            # Add return leg if round-trip
            if return_date:
                payload["query"]["queryLegs"].append({
                    "originPlaceId": {"iata": dest_code},
                    "destinationPlaceId": {"iata": origin_code},
                    "date": {
                        "year": return_date.year,
                        "month": return_date.month,
                        "day": return_date.day
                    }
                })

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/flights/live/search/create",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # Extract session token
                session_token = data.get("sessionToken")
                return session_token

        except Exception as e:
            logger.error(f"Failed to create search: {e}", exc_info=True)
            return None

    async def _poll_search_results(
        self,
        session_token: str,
        max_attempts: int = 5,
        **filters
    ) -> List[FlightCard]:
        """Poll search results until complete"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for attempt in range(max_attempts):
                    response = await client.post(
                        f"{self.base_url}/flights/live/search/poll",
                        headers=self.headers,
                        json={"sessionToken": session_token}
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Check if results are complete
                    status = data.get("status", "")
                    if status == "RESULT_STATUS_COMPLETE":
                        return self._parse_flights(data, **filters)

                    # Wait before polling again
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(settings.SKYSCANNER_POLLING_DELAY)

                # Return partial results if not complete
                logger.warning("Skyscanner search did not complete, returning partial results")
                return self._parse_flights(data, **filters)

        except Exception as e:
            logger.error(f"Failed to poll results: {e}")
            return []

    async def _resolve_airport(self, location: str) -> Optional[str]:
        """Resolve location to IATA airport code"""
        # If already a 3-letter code, return as-is
        if len(location) == 3 and location.isalpha():
            return location.upper()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/autosuggest/flights",
                    headers=self.headers,
                    params={
                        "query": location,
                        "market": self.market,
                        "locale": self.locale
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Get first airport suggestion
                places = data.get("places", [])
                if places:
                    return places[0].get("iata")

                return None

        except Exception as e:
            logger.error(f"Failed to resolve airport {location}: {e}")
            return None

    async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Get detailed flight information"""
        logger.warning("Skyscanner get_flight_details not fully implemented")
        return {}

    def _parse_flights(self, api_response: Dict[str, Any], **filters) -> List[FlightCard]:
        """Parse Skyscanner API response into FlightCard objects"""
        flights = []

        try:
            content = api_response.get("content", {})
            itineraries = content.get("results", {}).get("itineraries", {})
            legs = content.get("results", {}).get("legs", {})
            segments = content.get("results", {}).get("segments", {})
            places = content.get("results", {}).get("places", {})
            carriers = content.get("results", {}).get("carriers", {})

            # Apply filters
            max_stops = filters.get("max_stops")
            price_max = filters.get("price_max")

            for itin_id, itin in list(itineraries.items())[:settings.SKYSCANNER_MAX_RESULTS]:  # Use configured limit
                try:
                    # Get pricing
                    price_options = itin.get("pricingOptions", [])
                    if not price_options:
                        continue

                    price = float(price_options[0].get("price", {}).get("amount", 0))

                    # Apply price filter
                    if price_max and price > price_max:
                        continue

                    # Get first leg (outbound)
                    leg_ids = itin.get("legIds", [])
                    if not leg_ids:
                        continue

                    leg_id = leg_ids[0]
                    leg = legs.get(leg_id, {})

                    # Get stops
                    stop_count = leg.get("stopCount", 0)
                    if max_stops is not None and stop_count > max_stops:
                        continue

                    # Get origin and destination
                    origin_id = leg.get("originPlaceId")
                    dest_id = leg.get("destinationPlaceId")
                    origin_place = places.get(origin_id, {})
                    dest_place = places.get(dest_id, {})

                    # Get departure and arrival times
                    depart_time = datetime.fromisoformat(leg.get("departureDateTime", "").replace("Z", "+00:00"))
                    arrive_time = datetime.fromisoformat(leg.get("arrivalDateTime", "").replace("Z", "+00:00"))
                    duration = leg.get("durationInMinutes", 0)

                    # Get carrier info
                    segment_ids = leg.get("segmentIds", [])
                    if not segment_ids:
                        continue

                    first_segment = segments.get(segment_ids[0], {})
                    carrier_id = first_segment.get("marketingCarrierId")
                    carrier = carriers.get(carrier_id, {})
                    carrier_name = carrier.get("name", "Unknown")
                    carrier_code = carrier.get("iata", "XX")

                    # Get flight number
                    flight_number = first_segment.get("flightNumber", "")

                    # Build deeplink
                    deeplink = price_options[0].get("items", [{}])[0].get("deepLink", "")

                    flight = FlightCard(
                        provider="skyscanner",
                        carrier=carrier_name,
                        carrier_code=carrier_code,
                        flight_number=f"{carrier_code}{flight_number}",
                        origin=origin_place.get("name", ""),
                        origin_code=origin_place.get("iata", ""),
                        destination=dest_place.get("name", ""),
                        destination_code=dest_place.get("iata", ""),
                        depart_time=depart_time,
                        arrive_time=arrive_time,
                        duration_minutes=duration,
                        stops=stop_count,
                        price=price,
                        currency=price_options[0].get("price", {}).get("unit", "USD"),
                        cabin_class="economy",  # Default
                        deeplink=deeplink,
                        citations=[deeplink]
                    )
                    flights.append(flight)

                except Exception as e:
                    logger.warning(f"Failed to parse flight: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to parse flights response: {e}", exc_info=True)

        return flights
