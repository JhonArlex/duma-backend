-- ============================================================================
-- ESQUEMA DE BASE DE DATOS POSTGRESQL PARA DUMA EXPRESS
-- ============================================================================

-- Extensiones requeridas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TABLA: users
-- Campos sensibles se almacenan encriptados (TEXT para datos encriptados)
-- email_hash permite búsquedas sin exponer el email real
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- Email encriptado + hash para búsquedas
    email TEXT NOT NULL,                           -- ENCRYPTED
    email_hash VARCHAR(64) UNIQUE NOT NULL,        -- SHA-256 hash for lookups
    password_hash VARCHAR(255),
    -- Datos personales - ENCRYPTED
    display_name TEXT NOT NULL,                    -- ENCRYPTED
    phone_number TEXT,                             -- ENCRYPTED
    identificacion TEXT,                           -- ENCRYPTED
    locker_code TEXT,                              -- ENCRYPTED
    -- Datos no sensibles - sin encriptar (para queries)
    photo_url TEXT,
    country VARCHAR(100) DEFAULT 'Venezuela',
    default_currency VARCHAR(10) DEFAULT 'USD',
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    auth_provider VARCHAR(50) DEFAULT 'email',
    auth_provider_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Index on email_hash for login lookups (NOT on encrypted email)
CREATE INDEX IF NOT EXISTS idx_users_email_hash ON users(email_hash);
CREATE INDEX IF NOT EXISTS idx_users_auth_provider ON users(auth_provider, auth_provider_id);

-- ============================================================================
-- TABLA: addresses
-- Datos de dirección encriptados para proteger ubicación del usuario
-- Foreign keys (id, user_id) NO encriptados para permitir JOINs
-- ============================================================================
CREATE TABLE IF NOT EXISTS addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- NOT encrypted (FK)
    type VARCHAR(20) NOT NULL CHECK (type IN ('usa_locker', 'vzla_home', 'other')),  -- NOT encrypted (filter)
    -- Datos de dirección - ENCRYPTED
    label TEXT,                                    -- ENCRYPTED
    address_line_1 TEXT NOT NULL,                  -- ENCRYPTED
    address_line_2 TEXT,                           -- ENCRYPTED
    city TEXT NOT NULL,                            -- ENCRYPTED
    state TEXT,                                    -- ENCRYPTED
    postal_code TEXT,                              -- ENCRYPTED
    -- Datos no encriptados (para filtros/reportes)
    country VARCHAR(100) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_addresses_user ON addresses(user_id);

-- ============================================================================
-- TABLA: stores
-- ============================================================================
CREATE TABLE IF NOT EXISTS stores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    base_url TEXT NOT NULL,
    logo_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Datos iniciales de tiendas
INSERT INTO stores (name, slug, base_url, display_order) VALUES
    ('Amazon', 'amazon', 'https://www.amazon.com', 1),
    ('eBay', 'ebay', 'https://www.ebay.com', 2),
    ('Walmart', 'walmart', 'https://www.walmart.com', 3),
    ('Target', 'target', 'https://www.target.com', 4),
    ('Best Buy', 'bestbuy', 'https://www.bestbuy.com', 5)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- TABLA: orders
-- ============================================================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    shipping_address_id UUID REFERENCES addresses(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
    payment_status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    subtotal DECIMAL(12, 2) NOT NULL,
    platform_fee DECIMAL(12, 2) DEFAULT 0,
    shipping_usa DECIMAL(12, 2) DEFAULT 0,
    shipping_vzla DECIMAL(12, 2) DEFAULT 0,
    taxes_estimated DECIMAL(12, 2) DEFAULT 0,
    total_usd DECIMAL(12, 2) NOT NULL,
    total_bs DECIMAL(18, 2),
    exchange_rate DECIMAL(12, 4),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(order_number);

-- ============================================================================
-- TABLA: order_items
-- ============================================================================
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    store_id UUID REFERENCES stores(id),
    product_url TEXT NOT NULL,
    title VARCHAR(500),
    image_url TEXT,
    variant_size VARCHAR(100),
    variant_color VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price DECIMAL(12, 2) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'pending'
        CHECK (status IN ('pending', 'purchased', 'shipped', 'delivered')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_store ON order_items(store_id);

-- ============================================================================
-- TABLA: carts
-- ============================================================================
CREATE TABLE IF NOT EXISTS carts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'active'
        CHECK (status IN ('active', 'abandoned', 'converted')),
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_carts_user ON carts(user_id);

-- ============================================================================
-- TABLA: cart_items
-- ============================================================================
CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id UUID NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    store_id UUID REFERENCES stores(id),
    product_url TEXT NOT NULL,
    title VARCHAR(500),
    image_url TEXT,
    variant_size VARCHAR(100),
    variant_color VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price DECIMAL(12, 2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id);

-- ============================================================================
-- TABLA: payments
-- ============================================================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id),
    user_id UUID NOT NULL REFERENCES users(id),
    payment_provider VARCHAR(50) NOT NULL,
    provider_txn_id VARCHAR(255),
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    payment_method VARCHAR(50),
    card_last_four VARCHAR(4),
    card_brand VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_provider_txn ON payments(payment_provider, provider_txn_id);

-- ============================================================================
-- TABLA: exchange_rates
-- ============================================================================
CREATE TABLE IF NOT EXISTS exchange_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_currency VARCHAR(10) NOT NULL,
    to_currency VARCHAR(10) NOT NULL,
    rate DECIMAL(18, 4) NOT NULL,
    source VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    effective_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_currencies ON exchange_rates(from_currency, to_currency);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_active ON exchange_rates(is_active, effective_date DESC);

-- ============================================================================
-- TABLA: order_status_history
-- ============================================================================
CREATE TABLE IF NOT EXISTS order_status_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_status_history_order ON order_status_history(order_id);

-- ============================================================================
-- TABLA: notifications
-- ============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    read_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read) WHERE NOT is_read;

-- ============================================================================
-- TRIGGERS PARA updated_at
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_carts_updated_at ON carts;
CREATE TRIGGER update_carts_updated_at
    BEFORE UPDATE ON carts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_cart_items_updated_at ON cart_items;
CREATE TRIGGER update_cart_items_updated_at
    BEFORE UPDATE ON cart_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
