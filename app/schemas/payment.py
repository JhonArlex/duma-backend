from marshmallow import Schema, fields, validate


class PaymentSchema(Schema):
    """Schema for payment serialization."""

    id = fields.UUID(dump_only=True)
    order_id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    payment_provider = fields.Str(dump_only=True)
    provider_txn_id = fields.Str(dump_only=True)
    amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    currency = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    payment_method = fields.Str(dump_only=True)
    card_last_four = fields.Str(dump_only=True)
    card_brand = fields.Str(dump_only=True)
    error_message = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    completed_at = fields.DateTime(dump_only=True)


class PaymentCreateSchema(Schema):
    """Schema for creating a payment."""

    order_id = fields.UUID(required=True)
    payment_provider = fields.Str(required=True, validate=validate.OneOf(['stripe', 'braintree', 'paypal']))
    payment_method = fields.Str(validate=validate.OneOf(['card', 'bank_transfer', 'wallet']))
    # Stripe specific
    stripe_token = fields.Str()
    stripe_payment_method_id = fields.Str()
    # Braintree specific
    braintree_nonce = fields.Str()


class PaymentIntentSchema(Schema):
    """Schema for Stripe payment intent response."""

    client_secret = fields.Str()
    payment_intent_id = fields.Str()
    amount = fields.Decimal(as_string=True, places=2)
    currency = fields.Str()


class RefundSchema(Schema):
    """Schema for payment refund."""

    payment_id = fields.UUID(required=True)
    amount = fields.Decimal(as_string=True, places=2)  # Optional, full refund if not provided
    reason = fields.Str(validate=validate.Length(max=500))
