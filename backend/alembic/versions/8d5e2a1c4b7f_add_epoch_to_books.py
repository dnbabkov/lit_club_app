"""Add optional epoch to books.

Revision ID: 8d5e2a1c4b7f
Revises: f38c712ab904
"""
from alembic import op
import sqlalchemy as sa


revision = "8d5e2a1c4b7f"
down_revision = "f38c712ab904"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("books", sa.Column("epoch", sa.String(length=10), nullable=True))


def downgrade():
    op.drop_column("books", "epoch")
