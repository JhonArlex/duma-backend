"""
Create roles and permissions tables.

Revision ID: 003_roles_permissions
Revises: 002_seed_initial_data
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003_roles_permissions'
down_revision = '002_seed_initial_data'
branch_labels = None
depends_on = None


def upgrade():
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(50), nullable=False, server_default='authenticated'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_roles_name', 'roles', ['name'], unique=True)
    op.create_index('idx_roles_type', 'roles', ['type'])

    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity', sa.String(50), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('conditions', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('role_id', 'entity', 'action', name='uq_permission_role_entity_action')
    )
    op.create_index('idx_permission_entity', 'permissions', ['entity'])
    op.create_index('idx_permission_action', 'permissions', ['action'])
    op.create_index('idx_permission_role_entity', 'permissions', ['role_id', 'entity'])

    # Add role_id column to users table
    op.add_column('users', sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_users_role_id',
        'users', 'roles',
        ['role_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_users_role_id', 'users', ['role_id'])

    # Create trigger for updated_at on roles
    op.execute('''
        CREATE TRIGGER update_roles_updated_at
        BEFORE UPDATE ON roles
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    ''')

    # Create trigger for updated_at on permissions
    op.execute('''
        CREATE TRIGGER update_permissions_updated_at
        BEFORE UPDATE ON permissions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    ''')


def downgrade():
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_roles_updated_at ON roles;')
    op.execute('DROP TRIGGER IF EXISTS update_permissions_updated_at ON permissions;')

    # Remove role_id from users
    op.drop_constraint('fk_users_role_id', 'users', type_='foreignkey')
    op.drop_index('idx_users_role_id', table_name='users')
    op.drop_column('users', 'role_id')

    # Drop permissions table
    op.drop_index('idx_permission_role_entity', table_name='permissions')
    op.drop_index('idx_permission_action', table_name='permissions')
    op.drop_index('idx_permission_entity', table_name='permissions')
    op.drop_table('permissions')

    # Drop roles table
    op.drop_index('idx_roles_type', table_name='roles')
    op.drop_index('idx_roles_name', table_name='roles')
    op.drop_table('roles')
