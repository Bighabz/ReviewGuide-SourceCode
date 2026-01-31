"""Add extended_search_enabled to users table

Revision ID: 20260131_0002
Revises: 20260131_0001
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260131_0002'
down_revision: Union[str, None] = '20260131_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add extended_search_enabled column to users table"""
    op.add_column(
        'users',
        sa.Column('extended_search_enabled', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False)
    )


def downgrade() -> None:
    """Remove extended_search_enabled column from users table"""
    op.drop_column('users', 'extended_search_enabled')
