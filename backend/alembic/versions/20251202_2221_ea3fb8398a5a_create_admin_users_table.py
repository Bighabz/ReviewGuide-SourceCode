"""create_admin_users_table

Revision ID: ea3fb8398a5a
Revises: bb6231e59108
Create Date: 2025-12-02 22:21:57.326320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea3fb8398a5a'
down_revision: Union[str, None] = 'bb6231e59108'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create admin_users table"""
    op.create_table(
        'admin_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_admin_users_username', 'admin_users', ['username'])
    op.create_index('idx_admin_users_email', 'admin_users', ['email'])


def downgrade() -> None:
    """Drop admin_users table"""
    op.drop_index('idx_admin_users_email', table_name='admin_users')
    op.drop_index('idx_admin_users_username', table_name='admin_users')
    op.drop_table('admin_users')
