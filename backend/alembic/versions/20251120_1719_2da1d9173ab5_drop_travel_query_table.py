"""drop_travel_query_table

Revision ID: 2da1d9173ab5
Revises: c72f693a0b6b
Create Date: 2025-11-20 17:19:44.993279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2da1d9173ab5'
down_revision: Union[str, None] = 'c72f693a0b6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop travel_query table - redundant with workflow state/slots"""
    op.drop_table('travel_query')


def downgrade() -> None:
    """Recreate travel_query table"""
    op.create_table(
        'travel_query',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('origin', sa.String(100), nullable=True),
        sa.Column('destination', sa.String(100), nullable=True),
        sa.Column('dates', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('pax', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('budget', sa.String(50), nullable=True),
        sa.Column('prefs', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='travelquerystatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_travel_query_user_id', 'travel_query', ['user_id'])
