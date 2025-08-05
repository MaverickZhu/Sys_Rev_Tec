"""Add primary_role_id column only

Revision ID: af0354f58298
Revises: a51a86e88dff
Create Date: 2025-07-30 10:06:46.741744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af0354f58298'
down_revision: Union[str, Sequence[str], None] = 'dc5bca58112f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add primary_role_id column to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('primary_role_id', sa.Integer(), nullable=True, comment='主要角色ID'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove primary_role_id column from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('primary_role_id')
