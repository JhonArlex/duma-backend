from typing import Optional, List
from flask import current_app

from app.extensions import db
from app.models.notification import Notification
from app.models.order import Order


class NotificationService:
    """Service for handling notifications."""

    @staticmethod
    def create_notification(
        user_id: str,
        type: str,
        title: str,
        message: str,
        data: Optional[dict] = None
    ) -> Notification:
        """Create a new notification."""
        notification = Notification.create_notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data
        )
        db.session.commit()
        return notification

    @staticmethod
    def get_user_notifications(
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        per_page: int = 20
    ) -> tuple:
        """
        Get notifications for a user.

        Returns:
            Tuple of (notifications, total_count).
        """
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        query = query.order_by(Notification.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page)

        return pagination.items, pagination.total

    @staticmethod
    def mark_as_read(notification_id: str, user_id: str) -> bool:
        """Mark a notification as read."""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return False

        notification.mark_as_read()
        db.session.commit()
        return True

    @staticmethod
    def mark_all_as_read(user_id: str) -> int:
        """Mark all notifications as read for a user."""
        count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()

        Notification.mark_all_as_read(user_id)
        db.session.commit()

        return count

    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """Get count of unread notifications."""
        return Notification.get_unread_count(user_id)

    @classmethod
    def notify_order_status_change(cls, order: Order, new_status: str) -> None:
        """Send notification for order status change."""
        status_messages = {
            'pending': ('Pedido Recibido', f'Tu pedido {order.order_number} ha sido recibido.'),
            'processing': ('Pedido en Proceso', f'Tu pedido {order.order_number} está siendo procesado.'),
            'shipped': ('Pedido Enviado', f'Tu pedido {order.order_number} ha sido enviado.'),
            'delivered': ('Pedido Entregado', f'Tu pedido {order.order_number} ha sido entregado.'),
            'cancelled': ('Pedido Cancelado', f'Tu pedido {order.order_number} ha sido cancelado.')
        }

        title, message = status_messages.get(
            new_status,
            ('Actualización de Pedido', f'Tu pedido {order.order_number} ha sido actualizado.')
        )

        cls.create_notification(
            user_id=str(order.user_id),
            type=Notification.TYPE_ORDER_UPDATE,
            title=title,
            message=message,
            data={'order_id': str(order.id), 'order_number': order.order_number}
        )

        # Send push notification via OneSignal
        cls._send_push_notification(str(order.user_id), title, message)

    @classmethod
    def notify_payment_received(cls, order: Order) -> None:
        """Send notification for payment received."""
        cls.create_notification(
            user_id=str(order.user_id),
            type=Notification.TYPE_PAYMENT,
            title='Pago Recibido',
            message=f'Hemos recibido tu pago para el pedido {order.order_number}.',
            data={'order_id': str(order.id), 'order_number': order.order_number}
        )

        cls._send_push_notification(
            str(order.user_id),
            'Pago Recibido',
            f'Hemos recibido tu pago para el pedido {order.order_number}.'
        )

    @staticmethod
    def _send_push_notification(user_id: str, title: str, message: str) -> bool:
        """Send push notification via OneSignal."""
        app_id = current_app.config.get('ONESIGNAL_APP_ID')
        api_key = current_app.config.get('ONESIGNAL_REST_API_KEY')

        if not app_id or not api_key:
            return False

        try:
            import requests

            headers = {
                'Authorization': f'Basic {api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'app_id': app_id,
                'include_external_user_ids': [user_id],
                'headings': {'en': title},
                'contents': {'en': message}
            }

            response = requests.post(
                'https://onesignal.com/api/v1/notifications',
                json=payload,
                headers=headers
            )

            return response.status_code == 200

        except Exception:
            return False

    @staticmethod
    def delete_notification(notification_id: str, user_id: str) -> bool:
        """Delete a notification."""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return False

        db.session.delete(notification)
        db.session.commit()
        return True
