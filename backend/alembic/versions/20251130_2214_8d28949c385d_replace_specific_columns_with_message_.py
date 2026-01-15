"""replace_specific_columns_with_message_metadata

Revision ID: 8d28949c385d
Revises: 5a2a99f67e4a
Create Date: 2025-11-30 22:14:47.727659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d28949c385d'
down_revision: Union[str, None] = '5a2a99f67e4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add message_metadata JSONB column to store ALL message metadata
    # This includes: followups, ui_blocks, next_suggestions, is_suggestion_click, citations, intent, status, etc.
    op.add_column('conversation_messages',
                  sa.Column('message_metadata', sa.dialects.postgresql.JSONB(), nullable=True))

    # Remove specific columns (replaced by generic message_metadata)
    op.drop_column('conversation_messages', 'ui_blocks')
    op.drop_column('conversation_messages', 'next_suggestions')
    op.drop_column('conversation_messages', 'is_suggestion_click')


def downgrade() -> None:
    # Add back specific columns
    op.add_column('conversation_messages',
                  sa.Column('ui_blocks', sa.dialects.postgresql.JSONB(), nullable=True))
    op.add_column('conversation_messages',
                  sa.Column('next_suggestions', sa.dialects.postgresql.JSONB(), nullable=True))
    op.add_column('conversation_messages',
                  sa.Column('is_suggestion_click', sa.Boolean(), nullable=True))

    # Remove message_metadata column
    op.drop_column('conversation_messages', 'message_metadata')
