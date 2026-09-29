"""add persisted achievement metadata

Revision ID: e8f7a6b5c4d3
Revises: d7e6f8a9b0c1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8f7a6b5c4d3"
down_revision: Union[str, Sequence[str], None] = "d7e6f8a9b0c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("achievement", sa.Column("title", sa.String(length=200), nullable=True))
    op.add_column("achievement", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("achievement", "description")
    op.drop_column("achievement", "title")
