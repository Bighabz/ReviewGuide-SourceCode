"""change_conversation_messages_session_id_to_uuid

Revision ID: bfb7325620b6
Revises: dc0c8ed00b34
Create Date: 2025-11-07 00:02:36.414359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfb7325620b6'
down_revision: Union[str, None] = 'dc0c8ed00b34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the foreign key constraint first
    op.drop_constraint('conversation_messages_session_id_fkey', 'conversation_messages', type_='foreignkey')

    # Change column type from Integer to String(255) for UUID
    op.alter_column('conversation_messages', 'session_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(255),
                    existing_nullable=False)


def downgrade() -> None:
    # Change back to Integer
    op.alter_column('conversation_messages', 'session_id',
                    existing_type=sa.String(255),
                    type_=sa.Integer(),
                    existing_nullable=False)

    # Re-add the foreign key constraint
    op.create_foreign_key('conversation_messages_session_id_fkey',
                         'conversation_messages', 'sessions',
                         ['session_id'], ['id'],
                         ondelete='CASCADE')
