"""convert_uuid_to_integer_ids

Revision ID: dc0c8ed00b34
Revises: a5b5cd930fd1
Create Date: 2025-11-06 16:54:15.153953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc0c8ed00b34'
down_revision: Union[str, None] = 'a5b5cd930fd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Convert all UUID primary keys and foreign keys to Integer with autoincrement.
    This is a destructive migration - all existing data will be lost.
    """
    # Drop all tables in reverse dependency order
    op.drop_table('conversation_messages')
    op.drop_table('events')
    op.drop_table('travel_query')
    op.drop_table('affiliate_links')
    op.drop_table('conversations')
    op.drop_table('sessions')
    op.drop_table('users')
    op.drop_table('affiliate_merchants')
    op.drop_table('product_index')

    # Drop enum types if they exist
    op.execute("DROP TYPE IF EXISTS travelquerystatus CASCADE")
    op.execute("DROP TYPE IF EXISTS merchantstatus CASCADE")

    # Recreate enum types
    op.execute("CREATE TYPE travelquerystatus AS ENUM ('PENDING', 'COMPLETED', 'FAILED')")
    op.execute("CREATE TYPE merchantstatus AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED')")

    # Recreate users table with Integer ID
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('locale', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Recreate sessions table with Integer IDs
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)

    # Recreate conversations table with Integer IDs
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
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversations_session_id'), 'conversations', ['session_id'], unique=False)

    # Recreate conversation_messages table with Integer foreign key
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_conversation_messages_session_id'), 'conversation_messages', ['session_id'], unique=False)
    op.create_index(op.f('ix_conversation_messages_created_at'), 'conversation_messages', ['created_at'], unique=False)

    # Recreate events table with Integer IDs
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_events_conversation_id'), 'events', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_events_session_id'), 'events', ['session_id'], unique=False)
    op.create_index(op.f('ix_events_type'), 'events', ['type'], unique=False)
    op.create_index(op.f('ix_events_created_at'), 'events', ['created_at'], unique=False)

    # Recreate travel_query table with Integer IDs
    op.create_table(
        'travel_query',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('origin', sa.String(length=100), nullable=True),
        sa.Column('destination', sa.String(length=100), nullable=True),
        sa.Column('dates', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('pax', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('budget', sa.String(length=50), nullable=True),
        sa.Column('prefs', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='travelquerystatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_travel_query_user_id'), 'travel_query', ['user_id'], unique=False)

    # Recreate affiliate_merchants table with Integer ID
    op.create_table(
        'affiliate_merchants',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('network', sa.String(length=100), nullable=False),
        sa.Column('deeplink_template', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'SUSPENDED', name='merchantstatus'), nullable=False),
        sa.Column('last_health_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Recreate affiliate_links table with Integer ID
    op.create_table(
        'affiliate_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_key', sa.String(length=255), nullable=False),
        sa.Column('product_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('deeplink', sa.Text(), nullable=False),
        sa.Column('merchant_name', sa.String(length=255), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=True),
        sa.Column('healthy', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_affiliate_links_entity_key'), 'affiliate_links', ['entity_key'], unique=False)

    # Recreate product_index table (no UUID, but included for completeness)
    op.create_table(
        'product_index',
        sa.Column('entity_key', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('attrs', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('source_urls', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('entity_key')
    )
    op.create_index(op.f('ix_product_index_brand'), 'product_index', ['brand'], unique=False)
    op.create_index(op.f('ix_product_index_category'), 'product_index', ['category'], unique=False)


def downgrade() -> None:
    """
    Downgrade is not supported as this is a destructive migration.
    """
    raise NotImplementedError("Downgrade from Integer IDs to UUID is not supported")
