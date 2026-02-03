from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.utils.permissions import require_superadmin, get_current_user

from app.extensions import db
from app.models.user import User
from app.models.address import Address
from app.schemas.user import UserSchema, UserUpdateSchema, PasswordChangeSchema, UserCreateSchema
from app.schemas.address import AddressSchema, AddressCreateSchema, AddressUpdateSchema

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    user_schema = UserSchema()
    return jsonify(user_schema.dump(user)), 200


@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    schema = UserUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # Update user fields
    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.session.commit()

    user_schema = UserSchema()
    return jsonify(user_schema.dump(user)), 200


@bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user password."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    if user.auth_provider != 'email':
        return jsonify({
            'error': 'oauth_user',
            'message': 'Cannot change password for OAuth users'
        }), 400

    schema = PasswordChangeSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    if not user.check_password(data['current_password']):
        return jsonify({'error': 'invalid_password', 'message': 'Current password is incorrect'}), 400

    user.set_password(data['new_password'])
    db.session.commit()

    return jsonify({'message': 'Password updated successfully'}), 200


# Address endpoints (Self)
@bp.route('/addresses', methods=['GET'])
@jwt_required()
def get_addresses():
    """Get all addresses for current user."""
    user_id = get_jwt_identity()
    addresses = Address.query.filter_by(user_id=user_id).all()

    address_schema = AddressSchema(many=True)
    return jsonify(address_schema.dump(addresses)), 200


@bp.route('/addresses', methods=['POST'])
@jwt_required()
def create_address():
    """Create a new address."""
    user_id = get_jwt_identity()
    schema = AddressCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # If this is the default address, unset other defaults
    if data.get('is_default'):
        Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})

    address = Address(user_id=user_id, **data)
    db.session.add(address)
    db.session.commit()

    address_schema = AddressSchema()
    return jsonify(address_schema.dump(address)), 201


@bp.route('/addresses/<uuid:address_id>', methods=['GET'])
@jwt_required()
def get_address(address_id):
    """Get a specific address."""
    user_id = get_jwt_identity()
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()

    if not address:
        return jsonify({'error': 'address_not_found', 'message': 'Address not found'}), 404

    address_schema = AddressSchema()
    return jsonify(address_schema.dump(address)), 200


@bp.route('/addresses/<uuid:address_id>', methods=['PUT'])
@jwt_required()
def update_address(address_id):
    """Update an address."""
    user_id = get_jwt_identity()
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()

    if not address:
        return jsonify({'error': 'address_not_found', 'message': 'Address not found'}), 404

    schema = AddressUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # If setting as default, unset other defaults
    if data.get('is_default'):
        Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})

    for key, value in data.items():
        if hasattr(address, key):
            setattr(address, key, value)

    db.session.commit()

    address_schema = AddressSchema()
    return jsonify(address_schema.dump(address)), 200


@bp.route('/addresses/<uuid:address_id>', methods=['DELETE'])
@jwt_required()
def delete_address(address_id):
    """Delete an address."""
    user_id = get_jwt_identity()
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()

    if not address:
        return jsonify({'error': 'address_not_found', 'message': 'Address not found'}), 404

    db.session.delete(address)
    db.session.commit()

    return jsonify({'message': 'Address deleted successfully'}), 200


@bp.route('/addresses/<uuid:address_id>/default', methods=['PUT'])
@jwt_required()
def set_default_address(address_id):
    """Set an address as default."""
    user_id = get_jwt_identity()
    address = Address.query.filter_by(id=address_id, user_id=user_id).first()

    if not address:
        return jsonify({'error': 'address_not_found', 'message': 'Address not found'}), 404

    # Unset other defaults
    Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})

    address.is_default = True
    db.session.commit()

    address_schema = AddressSchema()
    return jsonify(address_schema.dump(address)), 200


# =============================================================================
# Admin User Management
# =============================================================================

@bp.route('/admin', methods=['POST'])
@require_superadmin()
def create_user_admin():
    """Create a new user (Admin only)."""
    schema = UserCreateSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400
        
    # Check if email exists
    if User.query.filter_by(email=data['email']).first():
         return jsonify({'error': 'email_exists', 'message': 'Email already registered'}), 400
         
    user = User(
        email=data['email'],
        display_name=data.get('display_name'),
        phone_number=data.get('phone_number'),
        country=data.get('country'),
        role_id=data.get('role_id')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    user_schema = UserSchema()
    return jsonify(user_schema.dump(user)), 201


@bp.route('/<uuid:user_id>', methods=['GET'])
@require_superadmin()
def get_user_admin(user_id):
    """Get any user by ID (Admin only)."""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    user_schema = UserSchema()
    return jsonify(user_schema.dump(user)), 200


@bp.route('/<uuid:user_id>', methods=['PUT'])
@require_superadmin()
def update_user_admin(user_id):
    """Update any user (Admin only)."""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    schema = UserUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # Update user fields
    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.session.commit()

    user_schema = UserSchema()
    return jsonify(user_schema.dump(user)), 200


@bp.route('/<uuid:user_id>', methods=['DELETE'])
@require_superadmin()
def delete_user_admin(user_id):
    """Delete any user (Admin only)."""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    # Prevent deleting self
    current_user_id = get_jwt_identity()
    if str(user.id) == str(current_user_id):
         return jsonify({'error': 'self_delete', 'message': 'Cannot delete your own account'}), 400

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200


# =============================================================================
# Admin Address Management
# =============================================================================

@bp.route('/<uuid:user_id>/addresses', methods=['GET'])
@require_superadmin()
def get_user_addresses_admin(user_id):
    """Get all addresses for a specific user (Admin only)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    addresses = Address.query.filter_by(user_id=user_id).all()

    address_schema = AddressSchema(many=True)
    return jsonify(address_schema.dump(addresses)), 200


@bp.route('/<uuid:user_id>/addresses', methods=['POST'])
@require_superadmin()
def create_user_address_admin(user_id):
    """Create a new address for a specific user (Admin only)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    schema = AddressCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # If this is the default address, unset other defaults for THIS user
    if data.get('is_default'):
        Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})

    address = Address(user_id=user_id, **data)
    db.session.add(address)
    db.session.commit()

    address_schema = AddressSchema()
    return jsonify(address_schema.dump(address)), 201


@bp.route('/<uuid:user_id>/addresses/<uuid:address_id>', methods=['PUT'])
@require_superadmin()
def update_user_address_admin(user_id, address_id):
    """Update a specific address for a user (Admin only)."""
    # Verify user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    address = Address.query.filter_by(id=address_id, user_id=user_id).first()

    if not address:
        return jsonify({'error': 'address_not_found', 'message': 'Address not found'}), 404

    schema = AddressUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # If setting as default, unset other defaults
    if data.get('is_default'):
        Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})

    for key, value in data.items():
        if hasattr(address, key):
            setattr(address, key, value)

    db.session.commit()

    address_schema = AddressSchema()
    return jsonify(address_schema.dump(address)), 200


@bp.route('/<uuid:user_id>/addresses/<uuid:address_id>', methods=['DELETE'])
@require_superadmin()
def delete_user_address_admin(user_id, address_id):
    """Delete a specific address for a user (Admin only)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    address = Address.query.filter_by(id=address_id, user_id=user_id).first()

    if not address:
        return jsonify({'error': 'address_not_found', 'message': 'Address not found'}), 404

    db.session.delete(address)
    db.session.commit()

    return jsonify({'message': 'Address deleted successfully'}), 200
