from sqlalchemy import Column, Integer, String, UniqueConstraint
from lit_club_app.db.base import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    description = Column(String, nullable=True)
    normalized_title = Column(String, nullable=False)
    normalized_author = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('normalized_title', 'normalized_author', name='_title_author_uc'),
    )