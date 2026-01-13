from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema
from celery import Celery

# Database
db = SQLAlchemy()

# Migrations
migrate = Migrate()

# JWT Authentication
jwt = JWTManager()

# CORS
cors = CORS()

# Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

# Celery
celery = Celery()


# JWT Callbacks
@jwt.additional_claims_loader
def add_claims_to_access_token(user):
    """Add user permissions to JWT claims."""
    if hasattr(user, 'role') and user.role:
        return {
            "user_permissions": {
                "roleId": str(user.role_id),
                "roleName": user.role.name,
                "roleType": user.role.type,
                "permissions": user.role.get_permissions_dict()
            }
        }
    return {"user_permissions": None}


@jwt.user_identity_loader
def user_identity_lookup(user):
    """Return user ID as identity."""
    return str(user.id) if hasattr(user, 'id') else str(user)


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from database using JWT identity."""
    from app.models.user import User
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity, is_active=True).first()


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token."""
    return {
        'error': 'token_expired',
        'message': 'The token has expired'
    }, 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid token."""
    return {
        'error': 'invalid_token',
        'message': 'Token verification failed'
    }, 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    """Handle missing token."""
    return {
        'error': 'authorization_required',
        'message': 'Request does not contain an access token'
    }, 401


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    """Handle revoked token."""
    return {
        'error': 'token_revoked',
        'message': 'The token has been revoked'
    }, 401
