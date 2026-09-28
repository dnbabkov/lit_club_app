import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from lit_club_app.backend.books.models import Book
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.scripts import import_votes
from lit_club_app.backend.users.models import User


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeDb:
    def __init__(self, results):
        self.results = iter(results)
        self.executed = []
        self.commit_count = 0

    def execute(self, statement):
        self.executed.append(statement)
        try:
            return next(self.results)
        except StopIteration:
            return FakeResult([])

    def commit(self):
        self.commit_count += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_read_votes_uses_legacy_columns_and_ignores_epoch(tmp_path: Path):
    source = tmp_path / "votes.sqlite"
    with sqlite3.connect(source) as connection:
        connection.execute(
            "CREATE TABLE votes (user_id, book, score, epoch)"
        )
        connection.execute("INSERT INTO votes VALUES (?, ?, ?, ?)", ("42", "Book", 5, 123))
        connection.commit()

    assert import_votes.read_votes(source) == [("42", "Book", 5)]


def test_dry_run_filters_invalid_unmatched_ambiguous_and_existing(monkeypatch, capsys):
    votes = [
        (100, "Existing", 5),  # existing review: must not be insertable
        (100, "Exact Title", "4"),  # valid candidate
        (100, "DUNE", 4),  # ambiguous title, even though case differs
        (999, "Exact Title", 4),  # unmatched user
        ("not-an-id", "Exact Title", 4),  # invalid user id
        (100, None, 4),  # invalid book
        (100, "Missing", 4),  # unmatched book
        (100, "Exact Title", 0),  # invalid score
    ]
    db = FakeDb(
        [
            FakeResult([(1, 100)]),
            FakeResult(
                [(10, "Dune"), (11, "DUNE"), (12, "Exact Title"), (13, "Existing")]
            ),
            FakeResult([(1, 13)]),
        ]
    )
    monkeypatch.setattr(import_votes, "read_votes", lambda _: votes)
    monkeypatch.setattr(import_votes, "SessionLocal", lambda: db)
    monkeypatch.setattr(
        import_votes,
        "parse_args",
        lambda: SimpleNamespace(sqlite_path=Path("votes.sqlite"), apply=False),
    )

    assert import_votes.main() == 0

    output = capsys.readouterr().out
    assert "rows: 8" in output
    assert "invalid_user_id: 1" in output
    assert "unmatched_user: 1" in output
    assert "invalid_book: 1" in output
    assert "unmatched_book: 1" in output
    assert "ambiguous_book: 1" in output
    assert "invalid_score: 1" in output
    assert "existing_review: 1" in output
    assert "insertable: 1" in output
    assert "DRY-RUN: no PostgreSQL changes made" in output
    assert db.commit_count == 0


def test_apply_inserts_only_rating_with_null_text_and_non_anonymous(monkeypatch):
    db = FakeDb(
        [
            FakeResult([(7, 700)]),
            FakeResult([(70, "The Hobbit")]),
            FakeResult([]),
        ]
    )
    captured = {}

    class FakeInsert:
        def __init__(self, model):
            self.model = model
            self.rows = None

        def values(self, rows):
            self.rows = rows
            captured["rows"] = rows
            return self

        def on_conflict_do_nothing(self, **kwargs):
            captured["conflict"] = kwargs
            return self

    monkeypatch.setattr(import_votes, "read_votes", lambda _: [(700, "the hobbit", "3")])
    monkeypatch.setattr(import_votes, "SessionLocal", lambda: db)
    monkeypatch.setattr(import_votes, "insert", lambda model: FakeInsert(captured.setdefault("model", model)))
    monkeypatch.setattr(import_votes.settings, "db_host", "127.0.0.1")
    monkeypatch.setattr(
        import_votes,
        "parse_args",
        lambda: SimpleNamespace(sqlite_path=Path("votes.sqlite"), apply=True),
    )

    assert import_votes.main() == 0

    assert captured["model"] is Review
    assert captured["rows"] == [
        {
            "user_id": 7,
            "book_id": 70,
            "rating": 3,
            "anonymous": False,
            "review_text": None,
        }
    ]
    assert captured["conflict"]["index_elements"] == [Review.user_id, Review.book_id]
    assert db.commit_count == 1
    assert db.executed[0].is_select
    assert db.executed[1].is_select
    assert db.executed[2].is_select
    assert not hasattr(db.executed[3], "is_select")


def test_apply_refuses_non_local_host_before_reading_or_connecting(monkeypatch):
    monkeypatch.setattr(import_votes.settings, "db_host", "postgres.example.com")
    monkeypatch.setattr(import_votes, "read_votes", lambda _: pytest.fail("must not read source"))
    monkeypatch.setattr(import_votes, "SessionLocal", lambda: pytest.fail("must not connect"))
    monkeypatch.setattr(
        import_votes,
        "parse_args",
        lambda: SimpleNamespace(sqlite_path=Path("votes.sqlite"), apply=True),
    )

    with pytest.raises(SystemExit, match="configured database host is not local"):
        import_votes.main()


def test_default_mode_is_dry_run(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["import_votes.py", "votes.sqlite"])

    assert import_votes.parse_args().apply is False
