import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Cart(db.Model):
    """Cart model for shopping cart functionality."""

    __tablename__ = 'carts'

    STATUS_ACTIVE = 'active'
    STATUS_ABANDONED = 'abandoned'
    STATUS_CONVERTED = 'converted'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default=STATUS_ACTIVE)
    currency = db.Column(db.String(10), default='USD')
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='cart')
    items = db.relationship('CartItem', back_populates='cart', lazy='dynamic', cascade='all, delete-orphan')

    # Constraints
    __table_args__ = (
        db.CheckConstraint(
            status.in_([STATUS_ACTIVE, STATUS_ABANDONED, STATUS_CONVERTED]),
            name='check_cart_status'
        ),
    )

    @property
    def item_count(self):
        """Get total number of items in cart."""
        return sum(item.quantity for item in self.items)

    @property
    def subtotal(self):
        """Calculate cart subtotal."""
        return sum(item.quantity * item.unit_price for item in self.items) or Decimal('0')

    def add_item(self, product_url, unit_price, quantity=1, **kwargs):
        """Add item to cart or update quantity if exists."""
        existing_item = self.items.filter_by(product_url=product_url).first()
        if existing_item:
            existing_item.quantity += quantity
            existing_item.unit_price = unit_price
            for key, value in kwargs.items():
                if hasattr(existing_item, key):
                    setattr(existing_item, key, value)
            return existing_item
        else:
            item = CartItem(
                cart_id=self.id,
                product_url=product_url,
                unit_price=unit_price,
                quantity=quantity,
                **kwargs
            )
            db.session.add(item)
            return item

    def remove_item(self, item_id):
        """Remove item from cart."""
        item = self.items.filter_by(id=item_id).first()
        if item:
            db.session.delete(item)
            return True
        return False

    def clear(self):
        """Clear all items from cart."""
        self.items.delete()

    def to_dict(self, include_items=True):
        """Convert cart to dictionary."""
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'status': self.status,
            'currency': self.currency,
            'item_count': self.item_count,
            'subtotal': float(self.subtotal),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        return data

    def __repr__(self):
        return f'<Cart {self.id} - {self.item_count} items>'


class CartItem(db.Model):
    """Cart item model for individual products in a cart."""

    __tablename__ = 'cart_items'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = db.Column(UUID(as_uuid=True), db.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False, index=True)
    store_id = db.Column(UUID(as_uuid=True), db.ForeignKey('stores.id'), nullable=True)
    product_url = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    variant_size = db.Column(db.String(100), nullable=True)
    variant_color = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cart = db.relationship('Cart', back_populates='items')
    store = db.relationship('Store', back_populates='cart_items')

    # Constraints
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_cart_item_quantity'),
    )

    @property
    def total_price(self):
        """Calculate total price for this item."""
        return self.quantity * self.unit_price

    def to_dict(self):
        """Convert cart item to dictionary."""
        return {
            'id': str(self.id),
            'cart_id': str(self.cart_id),
            'store_id': str(self.store_id) if self.store_id else None,
            'store_name': self.store.name if self.store else None,
            'product_url': self.product_url,
            'title': self.title,
            'image_url': self.image_url,
            'variant_size': self.variant_size,
            'variant_color': self.variant_color,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price),
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<CartItem {self.title[:30] if self.title else self.id}>'
