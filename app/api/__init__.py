from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')


def register_routes(app):
    """Register all API routes."""
    from app.api import auth, users, orders, carts, stores, payments, roles

    api_bp.register_blueprint(auth.bp)
    api_bp.register_blueprint(users.bp)
    api_bp.register_blueprint(orders.bp)
    api_bp.register_blueprint(carts.bp)
    api_bp.register_blueprint(stores.bp)
    api_bp.register_blueprint(payments.bp)
    api_bp.register_blueprint(roles.bp)

    app.register_blueprint(api_bp)


def init_swagger(app):
    """Initialize Swagger documentation."""
    from app.api.swagger import api

    # Initialize Flask-RESTX with the app
    api.init_app(app)

    # Import documentation resources to register them
    from app.api import docs  # noqa: F401

    return api
