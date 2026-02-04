from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from marshmallow import ValidationError

from app.extensions import db, limiter
from app.models.user import User
from app.models.role import Role
from app.models.cart import Cart
from app.schemas.user import UserSchema, UserCreateSchema, LoginSchema, OAuthLoginSchema
from app.utils.errors import error_response, validation_error_response, ErrorCode

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['POST'])
@limiter.limit('5 per minute')
def register():
    """Register a new user."""
    schema = UserCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(validation_error_response(err.messages)), 400

    # Check if email already exists using hash lookup
    if User.email_exists(data['email']):
        return jsonify(error_response(ErrorCode.EMAIL_ALREADY_EXISTS)), 409

    # Get default role for new users
    default_role = Role.get_default_role()

    # Create user with encrypted fields
    user = User(
        display_name=data['display_name'],
        phone_number=data.get('phone_number'),
        country=data.get('country', 'Venezuela'),
        auth_provider='email',
        role_id=default_role.id if default_role else None
    )
    # Set email with hash for lookups
    user.set_email(data['email'])
    user.set_password(data['password'])

    db.session.add(user)
    db.session.flush()  # Get user.id before creating cart

    # Create cart for user
    cart = Cart(user_id=user.id)
    db.session.add(cart)

    db.session.commit()

    # Generate tokens
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)

    user_schema = UserSchema()
    return jsonify({
        'user': user_schema.dump(user),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201


@bp.route('/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    """Login with email and password."""
    schema = LoginSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(validation_error_response(err.messages)), 400

    # Find user by email using hash lookup
    user = User.get_by_email(data['email'])

    if not user or not user.check_password(data['password']):
        return jsonify(error_response(ErrorCode.INVALID_CREDENTIALS)), 401

    # Update last login
    user.update_last_login()
    db.session.commit()

    # Generate tokens
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)

    user_schema = UserSchema()
    return jsonify({
        'user': user_schema.dump(user),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


@bp.route('/oauth', methods=['POST'])
@limiter.limit('10 per minute')
def oauth_login():
    """Login or register with OAuth provider."""
    schema = OAuthLoginSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(validation_error_response(err.messages)), 400

    provider = data['provider']
    # In a real implementation, you would verify the token with the provider
    # For now, we'll trust the token and use provided email/name

    if not data.get('email'):
        return jsonify(error_response(ErrorCode.OAUTH_EMAIL_REQUIRED)), 400

    # Check if user exists with this OAuth provider
    user = User.query.filter_by(
        auth_provider=provider,
        auth_provider_id=data['token']
    ).first()

    if not user:
        # Check if email already exists with different provider
        existing_user = User.get_by_email(data['email'])
        if existing_user:
            return jsonify(error_response(
                ErrorCode.EMAIL_EXISTS_WITH_DIFFERENT_PROVIDER,
                message=f'Email already registered with {existing_user.auth_provider}'
            )), 409

        # Get default role for new users
        default_role = Role.get_default_role()

        # Create new user with encrypted fields
        user = User(
            display_name=data.get('display_name', data['email'].split('@')[0]),
            photo_url=data.get('photo_url'),
            auth_provider=provider,
            auth_provider_id=data['token'],
            email_verified=True,
            role_id=default_role.id if default_role else None
        )
        # Set email with hash
        user.set_email(data['email'])

        db.session.add(user)
        db.session.flush()

        # Create cart for user
        cart = Cart(user_id=user.id)
        db.session.add(cart)

    # Update last login
    user.update_last_login()
    db.session.commit()

    # Generate tokens
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)

    user_schema = UserSchema()
    return jsonify({
        'user': user_schema.dump(user),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    identity = get_jwt_identity()
    user = User.query.get(identity)

    if not user:
        return jsonify(error_response(ErrorCode.USER_NOT_FOUND)), 404
    
    if not user.is_active:
        return jsonify(error_response(ErrorCode.USER_INACTIVE)), 401

    access_token = create_access_token(identity=user)
    return jsonify({'access_token': access_token}), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    identity = get_jwt_identity()
    user = User.query.get(identity)

    if not user:
        return jsonify(error_response(ErrorCode.USER_NOT_FOUND)), 404

    user_schema = UserSchema()
    return jsonify(user_schema.dump(user)), 200


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should discard tokens)."""
    # In a production environment, you might want to blacklist the token
    # using Redis or a database table
    return jsonify({'message': 'Successfully logged out'}), 200
