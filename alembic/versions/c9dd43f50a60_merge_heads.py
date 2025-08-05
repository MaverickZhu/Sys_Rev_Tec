"""merge_heads

Revision ID: c9dd43f50a60
Revises: af0354f58298, remove_permissions
Create Date: 2025-08-05 12:31:39.595694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9dd43f50a60'
down_revision: Union[str, Sequence[str], None] = ('af0354f58298', 'remove_permissions')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
