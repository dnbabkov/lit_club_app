from typing import Sequence
from sqlalchemy.orm import Session

from lit_club_app.books.repository import BookRepository
from lit_club_app.core.exceptions import BookNotFoundError
from lit_club_app.reviews.models import Review
from lit_club_app.reviews.repository import ReviewRepository
from lit_club_app.reviews.schemas import ReviewRead
from lit_club_app.users.repository import UserRepository


class ReviewService:

    def __init__(self):
        self.review_repo = ReviewRepository()
        self.book_repo = BookRepository()
        self.user_repo = UserRepository()

    def create_or_update_review(self, db: Session, user_id: int, book_id: int, rating: int, anonymous: bool, review_text: str | None) -> Review:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        review = self.review_repo.get_by_user_and_book(db=db, user_id=user_id, book_id=book_id)
        if review is None:
            return self.review_repo.create_review(db=db, user_id=user_id, book_id=book_id, rating=rating, anonymous=anonymous, review_text=review_text)
        return self.review_repo.update_review(db=db, review=review, review_text=review_text, anonymous=anonymous, rating=rating)

    def get_reviews_for_book(self, db: Session, book_id: int) -> Sequence[Review]:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        return self.review_repo.get_all_for_book(db=db, book_id=book.id)

    def to_review_read(self, db: Session, review: Review) -> ReviewRead:
        if review.anonymous:
            username = None
        else:
            username = self.user_repo.get_username_by_id(db=db, user_id=review.user_id)
        result = {
            "id": review.id,
            "username": username,
            "book_id": review.book_id,
            "rating": review.rating,
            "review_text": review.review_text
        }
        return ReviewRead.model_validate(result)

    def to_reviews_read(self, db: Session, reviews: Sequence[Review]) -> list[ReviewRead]:
        return [self.to_review_read(db=db, review=review) for review in reviews]

    def get_book_review_for_user(self, db: Session, book_id: int, user_id: int) -> Review:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        return self.review_repo.get_by_user_and_book(db=db, user_id=user_id, book_id=book_id)

review_service = ReviewService()