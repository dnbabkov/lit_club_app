from typing import Sequence

from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from lit_club_app.selections.models import BookSelection, Nomination, Vote, WinnerSelectionSession, WinnerSelectionStep, \
    WinnerSelectionStepCandidate
from lit_club_app.common.enums import BookSelectionStatus, WinnerSelectionStatus


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

    def assign_winning_nomination_and_update_status(self, db: Session, selection: BookSelection, winning_nomination_id: int, target_status: BookSelectionStatus) -> BookSelection:
        try:
            selection.winning_nomination_id=winning_nomination_id
            selection.status=target_status
            db.commit()
            db.refresh(selection)
            return selection
        except Exception:
            db.rollback()
            raise

    def assign_winning_nomination_and_update_status_no_commit(self, db: Session, selection: BookSelection, winning_nomination_id: int, target_status: BookSelectionStatus) -> BookSelection:
        selection.winning_nomination_id = winning_nomination_id
        selection.status = target_status
        return selection

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

    def create_nomination(self, db: Session, user_id: int, book_id: int, selection: BookSelection, comment: str | None = None) -> Nomination:
        nomination = Nomination(user_id=user_id, selection_id=selection.id, book_id=book_id, comment=comment)
        try:
            db.add(nomination)
            db.commit()
            db.refresh(nomination)
            return nomination
        except Exception:
            db.rollback()
            raise

    def update_nomination(self, db: Session, nomination: Nomination, book_id: int, comment: str | None = None) -> Nomination:
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

    def update_nomination_comment(self, db: Session, nomination: Nomination, comment: str | None = None) -> Nomination:
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

    def get_user_votes_for_selection(self, db: Session, selection: BookSelection, user_id: int) -> Sequence[Vote]:
        selection_id = selection.id
        statement = (
            select(Vote)
            .join(Nomination, Vote.nomination_id == Nomination.id)
            .where(
                Nomination.selection_id == selection_id,
                Vote.user_id == user_id
            )
        )
        result = db.execute(statement)
        return result.scalars().all()

    def set_user_votes_for_selection( self, db: Session, selection: BookSelection, user_id: int, nomination_ids: list[int]) -> Sequence[Vote]:
        selection_id = selection.id

        nomination_ids_subquery = (
            select(Nomination.id)
            .where(Nomination.selection_id == selection_id)
        )

        statement = (
            delete(Vote)
            .where(
                Vote.user_id == user_id,
                Vote.nomination_id.in_(nomination_ids_subquery),
            )
        )
        try:
            db.execute(statement)
            votes = [Vote(user_id=user_id, nomination_id=nom_id) for nom_id in nomination_ids]
            db.add_all(votes)
            db.commit()
            return self.get_user_votes_for_selection(db=db, selection=selection, user_id=user_id)
        except Exception:
            db.rollback()
            raise

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

