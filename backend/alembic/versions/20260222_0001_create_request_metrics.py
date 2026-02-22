"""Create request_metrics table for RFC §4.2 QoS dashboards

Revision ID: 20260222_0001
Revises: 20260219_0001
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '20260222_0001'
down_revision: Union[str, None] = '20260219_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create request_metrics table"""
    op.create_table(
        'request_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('intent', sa.String(50), nullable=True),
        sa.Column('total_duration_ms', sa.Integer(), nullable=True),
        sa.Column('completeness', sa.String(20), server_default='full', nullable=True),
        sa.Column('tool_durations', JSONB(), server_default='{}', nullable=True),
        sa.Column('provider_errors', JSONB(), server_default='[]', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_request_metrics_created_at', 'request_metrics', ['created_at'])
    op.create_index('ix_request_metrics_request_id', 'request_metrics', ['request_id'])


def downgrade() -> None:
    """Drop request_metrics table"""
    op.drop_index('ix_request_metrics_request_id', table_name='request_metrics')
    op.drop_index('ix_request_metrics_created_at', table_name='request_metrics')
    op.drop_table('request_metrics')
