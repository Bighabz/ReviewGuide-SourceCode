"""Add conversation_messages table for persistent storage

Revision ID: c7b0ef9a4ff9
Revises: 001
Create Date: 2025-11-06 11:12:01.390646

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7b0ef9a4ff9'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversation_messages table for persistent message storage
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )

    # Create indexes for performance
    op.create_index(
        'ix_conversation_messages_session_id',
        'conversation_messages',
        ['session_id']
    )
    op.create_index(
        'ix_conversation_messages_created_at',
        'conversation_messages',
        ['created_at']
    )

    # Create composite index for efficient session + sequence queries
    op.create_index(
        'ix_conversation_messages_session_seq',
        'conversation_messages',
        ['session_id', 'sequence_number']
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_conversation_messages_session_seq')
    op.drop_index('ix_conversation_messages_created_at')
    op.drop_index('ix_conversation_messages_session_id')

    # Drop table
    op.drop_table('conversation_messages')
