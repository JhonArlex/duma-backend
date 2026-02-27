import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost:5432/duma_express'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    )
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Rate Limiting
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'redis://localhost:6379/1')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100/hour')

    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/2')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/3')

    # Stripe
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

    # Braintree
    BRAINTREE_MERCHANT_ID = os.getenv('BRAINTREE_MERCHANT_ID')
    BRAINTREE_PUBLIC_KEY = os.getenv('BRAINTREE_PUBLIC_KEY')
    BRAINTREE_PRIVATE_KEY = os.getenv('BRAINTREE_PRIVATE_KEY')
    BRAINTREE_ENVIRONMENT = os.getenv('BRAINTREE_ENVIRONMENT', 'sandbox')

    # OneSignal
    ONESIGNAL_APP_ID = os.getenv('ONESIGNAL_APP_ID')
    ONESIGNAL_REST_API_KEY = os.getenv('ONESIGNAL_REST_API_KEY')

    # SendGrid
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@dumaexpress.com')

    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'duma-express-files')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

    # Application
    APP_NAME = os.getenv('APP_NAME', 'Duma Express')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEFAULT_CURRENCY = os.getenv('DEFAULT_CURRENCY', 'USD')
    DEFAULT_COUNTRY = os.getenv('DEFAULT_COUNTRY', 'Venezuela')

    # Encryption - REQUIRED for data protection
    # Generate with: python -c "from app.utils.encryption import generate_encryption_key; print(generate_encryption_key())"
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    ENCRYPTION_SALT = os.getenv('ENCRYPTION_SALT', 'duma_express_salt_2024')


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost:5432/duma_express_test'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)

    # Test encryption key (DO NOT use in production)
    ENCRYPTION_KEY = 'test-encryption-key-for-testing-only'
    ENCRYPTION_SALT = 'test-salt-for-testing'


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    # Override with stricter settings for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20,
    }


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
