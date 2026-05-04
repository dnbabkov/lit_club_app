from typing import Sequence

from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from lit_club_app.backend.books.models import Book
from lit_club_app.backend.core.exceptions import BookNotFoundError, AlreadyAssignedError
from lit_club_app.backend.meetings.models import Meeting
from lit_club_app.backend.common.enums import MeetingStatus
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.users.models import User


class BookRepository:
    def get_by_id(self, db: Session, book_id: int) -> Book | None:
        statement = (
            select(Book)
            .where(Book.id == book_id)
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def get_by_norm_title_and_author(self, db: Session, norm_title: str, norm_author: str) -> Book | None:
        statement = (
            select(Book)
            .where(
                Book.normalized_title == norm_title,
                Book.normalized_author == norm_author
            )
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def create_book(self, db: Session, title: str, author: str, user_id: int, description: str | None = None) -> Book:

        clean_title = title.strip()
        clean_author = author.strip()

        book = Book(
            title=clean_title,
            author=clean_author,
            description=description,
            normalized_title=title.strip().lower(),
            normalized_author=author.strip().lower(),
            user_id=user_id
        )
        try:
            db.add(book)
            db.commit()
            db.refresh(book)
            return book
        except Exception:
            db.rollback()
            raise

    def update_book_fields(self, db: Session, title: str, author: str, book_id: int) -> Book:
        book = self.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        try:
            clean_title = title.strip()
            clean_author = author.strip()
            book.title = clean_title
            book.author = clean_author
            book.normalized_title = clean_title.lower()
            book.normalized_author = clean_author.lower()
            db.commit()
            db.refresh(book)
            return book
        except Exception:
            db.rollback()
            raise

    def delete_book(self, db: Session, book_id: int) -> None:
        book = self.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        try:
            statement = delete(Book).where(Book.id == book.id)
            db.execute(statement)
            db.commit()
            return
        except Exception:
            db.rollback()
            raise



    def assign_user_to_book(self, db: Session, book_id: int, user: User) -> Book:
        book = self.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        if book.user_id is not None:
            raise AlreadyAssignedError()
        try:
            book.user_id = user.id
            db.commit()
            db.refresh(book)
            return book
        except Exception:
            db.rollback()
            raise

    def get_all_books(self, db: Session) -> Sequence[Book]:
        statement = (select(Book))
        result = db.execute(statement)
        return result.scalars().all()

    def get_meeting_books(self, db: Session) -> Sequence[tuple[Book, MeetingStatus]]:
        statement = (
            select(Book, Meeting.status)
            .join(Meeting, Meeting.book_id == Book.id)
            .where(Meeting.status != MeetingStatus.BOOK_SELECTION)
        )
        result = db.execute(statement)
        return result.tuples().all()

    def add_description(self, db: Session, book: Book, description: str) -> Book:
        try:
            book.description = description
            db.commit()
            db.refresh(book)
            return book
        except Exception:
            db.rollback()
            raise

    def get_finished_books_unique(self, db: Session) -> Sequence[Book]:
        statement = (
            select(Book)
            .join(Meeting, Meeting.book_id == Book.id)
            .where(Meeting.status == MeetingStatus.FINISHED)
            .distinct()
        )
        result = db.execute(statement)
        return result.scalars().all()

    def get_book_rating(self, db: Session, book_id: int) -> float | None:
        book = self.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        statement = (
            select(func.round(func.avg(Review.rating), 1))
            .where(Review.book_id == book.id)
        )
        result = db.execute(statement)
        return result.scalar_one()