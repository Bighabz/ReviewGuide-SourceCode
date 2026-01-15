"""create_core_config_table

Revision ID: bb6231e59108
Revises: 8d28949c385d
Create Date: 2025-12-02 21:35:10.790577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb6231e59108'
down_revision: Union[str, None] = '8d28949c385d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create core_config table for environment variable overrides"""
    op.create_table(
        'core_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('idx_core_config_key', 'core_config', ['key'])


def downgrade() -> None:
    """Drop core_config table"""
    op.drop_index('idx_core_config_key', table_name='core_config')
    op.drop_table('core_config')
