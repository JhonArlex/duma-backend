"""Seed initial data (stores and default exchange rate)

Revision ID: 002_seed_initial_data
Revises: 001_initial_schema
Create Date: 2024-01-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import date

# revision identifiers, used by Alembic.
revision = '002_seed_initial_data'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # SEED: Tiendas soportadas
    # =========================================================================
    stores_table = sa.table(
        'stores',
        sa.column('id', postgresql.UUID),
        sa.column('name', sa.String),
        sa.column('slug', sa.String),
        sa.column('base_url', sa.Text),
        sa.column('logo_url', sa.Text),
        sa.column('is_active', sa.Boolean),
        sa.column('display_order', sa.Integer),
        sa.column('config', postgresql.JSONB),
    )

    op.bulk_insert(stores_table, [
        {
            'name': 'Amazon',
            'slug': 'amazon',
            'base_url': 'https://www.amazon.com',
            'logo_url': 'https://logo.clearbit.com/amazon.com',
            'is_active': True,
            'display_order': 1,
            'config': '{"supported_countries": ["US"], "scraping_enabled": true}',
        },
        {
            'name': 'eBay',
            'slug': 'ebay',
            'base_url': 'https://www.ebay.com',
            'logo_url': 'https://logo.clearbit.com/ebay.com',
            'is_active': True,
            'display_order': 2,
            'config': '{"supported_countries": ["US"], "scraping_enabled": true}',
        },
        {
            'name': 'Walmart',
            'slug': 'walmart',
            'base_url': 'https://www.walmart.com',
            'logo_url': 'https://logo.clearbit.com/walmart.com',
            'is_active': True,
            'display_order': 3,
            'config': '{"supported_countries": ["US"], "scraping_enabled": true}',
        },
        {
            'name': 'Target',
            'slug': 'target',
            'base_url': 'https://www.target.com',
            'logo_url': 'https://logo.clearbit.com/target.com',
            'is_active': True,
            'display_order': 4,
            'config': '{"supported_countries": ["US"], "scraping_enabled": true}',
        },
        {
            'name': 'Best Buy',
            'slug': 'bestbuy',
            'base_url': 'https://www.bestbuy.com',
            'logo_url': 'https://logo.clearbit.com/bestbuy.com',
            'is_active': True,
            'display_order': 5,
            'config': '{"supported_countries": ["US"], "scraping_enabled": true}',
        },
        {
            'name': 'Shein',
            'slug': 'shein',
            'base_url': 'https://www.shein.com',
            'logo_url': 'https://logo.clearbit.com/shein.com',
            'is_active': True,
            'display_order': 6,
            'config': '{"supported_countries": ["US"], "scraping_enabled": true}',
        },
        {
            'name': 'AliExpress',
            'slug': 'aliexpress',
            'base_url': 'https://www.aliexpress.com',
            'logo_url': 'https://logo.clearbit.com/aliexpress.com',
            'is_active': True,
            'display_order': 7,
            'config': '{"supported_countries": ["US", "CN"], "scraping_enabled": true}',
        },
        {
            'name': 'Otra Tienda',
            'slug': 'other',
            'base_url': 'https://www.google.com',
            'logo_url': None,
            'is_active': True,
            'display_order': 99,
            'config': '{"supported_countries": ["US"], "scraping_enabled": false}',
        },
    ])

    # =========================================================================
    # SEED: Tasa de cambio inicial (USD -> VES)
    # =========================================================================
    exchange_rates_table = sa.table(
        'exchange_rates',
        sa.column('from_currency', sa.String),
        sa.column('to_currency', sa.String),
        sa.column('rate', sa.Numeric),
        sa.column('source', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('effective_date', sa.Date),
    )

    op.bulk_insert(exchange_rates_table, [
        {
            'from_currency': 'USD',
            'to_currency': 'VES',
            'rate': 36.50,  # Tasa de ejemplo, actualizar según BCV/paralelo
            'source': 'manual',
            'is_active': True,
            'effective_date': date.today(),
        },
    ])


def downgrade():
    # Remove seed data
    op.execute("DELETE FROM exchange_rates WHERE source = 'manual'")
    op.execute("DELETE FROM stores")
