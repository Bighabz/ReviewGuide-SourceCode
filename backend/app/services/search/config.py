"""
Search Provider Configuration
Load from YAML or environment variables
"""
from app.core.centralized_logger import get_logger
import os
import importlib
from pathlib import Path
import yaml
from dotenv import load_dotenv
from .registry import SearchProviderRegistry
from .manager import search_manager

logger = get_logger(__name__)

# Load .env file at module import time
load_dotenv()


def _load_provider_module(provider_name: str) -> None:
    """
    Load a single provider module by name.
    Only imports the provider that's actually being used.

    Args:
        provider_name: Name of the provider (e.g., "perplexity", "tavily")
    """
    try:
        # Import only the specific provider module we need
        module_path = f"app.services.search.providers.{provider_name}_provider"
        importlib.import_module(module_path)
        logger.info(f"Loaded search provider module: {provider_name}")
    except ImportError as e:
        logger.error(f"Failed to import provider {provider_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading provider {provider_name}: {e}")
        raise


def setup_search_provider(config_path: str = None) -> None:
    """
    Setup search provider from configuration.
    Only loads the single provider specified in config.

    Args:
        config_path: Path to YAML config file (optional)

    Usage:
        # Auto-detect config
        setup_search_provider()

        # Use specific config
        setup_search_provider("config/search.yaml")

        # Use environment variables
        export SEARCH_PROVIDER=perplexity
        export PERPLEXITY_API_KEY=your_key
    """
    logger.info("Setting up search provider...")

    # Try YAML config first
    if config_path is None:
        default_path = Path(__file__).parent.parent.parent.parent / "config" / "search.yaml"
        if default_path.exists():
            config_path = str(default_path)

    if config_path and Path(config_path).exists():
        _load_from_yaml(config_path)
    else:
        _load_from_env()

    # Log result
    provider_name = search_manager.get_provider_name()
    if provider_name:
        logger.info(f"✓ Search provider active: {provider_name}")
    else:
        logger.warning("✗ No search provider configured!")


def _load_from_yaml(config_path: str) -> None:
    """Load from YAML configuration - only imports the specified provider"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        provider_config = config.get('search_provider', {})

        if not provider_config.get('enabled', False):
            logger.warning("Search provider disabled in config")
            return

        name = provider_config.get('name')
        if not name:
            logger.error("No provider name specified in config")
            return

        # Import only the provider we need
        _load_provider_module(name)

        provider_config_data = provider_config.get('config', {})

        # Substitute environment variables
        provider_config_data = _substitute_env_vars(provider_config_data)

        # Create provider instance
        provider = SearchProviderRegistry.create_provider(name, provider_config_data)

        if provider:
            search_manager.set_provider(provider)

    except Exception as e:
        logger.error(f"Failed to load search config: {e}")


def _load_from_env() -> None:
    """Load from environment variables - only imports the specified provider"""
    provider_name = os.getenv('SEARCH_PROVIDER', 'perplexity')

    if not provider_name:
        logger.warning("No SEARCH_PROVIDER set in environment")
        return

    # Import only the provider we need
    _load_provider_module(provider_name)

    # Get provider config from env
    config = _get_provider_config_from_env(provider_name)

    if not config:
        logger.warning(f"No configuration found for provider: {provider_name}")
        return

    # Create provider instance
    provider = SearchProviderRegistry.create_provider(provider_name, config)

    if provider:
        search_manager.set_provider(provider)


def _get_provider_config_from_env(provider_name: str) -> dict:
    """Extract provider config from environment"""
    provider_upper = provider_name.upper()
    config = {}

    api_key = os.getenv(f'{provider_upper}_API_KEY') or os.getenv('PERPLEXITY_API_KEY')
    if api_key:
        config['api_key'] = api_key

    # Optional configs - try both patterns: PROVIDER_PARAM and PROVIDER_SEARCH_PARAM
    base_url = (
        os.getenv(f'{provider_upper}_BASE_URL') or
        os.getenv(f'{provider_upper}_SEARCH_BASE_URL')
    )
    if base_url:
        config['base_url'] = base_url

    model = (
        os.getenv(f'{provider_upper}_MODEL') or
        os.getenv(f'{provider_upper}_SEARCH_MODEL')
    )
    if model:
        config['model'] = model

    timeout = (
        os.getenv(f'{provider_upper}_TIMEOUT') or
        os.getenv(f'{provider_upper}_SEARCH_TIMEOUT')
    )
    if timeout:
        config['timeout'] = float(timeout)

    # Domain filters - try provider-specific first, then generic
    product_domains = (
        os.getenv(f'{provider_upper}_PRODUCT_DOMAINS') or
        os.getenv('PERPLEXITY_PRODUCT_DOMAINS')  # Fallback for backwards compatibility
    )
    if product_domains:
        config['product_domains'] = product_domains

    service_domains = (
        os.getenv(f'{provider_upper}_SERVICE_DOMAINS') or
        os.getenv('PERPLEXITY_SERVICE_DOMAINS')  # Fallback for backwards compatibility
    )
    if service_domains:
        config['service_domains'] = service_domains

    travel_domains = (
        os.getenv(f'{provider_upper}_TRAVEL_DOMAINS') or
        os.getenv('PERPLEXITY_TRAVEL_DOMAINS')  # Fallback for backwards compatibility
    )
    if travel_domains:
        config['travel_domains'] = travel_domains

    return config


def _substitute_env_vars(config: dict) -> dict:
    """Replace ${VAR} with environment values and handle type conversion"""
    substituted = {}

    for key, value in config.items():
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            var_name = value[2:-1]
            env_value = os.getenv(var_name)
            if env_value:
                # Handle type conversion for known fields
                if key == 'timeout':
                    try:
                        substituted[key] = float(env_value)
                    except ValueError:
                        logger.warning(f"Invalid timeout value: {env_value}, using default")
                        substituted[key] = 30.0
                else:
                    substituted[key] = env_value
            else:
                logger.warning(f"Environment variable not found: {var_name}")
                substituted[key] = value
        else:
            substituted[key] = value

    return substituted


def get_search_manager():
    """Get the configured search manager"""
    return search_manager
