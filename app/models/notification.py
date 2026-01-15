import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db


class Notification(db.Model):
    """Notification model for user notifications."""

    __tablename__ = 'notifications'

    # Type choices
    TYPE_ORDER_UPDATE = 'order_update'
    TYPE_PAYMENT = 'payment'
    TYPE_PROMO = 'promo'
    TYPE_SYSTEM = 'system'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(JSONB, default=dict)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    user = db.relationship('User', back_populates='notifications')

    # Indexes
    __table_args__ = (
        db.Index('idx_notifications_unread', 'user_id', 'is_read', postgresql_where=(~is_read)),
    )

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    @classmethod
    def create_notification(cls, user_id, type, title, message, data=None):
        """Create a new notification."""
        notification = cls(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data or {}
        )
        db.session.add(notification)
        return notification

    @classmethod
    def get_unread_count(cls, user_id):
        """Get count of unread notifications for a user."""
        return cls.query.filter_by(user_id=user_id, is_read=False).count()

    @classmethod
    def mark_all_as_read(cls, user_id):
        """Mark all notifications as read for a user."""
        cls.query.filter_by(user_id=user_id, is_read=False).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })

    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
        }

    def __repr__(self):
        return f'<Notification {self.title[:30]}>'
