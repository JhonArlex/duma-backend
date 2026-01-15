"""
API endpoints for Role and Permission management.

All endpoints require superadmin access.
"""
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from app.extensions import db
from app.models.role import Role, Permission, PermissionAction, PermissionEntity
from app.models.user import User
from app.utils.permissions import require_superadmin, get_current_user
from app.schemas.role import (
    RoleSchema,
    RoleCreateSchema,
    RoleUpdateSchema,
    PermissionUpdateSchema,
    UserRoleAssignSchema
)

bp = Blueprint('roles', __name__, url_prefix='/roles')


# =============================================================================
# Role Management
# =============================================================================

@bp.route('', methods=['GET'])
@require_superadmin()
def get_roles():
    """Get all roles."""
    roles = Role.query.order_by(Role.created_at).all()

    include_permissions = request.args.get('include_permissions', 'false').lower() == 'true'

    return jsonify([
        role.to_dict(include_permissions=include_permissions)
        for role in roles
    ]), 200


@bp.route('/<uuid:role_id>', methods=['GET'])
@require_superadmin()
def get_role(role_id):
    """Get a specific role with its permissions."""
    role = Role.query.get(role_id)

    if not role:
        return jsonify({'error': 'role_not_found', 'message': 'Role not found'}), 404

    return jsonify(role.to_dict(include_permissions=True)), 200


@bp.route('', methods=['POST'])
@require_superadmin()
def create_role():
    """Create a new role."""
    schema = RoleCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # Check if name already exists
    if Role.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'name_exists', 'message': 'Role name already exists'}), 409

    # Create role
    role = Role(
        name=data['name'],
        description=data.get('description'),
        type=data.get('type', Role.TYPE_AUTHENTICATED),
        is_system=False,  # User-created roles are not system roles
        is_default=False
    )
    db.session.add(role)
    db.session.flush()

    # Create default permissions (all disabled)
    for entity in PermissionEntity.ALL_ENTITIES:
        for action in PermissionAction.ALL_ACTIONS:
            permission = Permission(
                role_id=role.id,
                entity=entity,
                action=action,
                is_enabled=False
            )
            db.session.add(permission)

    db.session.commit()

    return jsonify(role.to_dict(include_permissions=True)), 201


@bp.route('/<uuid:role_id>', methods=['PUT'])
@require_superadmin()
def update_role(role_id):
    """Update a role."""
    role = Role.query.get(role_id)

    if not role:
        return jsonify({'error': 'role_not_found', 'message': 'Role not found'}), 404

    schema = RoleUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # Check name uniqueness if changing
    if 'name' in data and data['name'] != role.name:
        if Role.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'name_exists', 'message': 'Role name already exists'}), 409
        role.name = data['name']

    if 'description' in data:
        role.description = data['description']

    db.session.commit()

    return jsonify(role.to_dict(include_permissions=True)), 200


@bp.route('/<uuid:role_id>', methods=['DELETE'])
@require_superadmin()
def delete_role(role_id):
    """Delete a role."""
    role = Role.query.get(role_id)

    if not role:
        return jsonify({'error': 'role_not_found', 'message': 'Role not found'}), 404

    if role.is_system:
        return jsonify({
            'error': 'system_role',
            'message': 'Cannot delete system roles'
        }), 400

    # Check if role has users
    if role.users.count() > 0:
        return jsonify({
            'error': 'role_in_use',
            'message': f'Cannot delete role with {role.users.count()} assigned users'
        }), 400

    db.session.delete(role)
    db.session.commit()

    return jsonify({'message': 'Role deleted successfully'}), 200


# =============================================================================
# Permission Management
# =============================================================================

@bp.route('/<uuid:role_id>/permissions', methods=['GET'])
@require_superadmin()
def get_role_permissions(role_id):
    """Get all permissions for a role."""
    role = Role.query.get(role_id)

    if not role:
        return jsonify({'error': 'role_not_found', 'message': 'Role not found'}), 404

    return jsonify({
        'role_id': str(role.id),
        'role_name': role.name,
        'permissions': role.get_permissions_dict()
    }), 200


@bp.route('/<uuid:role_id>/permissions', methods=['PUT'])
@require_superadmin()
def update_role_permissions(role_id):
    """
    Update permissions for a role.

    Expected body format:
    {
        "permissions": {
            "user": {
                "create": true,
                "read": true,
                "read_all": false,
                "update": true,
                "delete": false
            },
            "order": {
                "create": true,
                "read": true,
                ...
            }
        }
    }
    """
    role = Role.query.get(role_id)

    if not role:
        return jsonify({'error': 'role_not_found', 'message': 'Role not found'}), 404

    if role.type == Role.TYPE_SUPERADMIN:
        return jsonify({
            'error': 'superadmin_role',
            'message': 'Cannot modify superadmin permissions'
        }), 400

    schema = PermissionUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    permissions_data = data.get('permissions', {})

    # Update permissions
    for entity, actions in permissions_data.items():
        if entity not in PermissionEntity.ALL_ENTITIES:
            continue

        for action, is_enabled in actions.items():
            if action not in PermissionAction.ALL_ACTIONS:
                continue

            role.set_permission(entity, action, is_enabled)

    db.session.commit()

    return jsonify({
        'role_id': str(role.id),
        'role_name': role.name,
        'permissions': role.get_permissions_dict()
    }), 200


