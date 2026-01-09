from flask import Flask, jsonify
from flask_cors import CORS

from app.config import get_config
from app.extensions import db, migrate, jwt, limiter, celery


def create_app(config_object=None):
    """
    Application factory for creating Flask app.

    Args:
        config_object: Configuration object to use. If None, uses get_config().

    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)

    # Load configuration
    if config_object is None:
        config_object = get_config()
    app.config.from_object(config_object)

    # Initialize extensions
    register_extensions(app)

    # Initialize Celery
    from app.celery_utils import init_celery
    init_celery(celery, app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_commands(app)

    return app


def register_extensions(app):
    """Register Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })


def register_blueprints(app):
    """Register Flask blueprints."""
    from app.api import register_routes, init_swagger
    register_routes(app)

    # Initialize Swagger documentation
    init_swagger(app)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'version': app.config.get('APP_VERSION', '1.0.0')}), 200


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'bad_request',
            'message': 'The request was invalid or cannot be served.'
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'unauthorized',
            'message': 'Authentication is required.'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'forbidden',
            'message': 'You do not have permission to access this resource.'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'not_found',
            'message': 'The requested resource was not found.'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': 'method_not_allowed',
            'message': 'The method is not allowed for this resource.'
        }), 405

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'rate_limit_exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'internal_server_error',
            'message': 'An unexpected error occurred.'
        }), 500


