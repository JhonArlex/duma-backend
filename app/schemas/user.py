from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
import re
from app.schemas.role import RoleSchema


class UserSchema(Schema):
    """Schema for user serialization."""

    id = fields.UUID(dump_only=True)
    email = fields.Email(required=True)
    display_name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    phone_number = fields.Str(validate=validate.Length(max=50))
    identificacion = fields.Str(validate=validate.Length(max=50))
    photo_url = fields.Str()
    country = fields.Str(validate=validate.Length(max=100))
    default_currency = fields.Str(validate=validate.Length(max=10))
    locker_code = fields.Str(validate=validate.Length(max=50))
    email_verified = fields.Bool(dump_only=True)
    auth_provider = fields.Str(dump_only=True)
    role = fields.Nested('RoleSchema', dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    last_login = fields.DateTime(dump_only=True)


class UserCreateSchema(Schema):
    """Schema for user registration."""

    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128)
    )
    display_name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    phone_number = fields.Str(validate=validate.Length(max=50))
    country = fields.Str(validate=validate.Length(max=100))

    @validates('password')
    def validate_password(self, value):
        """Validate password strength."""
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', value):
            raise ValidationError('Password must contain at least one digit.')


class UserUpdateSchema(Schema):
    """Schema for user profile update."""

    display_name = fields.Str(validate=validate.Length(min=2, max=255))
    phone_number = fields.Str(validate=validate.Length(max=50))
    identificacion = fields.Str(validate=validate.Length(max=50))
    photo_url = fields.Str()
    country = fields.Str(validate=validate.Length(max=100))
    default_currency = fields.Str(validate=validate.Length(max=10))
    locker_code = fields.Str(validate=validate.Length(max=50))


class LoginSchema(Schema):
    """Schema for user login."""

    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class PasswordChangeSchema(Schema):
    """Schema for password change."""

    current_password = fields.Str(required=True, load_only=True)
    new_password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128)
    )

    @validates('new_password')
    def validate_password(self, value):
        """Validate password strength."""
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', value):
            raise ValidationError('Password must contain at least one digit.')


class OAuthLoginSchema(Schema):
    """Schema for OAuth login."""

    provider = fields.Str(required=True, validate=validate.OneOf(['google', 'apple']))
    token = fields.Str(required=True)
    email = fields.Email()
    display_name = fields.Str()
    photo_url = fields.Str()
