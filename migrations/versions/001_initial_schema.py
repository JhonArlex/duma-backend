"""Initial database schema for Duma Express

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-01 00:00:00.000000

Based on: /arquitectura/migracion_postgresql.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # =========================================================================
    # TABLA: users
    # Campos sensibles almacenados encriptados (TEXT)
    # email_hash permite búsquedas sin exponer el email real
    # =========================================================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        # Email encriptado + hash para búsquedas
        sa.Column('email', sa.Text(), nullable=False),  # ENCRYPTED
        sa.Column('email_hash', sa.String(64), unique=True, nullable=False),  # SHA-256 hash
        sa.Column('password_hash', sa.String(255), nullable=True),
        # Datos personales - ENCRYPTED
        sa.Column('display_name', sa.Text(), nullable=False),  # ENCRYPTED
        sa.Column('phone_number', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('identificacion', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('locker_code', sa.Text(), nullable=True),  # ENCRYPTED
        # Datos no sensibles - sin encriptar
        sa.Column('photo_url', sa.Text(), nullable=True),
        sa.Column('country', sa.String(100), server_default='Venezuela'),
        sa.Column('default_currency', sa.String(10), server_default='USD'),
        sa.Column('email_verified', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('auth_provider', sa.String(50), server_default='email'),
        sa.Column('auth_provider_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_users_email_hash', 'users', ['email_hash'])
    op.create_index('idx_users_auth_provider', 'users', ['auth_provider', 'auth_provider_id'])

    # =========================================================================
    # TABLA: addresses
    # Datos de dirección encriptados para proteger ubicación del usuario
    # Foreign keys NO encriptados para permitir JOINs
    # =========================================================================
    op.create_table(
        'addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),  # NOT encrypted (filter)
        # Datos de dirección - ENCRYPTED
        sa.Column('label', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('address_line_1', sa.Text(), nullable=False),  # ENCRYPTED
        sa.Column('address_line_2', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('city', sa.Text(), nullable=False),  # ENCRYPTED
        sa.Column('state', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('postal_code', sa.Text(), nullable=True),  # ENCRYPTED
        # Datos no encriptados
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint("type IN ('usa_locker', 'vzla_home', 'other')", name='check_address_type'),
    )
    op.create_index('idx_addresses_user', 'addresses', ['user_id'])

    # =========================================================================
    # TABLA: stores
    # =========================================================================
    op.create_table(
        'stores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('base_url', sa.Text(), nullable=False),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.Column('config', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # =========================================================================
    # TABLA: orders
    # =========================================================================
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('shipping_address_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('addresses.id'), nullable=True),
        sa.Column('order_number', sa.String(50), unique=True, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('payment_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('subtotal', sa.Numeric(12, 2), nullable=False),
        sa.Column('platform_fee', sa.Numeric(12, 2), server_default='0'),
        sa.Column('shipping_usa', sa.Numeric(12, 2), server_default='0'),
        sa.Column('shipping_vzla', sa.Numeric(12, 2), server_default='0'),
        sa.Column('taxes_estimated', sa.Numeric(12, 2), server_default='0'),
        sa.Column('total_usd', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_bs', sa.Numeric(18, 2), nullable=True),
        sa.Column('exchange_rate', sa.Numeric(12, 4), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')",
            name='check_order_status'
        ),
        sa.CheckConstraint(
            "payment_status IN ('pending', 'paid', 'failed', 'refunded')",
            name='check_payment_status'
        ),
    )
    op.create_index('idx_orders_user', 'orders', ['user_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_created', 'orders', ['created_at'])
    op.create_index('idx_orders_number', 'orders', ['order_number'])

    # =========================================================================
    # TABLA: order_items
    # =========================================================================
    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id'), nullable=True),
        sa.Column('product_url', sa.Text(), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('variant_size', sa.String(100), nullable=True),
        sa.Column('variant_color', sa.String(100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint('quantity > 0', name='check_order_item_quantity'),
        sa.CheckConstraint(
            "status IN ('pending', 'purchased', 'shipped', 'delivered')",
            name='check_order_item_status'
        ),
    )
    op.create_index('idx_order_items_order', 'order_items', ['order_id'])
    op.create_index('idx_order_items_store', 'order_items', ['store_id'])

    # =========================================================================
    # TABLA: carts
    # =========================================================================
    op.create_table(
        'carts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('currency', sa.String(10), server_default='USD'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint(
            "status IN ('active', 'abandoned', 'converted')",
            name='check_cart_status'
        ),
    )
    op.create_index('idx_carts_user', 'carts', ['user_id'])

    # =========================================================================
    # TABLA: cart_items
    # =========================================================================
    op.create_table(
        'cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('stores.id'), nullable=True),
        sa.Column('product_url', sa.Text(), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('variant_size', sa.String(100), nullable=True),
        sa.Column('variant_color', sa.String(100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.CheckConstraint('quantity > 0', name='check_cart_item_quantity'),
    )
    op.create_index('idx_cart_items_cart', 'cart_items', ['cart_id'])

    # =========================================================================
    # TABLA: payments
    # =========================================================================
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('payment_provider', sa.String(50), nullable=False),
        sa.Column('provider_txn_id', sa.String(255), nullable=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(10), server_default='USD'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('card_last_four', sa.String(4), nullable=True),
        sa.Column('card_brand', sa.String(50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed', 'refunded')",
            name='check_payment_status_values'
        ),
    )
    op.create_index('idx_payments_order', 'payments', ['order_id'])
    op.create_index('idx_payments_user', 'payments', ['user_id'])
    op.create_index('idx_payments_provider_txn', 'payments', ['payment_provider', 'provider_txn_id'])

    # =========================================================================
    # TABLA: exchange_rates
    # =========================================================================
    op.create_table(
        'exchange_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('from_currency', sa.String(10), nullable=False),
        sa.Column('to_currency', sa.String(10), nullable=False),
        sa.Column('rate', sa.Numeric(18, 4), nullable=False),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_exchange_rates_currencies', 'exchange_rates', ['from_currency', 'to_currency'])
    op.create_index('idx_exchange_rates_active', 'exchange_rates', ['is_active', 'effective_date'])

    # =========================================================================
    # TABLA: order_status_history
    # =========================================================================
    op.create_table(
        'order_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('previous_status', sa.String(50), nullable=True),
        sa.Column('new_status', sa.String(50), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('idx_order_status_history_order', 'order_status_history', ['order_id'])

    # =========================================================================
    # TABLA: notifications
    # =========================================================================
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', postgresql.JSONB(), server_default='{}'),
        sa.Column('is_read', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_notifications_user', 'notifications', ['user_id'])
    # Partial index for unread notifications
    op.execute('''
        CREATE INDEX idx_notifications_unread
        ON notifications (user_id, is_read)
        WHERE NOT is_read
    ''')

    # =========================================================================
    # TRIGGERS: updated_at automático
    # =========================================================================
    op.execute('''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    ''')

    # Trigger para users
    op.execute('''
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    ''')

    # Trigger para orders
    op.execute('''
        CREATE TRIGGER update_orders_updated_at
            BEFORE UPDATE ON orders
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    ''')

    # Trigger para carts
    op.execute('''
        CREATE TRIGGER update_carts_updated_at
            BEFORE UPDATE ON carts
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    ''')

    # Trigger para cart_items
    op.execute('''
        CREATE TRIGGER update_cart_items_updated_at
            BEFORE UPDATE ON cart_items
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    ''')


def downgrade():
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_cart_items_updated_at ON cart_items')
    op.execute('DROP TRIGGER IF EXISTS update_carts_updated_at ON carts')
    op.execute('DROP TRIGGER IF EXISTS update_orders_updated_at ON orders')
    op.execute('DROP TRIGGER IF EXISTS update_users_updated_at ON users')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('notifications')
    op.drop_table('order_status_history')
    op.drop_table('exchange_rates')
    op.drop_table('payments')
    op.drop_table('cart_items')
    op.drop_table('carts')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('stores')
    op.drop_table('addresses')
    op.drop_table('users')
