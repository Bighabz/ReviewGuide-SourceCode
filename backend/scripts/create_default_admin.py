"""
Create default admin user

Creates a default admin user with username 'admin' and password 'admin123456'
This is used during database reset to ensure there's always an admin account.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import init_db, close_db
from app.repositories.admin_user_repository import AdminUserRepository
from app.utils.auth import hash_password


async def create_default_admin():
    """Create default admin user if it doesn't exist"""
    print("Creating default admin user...")

    # Initialize database
    await init_db()

    # Import AsyncSessionLocal AFTER init_db() has run
    from app.core.database import AsyncSessionLocal

    # Create admin user
    async with AsyncSessionLocal() as db:
        repo = AdminUserRepository(db)

        # Check if admin user already exists
        existing_admin = await repo.get_by_username("admin")

        if existing_admin:
            print("⚠️  Admin user already exists, skipping creation")
        else:
            # Hash the password
            password_hash = hash_password("admin123456")

            # Create new admin user
            await repo.create(
                username="admin",
                email="admin@reviewguide.ai",
                password_hash=password_hash
            )
            print("✅ Default admin user created successfully")
            print("")
            print("   Username: admin")
            print("   Password: admin123456")
            print("   Email:    admin@reviewguide.ai")
            print("")
            print("   ⚠️  IMPORTANT: Change this password after first login!")

    # Close database
    await close_db()


if __name__ == "__main__":
    asyncio.run(create_default_admin())
