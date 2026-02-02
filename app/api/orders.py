from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from decimal import Decimal

from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.address import Address
from app.models.store import Store
from app.models.exchange_rate import ExchangeRate
from app.schemas.order import OrderSchema, OrderCreateSchema, OrderStatusUpdateSchema

bp = Blueprint('orders', __name__, url_prefix='/orders')


def generate_order_number():
    """Generate a unique order number."""
    from datetime import datetime
    import random
    year = datetime.utcnow().year
    # Get the count of orders this year
    count = Order.query.filter(
        db.extract('year', Order.created_at) == year
    ).count() + 1
    return f'DUM-{year}-{count:06d}'


@bp.route('', methods=['GET'])
@jwt_required()
def get_orders():
    """Get all orders for current user."""
    user_id = get_jwt_identity()

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 50)  # Max 50 per page

    # Status filter
    status = request.args.get('status')

    query = Order.query.filter_by(user_id=user_id)

    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Order.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page)

    order_schema = OrderSchema(many=True)
    return jsonify({
        'orders': order_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@bp.route('/<uuid:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get a specific order."""
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({'error': 'order_not_found', 'message': 'Order not found'}), 404

    order_schema = OrderSchema()
    result = order_schema.dump(order)
    result['items'] = [item.to_dict() for item in order.items]
    return jsonify(result), 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    """Create a new order."""
    user_id = get_jwt_identity()
    schema = OrderCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # Verify shipping address belongs to user
    address = Address.query.filter_by(
        id=data['shipping_address_id'],
        user_id=user_id
    ).first()

    if not address:
        return jsonify({'error': 'invalid_address', 'message': 'Shipping address not found'}), 400

    # Get current exchange rate
    exchange_rate = ExchangeRate.get_current_rate('USD', 'VES')

    # Create order
    order = Order(
        user_id=user_id,
        shipping_address_id=data['shipping_address_id'],
        order_number=generate_order_number(),
        notes=data.get('notes'),
        subtotal=Decimal('0'),
        total_usd=Decimal('0'),
        exchange_rate=Decimal(str(exchange_rate.rate)) if exchange_rate else None
    )
    db.session.add(order)
    db.session.flush()  # Get the order ID

    # Create order items
    subtotal = Decimal('0')
    for item_data in data['items']:
        # Get store if provided
        store_id = item_data.get('store_id')
        if store_id:
            store = Store.query.get(store_id)
            if not store or not store.is_active:
                store_id = None

        unit_price = Decimal(str(item_data['unit_price']))
        quantity = item_data['quantity']
        total_price = unit_price * quantity

        order_item = OrderItem(
            order_id=order.id,
            store_id=store_id,
            product_url=item_data['product_url'],
            title=item_data.get('title'),
            image_url=item_data.get('image_url'),
            variant_size=item_data.get('variant_size'),
            variant_color=item_data.get('variant_color'),
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            notes=item_data.get('notes')
        )
        db.session.add(order_item)
        subtotal += total_price

    # Calculate totals
    order.subtotal = subtotal
    # Platform fee: 10% of subtotal (configurable)
    order.platform_fee = subtotal * Decimal('0.10')
    order.total_usd = order.subtotal + order.platform_fee
    if order.exchange_rate:
        order.total_bs = order.total_usd * order.exchange_rate

    db.session.commit()

    order_schema = OrderSchema()
    result = order_schema.dump(order)
    result['items'] = [item.to_dict() for item in order.items]
    return jsonify(result), 201


@bp.route('/<uuid:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    """Update order status (for admin or status transitions)."""
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({'error': 'order_not_found', 'message': 'Order not found'}), 404

    schema = OrderStatusUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    new_status = data['status']

    # Validate status transitions
    valid_transitions = {
        Order.STATUS_PENDING: [Order.STATUS_PROCESSING, Order.STATUS_CANCELLED],
        Order.STATUS_PROCESSING: [Order.STATUS_SHIPPED, Order.STATUS_CANCELLED],
        Order.STATUS_SHIPPED: [Order.STATUS_DELIVERED],
        Order.STATUS_DELIVERED: [],
        Order.STATUS_CANCELLED: []
    }

    if new_status not in valid_transitions.get(order.status, []):
        return jsonify({
            'error': 'invalid_transition',
            'message': f'Cannot transition from {order.status} to {new_status}'
        }), 400

    order.update_status(new_status, changed_by=user_id, notes=data.get('notes'))
    db.session.commit()

    order_schema = OrderSchema()
    return jsonify(order_schema.dump(order)), 200


@bp.route('/<uuid:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    """Cancel an order."""
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({'error': 'order_not_found', 'message': 'Order not found'}), 404

    if order.status not in [Order.STATUS_PENDING, Order.STATUS_PROCESSING]:
        return jsonify({
            'error': 'cannot_cancel',
            'message': 'Order cannot be cancelled in its current status'
        }), 400

    order.update_status(Order.STATUS_CANCELLED, changed_by=user_id, notes='Cancelled by user')
    db.session.commit()

    order_schema = OrderSchema()
    return jsonify(order_schema.dump(order)), 200


@bp.route('/<uuid:order_id>/history', methods=['GET'])
@jwt_required()
def get_order_history(order_id):
    """Get order status history."""
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({'error': 'order_not_found', 'message': 'Order not found'}), 404

    history = [h.to_dict() for h in order.status_history.order_by('created_at')]
    return jsonify({'history': history}), 200


@bp.route('/admin', methods=['POST'])
@require_superadmin()
def create_order_admin():
    """Create a new order (Admin only)."""
    schema = OrderCreateSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    # User ID must be provided in admin creation, or inferred?
    # Schema might not have user_id. I might need to accept it from request.json separately if schema filters it.
    # Assuming request.json has 'user_id'.
    user_id = request.json.get('user_id')
    if not user_id:
         return jsonify({'error': 'missing_user', 'message': 'User ID is required'}), 400

    # Verify shipping address belongs to user
    address = Address.query.filter_by(
        id=data['shipping_address_id'],
        user_id=user_id
    ).first()

    if not address:
        return jsonify({'error': 'invalid_address', 'message': 'Shipping address not found'}), 400

    # Get current exchange rate
    exchange_rate = ExchangeRate.get_current_rate('USD', 'VES')

    # Create order
    order = Order(
        user_id=user_id,
        shipping_address_id=data['shipping_address_id'],
        order_number=generate_order_number(),
        notes=data.get('notes'),
        subtotal=Decimal('0'),
        total_usd=Decimal('0'),
        exchange_rate=Decimal(str(exchange_rate.rate)) if exchange_rate else None
    )
    db.session.add(order)
    db.session.flush()

    # Create order items
    subtotal = Decimal('0')
    for item_data in data['items']:
        store_id = item_data.get('store_id')
        if store_id:
            store = Store.query.get(store_id)
            if not store or not store.is_active:
                store_id = None

        unit_price = Decimal(str(item_data['unit_price']))
        quantity = item_data['quantity']
        total_price = unit_price * quantity

        order_item = OrderItem(
            order_id=order.id,
            store_id=store_id,
            product_url=item_data['product_url'],
            title=item_data.get('title'),
            image_url=item_data.get('image_url'),
            variant_size=item_data.get('variant_size'),
            variant_color=item_data.get('variant_color'),
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            notes=item_data.get('notes')
        )
        db.session.add(order_item)
        subtotal += total_price

    # Calculate totals
    order.subtotal = subtotal
    order.platform_fee = subtotal * Decimal('0.10')
    order.total_usd = order.subtotal + order.platform_fee
    if order.exchange_rate:
        order.total_bs = order.total_usd * order.exchange_rate

    db.session.commit()

    order_schema = OrderSchema()
    result = order_schema.dump(order)
    result['items'] = [item.to_dict() for item in order.items]
    return jsonify(result), 201
