import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.utils.encrypted_type import EncryptedString


class Address(db.Model):
    """
    Address model for user shipping addresses.

    ENCRYPTION NOTES:
    - Address details are encrypted as they contain personal location data
    - Foreign keys (id, user_id) are NOT encrypted to allow proper joins
    - 'type', 'is_default', 'country' are NOT encrypted (needed for filtering)
    - Encrypted fields: label, address_line_1, address_line_2, city, state, postal_code
    """

    __tablename__ = 'addresses'

    # Primary key - NOT encrypted (needed for relationships)
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key - NOT encrypted (needed for joins)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Address type - NOT encrypted (needed for filtering)
    type = db.Column(db.String(20), nullable=False)  # 'usa_locker', 'vzla_home', 'other'

    # Address details - ENCRYPTED
    label = db.Column(EncryptedString(100), nullable=True)  # 'Casa', 'Oficina', etc.
    address_line_1 = db.Column(EncryptedString(255), nullable=False)
    address_line_2 = db.Column(EncryptedString(255), nullable=True)
    city = db.Column(EncryptedString(100), nullable=False)
    state = db.Column(EncryptedString(100), nullable=True)
    postal_code = db.Column(EncryptedString(20), nullable=True)

    # Country - NOT encrypted (might be needed for filtering/reports)
    country = db.Column(db.String(100), nullable=False)

    # Flags - NOT encrypted
    is_default = db.Column(db.Boolean, default=False)

    # Timestamps - NOT encrypted
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='addresses')
    orders = db.relationship('Order', back_populates='shipping_address', lazy='dynamic')

    # Constraint for type values
    __table_args__ = (
        db.CheckConstraint(
            type.in_(['usa_locker', 'vzla_home', 'other', 'shipping']),
            name='check_address_type'
        ),
    )

    def to_dict(self):
        """Convert address to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'type': self.type,
            'label': self.label,
            'address_line_1': self.address_line_1,
            'address_line_2': self.address_line_2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [self.address_line_1]
        if self.address_line_2:
            parts.append(self.address_line_2)
        parts.append(f'{self.city}, {self.state or ""} {self.postal_code or ""}'.strip())
        parts.append(self.country)
        return ', '.join(filter(None, parts))

    def __repr__(self):
        return f'<Address {self.id}>'
