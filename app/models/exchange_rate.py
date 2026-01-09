import uuid
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db


class ExchangeRate(db.Model):
    """Exchange rate model for currency conversion."""

    __tablename__ = 'exchange_rates'

    # Source choices
    SOURCE_BCV = 'bcv'
    SOURCE_PARALLEL = 'parallel'
    SOURCE_MANUAL = 'manual'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Numeric(18, 4), nullable=False)
    source = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    effective_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        db.Index('idx_exchange_rates_currencies', 'from_currency', 'to_currency'),
        db.Index('idx_exchange_rates_active', 'is_active', 'effective_date'),
    )

    @classmethod
    def get_current_rate(cls, from_currency='USD', to_currency='VES'):
        """Get the current active exchange rate."""
        return cls.query.filter_by(
            from_currency=from_currency,
            to_currency=to_currency,
            is_active=True
        ).order_by(cls.effective_date.desc()).first()

    @classmethod
    def create_rate(cls, from_currency, to_currency, rate, source=None):
        """Create a new exchange rate and deactivate previous ones."""
        # Deactivate previous rates for this currency pair
        cls.query.filter_by(
            from_currency=from_currency,
            to_currency=to_currency,
            is_active=True
        ).update({'is_active': False})

        # Create new rate
        new_rate = cls(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            source=source,
            is_active=True,
            effective_date=date.today()
        )
        db.session.add(new_rate)
        return new_rate

    def convert(self, amount):
        """Convert amount using this rate."""
        return float(amount) * float(self.rate)

    def to_dict(self):
        """Convert exchange rate to dictionary."""
        return {
            'id': str(self.id),
            'from_currency': self.from_currency,
            'to_currency': self.to_currency,
            'rate': float(self.rate),
            'source': self.source,
            'is_active': self.is_active,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<ExchangeRate {self.from_currency}/{self.to_currency} = {self.rate}>'
