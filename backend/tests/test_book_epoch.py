from sqlalchemy import select

from lit_club_app.backend.books.models import Book
from lit_club_app.backend.common.enums import MeetingStatus, Roles
from lit_club_app.backend.meetings.models import Meeting
from lit_club_app.backend.tests.auth_helpers import register_user
from lit_club_app.backend.users.models import User


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def promote_to_moderator(db_session, login: str) -> None:
    user = db_session.execute(select(User).where(User.telegram_login == login)).scalar_one()
    user.role = Roles.MODERATOR
    db_session.commit()


def create_selection(client, db_session, moderator_token: str) -> int:
    moderator = Meeting(status=MeetingStatus.BOOK_SELECTION, book_id=None, scheduled_for=None)
    db_session.add(moderator)
    db_session.commit()
    db_session.refresh(moderator)
    response = client.post(
        "/selections/",
        json={"meeting_id": moderator.id},
        headers=auth_headers(moderator_token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_book_epoch_is_absent_from_model_and_book_api(client, db_session):
    token = register_user(client, "reader", "reader_login")

    response = client.post(
        "/books/",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "description": None,
            "epoch": "ignored legacy value",
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    assert "epoch" not in response.json()

    book_id = response.json()["id"]
    read_back = client.get(
        f"/books/{book_id}",
        headers=auth_headers(token),
    )
    assert read_back.status_code == 200, read_back.text
    assert "epoch" not in read_back.json()

    stored = db_session.execute(select(Book).where(Book.id == book_id)).scalar_one()
    assert not hasattr(stored, "epoch")
    assert stored.meeting_date is None


def test_book_epoch_patch_is_ignored_and_other_book_fields_still_work(client, db_session):
    token = register_user(client, "reader", "reader_login")
    create_response = client.post(
        "/books/",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "description": None,
            "meeting_date": "2026-09-28",
        },
        headers=auth_headers(token),
    )
    book_id = create_response.json()["id"]

    omitted = client.patch(
        f"/books/{book_id}",
        params={
            "title": "Dune revised",
            "author": "Frank Herbert",
            "epoch": "legacy query value",
        },
        headers=auth_headers(token),
    )
    assert omitted.status_code == 200, omitted.text
    assert "epoch" not in omitted.json()
    assert omitted.json()["title"] == "Dune revised"
    assert omitted.json()["meeting_date"] == "2026-09-28"

    stored = db_session.execute(select(Book).where(Book.id == book_id)).scalar_one()
    assert not hasattr(stored, "epoch")
    assert stored.meeting_date.isoformat() == "2026-09-28"


def test_nomination_flows_do_not_expose_or_store_epoch(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "reader", "reader_login")
    selection_id = create_selection(client, db_session, moderator_token)

    created = client.post(
        f"/selections/{selection_id}/nominations/new",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "epoch": "first",
            "meeting_date": "2026-09-28",
            "comment": None,
        },
        headers=auth_headers(user_token),
    )
    assert created.status_code == 201, created.text
    assert "epoch" not in created.json()
    assert created.json()["meeting_date"] == "2026-09-28"

    changed = client.patch(
        f"/selections/{selection_id}/nominations/me/change-book/new",
        json={
            "title": "Foundation",
            "author": "Isaac Asimov",
            "epoch": "second",
            "meeting_date": "2027-01-02",
        },
        headers=auth_headers(user_token),
    )
    assert changed.status_code == 200, changed.text
    assert "epoch" not in changed.json()
    assert changed.json()["meeting_date"] == "2027-01-02"

    edited = client.patch(
        f"/selections/{selection_id}/nominations/me/edit-new-book",
        json={"title": "Foundation", "author": "Isaac Asimov"},
        headers=auth_headers(user_token),
    )
    assert edited.status_code == 200, edited.text
    assert "epoch" not in edited.json()
    assert edited.json()["meeting_date"] == "2027-01-02"

    explicitly_cleared = client.patch(
        f"/selections/{selection_id}/nominations/me/edit-new-book",
        json={"title": "Foundation", "author": "Isaac Asimov", "epoch": None},
        headers=auth_headers(user_token),
    )
    assert explicitly_cleared.status_code == 200, explicitly_cleared.text
    assert "epoch" not in explicitly_cleared.json()
    assert explicitly_cleared.json()["meeting_date"] == "2027-01-02"

    stored_books = db_session.execute(select(Book)).scalars().all()
    assert len(stored_books) == 2
    assert all(not hasattr(book, "epoch") for book in stored_books)
