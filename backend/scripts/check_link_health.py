#!/usr/bin/env python3
"""
CLI script to manually run link health checker
Usage: python scripts/check_link_health.py [--stats-only]
"""
import asyncio
import sys
import argparse
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
env_file = backend_dir / ".env"
load_dotenv(env_file)


async def main():
    """Main CLI entry point"""
    # Initialize database connection FIRST
    from app.core.database import init_db
    await init_db()

    # NOW import health checker functions (after DB is initialized)
    from app.services.link_health_checker import run_health_check, get_health_stats

    parser = argparse.ArgumentParser(
        description="Check health of affiliate links"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show current statistics without checking links"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=10,
        help="Maximum concurrent health checks (default: 10)"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("LINK HEALTH CHECKER CLI")
    print("=" * 80)

    if args.stats_only:
        print("\nFetching current statistics...\n")
        stats = await get_health_stats()

        if "error" in stats:
            print(f"❌ Error: {stats['error']}")
            return 1

        print(f"📊 Link Health Statistics:")
        print(f"   Total Links:       {stats['total']}")
        print(f"   Healthy Links:     {stats['healthy']} ✅")
        print(f"   Unhealthy Links:   {stats['unhealthy']} ⚠️")
        print(f"   Health Percentage: {stats['health_percentage']:.1f}%")
        print(f"   Timestamp:         {stats['timestamp']}")
        print()

    else:
        print("\n🔍 Starting link health check...\n")

        from app.services.link_health_checker import LinkHealthChecker

        async with LinkHealthChecker(
            timeout=args.timeout,
            max_concurrent=args.max_concurrent
        ) as checker:
            stats = await checker.check_all_links()

        if "error" in stats:
            print(f"❌ Error: {stats['error']}")
            return 1

        print()
        print("=" * 80)
        print("✅ HEALTH CHECK COMPLETE")
        print("=" * 80)
        print(f"Total Links Checked:  {stats['total']}")
        print(f"Healthy Links:        {stats['healthy']} ✅")
        print(f"Unhealthy Links:      {stats['unhealthy']} ⚠️")
        print(f"Links Updated:        {stats['updated']}")
        print(f"Duration:             {stats.get('duration_seconds', 0):.2f}s")
        print()

        # Calculate health percentage
        if stats['total'] > 0:
            health_pct = (stats['healthy'] / stats['total']) * 100
            print(f"Health Percentage:    {health_pct:.1f}%")

            if health_pct < 50:
                print("\n⚠️  WARNING: Less than 50% of links are healthy!")
            elif health_pct < 80:
                print("\n⚠️  NOTICE: Link health is below 80%")
            else:
                print("\n✅ Link health is good!")

        print()

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
