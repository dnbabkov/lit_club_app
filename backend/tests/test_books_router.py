from datetime import date, datetime, timedelta

from sqlalchemy import select

from lit_club_app.backend.users.models import User
from lit_club_app.backend.books.models import Book
from lit_club_app.backend.meetings.models import Meeting
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.common.enums import Roles, MeetingStatus
from lit_club_app.backend.tests.auth_helpers import register_user


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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


def test_get_top_books_requires_auth_and_returns_empty_for_empty_database(client):
    response = client.get("/books/top")
    assert response.status_code in (401, 403)

    token = register_user(client, "user", "user_login")
    response = client.get("/books/top", headers=auth_headers(token))

    assert response.status_code == 200, response.text
    assert response.json() == []


def test_get_top_books_aggregates_rated_books_with_stable_top_ten_order(client, db_session):
    token = register_user(client, "reader", "reader_login")

    specifications = [
        ("one five", [5]),
        ("two fives first", [5, 5]),
        ("two fives second", [5, 5]),
        ("four and five", [4, 5]),
        ("four average", [4, 4, 4]),
        ("three average", [3, 3]),
        ("second six", [2]),
        ("third seven", [2]),
        ("fourth eight", [2]),
        ("fifth nine", [2]),
        ("sixth ten", [2]),
        ("seventh eleven", [2]),
        ("eighth twelve", [2]),
        ("unrated", []),
    ]
    books = [create_book_direct(db_session, title, "Author") for title, _ in specifications]

    next_user_number = 1
    for book, (_, ratings) in zip(books, specifications):
        for rating in ratings:
            user = User(
                username=f"reviewer{next_user_number}",
                telegram_login=f"reviewer_login{next_user_number}",
                tg_id=6_000_000_000 + next_user_number,
            )
            db_session.add(user)
            db_session.flush()
            create_review_direct(db_session, user.id, book.id, rating)
            next_user_number += 1

    before_books = db_session.query(Book).count()
    before_reviews = db_session.query(Review).count()

    response = client.get("/books/top", headers=auth_headers(token))

    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result) == 10
    assert [item["title"] for item in result] == [
        "two fives first",
        "two fives second",
        "one five",
        "four and five",
        "four average",
        "three average",
        "second six",
        "third seven",
        "fourth eight",
        "fifth nine",
    ]
    assert result[0]["average_rating"] == 5.0
    assert result[0]["review_count"] == 2
    assert result[3]["average_rating"] == 4.5
    assert result[3]["review_count"] == 2
    assert result[-1]["review_count"] == 1
    assert all(item["title"] != "unrated" for item in result)
    assert db_session.query(Book).count() == before_books
    assert db_session.query(Review).count() == before_reviews


def test_get_year_winners_requires_auth_and_empty_response_does_not_mutate_db(client, db_session):
    assert client.get("/books/year-winners").status_code in (401, 403)

    token = register_user(client, "reader", "reader_login")
    before_books = db_session.query(Book).count()
    before_reviews = db_session.query(Review).count()

    response = client.get("/books/year-winners", headers=auth_headers(token))

    assert response.status_code == 200, response.text
    assert response.json() == []
    assert db_session.query(Book).count() == before_books
    assert db_session.query(Review).count() == before_reviews


def test_get_year_winners_uses_september_boundaries_leap_dates_and_ascending_years(client, db_session, monkeypatch):
    token = register_user(client, "reader", "reader_login")
    selected_pools = []

    def deterministic_choice(candidates):
        selected_pools.append([candidate[0].title for candidate in candidates])
        return next(
            (candidate for candidate in candidates if candidate[0].title == "Exact tie one"),
            candidates[0],
        )

    monkeypatch.setattr("lit_club_app.backend.books.service.choice", deterministic_choice)

    def rated_book(title, meeting_date, ratings):
        book = Book(
            title=title,
            author="Author",
            meeting_date=meeting_date,
            normalized_title=title.lower(),
            normalized_author="author",
        )
        db_session.add(book)
        db_session.flush()
        for index, rating in enumerate(ratings):
            reviewer = User(
                username=f"{title.replace(' ', '_')}_{index}",
                telegram_login=f"{title.replace(' ', '_')}_{index}_login",
                tg_id=7_000_000_000 + db_session.query(User).count() + 1,
            )
            db_session.add(reviewer)
            db_session.flush()
            db_session.add(Review(user_id=reviewer.id, book_id=book.id, rating=rating, anonymous=False))
        db_session.commit()
        return book

    rated_book("Aug boundary", date(2020, 8, 31), [5])
    rated_book("Sep boundary", date(2020, 9, 1), [5])
    rated_book("Leap day winner", date(2024, 2, 29), [5])
    rated_book("Aug 2024 loser", date(2024, 8, 31), [4, 4])
    rated_book("Exact tie one", date(2025, 9, 1), [5])
    rated_book("Exact tie two", date(2025, 9, 2), [5])
    rated_book("Exact tie loser", date(2025, 9, 3), [4, 4])
    rated_book("Unrounded high", date(2026, 9, 1), [5, 4, 4, 4])
    rated_book("Rounded-looking low", date(2026, 9, 2), [5, 5, 4, 4, 3])
    unrated = Book(
        title="Undated and unrated",
        author="Author",
        meeting_date=None,
        normalized_title="undated and unrated",
        normalized_author="author",
    )
    db_session.add(unrated)
    db_session.commit()

    response = client.get("/books/year-winners", headers=auth_headers(token))

    assert response.status_code == 200, response.text
    assert [(item["start_year"], item["title"]) for item in response.json()] == [
        (2019, "Aug boundary"),
        (2020, "Sep boundary"),
        (2023, "Leap day winner"),
        (2025, "Exact tie one"),
        (2026, "Unrounded high"),
    ]
    assert {frozenset(pool) for pool in selected_pools} == {
        frozenset(("Aug boundary",)),
        frozenset(("Sep boundary",)),
        frozenset(("Leap day winner",)),
        frozenset(("Exact tie one", "Exact tie two")),
        frozenset(("Unrounded high",)),
    }
    assert all(item["title"] != "Undated and unrated" for item in response.json())


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
