from marshmallow import Schema, fields, validate


class StoreSchema(Schema):
    """Schema for store serialization."""

    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    slug = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    base_url = fields.Str(required=True, validate=validate.URL())
    logo_url = fields.Str()
    is_active = fields.Bool()
    display_order = fields.Int()
    config = fields.Method("get_config")

    def get_config(self, obj):
        if obj.config and isinstance(obj.config, str):
            import json
            try:
                return json.loads(obj.config)
            except json.JSONDecodeError:
                return {}
        return obj.config or {}


class StoreCreateSchema(Schema):
    """Schema for creating a store (admin only)."""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    slug = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    base_url = fields.Str(required=True, validate=validate.URL())
    logo_url = fields.Str()
    is_active = fields.Bool(load_default=True)
    display_order = fields.Int(load_default=0)
    config = fields.Dict(load_default=dict)
