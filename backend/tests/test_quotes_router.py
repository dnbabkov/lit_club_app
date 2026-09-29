import pytest
from sqlalchemy import select, text

from lit_club_app.backend.books.models import Book
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.quotes.models import Quote
from lit_club_app.backend.tests.auth_helpers import register_user
from lit_club_app.backend.users.models import User


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_book(db_session, title: str = "Dune") -> Book:
    book = Book(
        title=title,
        author="Frank Herbert",
        normalized_title=title.lower(),
        normalized_author="frank herbert",
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


def user_id(db_session, login: str) -> int:
    return db_session.scalar(select(User.id).where(User.telegram_login == login))


def set_role(db_session, login: str, role: Roles) -> None:
    user = db_session.execute(
        select(User).where(User.telegram_login == login)
    ).scalar_one()
    user.role = role
    db_session.commit()


def test_quotes_require_active_auth_for_read_and_create(client, db_session):
    book = make_book(db_session)
    assert client.get(f"/quotes/book/{book.id}").status_code in (401, 403)

    inactive_token = register_user(client, "inactive", "inactive_login")
    inactive = db_session.execute(
        select(User).where(User.telegram_login == "inactive_login")
    ).scalar_one()
    inactive.is_active = False
    db_session.commit()

    auth = headers(inactive_token)
    assert client.get(f"/quotes/book/{book.id}", headers=auth).status_code == 403
    assert client.post(
        "/quotes/", json={"book_id": book.id, "text": "text"}, headers=auth
    ).status_code == 403


def test_random_quote_requires_active_auth_and_is_not_captured_by_id_route(client, db_session):
    book = make_book(db_session)
    assert client.get("/quotes/random").status_code in (401, 403)

    token = register_user(client, "reader", "reader_login")
    created = client.post(
        "/quotes/", json={"book_id": book.id, "text": "route-specific"}, headers=headers(token)
    )
    assert created.status_code == 201, created.text

    response = client.get("/quotes/random", headers=headers(token))
    assert response.status_code == 200, response.text
    assert response.json() == {
        "book_id": book.id,
        "book_title": book.title,
        "book_author": book.author,
        "text": "route-specific",
    }


def test_random_quote_empty_database_returns_expected_404(client):
    token = register_user(client, "reader", "reader_login")

    response = client.get("/quotes/random", headers=headers(token))

    assert response.status_code == 404
    assert response.json()["detail"] == "Цитат пока нет"


def test_random_quote_joins_the_source_book_and_does_not_write(client, db_session):
    token = register_user(client, "reader", "reader_login")
    first_book = make_book(db_session, "Dune")
    second_book = make_book(db_session, "Hyperion")
    first = client.post(
        "/quotes/", json={"book_id": first_book.id, "text": "only dune"}, headers=headers(token)
    )
    second = client.post(
        "/quotes/", json={"book_id": second_book.id, "text": "only hyperion"}, headers=headers(token)
    )
    assert first.status_code == second.status_code == 201
    before = db_session.query(Quote).count()

    # There is no statistical assertion here: every valid result is checked against
    # the exact set of rows that was inserted above.
    response = client.get("/quotes/random", headers=headers(token))

    assert response.status_code == 200, response.text
    assert response.json() in [
        {
            "book_id": first_book.id,
            "book_title": first_book.title,
            "book_author": first_book.author,
            "text": "only dune",
        },
        {
            "book_id": second_book.id,
            "book_title": second_book.title,
            "book_author": second_book.author,
            "text": "only hyperion",
        },
    ]
    db_session.expire_all()
    assert db_session.query(Quote).count() == before


def test_create_quotes_supports_multiple_quotes_and_trims_text(client, db_session):
    token = register_user(client, "reader", "reader_login")
    book = make_book(db_session)

    first = client.post(
        "/quotes/",
        json={"book_id": book.id, "text": "  first quote  "},
        headers=headers(token),
    )
    second = client.post(
        "/quotes/",
        json={"book_id": book.id, "text": "second quote"},
        headers=headers(token),
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["text"] == "first quote"
    assert [quote["text"] for quote in client.get(
        f"/quotes/book/{book.id}", headers=headers(token)
    ).json()] == ["first quote", "second quote"]


@pytest.mark.parametrize("text", ["", "   ", "x" * 10001])
def test_quote_text_validation(client, db_session, text):
    token = register_user(client, "reader", "reader_login")
    book = make_book(db_session)
    response = client.post(
        "/quotes/", json={"book_id": book.id, "text": text}, headers=headers(token)
    )
    assert response.status_code == 422


def test_quote_book_must_exist(client):
    token = register_user(client, "reader", "reader_login")
    response = client.post(
        "/quotes/", json={"book_id": 9999, "text": "missing"}, headers=headers(token)
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_quote_list_is_book_specific_and_unknown_book_is_404(client, db_session):
    token = register_user(client, "reader", "reader_login")
    first_book = make_book(db_session, "Dune")
    second_book = make_book(db_session, "Hyperion")
    client.post(
        "/quotes/", json={"book_id": first_book.id, "text": "only dune"}, headers=headers(token)
    )
    client.post(
        "/quotes/", json={"book_id": second_book.id, "text": "only hyperion"}, headers=headers(token)
    )

    response = client.get(f"/quotes/book/{first_book.id}", headers=headers(token))
    assert [quote["text"] for quote in response.json()] == ["only dune"]
    missing = client.get("/quotes/book/9999", headers=headers(token))
    assert missing.status_code == 404


def test_quote_owner_can_edit_delete_but_moderator_nonowner_cannot(client, db_session):
    owner_token = register_user(client, "owner", "owner_login")
    moderator_token = register_user(client, "moderator", "moderator_login")
    set_role(db_session, "owner_login", Roles.MODERATOR)
    set_role(db_session, "moderator_login", Roles.MODERATOR)
    book = make_book(db_session)
    quote = client.post(
        "/quotes/", json={"book_id": book.id, "text": "original"}, headers=headers(owner_token)
    ).json()

    moderator = headers(moderator_token)
    assert client.patch(
        f"/quotes/{quote['id']}", json={"text": "changed"}, headers=moderator
    ).status_code == 403
    assert client.delete(f"/quotes/{quote['id']}", headers=moderator).status_code == 403

    owner = headers(owner_token)
    updated = client.patch(
        f"/quotes/{quote['id']}", json={"text": "  owner edit  "}, headers=owner
    )
    assert updated.status_code == 200
    assert updated.json()["text"] == "owner edit"
    assert client.delete(f"/quotes/{quote['id']}", headers=owner).status_code == 204


def test_admin_can_manage_foreign_quote_and_update_cannot_change_ownership(client, db_session):
    owner_token = register_user(client, "owner", "owner_login")
    admin_token = register_user(client, "admin", "admin_login")
    set_role(db_session, "admin_login", Roles.ADMIN)
    book = make_book(db_session)
    other_book = make_book(db_session, "Foundation")
    quote = client.post(
        "/quotes/", json={"book_id": book.id, "text": "original"}, headers=headers(owner_token)
    ).json()

    response = client.patch(
        f"/quotes/{quote['id']}",
        json={"text": "admin edit", "book_id": other_book.id, "user_id": user_id(db_session, "admin_login")},
        headers=headers(admin_token),
    )
    assert response.status_code == 200, response.text
    assert response.json()["book_id"] == book.id
    assert response.json()["user_id"] == user_id(db_session, "owner_login")
    assert client.delete(f"/quotes/{quote['id']}", headers=headers(admin_token)).status_code == 204


def test_missing_quote_update_and_delete_return_404(client, db_session):
    token = register_user(client, "reader", "reader_login")
    assert client.patch(
        "/quotes/9999", json={"text": "missing"}, headers=headers(token)
    ).status_code == 404
    assert client.delete("/quotes/9999", headers=headers(token)).status_code == 404


def test_book_delete_cascades_quotes_with_sqlite_foreign_keys(client, db_session):
    token = register_user(client, "reader", "reader_login")
    book = make_book(db_session)
    created = client.post(
        "/quotes/", json={"book_id": book.id, "text": "will cascade"}, headers=headers(token)
    ).json()

    db_session.execute(text("PRAGMA foreign_keys=ON"))
    db_session.delete(book)
    db_session.commit()
    assert db_session.get(Quote, created["id"]) is None
    foreign_key = next(
        key for key in Quote.__table__.c.book_id.foreign_keys if key.column.table.name == "books"
    )
    assert foreign_key.ondelete == "CASCADE"
    db_session.execute(text("PRAGMA foreign_keys=OFF"))
