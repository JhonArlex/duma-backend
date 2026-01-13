"""
Role and Permission models for RBAC system.

Similar to Strapi's role-based access control:
- Roles contain multiple permissions
- Users have one role
- Permissions are per-entity with CRUD actions
- Only superadmin can manage roles and permissions
"""
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db


# Actions available for each entity
class PermissionAction:
    """Permission action constants."""
    CREATE = 'create'
    READ = 'read'           # Individual read (by ID)
    READ_ALL = 'read_all'   # List/read all
    UPDATE = 'update'
    DELETE = 'delete'

    ALL_ACTIONS = [CREATE, READ, READ_ALL, UPDATE, DELETE]


# Entities that can have permissions
class PermissionEntity:
    """Permission entity constants - maps to database tables/resources."""
    USER = 'user'
    ADDRESS = 'address'
    STORE = 'store'
    ORDER = 'order'
    ORDER_ITEM = 'order_item'
    CART = 'cart'
    CART_ITEM = 'cart_item'
    PAYMENT = 'payment'
    EXCHANGE_RATE = 'exchange_rate'
    NOTIFICATION = 'notification'
    ROLE = 'role'
    PERMISSION = 'permission'

    ALL_ENTITIES = [
        USER, ADDRESS, STORE, ORDER, ORDER_ITEM,
        CART, CART_ITEM, PAYMENT, EXCHANGE_RATE,
        NOTIFICATION, ROLE, PERMISSION
    ]


