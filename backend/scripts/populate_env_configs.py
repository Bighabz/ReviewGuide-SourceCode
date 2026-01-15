"""
Populate core_config table with all env vars

Reads ALL variables from .env file and inserts them into core_config table.
Automatically encrypts sensitive values (API keys, secrets, passwords) before saving.

This is useful for --reset to have a baseline of configs in the database.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load .env file
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

from app.core.database import init_db, close_db
from app.repositories.config_repository import ConfigRepository
from app.services.config_encryption import get_config_encryption


def parse_env_file(env_file_path: Path) -> list[dict[str, str]]:
    """Parse .env file and return all key-value pairs"""
    configs = []

    if not env_file_path.exists():
        print(f"⚠️  No .env file found at {env_file_path}")
        return configs

    print(f"✅ Reading .env file from {env_file_path}")

    with open(env_file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            # Strip whitespace
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse key=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                configs.append({"key": key, "value": value})

    return configs


async def populate_configs():
    """Populate core_config with ALL variables from .env file (encrypts sensitive values)"""
    print("Populating core_config table with environment variables...")

    # Get encryption service
    encryption = get_config_encryption()

    if not encryption._fernet:
        print("⚠️  CONFIG_ENCRYPTION_KEY not set - sensitive values will NOT be encrypted!")
        print("   Generate a key with: python -m app.services.config_encryption")
        print("   Add it to .env as CONFIG_ENCRYPTION_KEY=<generated_key>")
        print("")
    else:
        print("✅ Encryption enabled - sensitive values will be encrypted")
        print("")

    # Parse .env file directly
    env_file = backend_dir / ".env"
    configs_to_insert = parse_env_file(env_file)

    print(f"Found {len(configs_to_insert)} variables in .env file")

    if len(configs_to_insert) == 0:
        print("⚠️  No variables found in .env file")
        return

    # Initialize database
    await init_db()

    # Import AsyncSessionLocal AFTER init_db() has run
    from app.core.database import AsyncSessionLocal

    # Encrypt sensitive values before inserting
    encrypted_count = 0
    for config in configs_to_insert:
        key = config["key"]
        value = config["value"]

        # Encrypt if this is a sensitive field and encryption is available
        if encryption._fernet and encryption.should_encrypt(key) and value:
            config["value"] = encryption.encrypt(value)
            encrypted_count += 1
            print(f"  🔒 Encrypted: {key}")

    # Insert into database
    async with AsyncSessionLocal() as db:
        repo = ConfigRepository(db)
        count = await repo.bulk_create(configs_to_insert)

    print("")
    print(f"✅ Inserted {count} configs into core_config table")
    print(f"   Encrypted {encrypted_count} sensitive configs")
    print(f"   Skipped {len(configs_to_insert) - count} configs (already exist)")

    # Close database
    await close_db()


if __name__ == "__main__":
    asyncio.run(populate_configs())
