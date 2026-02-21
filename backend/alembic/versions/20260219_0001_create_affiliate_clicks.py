"""Create affiliate_clicks table for click tracking analytics

Revision ID: 20260219_0001
Revises: 20260214_0001
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260219_0001'
down_revision: Union[str, None] = '20260214_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create affiliate_clicks table"""
    op.create_table(
        'affiliate_clicks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('product_name', sa.String(500), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('clicked_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_affiliate_clicks_session', 'affiliate_clicks', ['session_id'])
    op.create_index('idx_affiliate_clicks_provider', 'affiliate_clicks', ['provider', 'clicked_at'])


def downgrade() -> None:
    """Drop affiliate_clicks table"""
    op.drop_index('idx_affiliate_clicks_provider', table_name='affiliate_clicks')
    op.drop_index('idx_affiliate_clicks_session', table_name='affiliate_clicks')
    op.drop_table('affiliate_clicks')
