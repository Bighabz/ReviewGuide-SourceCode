"""Add api_usage_logs table for cost tracking

Revision ID: 20260131_0001
Revises: ea3fb8398a5a
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260131_0001'
down_revision: Union[str, None] = 'ea3fb8398a5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create api_usage_logs table for tracking API costs"""
    op.create_table(
        'api_usage_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('api_name', sa.String(50), nullable=False),
        sa.Column('tier', sa.SmallInteger(), nullable=False),
        sa.Column('cost_cents', sa.Integer(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_api_usage_user_month', 'api_usage_logs', ['user_id', 'created_at'])
    op.create_index('idx_api_usage_api_name', 'api_usage_logs', ['api_name', 'created_at'])


def downgrade() -> None:
    """Drop api_usage_logs table"""
    op.drop_index('idx_api_usage_api_name', table_name='api_usage_logs')
    op.drop_index('idx_api_usage_user_month', table_name='api_usage_logs')
    op.drop_table('api_usage_logs')
