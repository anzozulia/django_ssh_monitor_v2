"""
Unit tests for credential encryption utility.

Tests the EncryptionService class and helper functions.
"""

import pytest
from cryptography.fernet import Fernet

from apps.core.encryption import (
    EncryptionError,
    EncryptionService,
    decrypt_credential,
    encrypt_credential,
    generate_encryption_key,
)


class TestEncryptionService:
    """Tests for EncryptionService class."""

    def test_encrypt_decrypt_roundtrip(self, encryption_service):
        """Test that encrypting and decrypting returns the original value."""
        original = "my-secret-password"
        encrypted = encryption_service.encrypt(original)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == original
        assert encrypted != original  # Should be different from plaintext

    def test_encrypt_produces_different_output_each_time(self, encryption_service):
        """Test that encrypting the same value produces different ciphertext."""
        original = "my-secret-password"
        encrypted1 = encryption_service.encrypt(original)
        encrypted2 = encryption_service.encrypt(original)

        # Fernet uses timestamps/IVs, so same input produces different output
        assert encrypted1 != encrypted2

        # But both should decrypt to the same value
        assert encryption_service.decrypt(encrypted1) == original
        assert encryption_service.decrypt(encrypted2) == original

    def test_encrypt_empty_string_raises_error(self, encryption_service):
        """Test that encrypting an empty string raises EncryptionError."""
        with pytest.raises(EncryptionError, match="Cannot encrypt empty string"):
            encryption_service.encrypt("")

    def test_decrypt_empty_string_raises_error(self, encryption_service):
        """Test that decrypting an empty string raises EncryptionError."""
        with pytest.raises(EncryptionError, match="Cannot decrypt empty string"):
            encryption_service.decrypt("")

    def test_decrypt_invalid_ciphertext_raises_error(self, encryption_service):
        """Test that decrypting invalid ciphertext raises EncryptionError."""
        with pytest.raises(EncryptionError, match="Invalid token"):
            encryption_service.decrypt("not-valid-ciphertext")

    def test_decrypt_with_wrong_key_raises_error(self, encryption_key, settings):
        """Test that decrypting with wrong key raises EncryptionError."""
        # Encrypt with one key
        settings.CREDENTIAL_ENCRYPTION_KEY = encryption_key
        service1 = EncryptionService()
        encrypted = service1.encrypt("secret")

        # Try to decrypt with different key
        settings.CREDENTIAL_ENCRYPTION_KEY = Fernet.generate_key().decode("utf-8")
        service2 = EncryptionService()

        with pytest.raises(EncryptionError, match="Invalid token"):
            service2.decrypt(encrypted)

    def test_service_without_key_raises_error(self, settings):
        """Test that creating service without key raises EncryptionError."""
        settings.CREDENTIAL_ENCRYPTION_KEY = ""

        with pytest.raises(EncryptionError, match="Encryption key not configured"):
            EncryptionService()

    def test_service_with_invalid_key_raises_error(self, settings):
        """Test that creating service with invalid key raises EncryptionError."""
        settings.CREDENTIAL_ENCRYPTION_KEY = "not-a-valid-fernet-key"

        with pytest.raises(EncryptionError, match="Invalid encryption key"):
            EncryptionService()

    def test_encrypt_long_string(self, encryption_service):
        """Test encrypting a long string (like an SSH private key)."""
        # Simulate an SSH private key
        long_string = "-----BEGIN RSA PRIVATE KEY-----\n" + "x" * 1000 + "\n-----END RSA PRIVATE KEY-----"

        encrypted = encryption_service.encrypt(long_string)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == long_string

    def test_encrypt_unicode_characters(self, encryption_service):
        """Test encrypting strings with unicode characters."""
        unicode_string = "пароль-密码-🔐"

        encrypted = encryption_service.encrypt(unicode_string)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == unicode_string


class TestHelperFunctions:
    """Tests for convenience functions."""

    def test_generate_encryption_key_returns_valid_key(self):
        """Test that generate_encryption_key returns a valid Fernet key."""
        key = generate_encryption_key()

        # Should be a string
        assert isinstance(key, str)

        # Should be valid for Fernet
        fernet = Fernet(key.encode())
        assert fernet is not None

    def test_encrypt_credential_function(self, encryption_key, settings):
        """Test the encrypt_credential convenience function."""
        settings.CREDENTIAL_ENCRYPTION_KEY = encryption_key

        encrypted = encrypt_credential("test-password")
        assert encrypted != "test-password"
        assert len(encrypted) > 0

    def test_decrypt_credential_function(self, encryption_key, settings):
        """Test the decrypt_credential convenience function."""
        settings.CREDENTIAL_ENCRYPTION_KEY = encryption_key

        encrypted = encrypt_credential("test-password")
        decrypted = decrypt_credential(encrypted)

        assert decrypted == "test-password"
