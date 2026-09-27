"""Add comic chapters and pages.

Revision ID: f38c712ab904
Revises: d9417b2e6a30
"""
from alembic import op
import sqlalchemy as sa

revision = "f38c712ab904"
down_revision = "d9417b2e6a30"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "comic_chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("cover", sa.String(), nullable=True),
        sa.CheckConstraint("number > 0", name="comic_chapter_positive_number"),
    )
    op.create_table(
        "comic_pages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("comic_chapters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("image", sa.String(), nullable=False),
        sa.CheckConstraint("number > 0", name="comic_page_positive_number"),
    )
    op.create_index("ix_comic_pages_chapter_id", "comic_pages", ["chapter_id"])


def downgrade():
    op.drop_table("comic_pages")
    op.drop_table("comic_chapters")
