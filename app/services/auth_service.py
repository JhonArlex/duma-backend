from typing import Optional, Tuple
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db
from app.models.user import User
from app.models.cart import Cart


class AuthService:
    """Service for handling authentication operations."""

    @staticmethod
    def register_user(
        email: str,
        password: str,
        display_name: str,
        phone_number: Optional[str] = None,
        country: str = 'Venezuela'
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Register a new user with email and password.

        Returns:
            Tuple of (User, error_message). User is None if registration failed.
        """
        # Check if email exists
        if User.query.filter_by(email=email).first():
            return None, 'Email already registered'

        user = User(
            email=email,
            display_name=display_name,
            phone_number=phone_number,
            country=country,
            auth_provider='email'
        )
        user.set_password(password)

        db.session.add(user)

        # Create cart for user
        cart = Cart(user_id=user.id)
        db.session.add(cart)

        db.session.commit()
        return user, None

    @staticmethod
    def authenticate(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate user with email and password.

        Returns:
            Tuple of (User, error_message). User is None if authentication failed.
        """
        user = User.query.filter_by(email=email, is_active=True).first()

        if not user:
            return None, 'Invalid email or password'

        if not user.check_password(password):
            return None, 'Invalid email or password'

        user.update_last_login()
        db.session.commit()

        return user, None

    @staticmethod
    def oauth_login(
        provider: str,
        provider_id: str,
        email: str,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Handle OAuth login/registration.

        Returns:
            Tuple of (User, error_message). User is None if login failed.
        """
        # Check if user exists with this OAuth provider
        user = User.query.filter_by(
            auth_provider=provider,
            auth_provider_id=provider_id
        ).first()

        if user:
            user.update_last_login()
            db.session.commit()
            return user, None

        # Check if email exists with different provider
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return None, f'Email already registered with {existing_user.auth_provider}'

        # Create new user
        user = User(
            email=email,
            display_name=display_name or email.split('@')[0],
            photo_url=photo_url,
            auth_provider=provider,
            auth_provider_id=provider_id,
            email_verified=True
        )
        db.session.add(user)

        # Create cart for user
        cart = Cart(user_id=user.id)
        db.session.add(cart)

        db.session.commit()
        return user, None

    @staticmethod
    def generate_tokens(user: User) -> dict:
        """Generate access and refresh tokens for a user."""
        return {
            'access_token': create_access_token(identity=user),
            'refresh_token': create_refresh_token(identity=user)
        }

    @staticmethod
    def refresh_access_token(user_id: str) -> Optional[str]:
        """Generate a new access token for a user."""
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return None
        return create_access_token(identity=user)

    @staticmethod
    def change_password(
        user: User,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user's password.

        Returns:
            Tuple of (success, error_message).
        """
        if user.auth_provider != 'email':
            return False, 'Cannot change password for OAuth users'

        if not user.check_password(current_password):
            return False, 'Current password is incorrect'

        user.set_password(new_password)
        db.session.commit()

        return True, None
