"""add_country_code_to_sessions

Revision ID: 082603a4c210
Revises: 2da1d9173ab5
Create Date: 2025-11-29 15:36:01.320229

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '082603a4c210'
down_revision: Union[str, None] = '2da1d9173ab5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add country_code column to sessions table
    op.add_column('sessions', sa.Column('country_code', sa.String(length=2), nullable=True))
    # Create index for faster lookups
    op.create_index(op.f('ix_sessions_country_code'), 'sessions', ['country_code'], unique=False)


def downgrade() -> None:
    # Remove index and column
    op.drop_index(op.f('ix_sessions_country_code'), table_name='sessions')
    op.drop_column('sessions', 'country_code')
