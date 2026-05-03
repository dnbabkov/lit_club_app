from collections import defaultdict
from typing import Sequence

from sqlalchemy.orm import Session

from lit_club_app.backend.books.models import Book
from lit_club_app.backend.books.repository import BookRepository
from lit_club_app.backend.books.schemas import BookWithReviewsRead, BookRead, BooksRead
from lit_club_app.backend.core.exceptions import BookNotFoundError, EmptyDescriptionError, BookAlreadyExistsError
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.reviews.repository import ReviewRepository
from lit_club_app.backend.reviews.service import review_service


class BookService:
    def __init__(self):
        self.book_repo = BookRepository()
        self.review_repo = ReviewRepository()

    def create_book(self, db: Session, title: str, author: str, description: str | None) -> Book:
        book = self.book_repo.get_by_norm_title_and_author(db=db, norm_title=title.strip().lower(), norm_author=author.strip().lower())
        if book is not None:
            raise BookAlreadyExistsError()
        return self.book_repo.create_book(db=db, title=title, author=author, description=description)

    def get_book(self, db: Session, book_id: int) -> Book:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        return book

    def get_all_books(self, db: Session) -> Sequence[Book]:
        return self.book_repo.get_all_books(db=db)

    def update_book_fields(self, db: Session, title: str, author: str, book_id: int) -> Book:
        book = self.book_repo.update_book_fields(db=db, title=title, author=author, book_id=book_id)
        return book

    def add_description_to_book(self, db: Session, book_id: int, description: str) -> Book:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
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

    def to_books_read(self, db: Session, books: Sequence[Book]) -> BooksRead:
        return BooksRead.model_validate(
            {
                "books": [BookRead.model_validate(book) for book in books]
            }
        )

book_service = BookService()