class WinnerSelectionSessionRepository:
    def get_by_id(self, db: Session, session_id: int,) -> WinnerSelectionSession | None:
        statement = (
            select(WinnerSelectionSession)
            .where(WinnerSelectionSession.id == session_id)
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def get_by_selection_id(self, db: Session, selection_id: int) -> WinnerSelectionSession | None:
        statement = (
            select(WinnerSelectionSession)
            .where(WinnerSelectionSession.selection_id == selection_id)
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def create_session(self, db: Session, selection_id: int) -> WinnerSelectionSession:
        session = WinnerSelectionSession(selection_id=selection_id)
        try:
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        except Exception:
            db.rollback()
            raise

    def update_status(self, db: Session, session: WinnerSelectionSession, target_status: WinnerSelectionStatus) -> WinnerSelectionSession:
        try:
            session.status = target_status
            db.commit()
            db.refresh(session)
            return session
        except Exception:
            db.rollback()
            raise

    def update_status_no_commit(self, db: Session, session: WinnerSelectionSession, target_status: WinnerSelectionStatus) -> WinnerSelectionSession:
        session.status = target_status
        return session

    def set_current_round(self, db: Session, session: WinnerSelectionSession, round_number: int) -> WinnerSelectionSession:
        try:
            session.current_round = round_number
            db.commit()
            db.refresh(session)
            return session
        except Exception:
            db.rollback()
            raise

    def set_winner_nomination(self, db: Session, session: WinnerSelectionSession, nomination_id: int) -> WinnerSelectionSession:
        try:
            session.winner_nomination_id = nomination_id
            db.commit()
            db.refresh(session)
            return session
        except Exception:
            db.rollback()
            raise

    def set_winner_and_status(self, db: Session, session:WinnerSelectionSession, nomination_id: int, target_status: WinnerSelectionStatus) -> WinnerSelectionSession:
        try:
            session.winner_nomination_id = nomination_id
            session.status = target_status
            db.commit()
            db.refresh(session)
            return session
        except Exception:
            db.rollback()
            raise

class WinnerSelectionStepRepository:
    def create_step(self, db: Session, session: WinnerSelectionSession, round_number: int, eliminated_nomination_id: int) -> WinnerSelectionStep:
        selection_step = WinnerSelectionStep(session_id=session.id, round_number=round_number, eliminated_nomination_id=eliminated_nomination_id)
        try:
            db.add(selection_step)
            db.commit()
            db.refresh(selection_step)
            return selection_step
        except Exception:
            db.rollback()
            raise

    def create_step_candidates(self, db: Session, step: WinnerSelectionStep, candidates_data: list[dict]) -> Sequence[WinnerSelectionStepCandidate]:
        try:
            step_candidates = [
                WinnerSelectionStepCandidate(
                    step_id=step.id,
                    nomination_id=candidate_data["nomination_id"],
                    vote_count=candidate_data["vote_count"],
                    elimination_weight=candidate_data["elimination_weight"],
                    elimination_probability=candidate_data["elimination_probability"],
                    was_eliminated=candidate_data["was_eliminated"],
                )
                for candidate_data in candidates_data
            ]
            db.add_all(step_candidates)
            db.commit()
            return self.get_candidates_for_step(db=db, step=step)
        except Exception:
            db.rollback()
            raise

    def get_steps_for_session(self, db: Session, session: WinnerSelectionSession) -> Sequence[WinnerSelectionStep]:
        statement = (
            select(WinnerSelectionStep)
            .where(WinnerSelectionStep.session_id == session.id)
            .order_by(WinnerSelectionStep.round_number)
        )
        result = db.execute(statement)
        return result.scalars().all()

    def get_candidates_for_step(self, db: Session, step: WinnerSelectionStep) -> Sequence[WinnerSelectionStepCandidate]:
        statement = (
            select(WinnerSelectionStepCandidate)
            .where(WinnerSelectionStepCandidate.step_id == step.id)
        )
        result = db.execute(statement)
        return result.scalars().all()

    def get_eliminated_nomination_ids_for_session(self, db: Session, session: WinnerSelectionSession) -> Sequence[int]:
        statement = (
            select(WinnerSelectionStep.eliminated_nomination_id)
            .where(WinnerSelectionStep.session_id == session.id)
            .order_by(WinnerSelectionStep.round_number)
        )
        result = db.execute(statement)
        return result.scalars().all()

    def persist_winner_selection_step(
            self,
            db: Session,
            session: WinnerSelectionSession,
            round_number: int,
            eliminated_nomination_id: int,
            candidates_data: list[dict],
            winner_nomination_id: int | None = None,
            target_status: WinnerSelectionStatus | None = None
    ) -> tuple[WinnerSelectionStep, Sequence[WinnerSelectionStepCandidate], WinnerSelectionSession]:
        try:
            step = WinnerSelectionStep(
                session_id=session.id,
                round_number=round_number,
                eliminated_nomination_id=eliminated_nomination_id
            )
            db.add(step)
            db.flush()

            step_candidates = [
                WinnerSelectionStepCandidate(
                    step_id=step.id,
                    nomination_id=candidate_data["nomination_id"],
                    vote_count=candidate_data["vote_count"],
                    elimination_weight=candidate_data["elimination_weight"],
                    elimination_probability=candidate_data["elimination_probability"],
                    was_eliminated=candidate_data["was_eliminated"],
                )
                for candidate_data in candidates_data
            ]
            db.add_all(step_candidates)

            session.current_round = round_number

            if winner_nomination_id is not None:
                session.winner_nomination_id = winner_nomination_id

            if target_status is not None:
                session.status = target_status

            db.commit()
            db.refresh(step)
            db.refresh(session)
            return step, step_candidates, session
        except Exception:
            db.rollback()
            raise
