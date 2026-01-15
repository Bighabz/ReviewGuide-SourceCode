"""refactor_conversation_messages_remove_structured_data_add_specific_columns

Revision ID: 5a2a99f67e4a
Revises: e07cce01b0a4
Create Date: 2025-11-30 22:02:01.867451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a2a99f67e4a'
down_revision: Union[str, None] = 'e07cce01b0a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new JSONB columns for specific message data
    op.add_column('conversation_messages',
                  sa.Column('ui_blocks', sa.dialects.postgresql.JSONB(), nullable=True))
    op.add_column('conversation_messages',
                  sa.Column('next_suggestions', sa.dialects.postgresql.JSONB(), nullable=True))
    op.add_column('conversation_messages',
                  sa.Column('is_suggestion_click', sa.Boolean(), nullable=True))

    # Remove the generic structured_data column (replaced by specific columns)
    op.drop_column('conversation_messages', 'structured_data')


def downgrade() -> None:
    # Add back structured_data column
    op.add_column('conversation_messages',
                  sa.Column('structured_data', sa.dialects.postgresql.JSONB(), nullable=True))

    # Remove specific columns
    op.drop_column('conversation_messages', 'is_suggestion_click')
    op.drop_column('conversation_messages', 'next_suggestions')
    op.drop_column('conversation_messages', 'ui_blocks')