@bp.route('/<uuid:role_id>/permissions/<string:entity>/<string:action>', methods=['PUT'])
@require_superadmin()
def update_single_permission(role_id, entity, action):
    """
    Update a single permission.

    Body:
    {
        "is_enabled": true,
        "conditions": {"own_only": true}  // optional
    }
    """
    role = Role.query.get(role_id)

    if not role:
        return jsonify({'error': 'role_not_found', 'message': 'Role not found'}), 404

    if role.type == Role.TYPE_SUPERADMIN:
        return jsonify({
            'error': 'superadmin_role',
            'message': 'Cannot modify superadmin permissions'
        }), 400

    if entity not in PermissionEntity.ALL_ENTITIES:
        return jsonify({
            'error': 'invalid_entity',
            'message': f'Invalid entity: {entity}'
        }), 400

    if action not in PermissionAction.ALL_ACTIONS:
        return jsonify({
            'error': 'invalid_action',
            'message': f'Invalid action: {action}'
        }), 400

    data = request.json or {}
    is_enabled = data.get('is_enabled', True)
    conditions = data.get('conditions')

    role.set_permission(entity, action, is_enabled, conditions)
    db.session.commit()

    return jsonify({
        'entity': entity,
        'action': action,
        'is_enabled': is_enabled,
        'conditions': conditions
    }), 200


# =============================================================================
# User Role Assignment
# =============================================================================

@bp.route('/users', methods=['GET'])
@require_superadmin()
def get_users_with_roles():
    """Get all users with their roles."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    role_id = request.args.get('role_id')

    query = User.query

    if role_id:
        query = query.filter_by(role_id=role_id)

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)

    return jsonify({
        'users': [
            {
                'id': str(u.id),
                'email': u.email,
                'display_name': u.display_name,
                'is_active': u.is_active,
                'role': u.role.to_dict() if u.role else None,
                'created_at': u.created_at.isoformat() if u.created_at else None
            }
            for u in pagination.items
        ],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@bp.route('/users/<uuid:user_id>/role', methods=['PUT'])
@require_superadmin()
def assign_user_role(user_id):
    """Assign a role to a user."""
    current_user = get_current_user()

    # Cannot change own role
    if str(user_id) == str(current_user.id):
        return jsonify({
            'error': 'self_modification',
            'message': 'Cannot change your own role'
        }), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'user_not_found', 'message': 'User not found'}), 404

    schema = UserRoleAssignSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    role = Role.query.get(data['role_id'])

    if not role:
        return jsonify({'error': 'role_not_found', 'message': 'Role not found'}), 404

    user.role_id = role.id
    db.session.commit()

    return jsonify({
        'user_id': str(user.id),
        'role': role.to_dict()
    }), 200


# =============================================================================
# Utility Endpoints
# =============================================================================

@bp.route('/entities', methods=['GET'])
@require_superadmin()
def get_entities():
    """Get all available entities and actions."""
    return jsonify({
        'entities': PermissionEntity.ALL_ENTITIES,
        'actions': PermissionAction.ALL_ACTIONS
    }), 200


@bp.route('/default', methods=['GET'])
@require_superadmin()
def get_default_role():
    """Get the default role for new users."""
    role = Role.get_default_role()

    if not role:
        return jsonify({'error': 'no_default', 'message': 'No default role configured'}), 404

    return jsonify(role.to_dict(include_permissions=True)), 200


@bp.route('/<uuid:role_id>/set-default', methods=['POST'])
@require_superadmin()
def set_default_role(role_id):
    """Set a role as the default for new users."""
    role = Role.query.get(role_id)

    if not role:
        return jsonify({'error': 'role_not_found', 'message': 'Role not found'}), 404

    if role.type == Role.TYPE_SUPERADMIN:
        return jsonify({
            'error': 'invalid_default',
            'message': 'Cannot set superadmin as default role'
        }), 400

    # Remove default from all roles
    Role.query.update({'is_default': False})

    # Set new default
    role.is_default = True
    db.session.commit()

    return jsonify({
        'message': f'Role "{role.name}" is now the default role',
        'role': role.to_dict()
    }), 200
