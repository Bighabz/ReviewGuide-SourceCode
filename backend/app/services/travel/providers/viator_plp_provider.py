"""
Viator PLP (Product Listing Page) Provider (Stub)

Generates Viator activity search URLs with affiliate links.
Only active when VIATOR_AFFILIATE_ID environment variable is set.
Ready for use once affiliate partnership is approved.
"""
from app.core.centralized_logger import get_logger
from urllib.parse import quote_plus
from app.core.config import settings

logger = get_logger(__name__)


class ViatorPLPLinkGenerator:
    """Generates Viator activity search URLs with affiliate tracking."""

    @staticmethod
    def generate_activity_search_url(
        destination: str,
    ) -> str:
        """
        Generate Viator activity search PLP URL.

        Format: https://www.viator.com/searchResults/all?text={dest}&pid={VIATOR_AFFILIATE_ID}
        """
        encoded_dest = quote_plus(destination)
        base_url = f"https://www.viator.com/searchResults/all?text={encoded_dest}"

        affiliate_id = settings.VIATOR_AFFILIATE_ID
        if affiliate_id:
            base_url += f"&pid={affiliate_id}"

        return base_url
