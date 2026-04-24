from sqlalchemy import Column, Integer, String, Enum, ForeignKey, UniqueConstraint
from lit_club_app.db.base import Base

from lit_club_app.common.enums import BookSelectionStatus

class BookSelection(Base):
    __tablename__ = "book_selections"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), unique=True, nullable=False)
    status = Column(Enum(BookSelectionStatus), nullable=False, default=BookSelectionStatus.NOMINATIONS_OPEN)
    winning_nomination_id = Column(Integer, ForeignKey("nominations.id"), nullable=True)

class Nomination(Base):
    __tablename__ = "nominations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    selection_id = Column(Integer, ForeignKey("book_selections.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    comment = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'selection_id', name='_user_selection_uc'),
    )

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nomination_id = Column(Integer, ForeignKey("nominations.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'nomination_id', name='_user_nomination_uc'),
    )