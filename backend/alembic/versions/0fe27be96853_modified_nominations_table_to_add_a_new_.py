"""modified nominations table to add a new field

Revision ID: 0fe27be96853
Revises: e417adfec845
Create Date: 2026-05-08 21:57:37.849795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0fe27be96853"
down_revision: Union[str, Sequence[str], None] = "e417adfec845"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


nomination_book_source_enum = sa.Enum(
    "EXISTING_BOOK",
    "NEW_BOOK",
    name="nominationbooksource",
)


def upgrade() -> None:
    nomination_book_source_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "nominations",
        sa.Column(
            "book_source",
            nomination_book_source_enum,
            nullable=False,
            server_default="NEW_BOOK",
        ),
    )

    op.alter_column(
        "nominations",
        "book_source",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("nominations", "book_source")

    nomination_book_source_enum.drop(op.get_bind(), checkfirst=True)