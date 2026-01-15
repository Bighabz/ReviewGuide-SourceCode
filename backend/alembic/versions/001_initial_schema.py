"""initial schema with all tables

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all database tables"""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('locale', sa.String(10), default='en', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('meta', postgresql.JSONB(), default={}),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('last_turn_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )

    # Create affiliate_merchants table
    op.create_table(
        'affiliate_merchants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('network', sa.String(100), nullable=False),
        sa.Column('deeplink_template', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'SUSPENDED', name='merchantstatus'), default='ACTIVE', nullable=False),
        sa.Column('last_health_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Create product_index table
    op.create_table(
        'product_index',
        sa.Column('entity_key', sa.String(255), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('brand', sa.String(100), nullable=True, index=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('attrs', postgresql.JSONB(), default={}),
        sa.Column('source_urls', postgresql.JSONB(), default=[]),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Create affiliate_links table (updated schema with all fields)
    op.create_table(
        'affiliate_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_key', sa.String(255), nullable=False, index=True),
        sa.Column('product_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('deeplink', sa.Text(), nullable=False),
        sa.Column('merchant_name', sa.String(255), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(10), default='USD', nullable=False),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=True),
        sa.Column('healthy', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Create travel_query table
    op.create_table(
        'travel_query',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('origin', sa.String(100), nullable=True),
        sa.Column('destination', sa.String(100), nullable=True),
        sa.Column('dates', postgresql.JSONB(), default={}),
        sa.Column('pax', postgresql.JSONB(), default={}),
        sa.Column('budget', sa.String(50), nullable=True),
        sa.Column('prefs', postgresql.JSONB(), default={}),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='travelquerystatus'), default='PENDING', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('type', sa.String(100), nullable=False, index=True),
        sa.Column('payload', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    """Drop all database tables"""
    op.drop_table('events')
    op.drop_table('travel_query')
    op.drop_table('affiliate_links')
    op.drop_table('product_index')
    op.drop_table('affiliate_merchants')
    op.drop_table('conversations')
    op.drop_table('sessions')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS merchantstatus')
    op.execute('DROP TYPE IF EXISTS travelquerystatus')
