from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime

from app.extensions import db
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.address import Address
from app.models.store import Store
from app.models.exchange_rate import ExchangeRate


class OrderService:
    """Service for handling order operations."""

    PLATFORM_FEE_PERCENTAGE = Decimal('0.10')  # 10%

    @staticmethod
    def generate_order_number() -> str:
        """Generate a unique order number."""
        year = datetime.utcnow().year
        count = Order.query.filter(
            db.extract('year', Order.created_at) == year
        ).count() + 1
        return f'DUM-{year}-{count:06d}'

    @classmethod
    def create_order(
        cls,
        user_id: str,
        shipping_address_id: str,
        items: List[dict],
        notes: Optional[str] = None
    ) -> Tuple[Optional[Order], Optional[str]]:
        """
        Create a new order.

        Returns:
            Tuple of (Order, error_message). Order is None if creation failed.
        """
        # Verify shipping address
        address = Address.query.filter_by(
            id=shipping_address_id,
            user_id=user_id
        ).first()

        if not address:
            return None, 'Shipping address not found'

        if not items:
            return None, 'Order must have at least one item'

        # Get current exchange rate
        exchange_rate = ExchangeRate.get_current_rate('USD', 'VES')

        # Create order
        order = Order(
            user_id=user_id,
            shipping_address_id=shipping_address_id,
            order_number=cls.generate_order_number(),
            notes=notes,
            subtotal=Decimal('0'),
            total_usd=Decimal('0'),
            exchange_rate=Decimal(str(exchange_rate.rate)) if exchange_rate else None
        )
        db.session.add(order)
        db.session.flush()

        # Create order items
        subtotal = Decimal('0')
        for item_data in items:
            store_id = item_data.get('store_id')
            if store_id:
                store = Store.query.get(store_id)
                if not store or not store.is_active:
                    store_id = None

            unit_price = Decimal(str(item_data['unit_price']))
            quantity = item_data['quantity']
            total_price = unit_price * quantity

            order_item = OrderItem(
                order_id=order.id,
                store_id=store_id,
                product_url=item_data['product_url'],
                title=item_data.get('title'),
                image_url=item_data.get('image_url'),
                variant_size=item_data.get('variant_size'),
                variant_color=item_data.get('variant_color'),
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                notes=item_data.get('notes')
            )
            db.session.add(order_item)
            subtotal += total_price

        # Calculate totals
        order.subtotal = subtotal
        order.platform_fee = subtotal * cls.PLATFORM_FEE_PERCENTAGE
        order.total_usd = order.subtotal + order.platform_fee
        if order.exchange_rate:
            order.total_bs = order.total_usd * order.exchange_rate

        # Create initial status history
        history = OrderStatusHistory(
            order_id=order.id,
            previous_status=None,
            new_status=Order.STATUS_PENDING,
            notes='Order created'
        )
        db.session.add(history)

        db.session.commit()
        return order, None

    @staticmethod
    def get_user_orders(
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[Order], int]:
        """
        Get orders for a user with pagination.

        Returns:
            Tuple of (orders, total_count).
        """
        query = Order.query.filter_by(user_id=user_id)

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(Order.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page)

        return pagination.items, pagination.total

    @staticmethod
    def update_order_status(
        order: Order,
        new_status: str,
        changed_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update order status with validation.

        Returns:
            Tuple of (success, error_message).
        """
        valid_transitions = {
            Order.STATUS_PENDING: [Order.STATUS_PROCESSING, Order.STATUS_CANCELLED],
            Order.STATUS_PROCESSING: [Order.STATUS_SHIPPED, Order.STATUS_CANCELLED],
            Order.STATUS_SHIPPED: [Order.STATUS_DELIVERED],
            Order.STATUS_DELIVERED: [],
            Order.STATUS_CANCELLED: []
        }

        if new_status not in valid_transitions.get(order.status, []):
            return False, f'Cannot transition from {order.status} to {new_status}'

        order.update_status(new_status, changed_by=changed_by, notes=notes)
        db.session.commit()

        return True, None

    @staticmethod
    def cancel_order(
        order: Order,
        user_id: str,
        notes: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Cancel an order.

        Returns:
            Tuple of (success, error_message).
        """
        if order.status not in [Order.STATUS_PENDING, Order.STATUS_PROCESSING]:
            return False, 'Order cannot be cancelled in its current status'

        order.update_status(
            Order.STATUS_CANCELLED,
            changed_by=user_id,
            notes=notes or 'Cancelled by user'
        )
        db.session.commit()

        return True, None

    @staticmethod
    def calculate_order_totals(order: Order) -> None:
        """Recalculate order totals."""
        order.calculate_totals()
        db.session.commit()
