"""add_structured_data_to_conversation_messages

Revision ID: e07cce01b0a4
Revises: 082603a4c210
Create Date: 2025-11-30 21:18:14.922734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e07cce01b0a4'
down_revision: Union[str, None] = '082603a4c210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add structured_data JSONB column to conversation_messages table
    # This will store the full structured message data (intro, questions, closing, etc.)
    # while keeping the content column for backward compatibility and simple text storage
    op.add_column('conversation_messages',
                  sa.Column('structured_data', sa.dialects.postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    # Remove structured_data column
    op.drop_column('conversation_messages', 'structured_data')
