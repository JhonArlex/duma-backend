import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class Order(db.Model):
    """Order model for customer orders."""

    __tablename__ = 'orders'

    # Status choices
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_REFUNDED = 'refunded'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    shipping_address_id = db.Column(UUID(as_uuid=True), db.ForeignKey('addresses.id'), nullable=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False, default=STATUS_PENDING, index=True)
    payment_status = db.Column(db.String(50), nullable=False, default=PAYMENT_STATUS_PENDING)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    platform_fee = db.Column(db.Numeric(12, 2), default=Decimal('0'))
    shipping_usa = db.Column(db.Numeric(12, 2), default=Decimal('0'))
    shipping_vzla = db.Column(db.Numeric(12, 2), default=Decimal('0'))
    taxes_estimated = db.Column(db.Numeric(12, 2), default=Decimal('0'))
    total_usd = db.Column(db.Numeric(12, 2), nullable=False)
    total_bs = db.Column(db.Numeric(18, 2), nullable=True)
    exchange_rate = db.Column(db.Numeric(12, 4), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)
    shipped_at = db.Column(db.DateTime(timezone=True), nullable=True)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    user = db.relationship('User', back_populates='orders')
    shipping_address = db.relationship('Address', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='order', lazy='dynamic')
    status_history = db.relationship('OrderStatusHistory', back_populates='order', lazy='dynamic', cascade='all, delete-orphan')

    # Constraints
    __table_args__ = (
        db.CheckConstraint(
            status.in_([STATUS_PENDING, STATUS_PROCESSING, STATUS_SHIPPED, STATUS_DELIVERED, STATUS_CANCELLED]),
            name='check_order_status'
        ),
        db.CheckConstraint(
            payment_status.in_([PAYMENT_STATUS_PENDING, PAYMENT_STATUS_PAID, PAYMENT_STATUS_FAILED, PAYMENT_STATUS_REFUNDED]),
            name='check_payment_status'
        ),
    )

    def calculate_totals(self):
        """Recalculate order totals from items."""
        self.subtotal = sum(item.total_price for item in self.items) or Decimal('0')
        self.total_usd = (
            self.subtotal +
            (self.platform_fee or Decimal('0')) +
            (self.shipping_usa or Decimal('0')) +
            (self.shipping_vzla or Decimal('0')) +
            (self.taxes_estimated or Decimal('0'))
        )
        if self.exchange_rate:
            self.total_bs = self.total_usd * self.exchange_rate

    def update_status(self, new_status, changed_by=None, notes=None):
        """Update order status and log to history."""
        old_status = self.status
        self.status = new_status

        # Update timestamps based on status
        if new_status == self.STATUS_SHIPPED:
            self.shipped_at = datetime.utcnow()
        elif new_status == self.STATUS_DELIVERED:
            self.delivered_at = datetime.utcnow()

        # Create history entry
        history = OrderStatusHistory(
            order_id=self.id,
            previous_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes
        )
        db.session.add(history)

    def to_dict(self, include_items=False):
        """Convert order to dictionary."""
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'order_number': self.order_number,
            'status': self.status,
            'payment_status': self.payment_status,
            'subtotal': float(self.subtotal),
            'platform_fee': float(self.platform_fee or 0),
            'shipping_usa': float(self.shipping_usa or 0),
            'shipping_vzla': float(self.shipping_vzla or 0),
            'taxes_estimated': float(self.taxes_estimated or 0),
            'total_usd': float(self.total_usd),
            'total_bs': float(self.total_bs) if self.total_bs else None,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
        }
        if self.shipping_address:
            data['shipping_address'] = self.shipping_address.to_dict()
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        return data

    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    """Order item model for individual products in an order."""

    __tablename__ = 'order_items'

    STATUS_PENDING = 'pending'
    STATUS_PURCHASED = 'purchased'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    store_id = db.Column(UUID(as_uuid=True), db.ForeignKey('stores.id'), nullable=True, index=True)
    product_url = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    variant_size = db.Column(db.String(100), nullable=True)
    variant_color = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    order = db.relationship('Order', back_populates='items')
    store = db.relationship('Store', back_populates='order_items')

    # Constraints
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_order_item_quantity'),
        db.CheckConstraint(
            status.in_([STATUS_PENDING, STATUS_PURCHASED, STATUS_SHIPPED, STATUS_DELIVERED]),
            name='check_order_item_status'
        ),
    )

    def calculate_total(self):
        """Calculate total price from quantity and unit price."""
        self.total_price = self.quantity * self.unit_price

    def to_dict(self):
        """Convert order item to dictionary."""
        return {
            'id': str(self.id),
            'order_id': str(self.order_id),
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
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<OrderItem {self.title[:30] if self.title else self.id}>'


class OrderStatusHistory(db.Model):
    """Order status history for tracking status changes."""

    __tablename__ = 'order_status_history'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    previous_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    changed_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    order = db.relationship('Order', back_populates='status_history')

    def to_dict(self):
        """Convert status history to dictionary."""
        return {
            'id': str(self.id),
            'order_id': str(self.order_id),
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'changed_by': str(self.changed_by) if self.changed_by else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<OrderStatusHistory {self.previous_status} -> {self.new_status}>'
