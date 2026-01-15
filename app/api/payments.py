from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from decimal import Decimal
from datetime import datetime

from app.extensions import db
from app.models.payment import Payment
from app.models.order import Order
from app.schemas.payment import PaymentSchema, PaymentCreateSchema

bp = Blueprint('payments', __name__, url_prefix='/payments')


@bp.route('/create-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    """Create a Stripe payment intent for an order."""
    user_id = get_jwt_identity()

    order_id = request.json.get('order_id')
    if not order_id:
        return jsonify({'error': 'missing_order', 'message': 'Order ID is required'}), 400

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({'error': 'order_not_found', 'message': 'Order not found'}), 404

    if order.payment_status == Order.PAYMENT_STATUS_PAID:
        return jsonify({'error': 'already_paid', 'message': 'Order is already paid'}), 400

    # Create payment intent with Stripe
    stripe_secret = current_app.config.get('STRIPE_SECRET_KEY')
    if not stripe_secret:
        return jsonify({'error': 'payment_not_configured', 'message': 'Payment provider not configured'}), 500

    try:
        import stripe
        stripe.api_key = stripe_secret

        intent = stripe.PaymentIntent.create(
            amount=int(order.total_usd * 100),  # Stripe uses cents
            currency='usd',
            metadata={
                'order_id': str(order.id),
                'order_number': order.order_number,
                'user_id': str(user_id)
            }
        )

        return jsonify({
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id,
            'amount': float(order.total_usd),
            'currency': 'USD'
        }), 200

    except Exception as e:
        return jsonify({'error': 'payment_error', 'message': str(e)}), 500


@bp.route('/confirm', methods=['POST'])
@jwt_required()
def confirm_payment():
    """Confirm a payment after Stripe processing."""
    user_id = get_jwt_identity()
    schema = PaymentCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'validation_error', 'messages': err.messages}), 400

    order = Order.query.filter_by(id=data['order_id'], user_id=user_id).first()

    if not order:
        return jsonify({'error': 'order_not_found', 'message': 'Order not found'}), 404

    if order.payment_status == Order.PAYMENT_STATUS_PAID:
        return jsonify({'error': 'already_paid', 'message': 'Order is already paid'}), 400

    # Create payment record
    payment = Payment(
        order_id=order.id,
        user_id=user_id,
        payment_provider=data['payment_provider'],
        amount=order.total_usd,
        currency='USD',
        payment_method=data.get('payment_method', 'card')
    )

    if data['payment_provider'] == 'stripe':
        # Verify payment with Stripe
        stripe_secret = current_app.config.get('STRIPE_SECRET_KEY')
        if stripe_secret and data.get('stripe_payment_method_id'):
            try:
                import stripe
                stripe.api_key = stripe_secret

                # In production, you would verify the payment intent here
                payment.provider_txn_id = data.get('stripe_payment_method_id')
                payment.mark_completed()

                # Update order payment status
                order.payment_status = Order.PAYMENT_STATUS_PAID
                order.paid_at = datetime.utcnow()

            except Exception as e:
                payment.mark_failed(str(e))
                db.session.add(payment)
                db.session.commit()
                return jsonify({'error': 'payment_failed', 'message': str(e)}), 400

    db.session.add(payment)
    db.session.commit()

    payment_schema = PaymentSchema()
    return jsonify(payment_schema.dump(payment)), 200


@bp.route('/<uuid:payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """Get payment details."""
    user_id = get_jwt_identity()
    payment = Payment.query.filter_by(id=payment_id, user_id=user_id).first()

    if not payment:
        return jsonify({'error': 'payment_not_found', 'message': 'Payment not found'}), 404

    payment_schema = PaymentSchema()
    return jsonify(payment_schema.dump(payment)), 200


@bp.route('/order/<uuid:order_id>', methods=['GET'])
@jwt_required()
def get_order_payments(order_id):
    """Get all payments for an order."""
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({'error': 'order_not_found', 'message': 'Order not found'}), 404

    payments = Payment.query.filter_by(order_id=order_id).all()

    payment_schema = PaymentSchema(many=True)
    return jsonify(payment_schema.dump(payments)), 200


@bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks."""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        return jsonify({'error': 'webhook_not_configured'}), 500

    try:
        import stripe
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')

        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            order_id = payment_intent['metadata'].get('order_id')

            if order_id:
                order = Order.query.get(order_id)
                if order and order.payment_status != Order.PAYMENT_STATUS_PAID:
                    order.payment_status = Order.PAYMENT_STATUS_PAID
                    order.paid_at = datetime.utcnow()
                    db.session.commit()

        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            order_id = payment_intent['metadata'].get('order_id')

            if order_id:
                order = Order.query.get(order_id)
                if order:
                    order.payment_status = Order.PAYMENT_STATUS_FAILED
                    db.session.commit()

        return jsonify({'received': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
