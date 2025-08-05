"""Remove permissions system

Revision ID: remove_permissions
Revises: 
Create Date: 2025-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_permissions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Remove permissions system tables and columns"""
    
    # Remove permission-related columns from users table first
    try:
        op.drop_column('users', 'primary_role_id')
    except:
        pass
    try:
        op.drop_column('users', 'role')
    except:
        pass
    try:
        op.drop_column('users', 'is_superuser')
    except:
        pass
    
    # Drop association tables (due to foreign key constraints)
    try:
        op.drop_table('user_roles')
    except:
        pass
    try:
        op.drop_table('role_permissions')
    except:
        pass
    try:
        op.drop_table('user_permissions')
    except:
        pass
    try:
        op.drop_table('permission_group_permissions')
    except:
        pass
    
    # Drop main permission tables
    try:
        op.drop_table('resource_permissions')
    except:
        pass
    try:
        op.drop_table('permission_groups')
    except:
        pass
    try:
        op.drop_table('permissions')
    except:
        pass
    try:
        op.drop_table('roles')
    except:
        pass


def downgrade():
    """Recreate permissions system (not implemented)"""
    # This would be complex to implement and is not needed for this migration
    pass