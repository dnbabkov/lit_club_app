from sqlalchemy import select

from lit_club_app.users.models import User
from lit_club_app.books.models import Book
from lit_club_app.reviews.models import Review


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


def get_user_id(db_session, telegram_login: str) -> int:
    user = db_session.execute(
        select(User).where(User.telegram_login == telegram_login)
    ).scalar_one()
    return user.id


def test_create_review_requires_auth(client, db_session):
    book = create_book_direct(db_session, "Dune", "Frank Herbert")

    response = client.post(
        "/reviews/",
        json={
            "book_id": book.id,
            "rating": 5,
            "anonymous": False,
            "review_text": "Great",
        },
    )

    assert response.status_code in (401, 403)


def test_create_review_success_non_anonymous(client, db_session):
    token = register_user(client, "user", "user_login")
    book = create_book_direct(db_session, "Dune", "Frank Herbert")

    response = client.post(
        "/reviews/",
        json={
            "book_id": book.id,
            "rating": 5,
            "anonymous": False,
            "review_text": "Great",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["book_id"] == book.id
    assert data["rating"] == 5
    assert data["review_text"] == "Great"
    assert data["username"] == "user"


def test_create_review_success_anonymous(client, db_session):
    token = register_user(client, "user", "user_login")
    book = create_book_direct(db_session, "Dune", "Frank Herbert")

    response = client.post(
        "/reviews/",
        json={
            "book_id": book.id,
            "rating": 4,
            "anonymous": True,
            "review_text": "Nice",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["book_id"] == book.id
    assert data["rating"] == 4
    assert data["review_text"] == "Nice"
    assert data["username"] is None


def test_create_review_updates_existing_review(client, db_session):
    token = register_user(client, "user", "user_login")
    user_id = get_user_id(db_session, "user_login")
    book = create_book_direct(db_session, "Dune", "Frank Herbert")

    first = client.post(
        "/reviews/",
        json={
            "book_id": book.id,
            "rating": 5,
            "anonymous": False,
            "review_text": "Great",
        },
        headers=auth_headers(token),
    )
    assert first.status_code == 200, first.text

    second = client.post(
        "/reviews/",
        json={
            "book_id": book.id,
            "rating": 3,
            "anonymous": True,
            "review_text": "Changed my mind",
        },
        headers=auth_headers(token),
    )
    assert second.status_code == 200, second.text

    data = second.json()
    assert data["rating"] == 3
    assert data["review_text"] == "Changed my mind"
    assert data["username"] is None

    reviews = db_session.execute(
        select(Review).where(Review.user_id == user_id, Review.book_id == book.id)
    ).scalars().all()
    assert len(reviews) == 1


def test_create_review_book_not_found_returns_404(client):
    token = register_user(client, "user", "user_login")

    response = client.post(
        "/reviews/",
        json={
            "book_id": 9999,
            "rating": 5,
            "anonymous": False,
            "review_text": "Great",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_get_my_review_for_book_success(client, db_session):
    token = register_user(client, "user", "user_login")
    book = create_book_direct(db_session, "Dune", "Frank Herbert")

    create_response = client.post(
        "/reviews/",
        json={
            "book_id": book.id,
            "rating": 5,
            "anonymous": False,
            "review_text": "Great",
        },
        headers=auth_headers(token),
    )
    assert create_response.status_code == 200, create_response.text

    get_response = client.get(
        f"/reviews/book/{book.id}",
        headers=auth_headers(token),
    )
    assert get_response.status_code == 200, get_response.text

    data = get_response.json()
    assert data["book_id"] == book.id
    assert data["rating"] == 5
    assert data["review_text"] == "Great"
    assert data["username"] == "user"


def test_get_my_review_for_unknown_book_returns_404(client):
    token = register_user(client, "user", "user_login")

    response = client.get(
        "/reviews/book/9999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"