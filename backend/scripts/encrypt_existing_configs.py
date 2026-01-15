"""
Migration Script: Encrypt Existing Sensitive Configs

Encrypts all sensitive configuration values in the database that are currently stored as plain text.
This is a one-time migration after implementing the config encryption system.

Usage:
    PYTHONPATH=/Users/truongnguyen/WORK/AI/TRAVEL_1/backend python backend/scripts/encrypt_existing_configs.py

Requirements:
    - CONFIG_ENCRYPTION_KEY must be set in .env
    - Database must be accessible
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Load .env file
env_file = Path(backend_dir) / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded .env from: {env_file}")
else:
    print(f"Warning: .env file not found at {env_file}")

from app.core.database import AsyncSessionLocal
from app.repositories.config_repository import ConfigRepository
from app.services.config_encryption import get_config_encryption, ENCRYPTED_FIELDS
from app.core.centralized_logger import get_logger

logger = get_logger(__name__)


async def encrypt_existing_configs():
    """
    Encrypt all sensitive configs in database that are currently plain text.

    Process:
    1. Get all configs from database
    2. Filter for sensitive keys (in ENCRYPTED_FIELDS)
    3. Check if already encrypted (has 'encrypted:' prefix)
    4. If not encrypted, encrypt and update in database
    """
    from app.core.database import AsyncSessionLocal as get_session

    encryption = get_config_encryption()

    # Check if encryption is available
    if not encryption._fernet:
        logger.error("CONFIG_ENCRYPTION_KEY not set - cannot encrypt configs")
        logger.error("Generate a key with: python -m app.services.config_encryption")
        return False

    logger.info("Starting encryption of existing sensitive configs...")
    logger.info(f"Sensitive fields to encrypt: {ENCRYPTED_FIELDS}")

    encrypted_count = 0
    already_encrypted_count = 0
    skipped_count = 0

    async with get_session() as db:
        repo = ConfigRepository(db)

        # Get all configs
        all_configs = await repo.get_all()
        logger.info(f"Found {len(all_configs)} total configs in database")

        for config in all_configs:
            key = config["key"]
            value = config["value"]
            config_id = config["id"]

            # Check if this is a sensitive field
            if key not in ENCRYPTED_FIELDS:
                continue

            # Check if already encrypted
            if encryption.is_encrypted(value):
                logger.info(f"✓ {key} - Already encrypted")
                already_encrypted_count += 1
                continue

            # Skip empty values
            if not value or value.strip() == "":
                logger.info(f"⊘ {key} - Skipping (empty value)")
                skipped_count += 1
                continue

            # Encrypt the value
            try:
                encrypted_value = encryption.encrypt(value)

                # Update in database
                await repo.update(config_id, encrypted_value)

                logger.info(f"✓ {key} - Encrypted successfully")
                encrypted_count += 1

            except Exception as e:
                logger.error(f"✗ {key} - Failed to encrypt: {e}")

    # Summary
    logger.info("\n" + "="*60)
    logger.info("ENCRYPTION MIGRATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total configs in database: {len(all_configs)}")
    logger.info(f"Newly encrypted: {encrypted_count}")
    logger.info(f"Already encrypted: {already_encrypted_count}")
    logger.info(f"Skipped (empty): {skipped_count}")
    logger.info(f"Total sensitive configs: {encrypted_count + already_encrypted_count + skipped_count}")
    logger.info("="*60)

    if encrypted_count > 0:
        logger.info("\n✓ Migration completed successfully!")
        logger.info("All sensitive configs are now encrypted in the database.")
        return True
    elif already_encrypted_count > 0:
        logger.info("\n✓ All sensitive configs were already encrypted.")
        return True
    else:
        logger.warning("\nNo sensitive configs found to encrypt.")
        return True


async def verify_encryption():
    """
    Verify that all sensitive configs are encrypted.
    """
    from app.core.database import AsyncSessionLocal as get_session

    encryption = get_config_encryption()

    logger.info("\n" + "="*60)
    logger.info("VERIFICATION: Checking encryption status...")
    logger.info("="*60)

    async with get_session() as db:
        repo = ConfigRepository(db)
        all_configs = await repo.get_all()

        unencrypted_sensitive = []

        for config in all_configs:
            key = config["key"]
            value = config["value"]

            # Check sensitive fields
            if key in ENCRYPTED_FIELDS:
                if value and not encryption.is_encrypted(value):
                    unencrypted_sensitive.append(key)
                    logger.warning(f"✗ {key} - NOT ENCRYPTED!")
                else:
                    logger.info(f"✓ {key} - Encrypted")

        if unencrypted_sensitive:
            logger.error(f"\n✗ Found {len(unencrypted_sensitive)} unencrypted sensitive configs:")
            for key in unencrypted_sensitive:
                logger.error(f"  - {key}")
            return False
        else:
            logger.info("\n✓ All sensitive configs are properly encrypted!")
            return True


async def main():
    """Main migration function"""
    from app.core.database import init_db, close_db

    logger.info("="*60)
    logger.info("CONFIG ENCRYPTION MIGRATION")
    logger.info("="*60)

    # Initialize database connection
    try:
        await init_db()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

    try:
        # Step 1: Encrypt existing configs
        success = await encrypt_existing_configs()

        if not success:
            logger.error("Migration failed!")
            sys.exit(1)

        # Step 2: Verify encryption
        verified = await verify_encryption()

        if verified:
            logger.info("\n✓ Migration and verification completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n✗ Verification failed!")
            sys.exit(1)
    finally:
        # Close database connection
        await close_db()
        logger.info("Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
