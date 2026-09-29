"""add quotes table

Revision ID: d7e6f8a9b0c1
Revises: c4d8e9f0a1b2
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7e6f8a9b0c1"
down_revision: Union[str, Sequence[str], None] = "c4d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quote",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quote_id"), "quote", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_quote_id"), table_name="quote")
    op.drop_table("quote")
