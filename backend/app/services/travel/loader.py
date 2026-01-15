"""
Configuration Loader
Loads provider configuration from YAML or environment variables
Automatically instantiates and registers providers
"""
from app.core.centralized_logger import get_logger
import os
import importlib
from typing import Dict, Any, List
from pathlib import Path
import yaml
from dotenv import load_dotenv
from .registry import ProviderRegistry
from .manager import travel_manager

logger = get_logger(__name__)

# Load .env file at module import time
load_dotenv()


def _auto_import_providers() -> None:
    """
    Auto-discover and import all provider modules in the providers directory.
    This triggers their @register decorators without hard-coding imports.
    """
    providers_dir = Path(__file__).parent / "providers"

    if not providers_dir.exists():
        logger.warning(f"Providers directory not found: {providers_dir}")
        return

    # Find all Python files in providers directory (except __init__.py)
    provider_files = [
        f.stem for f in providers_dir.glob("*.py")
        if f.is_file() and f.stem != "__init__"
    ]

    # Dynamically import each provider module
    for provider_name in provider_files:
        try:
            module_path = f"app.services.travel.providers.{provider_name}"
            importlib.import_module(module_path)
            logger.debug(f"Loaded travel provider: {provider_name}")
        except ImportError as e:
            logger.warning(f"Failed to import provider {provider_name}: {e}")
        except Exception as e:
            logger.error(f"Error loading provider {provider_name}: {e}")


