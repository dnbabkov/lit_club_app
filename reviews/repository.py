from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from lit_club_app.core.exceptions import BookNotFoundError
from lit_club_app.reviews.models import Review


class ReviewRepository:

    def get_by_id(self, db: Session, review_id: int) -> Review | None:
        statement = (
            select(Review)
            .where(Review.id == review_id)
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def get_by_user_and_book(self, db: Session, user_id: int, book_id: int) -> Review | None:
        statement = (
            select(Review)
            .where(
                Review.user_id == user_id,
                Review.book_id == book_id
            )
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def get_all_for_book(self, db: Session, book_id: int) -> Sequence[Review]:
        statement = (
            select(Review)
            .where(Review.book_id == book_id)
        )
        result = db.execute(statement)
        return result.scalars().all()

    def create_review(self, db: Session, user_id: int, book_id: int, rating: int, anonymous: bool, review_text: str | None) -> Review:
        review = Review(book_id=book_id, user_id=user_id, rating=rating, anonymous=anonymous, review_text=review_text)
        try:
            db.add(review)
            db.commit()
            db.refresh(review)
            return review
        except Exception:
            db.rollback()
            raise

    def update_review(self, db: Session, review: Review, rating: int, anonymous: bool, review_text: str | None) -> Review:
        try:
            review.rating = rating
            review.anonymous = anonymous
            review.review_text = review_text
            db.commit()
            db.refresh(review)
            return review
        except Exception:
            db.rollback()
            raise