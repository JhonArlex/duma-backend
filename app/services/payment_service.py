from typing import Optional, Tuple
from decimal import Decimal
from datetime import datetime
from flask import current_app

from app.extensions import db
from app.models.payment import Payment
from app.models.order import Order


class PaymentService:
    """Service for handling payment operations."""

    @staticmethod
    def create_stripe_payment_intent(order: Order) -> Tuple[Optional[dict], Optional[str]]:
        """
        Create a Stripe payment intent for an order.

        Returns:
            Tuple of (intent_data, error_message).
        """
        stripe_secret = current_app.config.get('STRIPE_SECRET_KEY')
        if not stripe_secret:
            return None, 'Stripe not configured'

        try:
            import stripe
            stripe.api_key = stripe_secret

            intent = stripe.PaymentIntent.create(
                amount=int(order.total_usd * 100),  # Stripe uses cents
                currency='usd',
                metadata={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'user_id': str(order.user_id)
                }
            )

            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': float(order.total_usd),
                'currency': 'USD'
            }, None

        except Exception as e:
            return None, str(e)

    @staticmethod
    def process_payment(
        order: Order,
        user_id: str,
        provider: str,
        provider_txn_id: Optional[str] = None,
        payment_method: str = 'card',
        card_last_four: Optional[str] = None,
        card_brand: Optional[str] = None
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Process and record a payment.

        Returns:
            Tuple of (Payment, error_message).
        """
        if order.payment_status == Order.PAYMENT_STATUS_PAID:
            return None, 'Order is already paid'

        payment = Payment(
            order_id=order.id,
            user_id=user_id,
            payment_provider=provider,
            provider_txn_id=provider_txn_id,
            amount=order.total_usd,
            currency='USD',
            payment_method=payment_method,
            card_last_four=card_last_four,
            card_brand=card_brand
        )

        try:
            # In production, verify the payment with the provider here
            payment.mark_completed(provider_txn_id)

            # Update order
            order.payment_status = Order.PAYMENT_STATUS_PAID
            order.paid_at = datetime.utcnow()

            db.session.add(payment)
            db.session.commit()

            return payment, None

        except Exception as e:
            payment.mark_failed(str(e))
            db.session.add(payment)
            db.session.commit()
            return None, str(e)

    @staticmethod
    def verify_stripe_payment(payment_intent_id: str) -> Tuple[bool, Optional[dict]]:
        """
        Verify a Stripe payment intent status.

        Returns:
            Tuple of (is_successful, payment_data).
        """
        stripe_secret = current_app.config.get('STRIPE_SECRET_KEY')
        if not stripe_secret:
            return False, None

        try:
            import stripe
            stripe.api_key = stripe_secret

            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return intent.status == 'succeeded', {
                'id': intent.id,
                'status': intent.status,
                'amount': intent.amount / 100,
                'currency': intent.currency,
                'metadata': intent.metadata
            }

        except Exception:
            return False, None

    @staticmethod
    def process_refund(
        payment: Payment,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Process a payment refund.

        Returns:
            Tuple of (success, error_message).
        """
        if payment.status != Payment.STATUS_COMPLETED:
            return False, 'Can only refund completed payments'

        refund_amount = amount or payment.amount

        if refund_amount > payment.amount:
            return False, 'Refund amount cannot exceed payment amount'

        try:
            if payment.payment_provider == 'stripe':
                stripe_secret = current_app.config.get('STRIPE_SECRET_KEY')
                if not stripe_secret:
                    return False, 'Stripe not configured'

                import stripe
                stripe.api_key = stripe_secret

                stripe.Refund.create(
                    payment_intent=payment.provider_txn_id,
                    amount=int(refund_amount * 100),
                    reason=reason or 'requested_by_customer'
                )

            payment.mark_refunded()

            # Update order status
            order = payment.order
            order.payment_status = Order.PAYMENT_STATUS_REFUNDED

            db.session.commit()
            return True, None

        except Exception as e:
            return False, str(e)

    @staticmethod
    def handle_stripe_webhook(event_type: str, data: dict) -> bool:
        """
        Handle Stripe webhook events.

        Returns:
            True if handled successfully.
        """
        try:
            if event_type == 'payment_intent.succeeded':
                order_id = data.get('metadata', {}).get('order_id')
                if order_id:
                    order = Order.query.get(order_id)
                    if order and order.payment_status != Order.PAYMENT_STATUS_PAID:
                        order.payment_status = Order.PAYMENT_STATUS_PAID
                        order.paid_at = datetime.utcnow()
                        db.session.commit()

            elif event_type == 'payment_intent.payment_failed':
                order_id = data.get('metadata', {}).get('order_id')
                if order_id:
                    order = Order.query.get(order_id)
                    if order:
                        order.payment_status = Order.PAYMENT_STATUS_FAILED
                        db.session.commit()

            return True

        except Exception:
            return False
