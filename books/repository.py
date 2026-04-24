from sqlalchemy import select
from sqlalchemy.orm import Session

from lit_club_app.books.models import Book

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
    def create_book(self, db: Session, title: str, author: str, description: str | None = None) -> Book:
        book = Book(title=title, author=author, description=description, normalized_title=title.strip().lower(), normalized_author=author.strip().lower())
        try:
            db.add(book)
            db.commit()
            db.refresh(book)
            return book
        except Exception:
            db.rollback()
            raise