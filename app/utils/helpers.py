import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, Union


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def format_currency(
    amount: Union[Decimal, float, int],
    currency: str = 'USD',
    locale: str = 'en_US'
) -> str:
    """
    Format amount as currency string.

    Args:
        amount: The amount to format
        currency: Currency code (USD, VES, etc.)
        locale: Locale for formatting

    Returns:
        Formatted currency string
    """
    symbols = {
        'USD': '$',
        'VES': 'Bs.',
        'EUR': '€'
    }

    symbol = symbols.get(currency, currency + ' ')
    formatted = f'{float(amount):,.2f}'

    return f'{symbol}{formatted}'


def parse_date(
    date_string: str,
    formats: Optional[list] = None
) -> Optional[date]:
    """
    Parse date string to date object.

    Args:
        date_string: Date string to parse
        formats: List of date formats to try

    Returns:
        Parsed date or None if parsing fails
    """
    if not formats:
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue

    return None


def parse_datetime(
    datetime_string: str,
    formats: Optional[list] = None
) -> Optional[datetime]:
    """
    Parse datetime string to datetime object.

    Args:
        datetime_string: Datetime string to parse
        formats: List of datetime formats to try

    Returns:
        Parsed datetime or None if parsing fails
    """
    if not formats:
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d'
        ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_string, fmt)
        except ValueError:
            continue

    return None


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize a string by stripping whitespace and limiting length.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ''
    return value.strip()[:max_length]


def is_valid_email(email: str) -> bool:
    """
    Basic email validation.

    Args:
        email: Email to validate

    Returns:
        True if email is valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def mask_email(email: str) -> str:
    """
    Mask an email address for privacy.

    Example: john@example.com -> j***@example.com
    """
    if not email or '@' not in email:
        return email

    local, domain = email.split('@')
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '***' + local[-1]

    return f'{masked_local}@{domain}'


def mask_card_number(card_number: str) -> str:
    """
    Mask a card number showing only last 4 digits.

    Example: 4111111111111111 -> ****-****-****-1111
    """
    if not card_number or len(card_number) < 4:
        return card_number

    last_four = card_number[-4:]
    return f'****-****-****-{last_four}'


def calculate_percentage(value: Union[Decimal, float], percentage: Union[Decimal, float]) -> Decimal:
    """
    Calculate percentage of a value.

    Args:
        value: Base value
        percentage: Percentage (e.g., 10 for 10%)

    Returns:
        Calculated percentage amount
    """
    return Decimal(str(value)) * Decimal(str(percentage)) / Decimal('100')


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.

    Args:
        text: Text to convert

    Returns:
        URL-friendly slug
    """
    import re
    import unicodedata

    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')

    # Convert to lowercase and replace spaces with hyphens
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)

    return text


def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate string to max length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating

    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
