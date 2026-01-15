"""
Link Health Checker Service
Monitors affiliate link health and updates database status
"""
from app.core.centralized_logger import get_logger
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import aiohttp
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate_link import AffiliateLink
from app.core.database import AsyncSessionLocal
from app.core.config import settings

logger = get_logger(__name__)


class LinkHealthChecker:
    """
    Link Health Checker Service

    Responsibilities:
    - Check if affiliate links are still valid and accessible
    - Update health status in database
    - Mark dead links as unhealthy
    - Provide statistics on link health
    """

    def __init__(self, timeout: int = 10, max_concurrent: int = 10):
        """
        Initialize health checker

        Args:
            timeout: Request timeout in seconds
            max_concurrent: Maximum concurrent health checks
        """
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                "User-Agent": "ReviewGuide-LinkChecker/1.0"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def check_link_health(self, url: str) -> bool:
        """
        Check if a single link is healthy

        Args:
            url: The affiliate link to check

        Returns:
            True if link is healthy, False otherwise
        """
        if not self.session:
            raise RuntimeError("LinkHealthChecker must be used as async context manager")

        try:
            async with self.session.head(url, allow_redirects=True) as response:
                # Consider 2xx and 3xx status codes as healthy
                is_healthy = response.status < 400

                if not is_healthy:
                    logger.warning(f"Unhealthy link (status {response.status}): {url[:100]}")

                return is_healthy

        except asyncio.TimeoutError:
            logger.warning(f"Timeout checking link: {url[:100]}")
            return False
        except aiohttp.ClientError as e:
            logger.warning(f"Error checking link: {url[:100]} - {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking link: {url[:100]} - {e}")
            return False

    async def check_all_links(self) -> Dict[str, Any]:
        """
        Check health of all affiliate links in database

        Returns:
            Dictionary with statistics:
            - total: Total links checked
            - healthy: Number of healthy links
            - unhealthy: Number of unhealthy links
            - updated: Number of links updated
        """
        logger.info("=" * 80)
        logger.info("LINK HEALTH CHECKER - Starting health check")

        stats = {
            "total": 0,
            "healthy": 0,
            "unhealthy": 0,
            "updated": 0,
            "start_time": datetime.utcnow(),
        }

        try:
            async with AsyncSessionLocal() as db:
                # Get all affiliate links
                result = await db.execute(select(AffiliateLink))
                links = result.scalars().all()

                stats["total"] = len(links)
                logger.info(f"Found {stats['total']} links to check")

                if not links:
                    logger.info("No links to check")
                    return stats

                # Check links in batches to avoid overwhelming servers
                semaphore = asyncio.Semaphore(self.max_concurrent)

                async def check_and_update(link: AffiliateLink):
                    """Check single link and update database"""
                    async with semaphore:
                        is_healthy = await self.check_link_health(link.deeplink)

                        # Update stats
                        if is_healthy:
                            stats["healthy"] += 1
                        else:
                            stats["unhealthy"] += 1

                        # Update database if health status changed
                        if link.healthy != is_healthy:
                            await db.execute(
                                update(AffiliateLink)
                                .where(AffiliateLink.id == link.id)
                                .values(
                                    healthy=is_healthy,
                                    updated_at=datetime.utcnow()
                                )
                            )
                            stats["updated"] += 1
                            logger.info(
                                f"Updated link health: {link.entity_key} "
                                f"({'healthy' if is_healthy else 'unhealthy'})"
                            )

                        return is_healthy

                # Check all links concurrently
                tasks = [check_and_update(link) for link in links]
                await asyncio.gather(*tasks, return_exceptions=True)

                # Commit changes
                await db.commit()

            stats["end_time"] = datetime.utcnow()
            stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()

            logger.info("Link health check complete:")
            logger.info(f"  - Total links: {stats['total']}")
            logger.info(f"  - Healthy: {stats['healthy']}")
            logger.info(f"  - Unhealthy: {stats['unhealthy']}")
            logger.info(f"  - Updated: {stats['updated']}")
            logger.info(f"  - Duration: {stats['duration_seconds']:.2f}s")

            return stats

        except Exception as e:
            logger.error(f"Error during health check: {e}", exc_info=True)
            stats["error"] = str(e)
            return stats

    async def get_health_statistics(self) -> Dict[str, Any]:
        """
        Get current health statistics without checking

        Returns:
            Dictionary with current link health stats
        """
        try:
            if not AsyncSessionLocal:
                return {
                    "error": "Database not initialized",
                    "timestamp": datetime.utcnow(),
                }

            async with AsyncSessionLocal() as db:
                # Count total links
                total_result = await db.execute(select(AffiliateLink))
                total = len(total_result.scalars().all())

                # Count healthy links
                healthy_result = await db.execute(
                    select(AffiliateLink).where(AffiliateLink.healthy == True)
                )
                healthy = len(healthy_result.scalars().all())

                # Count unhealthy links
                unhealthy = total - healthy

                # Calculate health percentage
                health_percentage = (healthy / total * 100) if total > 0 else 0

                return {
                    "total": total,
                    "healthy": healthy,
                    "unhealthy": unhealthy,
                    "health_percentage": round(health_percentage, 2),
                    "timestamp": datetime.utcnow(),
                }

        except Exception as e:
            logger.error(f"Error getting health statistics: {e}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.utcnow(),
            }


async def run_health_check():
    """
    Convenience function to run health check
    Can be called from CLI or cron job
    Uses configuration from settings
    """
    async with LinkHealthChecker(
        timeout=settings.LINK_HEALTH_CHECK_TIMEOUT,
        max_concurrent=settings.LINK_HEALTH_CHECK_MAX_CONCURRENT
    ) as checker:
        stats = await checker.check_all_links()
        return stats


async def get_health_stats():
    """
    Convenience function to get health statistics
    """
    checker = LinkHealthChecker()
    return await checker.get_health_statistics()


# Export
__all__ = ["LinkHealthChecker", "run_health_check", "get_health_stats"]