class ProviderLoader:
    """
    Loads and initializes providers from configuration
    Supports both YAML files and environment variables
    """

    @staticmethod
    def load_from_yaml(config_path: str) -> None:
        """
        Load providers from YAML configuration file

        Example YAML structure:
        ```yaml
        hotel_providers:
          - name: mock
            enabled: true
            config:
              api_key: mock_key

          - name: booking
            enabled: false
            config:
              api_key: ${BOOKING_API_KEY}
              affiliate_id: ${BOOKING_AFFILIATE_ID}

        flight_providers:
          - name: mock
            enabled: true
            config:
              api_key: mock_key

          - name: amadeus
            enabled: false
            config:
              api_key: ${AMADEUS_API_KEY}
              api_secret: ${AMADEUS_API_SECRET}
        ```

        Args:
            config_path: Path to YAML configuration file
        """
        config_file = Path(config_path)

        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}")
            return

        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            # Process hotel providers
            hotel_configs = config.get('hotel_providers', [])
            for provider_config in hotel_configs:
                if provider_config.get('enabled', False):
                    ProviderLoader._load_hotel_provider(provider_config)

            # Process flight providers
            flight_configs = config.get('flight_providers', [])
            for provider_config in flight_configs:
                if provider_config.get('enabled', False):
                    ProviderLoader._load_flight_provider(provider_config)

            logger.info(f"Loaded providers from {config_path}")

        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")

    @staticmethod
    def load_from_env() -> None:
        """
        Load providers from environment variables

        Looks for patterns like:
        - TRAVEL_HOTEL_PROVIDERS=mock,booking
        - TRAVEL_FLIGHT_PROVIDERS=mock,amadeus
        - BOOKING_API_KEY=...
        - AMADEUS_API_KEY=...
        """
        # Get enabled providers from env
        hotel_providers = os.getenv('TRAVEL_HOTEL_PROVIDERS', 'mock').split(',')
        flight_providers = os.getenv('TRAVEL_FLIGHT_PROVIDERS', 'mock').split(',')

        # Load hotel providers
        for provider_name in hotel_providers:
            provider_name = provider_name.strip()
            if not provider_name:
                continue

            config = ProviderLoader._get_provider_config_from_env(provider_name, 'hotel')
            if config:
                provider_config = {
                    'name': provider_name,
                    'config': config
                }
                ProviderLoader._load_hotel_provider(provider_config)

        # Load flight providers
        for provider_name in flight_providers:
            provider_name = provider_name.strip()
            if not provider_name:
                continue

            config = ProviderLoader._get_provider_config_from_env(provider_name, 'flight')
            if config:
                provider_config = {
                    'name': provider_name,
                    'config': config
                }
                ProviderLoader._load_flight_provider(provider_config)

    @staticmethod
    def _get_provider_config_from_env(provider_name: str, provider_type: str) -> Dict[str, Any]:
        """
        Extract provider configuration from environment variables

        Looks for:
        - {PROVIDER_NAME}_API_KEY
        - {PROVIDER_NAME}_API_SECRET
        - {PROVIDER_NAME}_AFFILIATE_ID
        etc.
        """
        provider_upper = provider_name.upper()
        config = {}

        # Common keys
        api_key = os.getenv(f'{provider_upper}_API_KEY')
        if api_key:
            config['api_key'] = api_key

        api_secret = os.getenv(f'{provider_upper}_API_SECRET')
        if api_secret:
            config['api_secret'] = api_secret

        affiliate_id = os.getenv(f'{provider_upper}_AFFILIATE_ID')
        if affiliate_id:
            config['affiliate_id'] = affiliate_id

        # For mock provider, use dummy key
        if provider_name == 'mock' and not config.get('api_key'):
            config['api_key'] = 'mock_key'

        return config

    @staticmethod
    def _load_hotel_provider(provider_config: Dict[str, Any]) -> None:
        """Load and register a hotel provider"""
        name = provider_config.get('name')
        config = provider_config.get('config', {})

        # Substitute environment variables in config
        config = ProviderLoader._substitute_env_vars(config)

        # Create provider instance
        provider = ProviderRegistry.create_hotel_provider(name, config)

        if provider:
            travel_manager.register_hotel_provider(provider)
            logger.info(f"✓ Loaded hotel provider: {name}")
        else:
            logger.warning(f"✗ Failed to load hotel provider: {name}")

    @staticmethod
    def _load_flight_provider(provider_config: Dict[str, Any]) -> None:
        """Load and register a flight provider"""
        name = provider_config.get('name')
        config = provider_config.get('config', {})

        # Substitute environment variables in config
        config = ProviderLoader._substitute_env_vars(config)

        # Create provider instance
        provider = ProviderRegistry.create_flight_provider(name, config)

        if provider:
            travel_manager.register_flight_provider(provider)
            logger.info(f"✓ Loaded flight provider: {name}")
        else:
            logger.warning(f"✗ Failed to load flight provider: {name}")

    @staticmethod
    def _substitute_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace ${VAR_NAME} patterns with environment variable values

        Example:
            {"api_key": "${BOOKING_API_KEY}"} -> {"api_key": "actual_key_value"}
        """
        substituted = {}

        for key, value in config.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Extract variable name
                var_name = value[2:-1]
                # Get from environment
                env_value = os.getenv(var_name)
                if env_value:
                    substituted[key] = env_value
                else:
                    logger.warning(f"Environment variable not found: {var_name}")
                    substituted[key] = value  # Keep original
            else:
                substituted[key] = value

        return substituted


# Convenience function
def setup_providers(config_path: str = None, use_env: bool = True) -> None:
    """
    Setup travel providers from configuration

    Args:
        config_path: Path to YAML config file (optional)
        use_env: Whether to load from environment variables (default: True)

    Usage:
        # Load from YAML only
        setup_providers(config_path="config/travel.yaml", use_env=False)

        # Load from environment variables only
        setup_providers(use_env=True)

        # Load from both (YAML takes precedence)
        setup_providers(config_path="config/travel.yaml", use_env=True)
    """
    logger.info("Setting up travel providers...")

    # Auto-discover and import all providers to trigger registration
    _auto_import_providers()

    # Load from YAML if provided
    if config_path:
        ProviderLoader.load_from_yaml(config_path)

    # Load from environment variables
    if use_env:
        ProviderLoader.load_from_env()

    # Log what was loaded
    providers = travel_manager.get_available_providers()
    logger.info(f"Available providers: {providers}")

    if not providers['hotels'] and not providers['flights']:
        logger.warning("No providers loaded! Travel functionality will not work.")
