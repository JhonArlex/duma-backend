import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from passlib.hash import argon2

from app.extensions import db
from app.utils.encrypted_type import EncryptedString


class User(db.Model):
    """
    User model for authentication and profile.

    ENCRYPTION NOTES:
    - Sensitive personal data fields are encrypted using EncryptedString
    - Foreign keys (id) are NOT encrypted to allow proper joins
    - The 'email' field has a separate 'email_hash' for lookups
    - Encrypted fields: display_name, phone_number, identificacion, locker_code
    """

    __tablename__ = 'users'

    # Primary key - NOT encrypted (needed for relationships)
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Role - foreign key to roles table
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('roles.id', ondelete='SET NULL'), nullable=True)

    # Email - stored encrypted, with hash for lookups
    email = db.Column(EncryptedString(255), nullable=False)
    email_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Password - already hashed, no additional encryption needed
    password_hash = db.Column(db.String(255), nullable=True)

    # Personal data - ENCRYPTED
    display_name = db.Column(EncryptedString(255), nullable=False)
    phone_number = db.Column(EncryptedString(50), nullable=True)
    identificacion = db.Column(EncryptedString(50), nullable=True)
    locker_code = db.Column(EncryptedString(50), nullable=True)

    # Non-sensitive data - NOT encrypted (needed for queries/filtering)
    photo_url = db.Column(db.Text, nullable=True)
    country = db.Column(db.String(100), default='Venezuela')
    default_currency = db.Column(db.String(10), default='USD')
    email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    auth_provider = db.Column(db.String(50), default='email')
    auth_provider_id = db.Column(db.String(255), nullable=True)

    # Timestamps - NOT encrypted
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    role = db.relationship('Role', back_populates='users')
    addresses = db.relationship('Address', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='user', lazy='dynamic')
    cart = db.relationship('Cart', back_populates='user', uselist=False, cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='user', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        db.Index('idx_users_auth_provider', 'auth_provider', 'auth_provider_id'),
        db.Index('idx_users_role_id', 'role_id'),
    )

    @staticmethod
    def hash_email(email: str) -> str:
        """
        Create a hash of the email for lookup purposes.

        Uses SHA-256 to create a consistent hash that can be indexed.
        """
        import hashlib
        return hashlib.sha256(email.lower().strip().encode()).hexdigest()

    def set_email(self, email: str):
        """Set email and its hash."""
        self.email = email
        self.email_hash = self.hash_email(email)

    @classmethod
    def get_by_email(cls, email: str):
        """Find user by email using the hash."""
        email_hash = cls.hash_email(email)
        return cls.query.filter_by(email_hash=email_hash, is_active=True).first()

    @classmethod
    def email_exists(cls, email: str) -> bool:
        """Check if email already exists."""
        email_hash = cls.hash_email(email)
        return cls.query.filter_by(email_hash=email_hash).first() is not None

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = argon2.hash(password)

    def check_password(self, password):
        """Verify the user's password."""
        if not self.password_hash:
            return False
        return argon2.verify(password, self.password_hash)

    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()

    def has_permission(self, entity: str, action: str) -> bool:
        """Check if user has a specific permission."""
        if not self.role:
            return False
        return self.role.has_permission(entity, action)

    def is_superadmin(self) -> bool:
        """Check if user is a superadmin."""
        if not self.role:
            return False
        return self.role.type == 'superadmin'

    def is_admin(self) -> bool:
        """Check if user is an admin (including superadmin)."""
        if not self.role:
            return False
        return self.role.type in ['superadmin', 'admin']

    def get_role_type(self) -> str:
        """Get the user's role type."""
        if not self.role:
            return 'authenticated'
        return self.role.type

    def to_dict(self, include_sensitive=False, include_role=True):
        """Convert user to dictionary."""
        data = {
            'id': str(self.id),
            'email': self.email,
            'display_name': self.display_name,
            'phone_number': self.phone_number,
            'photo_url': self.photo_url,
            'country': self.country,
            'default_currency': self.default_currency,
            'locker_code': self.locker_code,
            'email_verified': self.email_verified,
            'auth_provider': self.auth_provider,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_role and self.role:
            data['role'] = {
                'id': str(self.role.id),
                'name': self.role.name,
                'type': self.role.type
            }
        if include_sensitive:
            data['identificacion'] = self.identificacion
            data['is_active'] = self.is_active
            data['last_login'] = self.last_login.isoformat() if self.last_login else None
        return data

    def __repr__(self):
        return f'<User {self.id}>'
