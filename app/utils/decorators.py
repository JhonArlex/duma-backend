from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def admin_required(fn):
    """
    Decorator to require admin privileges.
    Must be used after @jwt_required().
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if not claims.get('is_admin', False):
            return jsonify({
                'error': 'admin_required',
                'message': 'Admin privileges required'
            }), 403
        return fn(*args, **kwargs)
    return wrapper


def rate_limit(limit_string):
    """
    Custom rate limiting decorator.
    Uses Flask-Limiter under the hood.

    Usage:
        @rate_limit('10 per minute')
        def my_endpoint():
            pass
    """
    def decorator(fn):
        from app.extensions import limiter
        return limiter.limit(limit_string)(fn)
    return decorator


def validate_json(*required_fields):
    """
    Decorator to validate that JSON body contains required fields.

    Usage:
        @validate_json('email', 'password')
        def login():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import request
            if not request.is_json:
                return jsonify({
                    'error': 'invalid_request',
                    'message': 'Request body must be JSON'
                }), 400

            data = request.get_json()
            missing = [field for field in required_fields if field not in data]

            if missing:
                return jsonify({
                    'error': 'missing_fields',
                    'message': f'Missing required fields: {", ".join(missing)}'
                }), 400

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def handle_exceptions(fn):
    """
    Decorator to handle exceptions and return proper JSON responses.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            return jsonify({
                'error': 'validation_error',
                'message': str(e)
            }), 400
        except PermissionError as e:
            return jsonify({
                'error': 'permission_denied',
                'message': str(e)
            }), 403
        except Exception as e:
            # Log the error in production
            return jsonify({
                'error': 'internal_error',
                'message': 'An unexpected error occurred'
            }), 500
    return wrapper


def paginate(default_per_page=10, max_per_page=100):
    """
    Decorator to handle pagination parameters.

    Adds 'page' and 'per_page' to kwargs from query parameters.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import request

            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', default_per_page, type=int)

            # Ensure valid values
            page = max(1, page)
            per_page = min(max(1, per_page), max_per_page)

            kwargs['page'] = page
            kwargs['per_page'] = per_page

            return fn(*args, **kwargs)
        return wrapper
    return decorator
