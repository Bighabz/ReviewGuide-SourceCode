"""
IP Geolocation Service
Detects user's country from IP address using ipinfo.io
"""
import httpx
from typing import Optional
from app.core.centralized_logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


async def detect_country_from_ip(ip_address: str) -> Optional[str]:
    """
    Detect country code from IP address using ipinfo.io

    Args:
        ip_address: Client IP address

    Returns:
        2-letter ISO country code (e.g., "US", "GB") or None if detection fails

    Example:
        >>> await detect_country_from_ip("8.8.8.8")
        "US"
    """
    try:
        # Skip detection for localhost/private IPs
        if ip_address in ["127.0.0.1", "localhost", "::1"] or ip_address.startswith("192.168.") or ip_address.startswith("10."):
            logger.debug(f"Skipping IP geolocation for local IP: {ip_address}")
            return settings.AMAZON_DEFAULT_COUNTRY

        # Build URL with token if available
        token = getattr(settings, 'IPINFO_TOKEN', None)
        if token:
            url = f"https://ipinfo.io/{ip_address}/json?token={token}"
        else:
            url = f"https://ipinfo.io/{ip_address}/json"
            logger.warning("IPINFO_TOKEN not set - using ipinfo.io without token (limited to 1,000 requests/day)")

        # Make request with timeout
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=3.0)

            if response.status_code == 200:
                data = response.json()
                country_code = data.get("country")

                if country_code and len(country_code) == 2:
                    logger.info(f"Detected country from IP {ip_address}: {country_code}")
                    return country_code.upper()
                else:
                    logger.warning(f"Invalid country code in response: {data}")
            else:
                logger.error(f"IPInfo API error {response.status_code}: {response.text}")

    except httpx.TimeoutException:
        logger.warning(f"IPInfo API timeout for IP: {ip_address}")
    except Exception as e:
        logger.error(f"Failed to detect country from IP {ip_address}: {e}")

    # Return default country on any error
    return settings.AMAZON_DEFAULT_COUNTRY


def extract_client_ip(request) -> str:
    """
    Extract client's real IP address from request
    Handles proxies, load balancers, and CloudFlare

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address
    """
    # Check CloudFlare header first (most reliable if using CF)
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip

    # Check X-Forwarded-For (standard proxy header)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct client IP
    if request.client:
        return request.client.host

    return "127.0.0.1"
