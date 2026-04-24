from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from lit_club_app.selections.models import BookSelection, Nomination, Vote
from lit_club_app.common.enums import BookSelectionStatus

class BookSelectionRepository:
    def get_by_id(self, db: Session, selection_id: int) -> BookSelection | None:
        statement = (
            select(BookSelection)
            .where(BookSelection.id == selection_id)
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def get_by_meeting_id(self, db: Session, meeting_id: int) -> BookSelection | None:
        statement = (
            select(BookSelection)
            .where(BookSelection.meeting_id == meeting_id)
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def create_selection(self, db: Session, meeting_id: int) -> BookSelection:
        selection = BookSelection(meeting_id=meeting_id)
        try:
            db.add(selection)
            db.commit()
            db.refresh(selection)
            return selection
        except Exception:
            db.rollback()
            raise
    def update_selection_status(self, db: Session, selection: BookSelection, target_status: BookSelectionStatus) -> BookSelection:
        try:
            selection.status = target_status
            db.commit()
            db.refresh(selection)
            return selection
        except Exception:
            db.rollback()
            raise
    def assign_winning_nomination(self, db: Session, selection: BookSelection, winning_nomination_id: int) -> BookSelection:
        try:
            selection.winning_nomination_id = winning_nomination_id
            db.commit()
            db.refresh(selection)
            return selection
        except Exception:
            db.rollback()
            raise

class NominationRepository:
    def get_by_id(self, db: Session, nomination_id: int) -> Nomination | None:
        statement = (
            select(Nomination)
            .where(Nomination.id == nomination_id)
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def get_all_for_selection(self, db: Session, selection: BookSelection) -> Sequence[Nomination]:
        selection_id = selection.id
        statement = (
            select(Nomination)
            .where(Nomination.selection_id == selection_id)
        )
        result = db.execute(statement)
        return result.scalars().all()
    def get_user_nomination_for_selection(self, db: Session, user_id: int, selection: BookSelection) -> Nomination | None:
        selection_id = selection.id
        statement = (
            select(Nomination)
            .where(
                Nomination.selection_id == selection_id,
                Nomination.user_id == user_id
            )
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def create_nomination(self, db: Session, user_id: int, book_id: int, selection: BookSelection, comment: str = None) -> Nomination:
        nomination = Nomination(user_id=user_id, selection_id=selection.id, book_id=book_id, comment=comment)
        try:
            db.add(nomination)
            db.commit()
            db.refresh(nomination)
            return nomination
        except Exception:
            db.rollback()
            raise
    def update_nomination(self, db: Session, nomination: Nomination, book_id: int, comment: str = None) -> Nomination:
        try:
            nomination.book_id = book_id
            if comment is not None:
                nomination.comment = comment
            db.commit()
            db.refresh(nomination)
            return nomination
        except Exception:
            db.rollback()
            raise
    def update_nomination_comment(self, db: Session, nomination: Nomination, comment: str = None) -> Nomination:
        try:
            nomination.comment = comment
            db.commit()
            db.refresh(nomination)
            return nomination
        except Exception:
            db.rollback()
            raise

class VoteRepository:
    def create_vote(self, db: Session, user_id: int, nomination_id: int) -> Vote:
        vote = Vote(user_id=user_id, nomination_id=nomination_id)
        try:
            db.add(vote)
            db.commit()
            db.refresh(vote)
            return vote
        except Exception:
            db.rollback()
            raise
    def get_votes_for_selection(self, db: Session, selection: BookSelection) -> Sequence[Vote]:
        selection_id = selection.id
        statement = (
            select(Vote)
            .join(Nomination, Vote.nomination_id == Nomination.id)
            .where(Nomination.selection_id == selection_id)
        )
        result = db.execute(statement)
        return result.scalars().all()
    def get_votes_for_nomination(self, db: Session, nomination: Nomination) -> Sequence[Vote]:
        nomination_id = nomination.id
        statement = select(Vote).where(Vote.nomination_id == nomination_id)
        result = db.execute(statement)
        return result.scalars().all()
    def get_vote_counts_for_selection(self, db: Session, selection: BookSelection) -> Sequence[tuple[int, int]]:
        statement = (
            select(
                Nomination.id,
                func.count(Vote.id).label("vote_count"),
            )
            .outerjoin(Vote, Vote.nomination_id == Nomination.id)
            .where(Nomination.selection_id == selection.id)
            .group_by(Nomination.id)
        )
        result = db.execute(statement)
        return result.tuples().all()