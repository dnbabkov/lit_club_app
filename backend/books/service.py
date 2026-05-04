from collections import defaultdict
from typing import Sequence

from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

from lit_club_app.backend.books.models import Book
from lit_club_app.backend.books.repository import BookRepository
from lit_club_app.backend.books.schemas import BookWithReviewsRead, BookRead, BooksRead, CanDeleteBookRead
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.core.exceptions import BookNotFoundError, EmptyDescriptionError, BookAlreadyExistsError, \
    NotYourBookError, UserNotFoundError, CantDeleteNominatedBookError
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.reviews.repository import ReviewRepository
from lit_club_app.backend.reviews.service import review_service
from lit_club_app.backend.selections.repository import NominationRepository
from lit_club_app.backend.users.models import User
from lit_club_app.backend.users.repository import UserRepository


class BookService:
    def __init__(self):
        self.book_repo = BookRepository()
        self.review_repo = ReviewRepository()
        self.user_repo = UserRepository()
        self.nomination_repo = NominationRepository()

    def can_user_delete_book(self, db: Session, book: Book, user: User) -> bool:
        nominated_book_ids = set(self.nomination_repo.get_all_nominated_books(db=db))
        is_nominated = book.id in nominated_book_ids

        has_delete_rights = (
                book.user_id is None
                or book.user_id == user.id
                or user.role == Roles.ADMIN
        )

        return has_delete_rights and not is_nominated

    def create_book(self, db: Session, title: str, author: str, description: str | None, user_id: int) -> Book:
        book = self.book_repo.get_by_norm_title_and_author(db=db, norm_title=title.strip().lower(), norm_author=author.strip().lower())
        if book is not None:
            raise BookAlreadyExistsError()
        return self.book_repo.create_book(db=db, title=title, author=author, description=description, user_id=user_id)

    def get_book(self, db: Session, book_id: int) -> Book:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        return book

    def get_all_books(self, db: Session) -> Sequence[Book]:
        return self.book_repo.get_all_books(db=db)

    def update_book_fields(self, db: Session, title: str, author: str, book_id: int, user: User) -> Book:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        if book.user_id is not None and book.user_id != user.id and user.role != Roles.ADMIN:
            raise NotYourBookError()
        book = self.book_repo.update_book_fields(db=db, title=title, author=author, book_id=book_id)
        return book

    def delete_book(self, db: Session, book_id: int, user: User) -> None:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        nominations = set(self.nomination_repo.get_all_nominated_books(db=db))
        if book.id in nominations:
            raise CantDeleteNominatedBookError()
        if book is None:
            raise BookNotFoundError()
        if book.user_id is None or book.user_id == user.id or user.role == Roles.ADMIN:
            return self.book_repo.delete_book(db=db, book_id=book_id)
        else:
            raise NotYourBookError()

    def assign_user_to_book(self, db: Session, book_id: int, user_id: int) -> Book:
        user = self.user_repo.get_by_id(db=db, user_id=user_id)
        if user is None:
            raise UserNotFoundError()
        book = self.book_repo.assign_user_to_book(db=db, book_id=book_id, user=user)
        return book

    def add_description_to_book(self, db: Session, book_id: int, description: str, user: User) -> Book:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        if book.user_id is not None and book.user_id != user.id and user.role != Roles.ADMIN:
            raise NotYourBookError()
        if not description.strip():
            raise EmptyDescriptionError()
        return self.book_repo.add_description(db=db, book=book, description=description)

    def get_finished_books(self, db: Session) -> Sequence[Book]:
        return self.book_repo.get_finished_books_unique(db=db)

    def get_finished_books_with_reviews(self, db: Session) -> list[BookWithReviewsRead]:
        finished_books = self.book_repo.get_finished_books_unique(db=db)
        book_ids = [book.id for book in finished_books]

        reviews = review_service.get_reviews_for_books(db=db, book_ids=book_ids)

        reviews_by_book_id: dict[int, list[Review]] = defaultdict(list)
        for review in reviews:
            reviews_by_book_id[review.book_id].append(review)

        results = []
        for book in finished_books:
            book_reviews = reviews_by_book_id.get(book.id, [])
            review_reads = review_service.to_reviews_read(db=db, reviews=book_reviews)

            result = {
                "book": BookRead.model_validate(book),
                "reviews": review_reads,
            }
            results.append(BookWithReviewsRead.model_validate(result))

        return results

    def to_books_read(self, db: Session, books: Sequence[Book], user: User) -> BooksRead:
        return BooksRead.model_validate(
            {
                "books": [CanDeleteBookRead.model_validate({
                    "book": book,
                    "can_delete": self.can_user_delete_book(db=db, book=book, user=user)
                }) for book in books]
            }
        )

book_service = BookService()