class Role(db.Model):
    """
    Role model - defines a set of permissions.

    Built-in roles:
    - superadmin: Full access to everything, can manage roles
    - admin: Administrative access, cannot manage roles
    - authenticated: Regular authenticated user (default)
    - public: Unauthenticated access
    """

    __tablename__ = 'roles'

    # Role types
    TYPE_SUPERADMIN = 'superadmin'
    TYPE_ADMIN = 'admin'
    TYPE_AUTHENTICATED = 'authenticated'
    TYPE_PUBLIC = 'public'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(50), nullable=False, default=TYPE_AUTHENTICATED)

    # Is this a system role that cannot be deleted?
    is_system = db.Column(db.Boolean, default=False)

    # Is this the default role for new users?
    is_default = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    permissions = db.relationship('Permission', back_populates='role', lazy='dynamic', cascade='all, delete-orphan')
    users = db.relationship('User', back_populates='role', lazy='dynamic')

    @classmethod
    def get_default_role(cls):
        """Get the default role for new users."""
        return cls.query.filter_by(is_default=True).first()

    @classmethod
    def get_by_name(cls, name: str):
        """Get role by name."""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_by_type(cls, role_type: str):
        """Get role by type."""
        return cls.query.filter_by(type=role_type).first()

    @classmethod
    def get_superadmin_role(cls):
        """Get the superadmin role."""
        return cls.query.filter_by(type=cls.TYPE_SUPERADMIN).first()

    @classmethod
    def get_public_role(cls):
        """Get the public role."""
        return cls.query.filter_by(type=cls.TYPE_PUBLIC).first()

    @classmethod
    def ensure_system_roles(cls):
        """Ensure all system roles exist in the database."""
        from app.extensions import db
        import uuid

        system_roles = [
            {
                'id': uuid.UUID('00000000-0000-0000-0000-000000000001'),
                'name': 'Super Administrador',
                'description': 'Acceso total al sistema. Puede gestionar roles y permisos.',
                'type': cls.TYPE_SUPERADMIN,
                'is_system': True,
                'is_default': False
            },
            {
                'id': uuid.UUID('00000000-0000-0000-0000-000000000002'),
                'name': 'Administrador',
                'description': 'Acceso administrativo. No puede gestionar roles.',
                'type': cls.TYPE_ADMIN,
                'is_system': True,
                'is_default': False
            },
            {
                'id': uuid.UUID('00000000-0000-0000-0000-000000000003'),
                'name': 'Usuario Autenticado',
                'description': 'Usuario regular con acceso a sus propios datos.',
                'type': cls.TYPE_AUTHENTICATED,
                'is_system': True,
                'is_default': True
            },
            {
                'id': uuid.UUID('00000000-0000-0000-0000-000000000004'),
                'name': 'Público',
                'description': 'Acceso público sin autenticación.',
                'type': cls.TYPE_PUBLIC,
                'is_system': True,
                'is_default': False
            }
        ]

        roles_created = 0
        for data in system_roles:
            role = cls.query.get(data['id'])
            if not role:
                # Also check by name/type to avoid unique constraint violations
                role = cls.query.filter((cls.name == data['name']) | (cls.type == data['type'])).first()
                if not role:
                    role = cls(
                        id=data['id'],
                        name=data['name'],
                        description=data['description'],
                        type=data['type'],
                        is_system=data['is_system'],
                        is_default=data['is_default']
                    )
                    db.session.add(role)
                    roles_created += 1
                else:
                    # Sync ID and flags if exists but different ID
                    role.id = data['id']
                    role.is_system = data['is_system']
                    role.is_default = data['is_default']

        if roles_created > 0:
            db.session.commit()
        
        return roles_created

    def has_permission(self, entity: str, action: str) -> bool:
        """Check if role has a specific permission."""
        # Superadmin has all permissions
        if self.type == self.TYPE_SUPERADMIN:
            return True

        return self.permissions.filter_by(
            entity=entity,
            action=action,
            is_enabled=True
        ).first() is not None

    def get_permissions_dict(self) -> dict:
        """Get all permissions as a dictionary organized by entity."""
        result = {}
        for entity in PermissionEntity.ALL_ENTITIES:
            result[entity] = {}
            for action in PermissionAction.ALL_ACTIONS:
                perm = self.permissions.filter_by(entity=entity, action=action).first()
                result[entity][action] = perm.is_enabled if perm else False
        return result

    def set_permission(self, entity: str, action: str, enabled: bool = True, conditions: dict = None):
        """Set a permission for this role."""
        perm = self.permissions.filter_by(entity=entity, action=action).first()

        if perm:
            perm.is_enabled = enabled
            if conditions:
                perm.conditions = conditions
        else:
            perm = Permission(
                role_id=self.id,
                entity=entity,
                action=action,
                is_enabled=enabled,
                conditions=conditions
            )
            db.session.add(perm)

        return perm

    def to_dict(self, include_permissions=False):
        """Convert role to dictionary."""
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'is_system': self.is_system,
            'is_default': self.is_default,
            'user_count': self.users.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_permissions:
            data['permissions'] = self.get_permissions_dict()
        return data

    def __repr__(self):
        return f'<Role {self.name}>'


class Permission(db.Model):
    """
    Permission model - defines access to an entity action.

    Each permission links:
    - A role
    - An entity (user, order, etc.)
    - An action (create, read, update, delete, read_all)
    - Whether it's enabled
    - Optional conditions (for row-level security)
    """

    __tablename__ = 'permissions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)

    # What entity and action this permission controls
    entity = db.Column(db.String(50), nullable=False, index=True)
    action = db.Column(db.String(20), nullable=False, index=True)

    # Is this permission enabled?
    is_enabled = db.Column(db.Boolean, default=True)

    # Conditions for row-level security (optional)
    # Example: {"own_only": true} means user can only access their own records
    conditions = db.Column(JSONB, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    role = db.relationship('Role', back_populates='permissions')

    # Unique constraint: one permission per role/entity/action combination
    __table_args__ = (
        db.UniqueConstraint('role_id', 'entity', 'action', name='uq_permission_role_entity_action'),
        db.Index('idx_permission_role_entity', 'role_id', 'entity'),
    )

    def to_dict(self):
        """Convert permission to dictionary."""
        return {
            'id': str(self.id),
            'role_id': str(self.role_id),
            'entity': self.entity,
            'action': self.action,
            'is_enabled': self.is_enabled,
            'conditions': self.conditions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Permission {self.role.name if self.role else "?"}: {self.entity}.{self.action}>'
