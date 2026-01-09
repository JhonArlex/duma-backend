from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.models.store import Store
from app.schemas.store import StoreSchema

bp = Blueprint('stores', __name__, url_prefix='/stores')


@bp.route('', methods=['GET'])
def get_stores():
    """Get all active stores."""
    stores = Store.get_active_stores()

    store_schema = StoreSchema(many=True)
    return jsonify(store_schema.dump(stores)), 200


@bp.route('/<string:slug>', methods=['GET'])
def get_store(slug):
    """Get store by slug."""
    store = Store.get_by_slug(slug)

    if not store:
        return jsonify({'error': 'store_not_found', 'message': 'Store not found'}), 404

    store_schema = StoreSchema()
    return jsonify(store_schema.dump(store)), 200


@bp.route('/<uuid:store_id>/config', methods=['GET'])
@jwt_required()
def get_store_config(store_id):
    """Get store configuration (for WebView)."""
    store = Store.query.get(store_id)

    if not store or not store.is_active:
        return jsonify({'error': 'store_not_found', 'message': 'Store not found'}), 404

    return jsonify({
        'id': str(store.id),
        'name': store.name,
        'slug': store.slug,
        'base_url': store.base_url,
        'config': store.config
    }), 200
