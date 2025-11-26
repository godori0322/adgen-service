"""init

Revision ID: efb3452565c5
Revises:
Create Date: 2025-11-26 17:25:02.162691
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'efb3452565c5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('business_type', sa.String(length=50)),
        sa.Column('location', sa.String(length=100)),
        sa.Column('menu_items', sa.Text()),
        sa.Column('business_hours', sa.String(length=100)),
        sa.Column('created_at', postgresql.TIMESTAMP()),
        sa.Column('updated_at', postgresql.TIMESTAMP())
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'ad_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete="CASCADE")),
        sa.Column('voice_text', sa.Text()),
        sa.Column('weather_info', sa.String(length=200)),
        sa.Column('gpt_prompt', sa.Text()),
        sa.Column('gpt_output_text', sa.Text()),
        sa.Column('diffusion_prompt', sa.Text()),
        sa.Column('image_url', sa.String(length=500)),
        sa.Column('hashtags', sa.Text()),
        sa.Column('created_at', postgresql.TIMESTAMP())
    )
    op.create_index('ix_ad_requests_id', 'ad_requests', ['id'])

    op.create_table(
        'user_memories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete="CASCADE")),
        sa.Column('marketing_strategy', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('embedding', sa.Text()),
        sa.Column('importance', sa.Float()),
        sa.Column('created_at', postgresql.TIMESTAMP()),
        sa.Column('updated_at', postgresql.TIMESTAMP())
    )
    op.create_index('ix_user_memories_id', 'user_memories', ['id'])
    op.create_index('ix_user_memories_user_id', 'user_memories', ['user_id'])


def downgrade() -> None:
    """Drop all tables."""

    op.drop_index('ix_user_memories_user_id', table_name='user_memories')
    op.drop_index('ix_user_memories_id', table_name='user_memories')
    op.drop_table('user_memories')

    op.drop_index('ix_ad_requests_id', table_name='ad_requests')
    op.drop_table('ad_requests')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
