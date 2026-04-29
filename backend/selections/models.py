from sqlalchemy import Column, Integer, String, Enum, ForeignKey, UniqueConstraint, Float, Boolean
from lit_club_app.backend.db.base import Base

from lit_club_app.backend.common.enums import BookSelectionStatus, WinnerSelectionStatus


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

class WinnerSelectionSession(Base):
    __tablename__ = "winner_selection_sessions"

    id = Column(Integer, primary_key=True, index=True)
    selection_id = Column(Integer, ForeignKey("book_selections.id"), nullable=False, unique=True)
    status = Column(Enum(WinnerSelectionStatus), default=WinnerSelectionStatus.IN_PROGRESS, nullable=False)
    current_round = Column(Integer, nullable=False, default=0)
    winner_nomination_id = Column(Integer, ForeignKey("nominations.id"), nullable=True)

class WinnerSelectionStep(Base):
    __tablename__ = "winner_selection_steps"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("winner_selection_sessions.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    eliminated_nomination_id = Column(Integer, ForeignKey("nominations.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint('session_id', 'round_number', name='_session_round_number_uc'),
    )

class WinnerSelectionStepCandidate(Base):
    __tablename__ = "winner_selection_step_candidates"

    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("winner_selection_steps.id"), nullable=False)
    nomination_id = Column(Integer, ForeignKey("nominations.id"), nullable=False)
    vote_count = Column(Integer, nullable=False)
    elimination_weight = Column(Float, nullable=False)
    elimination_probability = Column(Float, nullable=False)
    was_eliminated = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint('step_id', 'nomination_id', name='_step_nomination_uc'),
    )