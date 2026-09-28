"""Import votes from a legacy SQLite database into PostgreSQL reviews.

The default mode only reads both databases.  Use ``--apply`` explicitly to
insert reviews, and only when the configured PostgreSQL host is local.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from lit_club_app.backend.books.models import Book
from lit_club_app.backend.core.config import settings
from lit_club_app.backend.db.session import SessionLocal
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.users.models import User


INTEGER_RE = re.compile(r"^[+-]?\d+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sqlite_path", type=Path, help="legacy SQLite database")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="insert missing reviews (default is a read-only dry-run)",
    )
    return parser.parse_args()


def as_integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and INTEGER_RE.fullmatch(value):
        return int(value)
    return None


def read_votes(path: Path) -> list[tuple[Any, Any, Any]]:
    uri = f"file:{path.resolve()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as source:
        source.execute("PRAGMA query_only = ON")
        rows = source.execute("SELECT user_id, book, score, epoch FROM votes").fetchall()
    return [(row[0], row[1], row[2]) for row in rows]


def local_host(host: str) -> bool:
    return host.lower().rstrip(".") in {"localhost", "127.0.0.1", "::1"}


def report_counts(counts: Counter[str]) -> None:
    print("Source/report:")
    for label in (
        "rows",
        "invalid_user_id",
        "unmatched_user",
        "invalid_book",
        "unmatched_book",
        "ambiguous_book",
        "invalid_score",
        "existing_review",
        "insertable",
    ):
        print(f"  {label}: {counts[label]}")


def main() -> int:
    args = parse_args()
    if args.apply and not local_host(settings.db_host):
        raise SystemExit("Refusing --apply: configured database host is not local")

    try:
        votes = read_votes(args.sqlite_path)
    except sqlite3.Error as exc:
        raise SystemExit(f"Could not read SQLite votes database: {exc}") from exc

    with SessionLocal() as db:
        users = db.execute(select(User.id, User.tg_id)).all()
        books = db.execute(select(Book.id, Book.title)).all()
        reviews = db.execute(select(Review.user_id, Review.book_id)).all()

        users_by_tg_id = {tg_id: user_id for user_id, tg_id in users if tg_id is not None}
        books_by_title: dict[str, list[int]] = defaultdict(list)
        for book_id, title in books:
            if isinstance(title, str):
                books_by_title[title.lower()].append(book_id)
        existing = {(user_id, book_id) for user_id, book_id in reviews}

        counts: Counter[str] = Counter(rows=len(votes))
        unmatched_titles: Counter[str] = Counter()
        ambiguous_titles: Counter[str] = Counter()
        candidates: list[dict[str, Any]] = []

        for raw_user_id, raw_title, raw_score in votes:
            tg_id = as_integer(raw_user_id)
            if tg_id is None:
                counts["invalid_user_id"] += 1
                continue
            user_id = users_by_tg_id.get(tg_id)
            if user_id is None:
                counts["unmatched_user"] += 1
                continue

            if not isinstance(raw_title, str):
                counts["invalid_book"] += 1
                continue
            matching_books = books_by_title.get(raw_title.lower(), [])
            if not matching_books:
                counts["unmatched_book"] += 1
                unmatched_titles[raw_title] += 1
                continue
            if len(matching_books) != 1:
                counts["ambiguous_book"] += 1
                ambiguous_titles[raw_title] += 1
                continue

            score = as_integer(raw_score)
            if score is None or not 1 <= score <= 5:
                counts["invalid_score"] += 1
                continue

            book_id = matching_books[0]
            if (user_id, book_id) in existing:
                counts["existing_review"] += 1
                continue
            candidates.append(
                {
                    "user_id": user_id,
                    "book_id": book_id,
                    "rating": score,
                    "anonymous": False,
                    "review_text": None,
                }
            )

        counts["insertable"] = len(candidates)
        report_counts(counts)
        if unmatched_titles:
            print("Unmatched book titles:")
            for title, count in sorted(unmatched_titles.items(), key=lambda item: item[0].lower()):
                print(f"  {title!r}: {count}")
        if ambiguous_titles:
            print("Ambiguous book titles:")
            for title, count in sorted(ambiguous_titles.items(), key=lambda item: item[0].lower()):
                print(f"  {title!r}: {count}")

        if not args.apply:
            print("DRY-RUN: no PostgreSQL changes made")
            return 0

        if candidates:
            statement = insert(Review).values(candidates).on_conflict_do_nothing(
                index_elements=[Review.user_id, Review.book_id]
            )
            db.execute(statement)
        db.commit()
        print(f"APPLIED: attempted {len(candidates)} review inserts")
    return 0


if __name__ == "__main__":
    main()
