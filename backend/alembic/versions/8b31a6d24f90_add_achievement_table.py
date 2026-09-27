"""add achievement table

Revision ID: 8b31a6d24f90
Revises: c2f4f508f7ef
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8b31a6d24f90'
down_revision: Union[str, Sequence[str], None] = 'c2f4f508f7ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'achievement',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('path', sa.VARCHAR(), nullable=False),
        sa.Column('giver_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['giver_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('achievement')
