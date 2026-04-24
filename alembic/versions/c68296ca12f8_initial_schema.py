"""initial schema

Revision ID: c68296ca12f8
Revises: 
Create Date: 2026-04-24 17:56:21.687688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c68296ca12f8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("telegram_login", sa.String(), nullable=False),
        sa.Column("role", sa.Enum("MEMBER", "MODERATOR", name="roles"), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_telegram_login"), "users", ["telegram_login"], unique=True)

    # books
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("normalized_title", sa.String(), nullable=False),
        sa.Column("normalized_author", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_title", "normalized_author", name="_title_author_uc"),
    )
    op.create_index(op.f("ix_books_id"), "books", ["id"], unique=False)

    # meetings
    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("status", sa.Enum("BOOK_SELECTION", "SCHEDULED", "FINISHED", name="meetingstatus"), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meetings_id"), "meetings", ["id"], unique=False)

    # book_selections
    # ВАЖНО: winning_nomination_id пока без FK, чтобы не было цикла
    op.create_table(
        "book_selections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("NOMINATIONS_OPEN", "VOTING_OPEN", "VOTING_CLOSED", "WINNER_SELECTED", name="bookselectionstatus"), nullable=False),
        sa.Column("winning_nomination_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id"),
    )
    op.create_index(op.f("ix_book_selections_id"), "book_selections", ["id"], unique=False)

    # nominations
    op.create_table(
        "nominations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("selection_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.ForeignKeyConstraint(["selection_id"], ["book_selections.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "selection_id", name="_user_selection_uc"),
    )
    op.create_index(op.f("ix_nominations_id"), "nominations", ["id"], unique=False)

    # votes
    op.create_table(
        "votes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("nomination_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["nomination_id"], ["nominations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "nomination_id", name="_user_nomination_uc"),
    )
    op.create_index(op.f("ix_votes_id"), "votes", ["id"], unique=False)

    # Теперь можно добавить FK для winner
    op.create_foreign_key(
        "fk_book_selections_winning_nomination_id",
        "book_selections",
        "nominations",
        ["winning_nomination_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Сначала убираем циклический FK
    op.drop_constraint(
        "fk_book_selections_winning_nomination_id",
        "book_selections",
        type_="foreignkey",
    )

    op.drop_index(op.f("ix_votes_id"), table_name="votes")
    op.drop_table("votes")

    op.drop_index(op.f("ix_nominations_id"), table_name="nominations")
    op.drop_table("nominations")

    op.drop_index(op.f("ix_book_selections_id"), table_name="book_selections")
    op.drop_table("book_selections")

    op.drop_index(op.f("ix_meetings_id"), table_name="meetings")
    op.drop_table("meetings")

    op.drop_index(op.f("ix_books_id"), table_name="books")
    op.drop_table("books")

    op.drop_index(op.f("ix_users_telegram_login"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")