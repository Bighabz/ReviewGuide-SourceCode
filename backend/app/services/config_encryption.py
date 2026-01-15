"""
Config Encryption Service

Encrypts sensitive configuration values (API keys, secrets, tokens, passwords)
using Fernet symmetric encryption from cryptography library.

Encrypted values are stored in database with prefix "encrypted:" to identify them.
"""
from app.core.centralized_logger import get_logger
from cryptography.fernet import Fernet
from typing import Optional
import base64
import os

logger = get_logger(__name__)

# Sensitive config keys that should be encrypted
ENCRYPTED_FIELDS = {
    # API Keys
    "OPENAI_API_KEY",
    "PERPLEXITY_API_KEY",
    "AMADEUS_API_KEY",
    "AMADEUS_API_SECRET",
    "SKYSCANNER_API_KEY",
    "BOOKING_API_KEY",
    "EXPEDIA_API_KEY",
    "EBAY_APP_ID",
    "EBAY_CERT_ID",
    "AMAZON_ACCESS_KEY",
    "AMAZON_SECRET_KEY",
    "IPINFO_TOKEN",

    # Auth & Security
    "SECRET_KEY",
    "ADMIN_PASSWORD",

    # Observability
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
}

# Prefix to identify encrypted values in database
ENCRYPTED_PREFIX = "encrypted:"


class ConfigEncryption:
    """
    Handles encryption/decryption of sensitive config values.

    Uses Fernet symmetric encryption with a master key stored in environment.
    """

    def __init__(self):
        self._fernet = self._get_fernet()

    def _get_fernet(self) -> Optional[Fernet]:
        """Get Fernet cipher instance from master encryption key"""
        try:
            # Try to get encryption key from environment
            encryption_key = os.getenv("CONFIG_ENCRYPTION_KEY")

            if not encryption_key:
                logger.warning("[ConfigEncryption] CONFIG_ENCRYPTION_KEY not set - encryption disabled")
                return None

            # Fernet expects the key as bytes (already base64-encoded)
            # The key from .env is already in the correct format
            return Fernet(encryption_key.encode())

        except Exception as e:
            logger.error(f"[ConfigEncryption] Failed to initialize encryption: {e}")
            return None

    def should_encrypt(self, key: str) -> bool:
        """Check if a config key should be encrypted"""
        return key in ENCRYPTED_FIELDS

    def is_encrypted(self, value: str) -> bool:
        """Check if a value is already encrypted"""
        return isinstance(value, str) and value.startswith(ENCRYPTED_PREFIX)

    def encrypt(self, value: str) -> str:
        """
        Encrypt a config value.

        Args:
            value: Plain text value to encrypt

        Returns:
            Encrypted value with prefix "encrypted:BASE64_ENCRYPTED_DATA"
        """
        if not self._fernet:
            logger.warning("[ConfigEncryption] Encryption disabled - storing plain text")
            return value

        try:
            # Encrypt the value
            encrypted_bytes = self._fernet.encrypt(value.encode())
            encrypted_str = encrypted_bytes.decode()

            # Add prefix to identify as encrypted
            return f"{ENCRYPTED_PREFIX}{encrypted_str}"

        except Exception as e:
            logger.error(f"[ConfigEncryption] Encryption failed: {e}")
            return value

    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt a config value.

        Args:
            encrypted_value: Encrypted value with prefix "encrypted:BASE64_ENCRYPTED_DATA"

        Returns:
            Decrypted plain text value
        """
        if not self.is_encrypted(encrypted_value):
            # Not encrypted, return as-is
            return encrypted_value

        if not self._fernet:
            logger.error("[ConfigEncryption] Cannot decrypt - encryption key not available")
            return encrypted_value

        try:
            # Remove prefix
            encrypted_str = encrypted_value[len(ENCRYPTED_PREFIX):]

            # Decrypt
            decrypted_bytes = self._fernet.decrypt(encrypted_str.encode())
            return decrypted_bytes.decode()

        except Exception as e:
            logger.error(f"[ConfigEncryption] Decryption failed: {e}")
            return encrypted_value

    def mask_value(self, value: str) -> str:
        """
        Mask a sensitive value for display in admin UI.

        Returns:
            "*********" for encrypted/sensitive values
        """
        if self.is_encrypted(value):
            return "*********"

        # For non-encrypted sensitive values (during migration)
        if len(value) > 0:
            return "*********"

        return value


# Global encryption instance
_encryption: Optional[ConfigEncryption] = None


def get_config_encryption() -> ConfigEncryption:
    """Get global config encryption instance (singleton)"""
    global _encryption
    if _encryption is None:
        _encryption = ConfigEncryption()
    return _encryption


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Run this once and store the output in .env as CONFIG_ENCRYPTION_KEY

    Returns:
        Base64-encoded Fernet key
    """
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    # Generate a new encryption key
    print("Generated CONFIG_ENCRYPTION_KEY:")
    print(generate_encryption_key())
    print("\nAdd this to your .env file:")
    print(f"CONFIG_ENCRYPTION_KEY={generate_encryption_key()}")
