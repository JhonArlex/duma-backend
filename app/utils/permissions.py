"""
Permission decorators and utilities for RBAC system.

Provides decorators for protecting endpoints based on roles and permissions.
"""
from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app.models.user import User
from app.models.role import Role, PermissionAction, PermissionEntity


class PermissionDenied(Exception):
    """Exception raised when permission is denied."""
    def __init__(self, message="Permission denied"):
        self.message = message
        super().__init__(self.message)


def get_current_user():
    """Get the current authenticated user from the request."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user

    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user and user.is_active:
            g.current_user = user
            return user
    except Exception:
        pass

    return None


def require_permission(entity: str, action: str, own_only_field: str = None):
    """
    Decorator to require a specific permission.

    Args:
        entity: The entity to check permission for (e.g., 'user', 'order')
        action: The action to check (e.g., 'create', 'read', 'update', 'delete')
        own_only_field: Optional field name to check for own-only access
                       (e.g., 'user_id' means only allow if resource.user_id == current_user.id)

    Example:
        @require_permission('order', 'read')
        def get_order(order_id):
            ...

        @require_permission('order', 'read', own_only_field='user_id')
        def get_order(order_id):
            # Will check if order.user_id == current_user.id when conditions include own_only
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'Authentication required'
                }), 401

            user = get_current_user()
            if not user:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'User not found or inactive'
                }), 401

            # Check permission
            if not user.has_permission(entity, action):
                return jsonify({
                    'error': 'forbidden',
                    'message': f'Permission denied: {entity}.{action}'
                }), 403

            # Store permission info for use in the view
            g.permission_entity = entity
            g.permission_action = action
            g.permission_own_only_field = own_only_field

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_superadmin():
    """
    Decorator to require superadmin role.

    Only superadmin users can access the decorated endpoint.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'Authentication required'
                }), 401

            user = get_current_user()
            if not user:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'User not found or inactive'
                }), 401

            if not user.is_superadmin():
                return jsonify({
                    'error': 'forbidden',
                    'message': 'Superadmin access required'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin():
    """
    Decorator to require admin role (including superadmin).

    Admin and superadmin users can access the decorated endpoint.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'Authentication required'
                }), 401

            user = get_current_user()
            if not user:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'User not found or inactive'
                }), 401

            if not user.is_admin():
                return jsonify({
                    'error': 'forbidden',
                    'message': 'Admin access required'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_own_only(user, resource, field_name: str = 'user_id') -> bool:
    """
    Check if user can access resource based on own_only condition.

    Args:
        user: The current user
        resource: The resource being accessed
        field_name: The field to check ownership (default: 'user_id')

    Returns:
        True if user can access, False otherwise
    """
    if not user or not resource:
        return False

    # Superadmin can access anything
    if user.is_superadmin():
        return True

    # Admin can access anything
    if user.is_admin():
        return True

    # Check ownership
    resource_user_id = getattr(resource, field_name, None)
    if resource_user_id is None:
        return False

    return str(resource_user_id) == str(user.id)


def filter_query_by_permission(query, model, user, entity: str, action: str = 'read_all'):
    """
    Filter a SQLAlchemy query based on user permissions.

    If the user has own_only condition, filter to only their records.

    Args:
        query: SQLAlchemy query object
        model: The model class
        user: Current user
        entity: Entity being queried
        action: Action being performed

    Returns:
        Filtered query
    """
    if not user or not user.role:
        return query.filter(False)  # Return empty result

    # Superadmin sees all
    if user.is_superadmin():
        return query

    # Admin sees all
    if user.is_admin():
        return query

    # Check permission
    if not user.has_permission(entity, action):
        return query.filter(False)  # Return empty result

    # Get permission to check conditions
    perm = user.role.permissions.filter_by(
        entity=entity,
        action=action,
        is_enabled=True
    ).first()

    if perm and perm.conditions and perm.conditions.get('own_only'):
        # Filter to own records only
        if hasattr(model, 'user_id'):
            query = query.filter(model.user_id == user.id)
        elif hasattr(model, 'id') and model.__tablename__ == 'users':
            query = query.filter(model.id == user.id)

    return query


def get_permission_conditions(user, entity: str, action: str) -> dict:
    """
    Get the conditions for a user's permission.

    Args:
        user: The user
        entity: The entity
        action: The action

    Returns:
        Dictionary of conditions or empty dict
    """
    if not user or not user.role:
        return {}

    perm = user.role.permissions.filter_by(
        entity=entity,
        action=action,
        is_enabled=True
    ).first()

    return perm.conditions if perm and perm.conditions else {}


# Export permission constants for convenience
Actions = PermissionAction
Entities = PermissionEntity
