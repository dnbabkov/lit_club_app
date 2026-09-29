from sqlalchemy import func, select
from sqlalchemy.orm import Session

from lit_club_app.backend.books.models import Book
from lit_club_app.backend.core.exceptions import BookNotFoundError
from lit_club_app.backend.quotes.models import Quote
from lit_club_app.backend.quotes.schemas import QuoteRead, RandomQuoteRead
from lit_club_app.backend.users.models import User


class QuoteService:
    def get_for_book(self, db: Session, book_id: int) -> list[QuoteRead]:
        if db.get(Book, book_id) is None:
            raise BookNotFoundError()
        rows = db.execute(
            select(Quote, User.username)
            .join(User, User.id == Quote.user_id)
            .where(Quote.book_id == book_id)
            .order_by(Quote.id)
        ).all()
        return [self._to_read(quote, username) for quote, username in rows]

    def get_random(self, db: Session) -> RandomQuoteRead | None:
        row = db.execute(
            select(Quote, Book.title, Book.author)
            .join(Book, Book.id == Quote.book_id)
            .order_by(func.random())
            .limit(1)
        ).first()
        if row is None:
            return None
        quote, book_title, book_author = row
        return RandomQuoteRead(
            book_id=quote.book_id,
            book_title=book_title,
            book_author=book_author,
            text=quote.text,
        )

    def create(self, db: Session, book_id: int, user_id: int, text: str) -> QuoteRead:
        if db.get(Book, book_id) is None:
            raise BookNotFoundError()
        quote = Quote(book_id=book_id, user_id=user_id, text=text)
        db.add(quote)
        db.commit()
        db.refresh(quote)
        username = db.scalar(select(User.username).where(User.id == user_id))
        return self._to_read(quote, username)

    def update(self, db: Session, quote_id: int, user: User, text: str) -> QuoteRead | None:
        quote = db.get(Quote, quote_id)
        if quote is None:
            return None
        if quote.user_id != user.id and user.role.value != "admin":
            raise PermissionError
        quote.text = text
        db.commit()
        db.refresh(quote)
        return self._to_read(quote, db.scalar(select(User.username).where(User.id == quote.user_id)))

    def delete(self, db: Session, quote_id: int, user: User) -> bool | None:
        quote = db.get(Quote, quote_id)
        if quote is None:
            return None
        if quote.user_id != user.id and user.role.value != "admin":
            raise PermissionError
        db.delete(quote)
        db.commit()
        return True

    @staticmethod
    def _to_read(quote: Quote, username: str) -> QuoteRead:
        return QuoteRead(
            id=quote.id,
            book_id=quote.book_id,
            user_id=quote.user_id,
            username=username,
            text=quote.text,
        )


quote_service = QuoteService()
