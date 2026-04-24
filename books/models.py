from sqlalchemy import Column, Integer, String, UniqueConstraint
from lit_club_app.db.base import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    description = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('title', 'author', name='_title_author_uc'),
    )