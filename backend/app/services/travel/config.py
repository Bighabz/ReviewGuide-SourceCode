"""
Travel Provider Configuration
Simplified - Uses loader system for automatic provider discovery
"""
from app.core.centralized_logger import get_logger
from pathlib import Path
from .loader import setup_providers
from .manager import travel_manager

logger = get_logger(__name__)


def setup_travel_providers(config_path: str = None) -> None:
    """
    Setup travel providers from configuration

    Args:
        config_path: Path to YAML config file (optional)
                    Default: looks for backend/config/travel.yaml
                    If not found, loads from environment variables

    Usage:
        # Auto-detect config file or use env vars
        setup_travel_providers()

        # Use specific config file
        setup_travel_providers("config/travel.yaml")

        # Use environment variables only
        setup_travel_providers(config_path=None)

    Configuration Methods:
        1. YAML file (recommended): config/travel.yaml
        2. Environment variables: TRAVEL_HOTEL_PROVIDERS=mock,booking
    """

    # Default config path
    if config_path is None:
        default_path = Path(__file__).parent.parent.parent.parent / "config" / "travel.yaml"
        if default_path.exists():
            config_path = str(default_path)

    # Use the loader system
    setup_providers(config_path=config_path, use_env=True)


def get_travel_manager():
    """Get the configured travel manager instance"""
    return travel_manager
