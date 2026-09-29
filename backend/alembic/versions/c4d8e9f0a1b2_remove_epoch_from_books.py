"""Remove the obsolete epoch field from books.

Revision ID: c4d8e9f0a1b2
Revises: b7c3d9e1f2a4
"""
from alembic import op


revision = "c4d8e9f0a1b2"
down_revision = "b7c3d9e1f2a4"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("books", "epoch")


def downgrade():
    # Existing epoch values cannot be recovered after this migration.
    import sqlalchemy as sa

    op.add_column("books", sa.Column("epoch", sa.String(length=10), nullable=True))
