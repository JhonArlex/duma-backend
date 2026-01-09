import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db


class Store(db.Model):
    """Store model for supported e-commerce platforms."""

    __tablename__ = 'stores'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    base_url = db.Column(db.Text, nullable=False)
    logo_url = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    config = db.Column(JSONB, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='store', lazy='dynamic')
    cart_items = db.relationship('CartItem', back_populates='store', lazy='dynamic')

    def to_dict(self):
        """Convert store to dictionary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
            'base_url': self.base_url,
            'logo_url': self.logo_url,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'config': self.config,
        }

    @classmethod
    def get_active_stores(cls):
        """Get all active stores ordered by display_order."""
        return cls.query.filter_by(is_active=True).order_by(cls.display_order).all()

    @classmethod
    def get_by_slug(cls, slug):
        """Get store by slug."""
        return cls.query.filter_by(slug=slug, is_active=True).first()

    def __repr__(self):
        return f'<Store {self.name}>'
