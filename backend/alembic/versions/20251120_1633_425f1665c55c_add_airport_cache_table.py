"""add_airport_cache_table

Revision ID: 425f1665c55c
Revises: bfb7325620b6
Create Date: 2025-11-20 16:33:50.102495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '425f1665c55c'
down_revision: Union[str, None] = 'bfb7325620b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create airport_cache table for caching city -> airport code lookups"""
    op.create_table(
        'airport_cache',
        sa.Column('city_name', sa.String(255), primary_key=True),
        sa.Column('airport_code', sa.String(10), nullable=False),
        sa.Column('airport_name', sa.String(500), nullable=True),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )

    # Create index on airport_code for reverse lookups
    op.create_index('ix_airport_cache_airport_code', 'airport_cache', ['airport_code'])

    # Pre-populate common city -> airport mappings
    op.execute("""
        INSERT INTO airport_cache (city_name, airport_code, airport_name, country_code) VALUES
        ('new york', 'JFK', 'John F. Kennedy International Airport', 'US'),
        ('nyc', 'JFK', 'John F. Kennedy International Airport', 'US'),
        ('miami', 'MIA', 'Miami International Airport', 'US'),
        ('los angeles', 'LAX', 'Los Angeles International Airport', 'US'),
        ('la', 'LAX', 'Los Angeles International Airport', 'US'),
        ('san francisco', 'SFO', 'San Francisco International Airport', 'US'),
        ('chicago', 'ORD', 'O''Hare International Airport', 'US'),
        ('london', 'LHR', 'London Heathrow Airport', 'GB'),
        ('paris', 'CDG', 'Charles de Gaulle Airport', 'FR'),
        ('berlin', 'BER', 'Berlin Brandenburg Airport', 'DE'),
        ('tokyo', 'NRT', 'Narita International Airport', 'JP'),
        ('singapore', 'SIN', 'Singapore Changi Airport', 'SG'),
        ('dubai', 'DXB', 'Dubai International Airport', 'AE'),
        ('sydney', 'SYD', 'Sydney Kingsford Smith Airport', 'AU'),
        ('toronto', 'YYZ', 'Toronto Pearson International Airport', 'CA'),
        ('hong kong', 'HKG', 'Hong Kong International Airport', 'HK'),
        ('bangkok', 'BKK', 'Suvarnabhumi Airport', 'TH'),
        ('amsterdam', 'AMS', 'Amsterdam Airport Schiphol', 'NL'),
        ('barcelona', 'BCN', 'Barcelona–El Prat Airport', 'ES'),
        ('rome', 'FCO', 'Leonardo da Vinci–Fiumicino Airport', 'IT'),
        ('madrid', 'MAD', 'Adolfo Suárez Madrid–Barajas Airport', 'ES'),
        ('frankfurt', 'FRA', 'Frankfurt Airport', 'DE'),
        ('munich', 'MUC', 'Munich Airport', 'DE'),
        ('vienna', 'VIE', 'Vienna International Airport', 'AT'),
        ('zurich', 'ZRH', 'Zurich Airport', 'CH'),
        ('istanbul', 'IST', 'Istanbul Airport', 'TR'),
        ('delhi', 'DEL', 'Indira Gandhi International Airport', 'IN'),
        ('mumbai', 'BOM', 'Chhatrapati Shivaji Maharaj International Airport', 'IN'),
        ('seoul', 'ICN', 'Incheon International Airport', 'KR'),
        ('beijing', 'PEK', 'Beijing Capital International Airport', 'CN'),
        ('shanghai', 'PVG', 'Shanghai Pudong International Airport', 'CN')
        ON CONFLICT (city_name) DO NOTHING
    """)


def downgrade() -> None:
    """Drop airport_cache table"""
    op.drop_index('ix_airport_cache_airport_code', 'airport_cache')
    op.drop_table('airport_cache')
