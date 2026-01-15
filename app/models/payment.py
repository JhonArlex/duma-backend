import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db


class Payment(db.Model):
    """Payment model for order payments."""

    __tablename__ = 'payments'

    # Provider choices
    PROVIDER_STRIPE = 'stripe'
    PROVIDER_BRAINTREE = 'braintree'
    PROVIDER_PAYPAL = 'paypal'

    # Status choices
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'

    # Payment method choices
    METHOD_CARD = 'card'
    METHOD_BANK_TRANSFER = 'bank_transfer'
    METHOD_WALLET = 'wallet'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id'), nullable=False, index=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    payment_provider = db.Column(db.String(50), nullable=False)
    provider_txn_id = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    status = db.Column(db.String(50), nullable=False, default=STATUS_PENDING)
    payment_method = db.Column(db.String(50), nullable=True)
    card_last_four = db.Column(db.String(4), nullable=True)
    card_brand = db.Column(db.String(50), nullable=True)
    extra_metadata = db.Column('metadata', JSONB, default=dict)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    order = db.relationship('Order', back_populates='payments')
    user = db.relationship('User', back_populates='payments')

    # Indexes
    __table_args__ = (
        db.Index('idx_payments_provider_txn', 'payment_provider', 'provider_txn_id'),
        db.CheckConstraint(
            status.in_([STATUS_PENDING, STATUS_COMPLETED, STATUS_FAILED, STATUS_REFUNDED]),
            name='check_payment_status'
        ),
    )

    def mark_completed(self, provider_txn_id=None):
        """Mark payment as completed."""
        self.status = self.STATUS_COMPLETED
        self.completed_at = datetime.utcnow()
        if provider_txn_id:
            self.provider_txn_id = provider_txn_id

    def mark_failed(self, error_message=None):
        """Mark payment as failed."""
        self.status = self.STATUS_FAILED
        if error_message:
            self.error_message = error_message

    def mark_refunded(self):
        """Mark payment as refunded."""
        self.status = self.STATUS_REFUNDED

    def to_dict(self):
        """Convert payment to dictionary."""
        return {
            'id': str(self.id),
            'order_id': str(self.order_id),
            'user_id': str(self.user_id),
            'payment_provider': self.payment_provider,
            'provider_txn_id': self.provider_txn_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'card_last_four': self.card_last_four,
            'card_brand': self.card_brand,
            'metadata': self.extra_metadata,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f'<Payment {self.id} - {self.status}>'
