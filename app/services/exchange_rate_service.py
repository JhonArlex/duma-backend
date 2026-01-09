from typing import Optional, Tuple
from decimal import Decimal
from datetime import date
from flask import current_app
import requests

from app.extensions import db
from app.models.exchange_rate import ExchangeRate


class ExchangeRateService:
    """Service for handling exchange rate operations."""

    @staticmethod
    def get_current_rate(
        from_currency: str = 'USD',
        to_currency: str = 'VES'
    ) -> Optional[ExchangeRate]:
        """Get the current active exchange rate."""
        return ExchangeRate.get_current_rate(from_currency, to_currency)

    @staticmethod
    def create_rate(
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        source: Optional[str] = None
    ) -> ExchangeRate:
        """Create a new exchange rate."""
        exchange_rate = ExchangeRate.create_rate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            source=source
        )
        db.session.commit()
        return exchange_rate

    @staticmethod
    def convert_amount(
        amount: Decimal,
        from_currency: str = 'USD',
        to_currency: str = 'VES'
    ) -> Tuple[Optional[Decimal], Optional[ExchangeRate]]:
        """
        Convert amount between currencies.

        Returns:
            Tuple of (converted_amount, exchange_rate_used).
        """
        rate = ExchangeRate.get_current_rate(from_currency, to_currency)
        if not rate:
            return None, None

        converted = Decimal(str(amount)) * rate.rate
        return converted, rate

    @classmethod
    def fetch_external_rate(cls, source: str = 'parallel') -> Tuple[Optional[Decimal], Optional[str]]:
        """
        Fetch exchange rate from external API.

        Returns:
            Tuple of (rate, error_message).
        """
        api_url = current_app.config.get('EXCHANGE_RATE_API_URL')

        if not api_url:
            # Use a default API or manual rate
            return cls._fetch_bcv_rate() if source == 'bcv' else cls._fetch_parallel_rate()

        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Assuming API returns rate for VES
            rate = data.get('rates', {}).get('VES')
            if rate:
                return Decimal(str(rate)), None

            return None, 'VES rate not found in API response'

        except Exception as e:
            return None, str(e)

    @staticmethod
    def _fetch_bcv_rate() -> Tuple[Optional[Decimal], Optional[str]]:
        """Fetch BCV official rate (placeholder implementation)."""
        # In production, implement actual BCV rate fetching
        # This is a placeholder that returns None
        return None, 'BCV rate fetching not implemented'

    @staticmethod
    def _fetch_parallel_rate() -> Tuple[Optional[Decimal], Optional[str]]:
        """Fetch parallel market rate (placeholder implementation)."""
        # In production, implement actual parallel rate fetching
        # This is a placeholder that returns None
        return None, 'Parallel rate fetching not implemented'

    @classmethod
    def update_rates(cls) -> Tuple[bool, Optional[str]]:
        """
        Update exchange rates from external sources.

        Returns:
            Tuple of (success, error_message).
        """
        # Try to fetch parallel rate first
        rate, error = cls.fetch_external_rate('parallel')

        if rate:
            cls.create_rate('USD', 'VES', rate, 'parallel')
            return True, None

        # Fallback to BCV rate
        rate, error = cls.fetch_external_rate('bcv')

        if rate:
            cls.create_rate('USD', 'VES', rate, 'bcv')
            return True, None

        return False, error or 'Failed to fetch exchange rate'

    @staticmethod
    def get_rate_history(
        from_currency: str = 'USD',
        to_currency: str = 'VES',
        days: int = 30
    ) -> list:
        """Get exchange rate history."""
        from datetime import timedelta

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        rates = ExchangeRate.query.filter(
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency,
            ExchangeRate.effective_date >= start_date,
            ExchangeRate.effective_date <= end_date
        ).order_by(ExchangeRate.effective_date.desc()).all()

        return [rate.to_dict() for rate in rates]

    @staticmethod
    def set_manual_rate(
        from_currency: str,
        to_currency: str,
        rate: Decimal
    ) -> ExchangeRate:
        """Manually set an exchange rate."""
        return ExchangeRateService.create_rate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            source='manual'
        )
