"""soft delete support

Revision ID: 9b6c186a9215
Revises: efb3452565c5
Create Date: 2025-11-26 17:25:25.002669
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9b6c186a9215'
down_revision: Union[str, Sequence[str], None] = 'efb3452565c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add soft delete columns."""

    op.add_column('users', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('deleted_at', postgresql.TIMESTAMP(), nullable=True))

    op.add_column('ad_requests', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('ad_requests', sa.Column('deleted_at', postgresql.TIMESTAMP(), nullable=True))

    op.add_column('user_memories', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('user_memories', sa.Column('deleted_at', postgresql.TIMESTAMP(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'is_deleted')

    op.drop_column('ad_requests', 'deleted_at')
    op.drop_column('ad_requests', 'is_deleted')

    op.drop_column('user_memories', 'deleted_at')
    op.drop_column('user_memories', 'is_deleted')
