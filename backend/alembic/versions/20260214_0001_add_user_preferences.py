"""Add preferences JSONB column to users table

Revision ID: 20260214_0001
Revises: 20260131_0002
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '20260214_0001'
down_revision: Union[str, None] = '20260131_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add preferences JSONB column to users table"""
    op.add_column(
        'users',
        sa.Column('preferences', JSONB, server_default='{}', nullable=False)
    )


def downgrade() -> None:
    """Remove preferences column from users table"""
    op.drop_column('users', 'preferences')
