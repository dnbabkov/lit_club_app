"""modified the books table to add cover and book files

Revision ID: e417adfec845
Revises: ae50c3420990
Create Date: 2026-05-07 21:31:05.576531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e417adfec845"
down_revision: Union[str, Sequence[str], None] = "ae50c3420990"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


uploaded_file_types_enum = sa.Enum(
    "BOOK_COVER",
    "BOOK_FILE",
    "ACHIEVEMENT_IMAGE",
    name="uploadedfiletypes",
)


def upgrade() -> None:
    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("stored_filename", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("file_kind", uploaded_file_types_enum, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column(
        "books",
        sa.Column("cover_file_id", sa.Integer(), nullable=True),
    )

    op.add_column(
        "books",
        sa.Column("book_file_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_books_cover_file_id_uploaded_files",
        "books",
        "uploaded_files",
        ["cover_file_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_books_book_file_id_uploaded_files",
        "books",
        "uploaded_files",
        ["book_file_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_books_book_file_id_uploaded_files",
        "books",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_books_cover_file_id_uploaded_files",
        "books",
        type_="foreignkey",
    )

    op.drop_column("books", "book_file_id")
    op.drop_column("books", "cover_file_id")

    op.drop_table("uploaded_files")

    uploaded_file_types_enum.drop(op.get_bind(), checkfirst=True)