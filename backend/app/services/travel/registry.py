"""
Provider Registry - Plugin System
Automatically discovers and registers providers based on configuration
No code changes needed to add/remove providers
"""
from app.core.centralized_logger import get_logger
from typing import Dict, Any, Type, Optional
from .base import HotelProvider, FlightProvider

logger = get_logger(__name__)


class ProviderRegistry:
    """
    Registry for travel providers
    Providers self-register using decorators
    """

    _hotel_providers: Dict[str, Type[HotelProvider]] = {}
    _flight_providers: Dict[str, Type[FlightProvider]] = {}

    @classmethod
    def register_hotel_provider(cls, name: str):
        """
        Decorator to register a hotel provider class

        Usage:
            @ProviderRegistry.register_hotel_provider("booking")
            class BookingHotelProvider(HotelProvider):
                pass
        """
        def decorator(provider_class: Type[HotelProvider]):
            cls._hotel_providers[name] = provider_class
            logger.debug(f"Registered hotel provider class: {name}")
            return provider_class
        return decorator

    @classmethod
    def register_flight_provider(cls, name: str):
        """
        Decorator to register a flight provider class

        Usage:
            @ProviderRegistry.register_flight_provider("skyscanner")
            class SkyscannerFlightProvider(FlightProvider):
                pass
        """
        def decorator(provider_class: Type[FlightProvider]):
            cls._flight_providers[name] = provider_class
            logger.debug(f"Registered flight provider class: {name}")
            return provider_class
        return decorator

    @classmethod
    def get_hotel_provider(cls, name: str) -> Optional[Type[HotelProvider]]:
        """Get hotel provider class by name"""
        return cls._hotel_providers.get(name)

    @classmethod
    def get_flight_provider(cls, name: str) -> Optional[Type[FlightProvider]]:
        """Get flight provider class by name"""
        return cls._flight_providers.get(name)

    @classmethod
    def list_hotel_providers(cls) -> list[str]:
        """List all registered hotel provider names"""
        return list(cls._hotel_providers.keys())

    @classmethod
    def list_flight_providers(cls) -> list[str]:
        """List all registered flight provider names"""
        return list(cls._flight_providers.keys())

    @classmethod
    def create_hotel_provider(cls, name: str, config: Dict[str, Any]) -> Optional[HotelProvider]:
        """
        Create a hotel provider instance from configuration

        Args:
            name: Provider name (e.g., "booking")
            config: Provider configuration dict

        Returns:
            Instantiated provider or None if not found
        """
        provider_class = cls.get_hotel_provider(name)
        if not provider_class:
            logger.warning(f"Hotel provider '{name}' not found in registry")
            return None

        try:
            # Extract required parameters
            api_key = config.get("api_key")
            if not api_key:
                logger.warning(f"Hotel provider '{name}' missing api_key in config")
                return None

            # Remove api_key from config to avoid passing it twice
            config_without_key = {k: v for k, v in config.items() if k != "api_key"}

            # Pass all config as kwargs
            instance = provider_class(api_key=api_key, **config_without_key)
            logger.info(f"Created hotel provider instance: {name}")
            return instance

        except Exception as e:
            logger.error(f"Failed to create hotel provider '{name}': {e}")
            return None

    @classmethod
    def create_flight_provider(cls, name: str, config: Dict[str, Any]) -> Optional[FlightProvider]:
        """
        Create a flight provider instance from configuration

        Args:
            name: Provider name (e.g., "amadeus")
            config: Provider configuration dict

        Returns:
            Instantiated provider or None if not found
        """
        provider_class = cls.get_flight_provider(name)
        if not provider_class:
            logger.warning(f"Flight provider '{name}' not found in registry")
            return None

        try:
            # Extract required parameters
            api_key = config.get("api_key")
            if not api_key:
                logger.warning(f"Flight provider '{name}' missing api_key in config")
                return None

            # Remove api_key from config to avoid passing it twice
            config_without_key = {k: v for k, v in config.items() if k != "api_key"}

            # Pass all config as kwargs
            instance = provider_class(api_key=api_key, **config_without_key)
            logger.info(f"Created flight provider instance: {name}")
            return instance

        except Exception as e:
            logger.error(f"Failed to create flight provider '{name}': {e}")
            return None
