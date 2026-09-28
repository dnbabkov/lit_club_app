"""Add optional meeting date to books.

Revision ID: b7c3d9e1f2a4
Revises: 8d5e2a1c4b7f
"""
from alembic import op
import sqlalchemy as sa


revision = "b7c3d9e1f2a4"
down_revision = "8d5e2a1c4b7f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("books", sa.Column("meeting_date", sa.Date(), nullable=True))


def downgrade():
    op.drop_column("books", "meeting_date")
