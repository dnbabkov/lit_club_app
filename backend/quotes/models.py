from sqlalchemy import Column, ForeignKey, Integer, String

from lit_club_app.backend.db.base import Base


class Quote(Base):
    __tablename__ = "quote"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(String, nullable=False)
