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


def test_book_epoch_is_optional_readable_and_limited_to_ten(client):
    token = register_user(client, "reader", "reader_login")

    without_epoch = client.post(
        "/books/",
        json={"title": "Dune", "author": "Frank Herbert", "description": None},
        headers=auth_headers(token),
    )
    assert without_epoch.status_code == 200, without_epoch.text
    assert without_epoch.json()["epoch"] is None
    read_back = client.get(
        f"/books/{without_epoch.json()['id']}",
        headers=auth_headers(token),
    )
    assert read_back.status_code == 200, read_back.text
    assert read_back.json()["epoch"] is None

    ten_chars = client.post(
        "/books/",
        json={"title": "1984", "author": "George Orwell", "description": None, "epoch": "1234567890"},
        headers=auth_headers(token),
    )
    assert ten_chars.status_code == 200, ten_chars.text
    assert ten_chars.json()["epoch"] == "1234567890"

    eleven_chars = client.post(
        "/books/",
        json={"title": "Foundation", "author": "Isaac Asimov", "description": None, "epoch": "12345678901"},
        headers=auth_headers(token),
    )
    assert eleven_chars.status_code == 422


def test_book_epoch_patch_omission_preserves_and_empty_query_clears(client, db_session):
    token = register_user(client, "reader", "reader_login")
    create_response = client.post(
        "/books/",
        json={"title": "Dune", "author": "Frank Herbert", "description": None, "epoch": "classic"},
        headers=auth_headers(token),
    )
    book_id = create_response.json()["id"]

    omitted = client.patch(
        f"/books/{book_id}",
        params={"title": "Dune revised", "author": "Frank Herbert"},
        headers=auth_headers(token),
    )
    assert omitted.status_code == 200, omitted.text
    assert omitted.json()["epoch"] == "classic"

    cleared = client.patch(
        f"/books/{book_id}",
        params={"title": "Dune final", "author": "Frank Herbert", "epoch": ""},
        headers=auth_headers(token),
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["epoch"] is None

    stored = db_session.execute(select(Book).where(Book.id == book_id)).scalar_one()
    assert stored.epoch is None


def test_nomination_new_change_and_edit_propagate_epoch(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "reader", "reader_login")
    selection_id = create_selection(client, db_session, moderator_token)

    created = client.post(
        f"/selections/{selection_id}/nominations/new",
        json={"title": "Dune", "author": "Frank Herbert", "epoch": "first", "comment": None},
        headers=auth_headers(user_token),
    )
    assert created.status_code == 201, created.text
    assert created.json()["epoch"] == "first"

    changed = client.patch(
        f"/selections/{selection_id}/nominations/me/change-book/new",
        json={"title": "Foundation", "author": "Isaac Asimov", "epoch": "second"},
        headers=auth_headers(user_token),
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["epoch"] == "second"

    edited = client.patch(
        f"/selections/{selection_id}/nominations/me/edit-new-book",
        json={"title": "Foundation", "author": "Isaac Asimov"},
        headers=auth_headers(user_token),
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["epoch"] == "second"

    explicitly_cleared = client.patch(
        f"/selections/{selection_id}/nominations/me/edit-new-book",
        json={"title": "Foundation", "author": "Isaac Asimov", "epoch": None},
        headers=auth_headers(user_token),
    )
    assert explicitly_cleared.status_code == 200, explicitly_cleared.text
    assert explicitly_cleared.json()["epoch"] is None


def test_reusing_title_author_does_not_overwrite_existing_epoch(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    first_user_token = register_user(client, "reader1", "reader1_login")
    second_user_token = register_user(client, "reader2", "reader2_login")
    selection_id = create_selection(client, db_session, moderator_token)

    first = client.post(
        f"/selections/{selection_id}/nominations/new",
        json={"title": "Dune", "author": "Frank Herbert", "epoch": "original", "comment": None},
        headers=auth_headers(first_user_token),
    )
    assert first.status_code == 201, first.text

    reused = client.post(
        f"/selections/{selection_id}/nominations/new",
        json={"title": "  dune ", "author": " frank herbert ", "epoch": "ignored", "comment": None},
        headers=auth_headers(second_user_token),
    )
    assert reused.status_code == 201, reused.text
    assert reused.json()["epoch"] == "original"

    stored = db_session.execute(
        select(Book).where(Book.normalized_title == "dune", Book.normalized_author == "frank herbert")
    ).scalar_one()
    assert stored.epoch == "original"
