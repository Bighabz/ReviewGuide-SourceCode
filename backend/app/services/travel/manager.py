"""
Travel Manager
Orchestrates hotel and flight providers with fallback logic
Includes caching and rate limiting
"""
from app.core.centralized_logger import get_logger
import hashlib
import json
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from .base import (
    HotelProvider,
    FlightProvider,
    HotelCard,
    FlightCard,
    TravelAPIError,
    ProviderNotAvailableError,
    RateLimitError
)
from app.core.redis_client import redis_get_with_retry, redis_set_with_retry
from app.core.config import settings

logger = get_logger(__name__)


class TravelManager:
    """
    Central manager for all travel providers
    Handles provider selection, fallback, and result aggregation
    Features:
    - Redis caching for search results
    - Rate limiting per provider
    - Automatic fallback on errors
    """

    def __init__(self, cache_ttl: int = 3600, enable_cache: bool = True):
        """
        Initialize Travel Manager

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            enable_cache: Enable/disable caching (default: True)
        """
        self.hotel_providers: List[HotelProvider] = []
        self.flight_providers: List[FlightProvider] = []
        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache
        self.rate_limit_tracker: Dict[str, List[datetime]] = {}  # provider -> timestamps

    def register_hotel_provider(self, provider: HotelProvider) -> None:
        """Register a hotel provider"""
        self.hotel_providers.append(provider)
        logger.info(f"Registered hotel provider: {provider.get_provider_name()}")

    def register_flight_provider(self, provider: FlightProvider) -> None:
        """Register a flight provider"""
        self.flight_providers.append(provider)
        logger.info(f"Registered flight provider: {provider.get_provider_name()}")

    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key from search parameters

        Args:
            prefix: Cache key prefix (e.g., 'hotel', 'flight')
            params: Search parameters dictionary

        Returns:
            Hash-based cache key
        """
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"travel:{prefix}:{param_hash}"

    async def _get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached results from Redis

        Args:
            cache_key: Cache key

        Returns:
            Cached results or None if not found
        """
        if not self.enable_cache:
            return None

        try:
            cached_data = await redis_get_with_retry(cache_key)
            if cached_data:
                logger.info(f"Cache hit: {cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

        return None

    async def _set_cached_results(self, cache_key: str, results: List[Any]) -> None:
        """
        Store results in Redis cache

        Args:
            cache_key: Cache key
            results: Results to cache (HotelCard or FlightCard objects)
        """
        if not self.enable_cache:
            return

        try:
            # Convert Pydantic models to dicts for JSON serialization
            serialized = [r.dict() if hasattr(r, 'dict') else r for r in results]
            await redis_set_with_retry(
                cache_key,
                json.dumps(serialized, default=str),
                ex=self.cache_ttl
            )
            logger.info(f"Cached {len(results)} results with TTL {self.cache_ttl}s")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def _check_rate_limit(self, provider_name: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        """
        Check if provider has exceeded rate limit

        Args:
            provider_name: Provider identifier
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if within rate limit, False if exceeded
        """
        now = datetime.now()
        cutoff = datetime.now().timestamp() - window_seconds

        # Get existing timestamps for this provider
        if provider_name not in self.rate_limit_tracker:
            self.rate_limit_tracker[provider_name] = []

        # Remove old timestamps outside the window
        self.rate_limit_tracker[provider_name] = [
            ts for ts in self.rate_limit_tracker[provider_name]
            if ts.timestamp() > cutoff
        ]

        # Check if limit exceeded
        if len(self.rate_limit_tracker[provider_name]) >= max_requests:
            logger.warning(f"Rate limit exceeded for {provider_name}: {max_requests} requests in {window_seconds}s")
            return False

        # Add current timestamp
        self.rate_limit_tracker[provider_name].append(now)
        return True

    async def search_hotels(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int = 2,
        rooms: int = 1,
        max_results: int = 10,
        **filters
    ) -> List[HotelCard]:
        """
        Search for hotels using available providers with fallback
        Includes Redis caching and rate limiting

        Args:
            destination: City or destination name
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            rooms: Number of rooms
            max_results: Maximum number of results to return
            **filters: Additional provider-specific filters

        Returns:
            List of HotelCard objects (aggregated from all providers)
        """
        if not self.hotel_providers:
            logger.warning("No hotel providers registered")
            return []

        # Generate cache key from parameters
        cache_params = {
            "destination": destination,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests": guests,
            "rooms": rooms,
            **filters
        }
        cache_key = self._generate_cache_key("hotels", cache_params)

        # Try to get cached results
        cached_results = await self._get_cached_results(cache_key)
        if cached_results:
            # Convert dicts back to HotelCard objects
            return [HotelCard(**hotel_data) for hotel_data in cached_results[:max_results]]

        all_results = []
        errors = []

        for provider in self.hotel_providers:
            try:
                # Check rate limit
                if not self._check_rate_limit(f"hotel_{provider.get_provider_name()}", max_requests=30, window_seconds=60):
                    logger.warning(f"Skipping {provider.get_provider_name()} due to rate limit")
                    continue

                logger.info(f"Searching hotels with {provider.get_provider_name()}")

                results = await provider.search_hotels(
                    destination=destination,
                    check_in=check_in,
                    check_out=check_out,
                    guests=guests,
                    rooms=rooms,
                    **filters
                )

                all_results.extend(results)
                logger.info(f"Found {len(results)} hotels from {provider.get_provider_name()}")

            except RateLimitError as e:
                logger.warning(f"Provider {provider.get_provider_name()} rate limited: {e}")
                continue  # Try next provider

            except TravelAPIError as e:
                error_msg = f"Provider {provider.get_provider_name()} failed: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue  # Try next provider

            except Exception as e:
                error_msg = f"Unexpected error with {provider.get_provider_name()}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                continue

        # Deduplicate and rank results
        deduplicated = self._deduplicate_hotels(all_results)
        ranked = self._rank_hotels(deduplicated)

        # Cache the results before returning
        if ranked:
            await self._set_cached_results(cache_key, ranked)

        return ranked[:max_results]

    async def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        return_date: Optional[date] = None,
        passengers: int = 1,
        cabin_class: str = "economy",
        max_results: int = 10,
        **filters
    ) -> List[FlightCard]:
        """
        Search for flights using available providers with fallback
        Includes Redis caching and rate limiting

        Args:
            origin: Origin airport code or city
            destination: Destination airport code or city
            depart_date: Departure date
            return_date: Return date (None for one-way)
            passengers: Number of passengers
            cabin_class: Cabin class
            max_results: Maximum number of results to return
            **filters: Additional provider-specific filters

        Returns:
            List of FlightCard objects (aggregated from all providers)
        """
        if not self.flight_providers:
            logger.warning("No flight providers registered")
            return []

        # Generate cache key from parameters
        cache_params = {
            "origin": origin,
            "destination": destination,
            "depart_date": depart_date.isoformat(),
            "return_date": return_date.isoformat() if return_date else None,
            "passengers": passengers,
            "cabin_class": cabin_class,
            **filters
        }
        cache_key = self._generate_cache_key("flights", cache_params)

        # Try to get cached results
        cached_results = await self._get_cached_results(cache_key)
        if cached_results:
            # Convert dicts back to FlightCard objects
            return [FlightCard(**flight_data) for flight_data in cached_results[:max_results]]

        all_results = []
        errors = []

        for provider in self.flight_providers:
            try:
                # Check rate limit
                if not self._check_rate_limit(f"flight_{provider.get_provider_name()}", max_requests=30, window_seconds=60):
                    logger.warning(f"Skipping {provider.get_provider_name()} due to rate limit")
                    continue

                logger.info(f"Searching flights with {provider.get_provider_name()}")

                results = await provider.search_flights(
                    origin=origin,
                    destination=destination,
                    depart_date=depart_date,
                    return_date=return_date,
                    passengers=passengers,
                    cabin_class=cabin_class,
                    **filters
                )

                all_results.extend(results)
                logger.info(f"Found {len(results)} flights from {provider.get_provider_name()}")

            except RateLimitError as e:
                logger.warning(f"Provider {provider.get_provider_name()} rate limited: {e}")
                continue  # Try next provider

            except TravelAPIError as e:
                error_msg = f"Provider {provider.get_provider_name()} failed: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue  # Try next provider

            except Exception as e:
                error_msg = f"Unexpected error with {provider.get_provider_name()}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                continue

        # Deduplicate and rank results
        deduplicated = self._deduplicate_flights(all_results)
        ranked = self._rank_flights(deduplicated)

        # Cache the results before returning
        if ranked:
            await self._set_cached_results(cache_key, ranked)

        return ranked[:max_results]

    def _deduplicate_hotels(self, hotels: List[HotelCard]) -> List[HotelCard]:
        """Remove duplicate hotels based on name and location"""
        seen = set()
        unique = []

        for hotel in hotels:
            # Create a unique key based on name and city
            key = f"{hotel.name.lower()}_{hotel.city.lower()}"

            if key not in seen:
                seen.add(key)
                unique.append(hotel)

        return unique

    def _deduplicate_flights(self, flights: List[FlightCard]) -> List[FlightCard]:
        """Remove duplicate flights based on carrier, flight number, and departure time"""
        seen = set()
        unique = []

        for flight in flights:
            # Create a unique key
            key = f"{flight.carrier_code}_{flight.flight_number}_{flight.depart_time.isoformat()}"

            if key not in seen:
                seen.add(key)
                unique.append(flight)

        return unique

    def _rank_hotels(self, hotels: List[HotelCard]) -> List[HotelCard]:
        """
        Rank hotels by score (rating, price, distance)
        Can be customized based on user preferences
        """
        def calculate_score(hotel: HotelCard) -> float:
            score = 0.0

            # Rating score (0-50 points)
            if hotel.rating:
                score += hotel.rating * 10  # Max 50 points for 5-star

            # Price score (0-30 points) - lower is better
            # Assume $50-500 range
            if hotel.price_nightly:
                normalized_price = (500 - min(hotel.price_nightly, 500)) / 500
                score += normalized_price * 30

            # Amenities score (0-20 points)
            score += min(len(hotel.amenities) * 2, 20)

            return score

        # Sort by score descending
        return sorted(hotels, key=calculate_score, reverse=True)

    def _rank_flights(self, flights: List[FlightCard]) -> List[FlightCard]:
        """
        Rank flights by score (price, duration, stops)
        Can be customized based on user preferences
        """
        def calculate_score(flight: FlightCard) -> float:
            score = 0.0

            # Price score (0-40 points) - lower is better
            # Assume $100-2000 range
            if flight.price:
                normalized_price = (2000 - min(flight.price, 2000)) / 2000
                score += normalized_price * 40

            # Duration score (0-30 points) - shorter is better
            # Assume 60-1200 minutes range
            normalized_duration = (1200 - min(flight.duration_minutes, 1200)) / 1200
            score += normalized_duration * 30

            # Stops score (0-30 points) - fewer is better
            if flight.stops == 0:
                score += 30
            elif flight.stops == 1:
                score += 15
            else:
                score += 5

            return score

        # Sort by score descending
        return sorted(flights, key=calculate_score, reverse=True)

    def get_available_providers(self) -> Dict[str, List[str]]:
        """Get list of available providers"""
        return {
            "hotels": [p.get_provider_name() for p in self.hotel_providers],
            "flights": [p.get_provider_name() for p in self.flight_providers]
        }


# Global travel manager instance with configuration from settings
# Cache is controlled by ENABLE_TRAVEL_CACHE and TRAVEL_CACHE_TTL in .env
travel_manager = TravelManager(
    cache_ttl=settings.TRAVEL_CACHE_TTL,
    enable_cache=settings.ENABLE_TRAVEL_CACHE
)
