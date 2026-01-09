from marshmallow import Schema, fields, validate


class OrderItemSchema(Schema):
    """Schema for order item serialization."""

    id = fields.UUID(dump_only=True)
    order_id = fields.UUID(dump_only=True)
    store_id = fields.UUID()
    store_name = fields.Str(dump_only=True)
    product_url = fields.Str(required=True, validate=validate.URL())
    title = fields.Str(validate=validate.Length(max=500))
    image_url = fields.Str()
    variant_size = fields.Str(validate=validate.Length(max=100))
    variant_color = fields.Str(validate=validate.Length(max=100))
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    unit_price = fields.Decimal(required=True, as_string=True, places=2)
    total_price = fields.Decimal(dump_only=True, as_string=True, places=2)
    notes = fields.Str()
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class OrderItemCreateSchema(Schema):
    """Schema for creating an order item."""

    store_id = fields.UUID()
    product_url = fields.Str(required=True, validate=validate.URL())
    title = fields.Str(validate=validate.Length(max=500))
    image_url = fields.Str()
    variant_size = fields.Str(validate=validate.Length(max=100))
    variant_color = fields.Str(validate=validate.Length(max=100))
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    unit_price = fields.Decimal(required=True, as_string=True, places=2)
    notes = fields.Str()


class OrderSchema(Schema):
    """Schema for order serialization."""

    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    order_number = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    payment_status = fields.Str(dump_only=True)
    subtotal = fields.Decimal(dump_only=True, as_string=True, places=2)
    platform_fee = fields.Decimal(dump_only=True, as_string=True, places=2)
    shipping_usa = fields.Decimal(dump_only=True, as_string=True, places=2)
    shipping_vzla = fields.Decimal(dump_only=True, as_string=True, places=2)
    taxes_estimated = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_usd = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_bs = fields.Decimal(dump_only=True, as_string=True, places=2)
    exchange_rate = fields.Decimal(dump_only=True, as_string=True, places=4)
    notes = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    paid_at = fields.DateTime(dump_only=True)
    shipped_at = fields.DateTime(dump_only=True)
    delivered_at = fields.DateTime(dump_only=True)
    shipping_address = fields.Nested('AddressSchema', dump_only=True)
    items = fields.List(fields.Nested(OrderItemSchema), dump_only=True)


class OrderCreateSchema(Schema):
    """Schema for creating an order."""

    shipping_address_id = fields.UUID(required=True)
    items = fields.List(fields.Nested(OrderItemCreateSchema), required=True, validate=validate.Length(min=1))
    notes = fields.Str()


class OrderUpdateSchema(Schema):
    """Schema for updating an order."""

    status = fields.Str(validate=validate.OneOf(['pending', 'processing', 'shipped', 'delivered', 'cancelled']))
    notes = fields.Str()


class OrderStatusUpdateSchema(Schema):
    """Schema for updating order status."""

    status = fields.Str(required=True, validate=validate.OneOf(['pending', 'processing', 'shipped', 'delivered', 'cancelled']))
    notes = fields.Str()
