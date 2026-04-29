from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, CheckConstraint, Float, Boolean, String, \
    UniqueConstraint
from lit_club_app.backend.db.base import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=False)
    anonymous = Column(Boolean, default=False, nullable=False)
    review_text = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint('user_id', 'book_id', name='_user_book_uc'),)