def register_commands(app):
    """Register CLI commands."""
    import click
    from decimal import Decimal
    from datetime import date

    @app.cli.command('db-init')
    def db_init():
        """Initialize database with migrations."""
        from flask_migrate import upgrade
        print('Running database migrations...')
        upgrade()
        print('Database initialized successfully.')

    @app.cli.command('db-reset')
    @click.option('--yes', is_flag=True, help='Confirm reset without prompting')
    def db_reset(yes):
        """Reset database (DROP ALL and recreate)."""
        if not yes:
            click.confirm('This will DELETE all data. Are you sure?', abort=True)

        print('Dropping all tables...')
        db.drop_all()
        print('Creating all tables...')
        db.create_all()
        print('Database reset successfully.')

    @app.cli.command('seed-stores')
    def seed_stores():
        """Seed initial store data."""
        from app.models.store import Store

        stores = [
            {
                'name': 'Amazon',
                'slug': 'amazon',
                'base_url': 'https://www.amazon.com',
                'logo_url': 'https://logo.clearbit.com/amazon.com',
                'display_order': 1,
                'config': {'supported_countries': ['US'], 'scraping_enabled': True}
            },
            {
                'name': 'eBay',
                'slug': 'ebay',
                'base_url': 'https://www.ebay.com',
                'logo_url': 'https://logo.clearbit.com/ebay.com',
                'display_order': 2,
                'config': {'supported_countries': ['US'], 'scraping_enabled': True}
            },
            {
                'name': 'Walmart',
                'slug': 'walmart',
                'base_url': 'https://www.walmart.com',
                'logo_url': 'https://logo.clearbit.com/walmart.com',
                'display_order': 3,
                'config': {'supported_countries': ['US'], 'scraping_enabled': True}
            },
            {
                'name': 'Target',
                'slug': 'target',
                'base_url': 'https://www.target.com',
                'logo_url': 'https://logo.clearbit.com/target.com',
                'display_order': 4,
                'config': {'supported_countries': ['US'], 'scraping_enabled': True}
            },
            {
                'name': 'Best Buy',
                'slug': 'bestbuy',
                'base_url': 'https://www.bestbuy.com',
                'logo_url': 'https://logo.clearbit.com/bestbuy.com',
                'display_order': 5,
                'config': {'supported_countries': ['US'], 'scraping_enabled': True}
            },
            {
                'name': 'Shein',
                'slug': 'shein',
                'base_url': 'https://www.shein.com',
                'logo_url': 'https://logo.clearbit.com/shein.com',
                'display_order': 6,
                'config': {'supported_countries': ['US'], 'scraping_enabled': True}
            },
            {
                'name': 'AliExpress',
                'slug': 'aliexpress',
                'base_url': 'https://www.aliexpress.com',
                'logo_url': 'https://logo.clearbit.com/aliexpress.com',
                'display_order': 7,
                'config': {'supported_countries': ['US', 'CN'], 'scraping_enabled': True}
            },
        ]

        count = 0
        for store_data in stores:
            existing = Store.query.filter_by(slug=store_data['slug']).first()
            if not existing:
                store = Store(**store_data)
                db.session.add(store)
                count += 1

        db.session.commit()
        print(f'Seeded {count} stores. Total: {Store.query.count()}')

    @app.cli.command('seed-exchange-rate')
    @click.option('--rate', type=float, required=True, help='Exchange rate USD to VES')
    @click.option('--source', default='manual', help='Rate source (bcv, parallel, manual)')
    def seed_exchange_rate(rate, source):
        """Set initial exchange rate USD -> VES."""
        from app.models.exchange_rate import ExchangeRate

        # Deactivate previous rates
        ExchangeRate.query.filter_by(
            from_currency='USD',
            to_currency='VES',
            is_active=True
        ).update({'is_active': False})

        # Create new rate
        new_rate = ExchangeRate(
            from_currency='USD',
            to_currency='VES',
            rate=Decimal(str(rate)),
            source=source,
            is_active=True,
            effective_date=date.today()
        )
        db.session.add(new_rate)
        db.session.commit()

        print(f'Exchange rate set: 1 USD = {rate} VES (source: {source})')

    @app.cli.command('update-exchange-rate')
    def update_exchange_rate():
        """Update exchange rates from external API."""
        from app.services.exchange_rate_service import ExchangeRateService

        success, error = ExchangeRateService.update_rates()
        if success:
            rate = ExchangeRateService.get_current_rate()
            print(f'Exchange rates updated: 1 USD = {rate.rate} VES')
        else:
            print(f'Failed to update exchange rates: {error}')

    @app.cli.command('generate-encryption-key')
    def generate_encryption_key():
        """Generate a new encryption key for ENCRYPTION_KEY env var."""
        from app.utils.encryption import generate_encryption_key as gen_key
        key = gen_key()
        print(f'Generated encryption key:\n{key}')
        print('\nAdd this to your .env file:')
        print(f'ENCRYPTION_KEY={key}')

    @app.cli.command('create-superadmin')
    @click.option('--email', required=True, help='Superadmin email')
    @click.option('--password', required=True, help='Superadmin password')
    @click.option('--name', default='Super Admin', help='Display name')
    def create_superadmin(email, password, name):
        """Create a superadmin user with full permissions."""
        from app.models.user import User
        from app.models.role import Role
        from app.models.cart import Cart

        # Get superadmin role
        superadmin_role = Role.get_superadmin_role()
        if not superadmin_role:
            print('Error: Superadmin role not found. Run migrations first.')
            return

        if User.email_exists(email):
            # Check if user exists and update role
            existing = User.get_by_email(email)
            if existing:
                existing.role_id = superadmin_role.id
                db.session.commit()
                print(f'User {email} upgraded to superadmin.')
                return

        user = User(
            display_name=name,
            country='Venezuela',
            auth_provider='email',
            email_verified=True,
            is_active=True,
            role_id=superadmin_role.id
        )
        user.set_email(email)
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        # Create cart
        cart = Cart(user_id=user.id)
        db.session.add(cart)

        db.session.commit()
        print(f'Superadmin user created: {email}')

    @app.cli.command('create-admin')
    @click.option('--email', required=True, help='Admin email')
    @click.option('--password', required=True, help='Admin password')
    @click.option('--name', default='Admin', help='Display name')
    def create_admin(email, password, name):
        """Create an admin user."""
        from app.models.user import User
        from app.models.role import Role
        from app.models.cart import Cart

        # Get admin role
        admin_role = Role.get_by_type(Role.TYPE_ADMIN)
        if not admin_role:
            print('Error: Admin role not found. Run migrations first.')
            return

        if User.email_exists(email):
            print(f'User with email {email} already exists.')
            return

        user = User(
            display_name=name,
            country='Venezuela',
            auth_provider='email',
            email_verified=True,
            is_active=True,
            role_id=admin_role.id
        )
        user.set_email(email)
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        # Create cart
        cart = Cart(user_id=user.id)
        db.session.add(cart)

        db.session.commit()
        print(f'Admin user created: {email}')

    @app.cli.command('show-routes')
    def show_routes():
        """Show all registered routes."""
        from flask import url_for
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
            output.append(f'{rule.endpoint:40s} {methods:20s} {rule.rule}')

        print('\n'.join(sorted(output)))

    @app.cli.command('seed-all')
    @click.option('--rate', type=float, default=36.50, help='Initial exchange rate USD to VES')
    def seed_all(rate):
        """Seed all initial data (stores + exchange rate)."""
        from app.models.store import Store
        from app.models.exchange_rate import ExchangeRate

        # Seed stores
        stores = [
            {'name': 'Amazon', 'slug': 'amazon', 'base_url': 'https://www.amazon.com', 'display_order': 1},
            {'name': 'eBay', 'slug': 'ebay', 'base_url': 'https://www.ebay.com', 'display_order': 2},
            {'name': 'Walmart', 'slug': 'walmart', 'base_url': 'https://www.walmart.com', 'display_order': 3},
            {'name': 'Target', 'slug': 'target', 'base_url': 'https://www.target.com', 'display_order': 4},
            {'name': 'Best Buy', 'slug': 'bestbuy', 'base_url': 'https://www.bestbuy.com', 'display_order': 5},
        ]

        store_count = 0
        for store_data in stores:
            existing = Store.query.filter_by(slug=store_data['slug']).first()
            if not existing:
                store = Store(**store_data)
                db.session.add(store)
                store_count += 1

        # Seed exchange rate
        existing_rate = ExchangeRate.get_current_rate('USD', 'VES')
        if not existing_rate:
            new_rate = ExchangeRate(
                from_currency='USD',
                to_currency='VES',
                rate=Decimal(str(rate)),
                source='manual',
                is_active=True,
                effective_date=date.today()
            )
            db.session.add(new_rate)
            print(f'Exchange rate set: 1 USD = {rate} VES')
        else:
            print(f'Exchange rate already exists: 1 USD = {existing_rate.rate} VES')

        db.session.commit()
        print(f'Seeded {store_count} stores.')
        print('Seed complete!')
