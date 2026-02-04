"""
Marshmallow schemas for Role and Permission validation.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError

from app.models.role import Role, PermissionEntity, PermissionAction


class RoleSchema(Schema):
    """Schema for role serialization."""
    id = fields.UUID(dump_only=True)
    name = fields.String()
    description = fields.String()
    type = fields.String()
    is_system = fields.Boolean()
    is_default = fields.Boolean()
    user_count = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    permissions = fields.Method('get_permissions', dump_only=True)
    
    def get_permissions(self, obj):
        """Get permissions as a dictionary."""
        return obj.get_permissions_dict()


class RoleCreateSchema(Schema):
    """Schema for creating a new role."""
    name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100)
    )
    description = fields.String(
        validate=validate.Length(max=500)
    )
    type = fields.String(
        validate=validate.OneOf([
            Role.TYPE_ADMIN,
            Role.TYPE_AUTHENTICATED
        ]),
        load_default=Role.TYPE_AUTHENTICATED
    )

    @validates('type')
    def validate_type(self, value):
        """Cannot create superadmin or public roles."""
        if value in [Role.TYPE_SUPERADMIN, Role.TYPE_PUBLIC]:
            raise ValidationError(f'Cannot create role with type: {value}')


class RoleUpdateSchema(Schema):
    """Schema for updating a role."""
    name = fields.String(
        validate=validate.Length(min=2, max=100)
    )
    description = fields.String(
        validate=validate.Length(max=500)
    )


class PermissionSchema(Schema):
    """Schema for permission serialization."""
    id = fields.UUID(dump_only=True)
    role_id = fields.UUID()
    entity = fields.String()
    action = fields.String()
    is_enabled = fields.Boolean()
    conditions = fields.Dict()
    created_at = fields.DateTime(dump_only=True)


class PermissionUpdateSchema(Schema):
    """
    Schema for updating multiple permissions.

    Expected format:
    {
        "permissions": {
            "user": {
                "create": true,
                "read": true,
                "read_all": false,
                "update": true,
                "delete": false
            },
            ...
        }
    }
    """
    permissions = fields.Dict(
        keys=fields.String(),
        values=fields.Dict(
            keys=fields.String(),
            values=fields.Boolean()
        ),
        required=True
    )

    @validates('permissions')
    def validate_permissions(self, value):
        """Validate entities and actions."""
        for entity, actions in value.items():
            if entity not in PermissionEntity.ALL_ENTITIES:
                raise ValidationError(f'Invalid entity: {entity}')

            for action in actions.keys():
                if action not in PermissionAction.ALL_ACTIONS:
                    raise ValidationError(f'Invalid action: {action}')


class SinglePermissionUpdateSchema(Schema):
    """Schema for updating a single permission."""
    is_enabled = fields.Boolean(required=True)
    conditions = fields.Dict(load_default=None)


class UserRoleAssignSchema(Schema):
    """Schema for assigning a role to a user."""
    role_id = fields.UUID(required=True)
