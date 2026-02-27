from marshmallow import Schema, fields, validate


class CartItemSchema(Schema):
    """Schema for cart item serialization."""

    id = fields.UUID(dump_only=True)
    cart_id = fields.UUID(dump_only=True)
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
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CartItemCreateSchema(Schema):
    """Schema for adding item to cart."""

    store_id = fields.UUID()
    product_url = fields.Str(required=True, validate=validate.URL())
    title = fields.Str(validate=validate.Length(max=500))
    image_url = fields.Str()
    variant_size = fields.Str(validate=validate.Length(max=100))
    variant_color = fields.Str(validate=validate.Length(max=100))
    quantity = fields.Int(load_default=1, validate=validate.Range(min=1))
    unit_price = fields.Decimal(required=True, as_string=True, places=2)
    notes = fields.Str()


class CartItemUpdateSchema(Schema):
    """Schema for updating cart item."""

    quantity = fields.Int(validate=validate.Range(min=1))
    variant_size = fields.Str(validate=validate.Length(max=100))
    variant_color = fields.Str(validate=validate.Length(max=100))
    notes = fields.Str()


class CartSchema(Schema):
    """Schema for cart serialization."""

    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    status = fields.Str(dump_only=True)
    currency = fields.Str()
    item_count = fields.Int(dump_only=True)
    subtotal = fields.Decimal(dump_only=True, as_string=True, places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    items = fields.List(fields.Nested(CartItemSchema), dump_only=True)
