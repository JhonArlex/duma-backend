from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from decimal import Decimal
from app.utils.permissions import require_superadmin

from app.extensions import db
from app.models.cart import Cart, CartItem
from app.models.store import Store
from app.schemas.cart import CartSchema, CartItemSchema, CartItemCreateSchema, CartItemUpdateSchema
from app.utils.errors import error_response, validation_error_response, ErrorCode

bp = Blueprint('carts', __name__, url_prefix='/carts')


def get_or_create_cart(user_id):
    """Get user's cart or create one if it doesn't exist."""
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart


@bp.route('', methods=['GET'])
@jwt_required()
def get_cart():
    """Get current user's cart."""
    user_id = get_jwt_identity()
    cart = get_or_create_cart(user_id)

    cart_schema = CartSchema()
    return jsonify(cart_schema.dump(cart)), 200


@bp.route('/items', methods=['POST'])
@jwt_required()
def add_item():
    """Add item to cart."""
    user_id = get_jwt_identity()
    cart = get_or_create_cart(user_id)

    schema = CartItemCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(validation_error_response(err.messages)), 400

    # Get store if provided
    store_id = data.get('store_id')
    if store_id:
        store = Store.query.get(store_id)
        if not store or not store.is_active:
            store_id = None

    # Check if item already exists in cart
    existing_item = CartItem.query.filter_by(
        cart_id=cart.id,
        product_url=data['product_url']
    ).first()

    if existing_item:
        # Update existing item
        existing_item.quantity += data.get('quantity', 1)
        existing_item.unit_price = Decimal(str(data['unit_price']))
        if data.get('title'):
            existing_item.title = data['title']
        if data.get('image_url'):
            existing_item.image_url = data['image_url']
        if data.get('variant_size'):
            existing_item.variant_size = data['variant_size']
        if data.get('variant_color'):
            existing_item.variant_color = data['variant_color']
        if data.get('notes'):
            existing_item.notes = data['notes']
        item = existing_item
    else:
        # Create new item
        item = CartItem(
            cart_id=cart.id,
            store_id=store_id,
            product_url=data['product_url'],
            title=data.get('title'),
            image_url=data.get('image_url'),
            variant_size=data.get('variant_size'),
            variant_color=data.get('variant_color'),
            quantity=data.get('quantity', 1),
            unit_price=Decimal(str(data['unit_price'])),
            notes=data.get('notes')
        )
        db.session.add(item)

    db.session.commit()

    cart_item_schema = CartItemSchema()
    return jsonify(cart_item_schema.dump(item)), 201


@bp.route('/items/<uuid:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    """Update cart item."""
    user_id = get_jwt_identity()
    cart = get_or_create_cart(user_id)

    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()

    if not item:
        return jsonify(error_response(ErrorCode.CART_ITEM_NOT_FOUND)), 404

    schema = CartItemUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    if 'quantity' in data:
        item.quantity = data['quantity']
    if 'notes' in data:
        item.notes = data['notes']

    db.session.commit()

    cart_item_schema = CartItemSchema()
    return jsonify(cart_item_schema.dump(item)), 200


@bp.route('/items/<uuid:item_id>', methods=['DELETE'])
@jwt_required()
def remove_item(item_id):
    """Remove item from cart."""
    user_id = get_jwt_identity()
    cart = get_or_create_cart(user_id)

    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()

    if not item:
        return jsonify({'error': 'item_not_found', 'message': 'Cart item not found'}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({'message': 'Item removed from cart'}), 200


@bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Clear all items from cart."""
    user_id = get_jwt_identity()
    cart = get_or_create_cart(user_id)

    CartItem.query.filter_by(cart_id=cart.id).delete()
    db.session.commit()

    return jsonify({'message': 'Cart cleared'}), 200


@bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    """Convert cart to order."""
    user_id = get_jwt_identity()
    cart = get_or_create_cart(user_id)

    items = list(cart.items)

    if not items:
        return jsonify(error_response('CART_EMPTY', message='Cart is empty')), 400

    shipping_address_id = request.json.get('shipping_address_id')
    if not shipping_address_id:
        return jsonify(error_response('SHIPPING_ADDRESS_REQUIRED', message='Shipping address is required')), 400

    # Prepare order data
    order_items = []
    for item in items:
        order_items.append({
            'store_id': str(item.store_id) if item.store_id else None,
            'product_url': item.product_url,
            'title': item.title,
            'image_url': item.image_url,
            'variant_size': item.variant_size,
            'variant_color': item.variant_color,
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'notes': item.notes
        })

    # Return data for order creation
    # The actual order creation should be done through the orders endpoint
    return jsonify({
        'message': 'Ready for checkout',
        'order_data': {
            'shipping_address_id': shipping_address_id,
            'items': order_items,
            'subtotal': float(cart.subtotal),
            'item_count': cart.item_count
        }
    }), 200


# =============================================================================
# Admin Cart Management
# =============================================================================

@bp.route('/admin/all', methods=['GET'])
@require_superadmin()
def get_all_carts_admin():
    """Get all carts (Admin only)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Cart.query.paginate(page=page, per_page=per_page)
    
    cart_schema = CartSchema(many=True)
    
    return jsonify({
        'carts': cart_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@bp.route('/admin/<uuid:cart_id>', methods=['GET'])
@require_superadmin()
def get_cart_admin(cart_id):
    """Get any cart by ID (Admin only)."""
    cart = Cart.query.get(cart_id)
    
    if not cart:
        return jsonify(error_response(ErrorCode.CART_NOT_FOUND)), 404
        
    cart_schema = CartSchema()
    return jsonify(cart_schema.dump(cart)), 200


@bp.route('/admin', methods=['POST'])
@require_superadmin()
def create_cart_admin():
    """Create a new cart for a user (Admin only)."""
    user_id = request.json.get('user_id')
    if not user_id:
         return jsonify(error_response(ErrorCode.MISSING_USER_ID)), 400
         
    # Check if cart exists
    cart = Cart.query.filter_by(user_id=user_id).first()
    if cart:
        return jsonify({'message': 'Cart already exists', 'id': cart.id}), 200
        
    cart = Cart(user_id=user_id)
    db.session.add(cart)
    db.session.commit()
    
    cart_schema = CartSchema()
    return jsonify(cart_schema.dump(cart)), 201
