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
    meeting = Meeting(status=MeetingStatus.BOOK_SELECTION, book_id=None, scheduled_for=None)
    db_session.add(meeting)
    db_session.commit()
    db_session.refresh(meeting)

    response = client.post(
        "/selections/",
        json={"meeting_id": meeting.id},
        headers=auth_headers(moderator_token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_meeting_date_is_optional_valid_and_readable(client):
    token = register_user(client, "reader", "reader_login")

    omitted = client.post(
        "/books/",
        json={"title": "Dune", "author": "Frank Herbert", "description": None},
        headers=auth_headers(token),
    )
    assert omitted.status_code == 200, omitted.text
    assert omitted.json()["meeting_date"] is None

    explicit = client.post(
        "/books/",
        json={
            "title": "1984",
            "author": "George Orwell",
            "description": None,
            "meeting_date": "2026-09-28",
        },
        headers=auth_headers(token),
    )
    assert explicit.status_code == 200, explicit.text
    assert explicit.json()["meeting_date"] == "2026-09-28"

    read_back = client.get(
        f"/books/{explicit.json()['id']}",
        headers=auth_headers(token),
    )
    assert read_back.status_code == 200, read_back.text
    assert read_back.json()["meeting_date"] == "2026-09-28"


def test_invalid_meeting_date_is_rejected_on_create_and_update(client):
    token = register_user(client, "reader", "reader_login")

    invalid_create = client.post(
        "/books/",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "description": None,
            "meeting_date": "2026-02-30",
        },
        headers=auth_headers(token),
    )
    assert invalid_create.status_code == 422

    created = client.post(
        "/books/",
        json={"title": "Dune", "author": "Frank Herbert", "description": None},
        headers=auth_headers(token),
    )
    book_id = created.json()["id"]
    invalid_update = client.patch(
        f"/books/{book_id}",
        params={
            "title": "Dune",
            "author": "Frank Herbert",
            "meeting_date": "not-a-date",
        },
        headers=auth_headers(token),
    )
    assert invalid_update.status_code == 422


def test_meeting_date_update_omission_preserves_and_explicit_clear_works(client, db_session):
    token = register_user(client, "reader", "reader_login")
    created = client.post(
        "/books/",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "description": None,
            "meeting_date": "2026-09-28",
        },
        headers=auth_headers(token),
    )
    book_id = created.json()["id"]

    omitted = client.patch(
        f"/books/{book_id}",
        params={"title": "Dune revised", "author": "Frank Herbert"},
        headers=auth_headers(token),
    )
    assert omitted.status_code == 200, omitted.text
    assert omitted.json()["meeting_date"] == "2026-09-28"

    cleared = client.patch(
        f"/books/{book_id}",
        params={"title": "Dune final", "author": "Frank Herbert", "meeting_date": ""},
        headers=auth_headers(token),
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["meeting_date"] is None

    stored = db_session.execute(select(Book).where(Book.id == book_id)).scalar_one()
    assert stored.meeting_date is None


def test_nomination_create_change_and_edit_preserve_and_clear_meeting_date(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "reader", "reader_login")
    selection_id = create_selection(client, db_session, moderator_token)

    created = client.post(
        f"/selections/{selection_id}/nominations/new",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "meeting_date": "2026-09-28",
            "comment": None,
        },
        headers=auth_headers(user_token),
    )
    assert created.status_code == 201, created.text
    assert created.json()["meeting_date"] == "2026-09-28"

    changed = client.patch(
        f"/selections/{selection_id}/nominations/me/change-book/new",
        json={
            "title": "Foundation",
            "author": "Isaac Asimov",
            "meeting_date": "2027-01-02",
        },
        headers=auth_headers(user_token),
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["meeting_date"] == "2027-01-02"

    omitted = client.patch(
        f"/selections/{selection_id}/nominations/me/edit-new-book",
        json={"title": "Foundation revised", "author": "Isaac Asimov"},
        headers=auth_headers(user_token),
    )
    assert omitted.status_code == 200, omitted.text
    assert omitted.json()["meeting_date"] == "2027-01-02"

    cleared = client.patch(
        f"/selections/{selection_id}/nominations/me/edit-new-book",
        json={"title": "Foundation final", "author": "Isaac Asimov", "meeting_date": None},
        headers=auth_headers(user_token),
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["meeting_date"] is None


def test_reusing_existing_book_does_not_overwrite_meeting_date(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    first_user_token = register_user(client, "reader1", "reader1_login")
    second_user_token = register_user(client, "reader2", "reader2_login")
    selection_id = create_selection(client, db_session, moderator_token)

    first = client.post(
        f"/selections/{selection_id}/nominations/new",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "meeting_date": "2026-09-28",
            "comment": None,
        },
        headers=auth_headers(first_user_token),
    )
    assert first.status_code == 201, first.text

    reused = client.post(
        f"/selections/{selection_id}/nominations/new",
        json={
            "title": "  dune ",
            "author": " frank herbert ",
            "meeting_date": "2099-01-01",
            "comment": None,
        },
        headers=auth_headers(second_user_token),
    )
    assert reused.status_code == 201, reused.text
    assert reused.json()["meeting_date"] == "2026-09-28"

    stored = db_session.execute(
        select(Book).where(
            Book.normalized_title == "dune",
            Book.normalized_author == "frank herbert",
        )
    ).scalar_one()
    assert stored.meeting_date.isoformat() == "2026-09-28"
