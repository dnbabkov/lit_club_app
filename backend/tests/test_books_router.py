from datetime import datetime, timedelta

from sqlalchemy import select

from lit_club_app.backend.users.models import User
from lit_club_app.backend.books.models import Book
from lit_club_app.backend.meetings.models import Meeting
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.common.enums import Roles, MeetingStatus


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_user(client, username: str, telegram_login: str, password: str = "1234") -> str:
    response = client.post(
        "/users/register",
        json={
            "username": username,
            "telegram_login": telegram_login,
            "password": password,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def create_book_direct(
    db_session,
    title: str,
    author: str,
    description: str | None = None,
) -> Book:
    book = Book(
        title=title.strip(),
        author=author.strip(),
        description=description,
        normalized_title=title.strip().lower(),
        normalized_author=author.strip().lower(),
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


def create_meeting_direct(
    db_session,
    status: MeetingStatus,
    book_id: int | None = None,
    scheduled_for: datetime | None = None,
) -> Meeting:
    meeting = Meeting(
        status=status,
        book_id=book_id,
        scheduled_for=scheduled_for,
    )
    db_session.add(meeting)
    db_session.commit()
    db_session.refresh(meeting)
    return meeting


def create_review_direct(
    db_session,
    user_id: int,
    book_id: int,
    rating: int,
    anonymous: bool = False,
    review_text: str | None = None,
) -> Review:
    review = Review(
        user_id=user_id,
        book_id=book_id,
        rating=rating,
        anonymous=anonymous,
        review_text=review_text,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return review


def get_user_id(db_session, telegram_login: str) -> int:
    user = db_session.execute(
        select(User).where(User.telegram_login == telegram_login)
    ).scalar_one()
    return user.id


def test_get_books_requires_auth(client):
    response = client.get("/books/")
    assert response.status_code in (401, 403)


def test_get_books_empty(client):
    token = register_user(client, "user", "user_login")

    response = client.get(
        "/books/",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "books" in data
    assert data["books"] == []


def test_create_book_success(client):
    token = register_user(client, "user", "user_login")

    response = client.post(
        "/books/",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "description": "Classic sci-fi",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Dune"
    assert data["author"] == "Frank Herbert"
    assert data["description"] == "Classic sci-fi"


def test_create_book_duplicate_returns_409(client):
    token = register_user(client, "user", "user_login")

    first = client.post(
        "/books/",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "description": None,
        },
        headers=auth_headers(token),
    )
    assert first.status_code == 200, first.text

    duplicate = client.post(
        "/books/",
        json={
            "title": "  dune  ",
            "author": " frank herbert ",
            "description": "Another description",
        },
        headers=auth_headers(token),
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Book already exists"


def test_get_book_success(client, db_session):
    token = register_user(client, "user", "user_login")
    book = create_book_direct(db_session, "Dune", "Frank Herbert", "Classic sci-fi")

    response = client.get(
        f"/books/{book.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == book.id
    assert data["title"] == "Dune"
    assert data["author"] == "Frank Herbert"
    assert data["description"] == "Classic sci-fi"


def test_get_book_404(client):
    token = register_user(client, "user", "user_login")

    response = client.get(
        "/books/9999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_change_description_success(client, db_session):
    token = register_user(client, "user", "user_login")
    book = create_book_direct(db_session, "Dune", "Frank Herbert", None)

    response = client.patch(
        f"/books/{book.id}/description",
        json={"description": "New description"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["description"] == "New description"


def test_change_description_empty_returns_400(client, db_session):
    token = register_user(client, "user", "user_login")
    book = create_book_direct(db_session, "Dune", "Frank Herbert", None)

    response = client.patch(
        f"/books/{book.id}/description",
        json={"description": "   "},
        headers=auth_headers(token),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Description cannot be empty"


def test_change_description_book_not_found_returns_404(client):
    token = register_user(client, "user", "user_login")

    response = client.patch(
        "/books/9999/description",
        json={"description": "New description"},
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_get_finished_books_returns_only_finished_books(client, db_session):
    token = register_user(client, "user", "user_login")

    finished_book = create_book_direct(db_session, "Dune", "Frank Herbert")
    scheduled_book = create_book_direct(db_session, "1984", "George Orwell")
    untouched_book = create_book_direct(db_session, "Foundation", "Isaac Asimov")

    create_meeting_direct(db_session, MeetingStatus.FINISHED, book_id=finished_book.id)
    create_meeting_direct(db_session, MeetingStatus.SCHEDULED, book_id=scheduled_book.id)

    response = client.get(
        "/books/finished",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    returned_ids = {item["id"] for item in data["books"]}

    assert finished_book.id in returned_ids
    assert scheduled_book.id not in returned_ids
    assert untouched_book.id not in returned_ids


def test_get_finished_with_reviews_returns_reviews_for_finished_books(client, db_session):
    token = register_user(client, "reader", "reader_login")
    reviewer_token = register_user(client, "reviewer", "reviewer_login")
    anon_token = register_user(client, "anon", "anon_login")

    reader_id = get_user_id(db_session, "reader_login")
    reviewer_id = get_user_id(db_session, "reviewer_login")
    anon_id = get_user_id(db_session, "anon_login")

    finished_book = create_book_direct(db_session, "Dune", "Frank Herbert", "Classic sci-fi")
    unfinished_book = create_book_direct(db_session, "1984", "George Orwell", "Dystopia")

    create_meeting_direct(db_session, MeetingStatus.FINISHED, book_id=finished_book.id)
    create_meeting_direct(db_session, MeetingStatus.SCHEDULED, book_id=unfinished_book.id)

    create_review_direct(
        db_session,
        user_id=reviewer_id,
        book_id=finished_book.id,
        rating=5,
        anonymous=False,
        review_text="Amazing",
    )
    create_review_direct(
        db_session,
        user_id=anon_id,
        book_id=finished_book.id,
        rating=4,
        anonymous=True,
        review_text="Pretty good",
    )
    create_review_direct(
        db_session,
        user_id=reader_id,
        book_id=unfinished_book.id,
        rating=3,
        anonymous=False,
        review_text="Not finished meeting",
    )

    response = client.get(
        "/books/finished-with-reviews",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    item = data[0]
    assert item["book"]["id"] == finished_book.id
    assert item["book"]["title"] == "Dune"
    assert len(item["reviews"]) == 2

    usernames = {review["username"] for review in item["reviews"]}
    assert "reviewer" in usernames
    assert None in usernames