"""Change conversation_messages ID from UUID to auto-increment

Revision ID: a5b5cd930fd1
Revises: c7b0ef9a4ff9
Create Date: 2025-11-06 11:53:42.579883

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5b5cd930fd1'
down_revision: Union[str, None] = 'c7b0ef9a4ff9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing table and recreate with BIGSERIAL id
    # This is safe since we just created it and it has no data yet

    # Drop indexes
    op.drop_index('ix_conversation_messages_session_seq', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_created_at', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_session_id', table_name='conversation_messages')

    # Drop table
    op.drop_table('conversation_messages')

    # Recreate table with BIGSERIAL id instead of UUID
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )

    # Recreate indexes
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
    op.create_index(
        'ix_conversation_messages_session_seq',
        'conversation_messages',
        ['session_id', 'sequence_number']
    )


def downgrade() -> None:
    # Revert back to UUID id

    # Drop indexes
    op.drop_index('ix_conversation_messages_session_seq', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_created_at', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_session_id', table_name='conversation_messages')

    # Drop table
    op.drop_table('conversation_messages')

    # Recreate with UUID id
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )

    # Recreate indexes
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
    op.create_index(
        'ix_conversation_messages_session_seq',
        'conversation_messages',
        ['session_id', 'sequence_number']
    )
