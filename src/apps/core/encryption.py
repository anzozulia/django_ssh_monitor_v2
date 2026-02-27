"""
Credential encryption utility using Fernet symmetric encryption.

Provides secure encryption/decryption for SSH credentials stored in the database.
"""

import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""

    pass


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data using Fernet.

    Usage:
        service = EncryptionService()
        encrypted = service.encrypt("my-secret-password")
        decrypted = service.decrypt(encrypted)
    """

    def __init__(self, key: str | None = None):
        """
        Initialize the encryption service.

        Args:
            key: Optional Fernet key. If not provided, uses CREDENTIAL_ENCRYPTION_KEY
                 from Django settings.

        Raises:
            EncryptionError: If no valid key is provided or configured.
        """
        self._key = key or settings.CREDENTIAL_ENCRYPTION_KEY
        if not self._key:
            raise EncryptionError(
                "Encryption key not configured. Set CREDENTIAL_ENCRYPTION_KEY " "in environment variables."
            )

        try:
            self._fernet = Fernet(self._key.encode() if isinstance(self._key, str) else self._key)
        except Exception as e:
            raise EncryptionError(f"Invalid encryption key: {e}") from e

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt.

        Returns:
            Base64-encoded encrypted string.

        Raises:
            EncryptionError: If encryption fails.
        """
        if not plaintext:
            raise EncryptionError("Cannot encrypt empty string")

        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode("utf-8"))
            return encrypted_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Encryption failed: {e}") from e

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: Base64-encoded encrypted string.

        Returns:
            Decrypted plaintext string.

        Raises:
            EncryptionError: If decryption fails (invalid key or corrupted data).
        """
        if not ciphertext:
            raise EncryptionError("Cannot decrypt empty string")

        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except InvalidToken as e:
            logger.error("Decryption failed: Invalid token (wrong key or corrupted data)")
            raise EncryptionError(
                "Decryption failed: Invalid token. This may indicate the encryption key "
                "has changed or the data is corrupted."
            ) from e
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Decryption failed: {e}") from e


def get_encryption_service() -> EncryptionService:
    """
    Factory function to get an EncryptionService instance.

    Returns:
        Configured EncryptionService instance.

    Raises:
        EncryptionError: If encryption key is not configured.
    """
    return EncryptionService()


def encrypt_credential(plaintext: str) -> str:
    """
    Convenience function to encrypt a credential.

    Args:
        plaintext: The credential to encrypt.

    Returns:
        Encrypted credential string.
    """
    return get_encryption_service().encrypt(plaintext)


def decrypt_credential(ciphertext: str) -> str:
    """
    Convenience function to decrypt a credential.

    Args:
        ciphertext: The encrypted credential.

    Returns:
        Decrypted credential string.
    """
    return get_encryption_service().decrypt(ciphertext)


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded Fernet key suitable for CREDENTIAL_ENCRYPTION_KEY.

    Note:
        This is a utility for initial setup. The generated key should be
        stored securely in environment variables, not in code.
    """
    return Fernet.generate_key().decode("utf-8")
