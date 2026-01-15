from typing import Optional, Tuple
from decimal import Decimal

from app.extensions import db
from app.models.cart import Cart, CartItem
from app.models.store import Store


class CartService:
    """Service for handling cart operations."""

    @staticmethod
    def get_or_create_cart(user_id: str) -> Cart:
        """Get user's cart or create one if it doesn't exist."""
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()
        return cart

    @staticmethod
    def add_item(
        cart: Cart,
        product_url: str,
        unit_price: Decimal,
        quantity: int = 1,
        store_id: Optional[str] = None,
        title: Optional[str] = None,
        image_url: Optional[str] = None,
        variant_size: Optional[str] = None,
        variant_color: Optional[str] = None,
        notes: Optional[str] = None
    ) -> CartItem:
        """
        Add item to cart or update if already exists.

        Returns:
            CartItem instance.
        """
        # Validate store if provided
        if store_id:
            store = Store.query.get(store_id)
            if not store or not store.is_active:
                store_id = None

        # Check for existing item
        existing_item = CartItem.query.filter_by(
            cart_id=cart.id,
            product_url=product_url
        ).first()

        if existing_item:
            existing_item.quantity += quantity
            existing_item.unit_price = unit_price
            if title:
                existing_item.title = title
            if image_url:
                existing_item.image_url = image_url
            if variant_size:
                existing_item.variant_size = variant_size
            if variant_color:
                existing_item.variant_color = variant_color
            if notes:
                existing_item.notes = notes
            db.session.commit()
            return existing_item

        # Create new item
        item = CartItem(
            cart_id=cart.id,
            store_id=store_id,
            product_url=product_url,
            title=title,
            image_url=image_url,
            variant_size=variant_size,
            variant_color=variant_color,
            quantity=quantity,
            unit_price=unit_price,
            notes=notes
        )
        db.session.add(item)
        db.session.commit()

        return item

    @staticmethod
    def update_item(
        cart: Cart,
        item_id: str,
        quantity: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[CartItem], Optional[str]]:
        """
        Update cart item.

        Returns:
            Tuple of (CartItem, error_message).
        """
        item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()

        if not item:
            return None, 'Cart item not found'

        if quantity is not None:
            if quantity < 1:
                return None, 'Quantity must be at least 1'
            item.quantity = quantity

        if notes is not None:
            item.notes = notes

        db.session.commit()
        return item, None

    @staticmethod
    def remove_item(cart: Cart, item_id: str) -> Tuple[bool, Optional[str]]:
        """
        Remove item from cart.

        Returns:
            Tuple of (success, error_message).
        """
        item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()

        if not item:
            return False, 'Cart item not found'

        db.session.delete(item)
        db.session.commit()

        return True, None

    @staticmethod
    def clear_cart(cart: Cart) -> None:
        """Clear all items from cart."""
        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()

    @staticmethod
    def get_cart_summary(cart: Cart) -> dict:
        """Get cart summary with totals."""
        return {
            'id': str(cart.id),
            'item_count': cart.item_count,
            'subtotal': float(cart.subtotal),
            'currency': cart.currency,
            'status': cart.status
        }

    @staticmethod
    def convert_to_order_items(cart: Cart) -> list:
        """Convert cart items to order item data format."""
        return [
            {
                'store_id': str(item.store_id) if item.store_id else None,
                'product_url': item.product_url,
                'title': item.title,
                'image_url': item.image_url,
                'variant_size': item.variant_size,
                'variant_color': item.variant_color,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'notes': item.notes
            }
            for item in cart.items
        ]
