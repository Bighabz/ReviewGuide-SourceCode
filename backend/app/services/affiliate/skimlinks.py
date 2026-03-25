"""
Skimlinks Link Wrapper Service

Server-side affiliate link wrapping for monetizing product URLs from
non-Amazon, non-eBay sources. Wraps supported merchant URLs with
go.skimresources.com redirect for Skimlinks affiliate tracking.

This is a standalone service (not a BaseAffiliateProvider subclass)
because Skimlinks wraps existing URLs rather than searching for products.
"""

import json
from typing import Optional, Set
from urllib.parse import quote, urlparse

import httpx

from app.core.centralized_logger import get_logger
from app.core.config import settings
from app.core.redis_client import redis_get_with_retry, redis_set_with_retry

logger = get_logger(__name__)

# Domains to NEVER wrap (already have direct affiliate programs)
EXCLUDED_DOMAINS = {
    # Amazon domains (removed from Skimlinks March 2020)
    "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr",
    "amazon.it", "amazon.es", "amazon.ca", "amazon.com.au",
    "amazon.in", "amazon.co.jp", "amazon.com.br", "amazon.sg",
    "amzn.to",
    # eBay domains (own EPN integration)
    "ebay.com", "ebay.co.uk", "ebay.de", "ebay.fr",
    "ebay.it", "ebay.es", "ebay.com.au", "ebay.ca",
}

REDIS_DOMAIN_CACHE_KEY = "skimlinks:merchant_domains"
DOMAIN_CACHE_TTL = 86400  # 24 hours

AUTH_URL = "https://authentication.skimapis.com/access_token"
DOMAINS_URL = "https://merchants.skimapis.com/v4/publisher/{publisher_id}/domains"
LINK_WRAPPER_BASE = "https://go.skimresources.com"


class SkimlinksLinkWrapper:
    """Server-side Skimlinks link wrapper for monetizing product URLs."""

    def __init__(self):
        self.publisher_id = settings.SKIMLINKS_PUBLISHER_ID
        self.domain_id = settings.SKIMLINKS_DOMAIN_ID
        self.site_id = f"{self.publisher_id}X{self.domain_id}"
        self.client_id = settings.SKIMLINKS_CLIENT_ID
        self.client_secret = settings.SKIMLINKS_CLIENT_SECRET
        self.enabled = settings.SKIMLINKS_API_ENABLED
        self._access_token: Optional[str] = None
        self._merchant_domains: Optional[Set[str]] = None

    async def wrap_url(
        self, url: str, xcust: Optional[str] = None
    ) -> str:
        """Wrap a URL with Skimlinks tracking if domain is supported.

        Returns original URL unchanged if not supported or disabled.
        """
        if not self.enabled:
            return url

        domain = self._extract_domain(url)
        if not domain:
            return url

        if domain in EXCLUDED_DOMAINS:
            return url

        domains = await self._get_merchant_domains()
        if domain not in domains:
            return url

        # Construct wrapped URL
        encoded_url = quote(url, safe="")
        wrapped = f"{LINK_WRAPPER_BASE}?id={self.site_id}&xs=1&url={encoded_url}"
        if xcust:
            wrapped += f"&xcust={xcust[:50]}"

        return wrapped

    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        """Extract bare domain from URL (strips www. prefix)."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain or None
        except Exception:
            return None

    async def _get_merchant_domains(self) -> Set[str]:
        """Get merchant domains from in-memory cache, Redis cache, or Merchant API."""
        # In-memory cache (fastest)
        if self._merchant_domains is not None:
            return self._merchant_domains

        # Try Redis cache
        try:
            cached = await redis_get_with_retry(REDIS_DOMAIN_CACHE_KEY)
            if cached:
                self._merchant_domains = set(json.loads(cached))
                return self._merchant_domains
        except Exception as e:
            logger.warning(f"Skimlinks domain cache read failed: {e}")

        # Cache miss -- fetch from API
        self._merchant_domains = await self._fetch_domains_from_api()

        # Write to Redis cache
        try:
            await redis_set_with_retry(
                REDIS_DOMAIN_CACHE_KEY,
                json.dumps(list(self._merchant_domains)),
                ex=DOMAIN_CACHE_TTL,
            )
        except Exception as e:
            logger.warning(f"Skimlinks domain cache write failed: {e}")

        return self._merchant_domains

    async def _fetch_domains_from_api(self) -> Set[str]:
        """Fetch all merchant domains from Skimlinks Merchant API."""
        token = await self._get_access_token()
        if not token:
            return set()

        url = DOMAINS_URL.format(publisher_id=self.publisher_id)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url, params={"access_token": token}
                )
            if resp.status_code != 200:
                logger.error(f"Skimlinks domains API: {resp.status_code}")
                return set()
            data = resp.json()
            domains = {d["domain"] for d in data.get("domains", [])}
            logger.info(f"Skimlinks: fetched {len(domains)} merchant domains")
            return domains
        except Exception as e:
            logger.error(f"Skimlinks domains fetch failed: {e}")
            return set()

    async def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token for Merchant API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(AUTH_URL, json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                })
            if resp.status_code != 200:
                logger.error(f"Skimlinks auth failed: {resp.status_code}")
                return None
            self._access_token = resp.json().get("access_token")
            return self._access_token
        except Exception as e:
            logger.error(f"Skimlinks auth error: {e}")
            return None


# Module-level singleton
skimlinks_wrapper = SkimlinksLinkWrapper()
