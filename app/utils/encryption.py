"""
Encryption module for sensitive user data.

This module provides encryption/decryption utilities using Fernet symmetric encryption.
Only personal data fields are encrypted, NOT foreign keys or relationships,
to allow proper database joins and queries.
"""
import base64
import os
from typing import Optional, Union
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app


class EncryptionError(Exception):
    """Custom exception for encryption errors."""
    pass


class EncryptionManager:
    """
    Manager for encrypting and decrypting sensitive data.

    Uses Fernet symmetric encryption with a key derived from
    a master secret key using PBKDF2.
    """

    _instance = None
    _fernet = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance."""
        if self._fernet is None:
            self._fernet = self._create_fernet()
        return self._fernet

    def _create_fernet(self) -> Fernet:
        """Create Fernet instance from encryption key."""
        encryption_key = self._get_encryption_key()
        return Fernet(encryption_key)

    def _get_encryption_key(self) -> bytes:
        """
        Derive encryption key from master secret.

        Uses PBKDF2 to derive a Fernet-compatible key from
        the configured master encryption key.
        """
        try:
            master_key = current_app.config.get('ENCRYPTION_KEY')
            if not master_key:
                raise EncryptionError(
                    'ENCRYPTION_KEY not configured. '
                    'Set it in your environment variables.'
                )

            # Use a fixed salt (should be stored securely in production)
            # In production, consider storing this separately
            salt = current_app.config.get(
                'ENCRYPTION_SALT',
                b'duma_express_salt_2024'
            )

            if isinstance(salt, str):
                salt = salt.encode()

            if isinstance(master_key, str):
                master_key = master_key.encode()

            # Derive a key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )

            key = base64.urlsafe_b64encode(kdf.derive(master_key))
            return key

        except Exception as e:
            if isinstance(e, EncryptionError):
                raise
            raise EncryptionError(f'Failed to derive encryption key: {str(e)}')

    def encrypt(self, data: Union[str, None]) -> Optional[str]:
        """
        Encrypt a string value.

        Args:
            data: Plain text string to encrypt

        Returns:
            Base64 encoded encrypted string, or None if input is None
        """
        if data is None:
            return None

        if not isinstance(data, str):
            data = str(data)

        try:
            fernet = self._get_fernet()
            encrypted = fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise EncryptionError(f'Encryption failed: {str(e)}')

    def decrypt(self, encrypted_data: Union[str, None]) -> Optional[str]:
        """
        Decrypt an encrypted string value.

        Args:
            encrypted_data: Base64 encoded encrypted string

        Returns:
            Decrypted plain text string, or None if input is None
        """
        if encrypted_data is None:
            return None

        try:
            fernet = self._get_fernet()
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = fernet.decrypt(decoded)
            return decrypted.decode('utf-8')
        except InvalidToken:
            raise EncryptionError(
                'Decryption failed: Invalid token. '
                'Data may be corrupted or encrypted with a different key.'
            )
        except Exception as e:
            raise EncryptionError(f'Decryption failed: {str(e)}')

    def rotate_key(self, old_key: str, new_key: str, encrypted_data: str) -> str:
        """
        Re-encrypt data with a new key.

        Useful for key rotation scenarios.

        Args:
            old_key: The old encryption key
            new_key: The new encryption key
            encrypted_data: Data encrypted with the old key

        Returns:
            Data encrypted with the new key
        """
        # Temporarily use old key to decrypt
        old_fernet = self._create_fernet_with_key(old_key)
        decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted = old_fernet.decrypt(decoded).decode('utf-8')

        # Encrypt with new key
        new_fernet = self._create_fernet_with_key(new_key)
        encrypted = new_fernet.encrypt(decrypted.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')

    def _create_fernet_with_key(self, key: str) -> Fernet:
        """Create a Fernet instance with a specific key."""
        salt = current_app.config.get('ENCRYPTION_SALT', b'duma_express_salt_2024')
        if isinstance(salt, str):
            salt = salt.encode()
        if isinstance(key, str):
            key = key.encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))
        return Fernet(derived_key)

    def reset(self):
        """Reset the cached Fernet instance. Useful for testing."""
        self._fernet = None


# Global encryption manager instance
encryption_manager = EncryptionManager()


def encrypt_value(value: Union[str, None]) -> Optional[str]:
    """Convenience function to encrypt a value."""
    return encryption_manager.encrypt(value)


def decrypt_value(value: Union[str, None]) -> Optional[str]:
    """Convenience function to decrypt a value."""
    return encryption_manager.decrypt(value)


def generate_encryption_key() -> str:
    """
    Generate a new random encryption key.

    Use this to generate a key for ENCRYPTION_KEY config.

    Returns:
        A secure random key string
    """
    return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
