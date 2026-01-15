"""
Seed default roles and permissions.

Revision ID: 004_seed_roles_permissions
Revises: 003_roles_permissions
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '004_seed_roles_permissions'
down_revision = '003_roles_permissions'
branch_labels = None
depends_on = None

# Role UUIDs (fixed for consistency)
SUPERADMIN_ROLE_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')
ADMIN_ROLE_ID = uuid.UUID('00000000-0000-0000-0000-000000000002')
AUTHENTICATED_ROLE_ID = uuid.UUID('00000000-0000-0000-0000-000000000003')
PUBLIC_ROLE_ID = uuid.UUID('00000000-0000-0000-0000-000000000004')

# All entities
ENTITIES = [
    'user', 'address', 'store', 'order', 'order_item',
    'cart', 'cart_item', 'payment', 'exchange_rate',
    'notification', 'role', 'permission'
]

# All actions
ACTIONS = ['create', 'read', 'read_all', 'update', 'delete']


def upgrade():
    # Get connection
    conn = op.get_bind()

    # Insert roles
    roles_table = sa.table(
        'roles',
        sa.column('id', postgresql.UUID),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('type', sa.String),
        sa.column('is_system', sa.Boolean),
        sa.column('is_default', sa.Boolean)
    )

    op.bulk_insert(roles_table, [
        {
            'id': str(SUPERADMIN_ROLE_ID),
            'name': 'Super Administrador',
            'description': 'Acceso total al sistema. Puede gestionar roles y permisos.',
            'type': 'superadmin',
            'is_system': True,
            'is_default': False
        },
        {
            'id': str(ADMIN_ROLE_ID),
            'name': 'Administrador',
            'description': 'Acceso administrativo. No puede gestionar roles.',
            'type': 'admin',
            'is_system': True,
            'is_default': False
        },
        {
            'id': str(AUTHENTICATED_ROLE_ID),
            'name': 'Usuario Autenticado',
            'description': 'Usuario regular con acceso a sus propios datos.',
            'type': 'authenticated',
            'is_system': True,
            'is_default': True  # Default role for new users
        },
        {
            'id': str(PUBLIC_ROLE_ID),
            'name': 'Público',
            'description': 'Acceso público sin autenticación.',
            'type': 'public',
            'is_system': True,
            'is_default': False
        }
    ])

    # Insert permissions
    permissions_table = sa.table(
        'permissions',
        sa.column('id', postgresql.UUID),
        sa.column('role_id', postgresql.UUID),
        sa.column('entity', sa.String),
        sa.column('action', sa.String),
        sa.column('is_enabled', sa.Boolean),
        sa.column('conditions', postgresql.JSONB)
    )

    permissions = []

    # =========================================================================
    # ADMIN ROLE PERMISSIONS - Full access except role management
    # =========================================================================
    for entity in ENTITIES:
        for action in ACTIONS:
            # Admin cannot manage roles or permissions
            if entity in ['role', 'permission']:
                is_enabled = False
            else:
                is_enabled = True

            permissions.append({
                'id': str(uuid.uuid4()),
                'role_id': str(ADMIN_ROLE_ID),
                'entity': entity,
                'action': action,
                'is_enabled': is_enabled,
                'conditions': None
            })

    # =========================================================================
    # AUTHENTICATED ROLE PERMISSIONS - Access to own data only
    # =========================================================================
    authenticated_permissions = {
        # User - can read/update own profile
        'user': {
            'create': False,
            'read': True,       # Own user only
            'read_all': False,
            'update': True,     # Own user only
            'delete': False
        },
        # Address - full CRUD on own addresses
        'address': {
            'create': True,     # Own addresses
            'read': True,       # Own addresses
            'read_all': True,   # Own addresses only
            'update': True,     # Own addresses
            'delete': True      # Own addresses
        },
        # Store - read only
        'store': {
            'create': False,
            'read': True,
            'read_all': True,
            'update': False,
            'delete': False
        },
        # Order - can create, read own orders
        'order': {
            'create': True,
            'read': True,       # Own orders
            'read_all': True,   # Own orders only
            'update': False,    # Cannot modify orders
            'delete': False
        },
        'order_item': {
            'create': False,    # Created with order
            'read': True,       # Own order items
            'read_all': True,
            'update': False,
            'delete': False
        },
        # Cart - full access to own cart
        'cart': {
            'create': True,
            'read': True,
            'read_all': False,
            'update': True,
            'delete': True
        },
        'cart_item': {
            'create': True,
            'read': True,
            'read_all': True,
            'update': True,
            'delete': True
        },
        # Payment - can create and read own payments
        'payment': {
            'create': True,
            'read': True,
            'read_all': True,   # Own payments only
            'update': False,
            'delete': False
        },
        # Exchange rate - read only
        'exchange_rate': {
            'create': False,
            'read': True,
            'read_all': True,
            'update': False,
            'delete': False
        },
        # Notification - read own notifications
        'notification': {
            'create': False,
            'read': True,
            'read_all': True,   # Own notifications only
            'update': True,     # Mark as read
            'delete': False
        },
        # Role/Permission - no access
        'role': {
            'create': False,
            'read': False,
            'read_all': False,
            'update': False,
            'delete': False
        },
        'permission': {
            'create': False,
            'read': False,
            'read_all': False,
            'update': False,
            'delete': False
        }
    }

    for entity, actions in authenticated_permissions.items():
        for action, is_enabled in actions.items():
            # Add condition for "own only" access
            conditions = None
            if is_enabled and entity in ['user', 'address', 'order', 'order_item', 'cart', 'cart_item', 'payment', 'notification']:
                conditions = {'own_only': True}

            permissions.append({
                'id': str(uuid.uuid4()),
                'role_id': str(AUTHENTICATED_ROLE_ID),
                'entity': entity,
                'action': action,
                'is_enabled': is_enabled,
                'conditions': conditions
            })

    # =========================================================================
    # PUBLIC ROLE PERMISSIONS - Very limited read access
    # =========================================================================
    public_permissions = {
        'store': {
            'create': False,
            'read': True,
            'read_all': True,
            'update': False,
            'delete': False
        },
        'exchange_rate': {
            'create': False,
            'read': True,
            'read_all': True,
            'update': False,
            'delete': False
        }
    }

    for entity in ENTITIES:
        if entity in public_permissions:
            actions = public_permissions[entity]
        else:
            actions = {a: False for a in ACTIONS}

        for action, is_enabled in actions.items():
            permissions.append({
                'id': str(uuid.uuid4()),
                'role_id': str(PUBLIC_ROLE_ID),
                'entity': entity,
                'action': action,
                'is_enabled': is_enabled,
                'conditions': None
            })

    # Insert all permissions
    op.bulk_insert(permissions_table, permissions)

    # Update existing users to have the authenticated role
    op.execute(f'''
        UPDATE users
        SET role_id = '{AUTHENTICATED_ROLE_ID}'
        WHERE role_id IS NULL;
    ''')


def downgrade():
    # Remove role assignments from users
    op.execute('UPDATE users SET role_id = NULL;')

    # Delete permissions
    op.execute('DELETE FROM permissions;')

    # Delete roles
    op.execute('DELETE FROM roles;')
