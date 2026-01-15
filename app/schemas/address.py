from marshmallow import Schema, fields, validate


class AddressSchema(Schema):
    """Schema for address serialization."""

    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    type = fields.Str(required=True, validate=validate.OneOf(['usa_locker', 'vzla_home', 'other']))
    label = fields.Str(validate=validate.Length(max=100))
    address_line_1 = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    address_line_2 = fields.Str(validate=validate.Length(max=255))
    city = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    state = fields.Str(validate=validate.Length(max=100))
    postal_code = fields.Str(validate=validate.Length(max=20))
    country = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    is_default = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    full_address = fields.Str(dump_only=True)


class AddressCreateSchema(Schema):
    """Schema for creating an address."""

    type = fields.Str(required=True, validate=validate.OneOf(['usa_locker', 'vzla_home', 'other']))
    label = fields.Str(validate=validate.Length(max=100))
    address_line_1 = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    address_line_2 = fields.Str(validate=validate.Length(max=255))
    city = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    state = fields.Str(validate=validate.Length(max=100))
    postal_code = fields.Str(validate=validate.Length(max=20))
    country = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    is_default = fields.Bool(load_default=False)


class AddressUpdateSchema(Schema):
    """Schema for updating an address."""

    type = fields.Str(validate=validate.OneOf(['usa_locker', 'vzla_home', 'other']))
    label = fields.Str(validate=validate.Length(max=100))
    address_line_1 = fields.Str(validate=validate.Length(min=1, max=255))
    address_line_2 = fields.Str(validate=validate.Length(max=255))
    city = fields.Str(validate=validate.Length(min=1, max=100))
    state = fields.Str(validate=validate.Length(max=100))
    postal_code = fields.Str(validate=validate.Length(max=20))
    country = fields.Str(validate=validate.Length(min=1, max=100))
    is_default = fields.Bool()
