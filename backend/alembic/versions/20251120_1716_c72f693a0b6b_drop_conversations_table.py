"""drop_conversations_table

Revision ID: c72f693a0b6b
Revises: 425f1665c55c
Create Date: 2025-11-20 17:16:28.705434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c72f693a0b6b'
down_revision: Union[str, None] = '425f1665c55c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop conversations and events tables - redundant/unused"""
    # Drop events first (has FK to conversations)
    op.drop_table('events')
    op.drop_table('conversations')


def downgrade() -> None:
    """Recreate conversations and events tables"""
    # Recreate conversations first
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('last_turn_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_session_id', 'conversations', ['session_id'])

    # Then recreate events (depends on conversations)
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('payload', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_events_conversation_id', 'events', ['conversation_id'])
    op.create_index('ix_events_session_id', 'events', ['session_id'])
    op.create_index('ix_events_type', 'events', ['type'])
    op.create_index('ix_events_created_at', 'events', ['created_at'])
