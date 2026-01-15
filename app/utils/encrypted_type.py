"""
SQLAlchemy custom type for encrypted columns.

This module provides a custom SQLAlchemy type that automatically
encrypts data before storing and decrypts when retrieving.
"""
from sqlalchemy import TypeDecorator, Text
from typing import Optional

from app.utils.encryption import encrypt_value, decrypt_value, EncryptionError


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type that encrypts/decrypts string values transparently.

    Usage:
        class User(db.Model):
            email = db.Column(EncryptedString(255), nullable=False)
            phone = db.Column(EncryptedString(50))

    Note:
        - Encrypted values are stored as Text (longer than original due to encryption)
        - Do NOT use this for columns that need to be indexed or used in WHERE clauses
        - Do NOT use for foreign keys or relationship columns
        - Searching/filtering on encrypted columns won't work as expected
    """

    impl = Text
    cache_ok = True

    def __init__(self, length: Optional[int] = None):
        """
        Initialize encrypted string type.

        Args:
            length: Original max length (informational only, stored value is longer)
        """
        super().__init__()
        self.length = length

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Encrypt value before storing in database.

        Args:
            value: Plain text value to encrypt
            dialect: SQLAlchemy dialect

        Returns:
            Encrypted value or None
        """
        if value is None:
            return None

        try:
            return encrypt_value(value)
        except EncryptionError:
            # In case of encryption error, you might want to log this
            # For now, we'll raise the error
            raise

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Decrypt value when reading from database.

        Args:
            value: Encrypted value from database
            dialect: SQLAlchemy dialect

        Returns:
            Decrypted plain text value or None
        """
        if value is None:
            return None

        try:
            return decrypt_value(value)
        except EncryptionError:
            # If decryption fails, return the raw value
            # This might happen with old unencrypted data during migration
            # You might want to log this for debugging
            return value


class EncryptedText(EncryptedString):
    """
    Alias for EncryptedString for longer text fields.

    Usage:
        class User(db.Model):
            notes = db.Column(EncryptedText())
    """
    pass


# Mapping of sensitive fields that should be encrypted per model
# This serves as documentation and can be used for migration scripts
ENCRYPTED_FIELDS = {
    'User': [
        'email',           # Email address
        'display_name',    # User's display name
        'phone_number',    # Phone number
        'identificacion',  # ID document number (cedula/DNI)
        'locker_code',     # USA locker code
    ],
    'Address': [
        'address_line_1',  # Street address
        'address_line_2',  # Additional address info
        'city',            # City name
        'state',           # State/province
        'postal_code',     # ZIP/postal code
    ],
    'Payment': [
        'card_last_four',  # Last 4 digits of card (already partially masked)
    ],
}
