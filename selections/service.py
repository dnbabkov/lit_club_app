from collections import Counter
from random import choices
from sqlalchemy.orm import Session

from lit_club_app.books.repository import BookRepository
from lit_club_app.meetings.repository import MeetingRepository
from lit_club_app.selections.repository import (
    BookSelectionRepository,
    NominationRepository,
    VoteRepository, WinnerSelectionSessionRepository, WinnerSelectionStepRepository,
)
from lit_club_app.common.enums import BookSelectionStatus, WinnerSelectionStatus
from lit_club_app.core.exceptions import (
    MeetingNotFoundError,
    BookSelectionNotFoundError,
    BookSelectionExistsError,
    NominationsNotOpenError,
    VotingNotOpenError,
    NoNominationsError,
    NoVotesError,
    NominationNotFoundError,
    UserAlreadyNominatedError,
    IncorrectVotingStatus,
    WrongNominationError, NoNominationVotesError, SessionNotFoundError, IncorrectSessionStatusError,
    NoEligibleNominationsError, SessionNotReadyToFinalizeError, NoWinnerFinalizeError, BookNotFoundError,
)
from lit_club_app.selections.schemas import (
    WinnerSelectionStateRead,
    WinnerSelectRead,
)
from lit_club_app.books.models import Book
from lit_club_app.selections.models import BookSelection, Nomination

class SelectionService:
    def __init__(self):
        self.meeting_repo = MeetingRepository()
        self.book_select_repo = BookSelectionRepository()
        self.nomination_repo = NominationRepository()
        self.vote_repo = VoteRepository()
        self.book_repo = BookRepository()
        self.winner_selection_repo = WinnerSelectionSessionRepository()
        self.winner_selection_step_repo = WinnerSelectionStepRepository()

    #--------Helpers---------
    def get_or_create_book(self, db: Session, author: str, title: str) -> Book:
        norm_title, norm_author = title.strip().lower(), author.strip().lower()

        book = self.book_repo.get_by_norm_title_and_author(db=db, norm_title=norm_title, norm_author=norm_author)

        if book is None:
            book = self.book_repo.create_book(db=db, title=title, author=author)

        return book

    def get_editable_user_nomination(self, db: Session, selection_id: int, user_id: int) -> Nomination:
        selection = self.book_select_repo.get_by_id(db=db, selection_id=selection_id)
        if selection is None:
            raise BookSelectionNotFoundError()
        if selection.status != BookSelectionStatus.NOMINATIONS_OPEN:
            raise NominationsNotOpenError()
        nomination = self.nomination_repo.get_user_nomination_for_selection(db=db, user_id=user_id, selection=selection)
        if nomination is None:
            raise NominationNotFoundError()
        return nomination

    # Selection methods
    def create_selection(self, db: Session, meeting_id: int) -> BookSelection:
        meeting = self.meeting_repo.get_by_id(db=db, meeting_id=meeting_id)
        if meeting is None:
            raise MeetingNotFoundError()

        selection = self.book_select_repo.get_by_meeting_id(db=db, meeting_id=meeting_id)

        if selection is None:
            selection = self.book_select_repo.create_selection(db=db, meeting_id=meeting_id)
            return selection
        raise BookSelectionExistsError()

    def open_voting(self, db: Session, selection_id: int):
        selection = self.book_select_repo.get_by_id(db=db, selection_id=selection_id)

        if selection is None:
            raise BookSelectionNotFoundError()

        nominations_list = self.nomination_repo.get_all_for_selection(db=db, selection=selection)

        if selection.status != BookSelectionStatus.NOMINATIONS_OPEN:
            raise IncorrectVotingStatus()
        if not nominations_list:
            raise NoNominationsError()

        return self.book_select_repo.update_selection_status(db=db, selection=selection, target_status=BookSelectionStatus.VOTING_OPEN)

    def close_voting(self, db: Session, selection_id: int):
        selection = self.book_select_repo.get_by_id(db=db, selection_id=selection_id)
        if selection is None:
            raise BookSelectionNotFoundError()
        if selection.status != BookSelectionStatus.VOTING_OPEN:
            raise IncorrectVotingStatus()
        votes = self.vote_repo.get_votes_for_selection(db=db, selection=selection)
        if not votes:
            raise NoVotesError()

        return self.book_select_repo.update_selection_status(db=db, selection=selection, target_status=BookSelectionStatus.VOTING_CLOSED)

    # Nomination methods
    def create_nomination(self, db: Session, selection_id: int, user_id: int, title: str, author: str, comment: str | None):
        selection = self.book_select_repo.get_by_id(db=db, selection_id=selection_id)
        if selection is None:
            raise BookSelectionNotFoundError()
        if selection.status != BookSelectionStatus.NOMINATIONS_OPEN:
            raise NominationsNotOpenError()
        nomination = self.nomination_repo.get_user_nomination_for_selection(db=db, user_id=user_id, selection=selection)
        if nomination is not None:
            raise UserAlreadyNominatedError()

        book = self.get_or_create_book(db=db, author=author, title=title)

        return self.nomination_repo.create_nomination(db=db, user_id=user_id, book_id=book.id, selection=selection, comment=comment)

    def replace_user_nomination(self, db: Session, selection_id: int, user_id: int, title: str, author: str, comment: str | None):
        nomination = self.get_editable_user_nomination(db=db, selection_id=selection_id, user_id=user_id)

        book = self.get_or_create_book(db=db, author=author, title=title)
        return self.nomination_repo.update_nomination(db=db, nomination=nomination, book_id=book.id, comment=comment)

    def update_user_nomination_comment(self, db: Session, selection_id: int, user_id: int, comment: str | None):
        nomination = self.get_editable_user_nomination(db=db, selection_id=selection_id, user_id=user_id)
        return self.nomination_repo.update_nomination_comment(db=db, nomination=nomination, comment=comment)

    def get_nominations_for_selection(self, db: Session, selection_id: int):
        selection = self.book_select_repo.get_by_id(db=db, selection_id=selection_id)
        if selection is None:
            raise BookSelectionNotFoundError()
        return self.nomination_repo.get_all_for_selection(db=db, selection=selection)

    # Voices methods
    def vote_for_nominations(self, db: Session, selection_id: int, user_id: int, nomination_ids: list[int]):
        selection = self.book_select_repo.get_by_id(db=db, selection_id=selection_id)
        if selection is None:
            raise BookSelectionNotFoundError()
        if selection.status != BookSelectionStatus.VOTING_OPEN:
            raise VotingNotOpenError()
        if not nomination_ids:
            raise NoNominationVotesError()
        nomination_ids = list(set(nomination_ids))
        for nom_id in nomination_ids:
            nomination = self.nomination_repo.get_by_id(db=db, nomination_id=nom_id)
            if not nomination:
                raise NominationNotFoundError()
            if nomination.selection_id != selection.id:
                raise WrongNominationError()
        return self.vote_repo.set_user_votes_for_selection(db=db, selection=selection, user_id=user_id, nomination_ids=nomination_ids)
    def get_vote_counts_for_selection(self, db: Session, selection_id: int):
        selection = self.book_select_repo.get_by_id(db=db, selection_id=selection_id)
        if selection is None:
            raise BookSelectionNotFoundError()
        if selection.status == BookSelectionStatus.NOMINATIONS_OPEN:
            raise VotingNotOpenError()
        return self.vote_repo.get_vote_counts_for_selection(db=db, selection=selection)

    # Winner determination methods
    def start_winner_selection(self, db: Session, selection_id: int) -> WinnerSelectionStateRead:
        selection = self.book_select_repo.get_by_id(db=db, selection_id=selection_id)
        if selection is None:
            raise BookSelectionNotFoundError()
        if selection.status != BookSelectionStatus.VOTING_CLOSED:
            raise IncorrectVotingStatus("Voting is still open or hasn't started, or selection is already ongoing")

        existing_session = self.winner_selection_repo.get_by_selection_id(db=db, selection_id=selection.id)
        if existing_session is not None:
            return self.get_winner_selection_state(db=db, session_id=existing_session.id)

        session = self.winner_selection_repo.create_session(db=db, selection_id=selection.id)
        return self.get_winner_selection_state(db=db, session_id=session.id)

    def advance_winner_selection_step(self, db: Session, session_id: int) -> WinnerSelectionStateRead:
        session = self.winner_selection_repo.get_by_id(db=db, session_id=session_id)

        if session is None:
            raise SessionNotFoundError()
        if session.status != WinnerSelectionStatus.IN_PROGRESS:
            raise IncorrectSessionStatusError()

        selection = self.book_select_repo.get_by_id(db=db, selection_id=session.selection_id)
        if selection is None:
            raise BookSelectionNotFoundError("How the fuck did you get here?!")

        nominations = self.nomination_repo.get_all_for_selection(db=db, selection=selection)
        if not nominations:
            raise NoNominationsError("How the hell did you get here with no nominations?!")

        eliminated_nominations = self.winner_selection_step_repo.get_eliminated_nomination_ids_for_session(db=db, session=session)
        eliminated_nominations = set(eliminated_nominations)

        active_nominations = [
            nom for nom in nominations if nom.id not in eliminated_nominations
        ]

        if not active_nominations:
            raise NoEligibleNominationsError("How the fuck do you have no nominations to choose from?!")
        elif len(active_nominations) == 1:
            self.winner_selection_repo.set_winner_and_status(db=db, session=session, nomination_id=active_nominations[0].id, target_status=WinnerSelectionStatus.READY_TO_FINALIZE)
            return self.get_winner_selection_state(db=db, session_id=session.id)

        selection_votes = self.vote_repo.get_vote_counts_for_selection(db=db, selection=selection)
        votes_dictionary = {}
        for nomination_id, vote_count in selection_votes:
            votes_dictionary[nomination_id] = vote_count

        active_nomination_ids = [nom.id for nom in active_nominations]

        active_nominations_weights = {}
        active_nominations_weights_sum = 0.0

        for active_nomination in active_nominations:
            vote_count = votes_dictionary.get(active_nomination.id, 0)
            weight = 1 / (vote_count + 1)
            active_nominations_weights[active_nomination.id] = weight
            active_nominations_weights_sum += weight

        active_nominations_probabilities = {}
        for active_nomination in active_nominations:
            prob = active_nominations_weights[active_nomination.id] / active_nominations_weights_sum
            active_nominations_probabilities[active_nomination.id] = prob

        eliminated_nomination_id = choices(
            population=active_nomination_ids,
            weights=[active_nominations_weights[nom_id] for nom_id in active_nomination_ids],
        )[0]

        candidates_data = []

        for active_nomination in active_nominations:
            nomination_id = active_nomination.id
            vote_count = votes_dictionary.get(nomination_id, 0)

            candidates_data.append(
                {
                    "nomination_id": nomination_id,
                    "vote_count": vote_count,
                    "elimination_weight": active_nominations_weights[nomination_id],
                    "elimination_probability": active_nominations_probabilities[nomination_id],
                    "was_eliminated": nomination_id == eliminated_nomination_id,
                }
            )

        next_round = session.current_round + 1

        remaining_nominations = [nom for nom in active_nominations if nom.id != eliminated_nomination_id]

        winner_nomination_id = None
        target_status = None

        if len(remaining_nominations) == 1:
            winner_nomination_id = remaining_nominations[0].id
            target_status = WinnerSelectionStatus.READY_TO_FINALIZE

        self.winner_selection_step_repo.persist_winner_selection_step(db=db,
                                                                      session=session,
                                                                      round_number=next_round,
                                                                      eliminated_nomination_id=eliminated_nomination_id,
                                                                      candidates_data=candidates_data,
                                                                      winner_nomination_id=winner_nomination_id,
                                                                      target_status=target_status
                                                                      )

        return self.get_winner_selection_state(db=db, session_id=session.id)

    def get_winner_selection_state(self, db: Session, session_id: int) -> WinnerSelectionStateRead:
        session = self.winner_selection_repo.get_by_id(db=db, session_id=session_id)
        if session is None:
            raise SessionNotFoundError("Tried to get state of a non-existent session")

        steps = self.winner_selection_step_repo.get_steps_for_session(db=db, session=session)

        steps_data = []

        for step in steps:
            step_candidates = self.winner_selection_step_repo.get_candidates_for_step(db=db, step=step)
            candidates_data = []
            for candidate in step_candidates:
                candidate_dict = {
                    "nomination_id": candidate.nomination_id,
                    "vote_count": candidate.vote_count,
                    "elimination_weight": candidate.elimination_weight,
                    "elimination_probability": candidate.elimination_probability,
                    "was_eliminated": candidate.was_eliminated
                }
                candidates_data.append(candidate_dict)
            step_dict = {
                "step_id": step.id,
                "round_number": step.round_number,
                "eliminated_nomination_id": step.eliminated_nomination_id,
                "candidates": candidates_data,
            }
            steps_data.append(step_dict)

        state = {
            "session_id": session.id,
            "selection_id": session.selection_id,
            "status": session.status,
            "current_round": session.current_round,
            "winner_nomination_id": session.winner_nomination_id,
            "steps": steps_data
        }

        return WinnerSelectionStateRead.model_validate(state)

    def finalize_winner_selection(self, db: Session, session_id: int) -> WinnerSelectRead:
        session = self.winner_selection_repo.get_by_id(db=db, session_id=session_id)
        if session is None:
            raise SessionNotFoundError("Can't finalize non-existent session. How did you even get here?")
        if session.status != WinnerSelectionStatus.READY_TO_FINALIZE:
            raise SessionNotReadyToFinalizeError("Not ready or already finalized")

        winner_nomination_id = session.winner_nomination_id
        if winner_nomination_id is None:
            raise NoWinnerFinalizeError("Trying to finalize with no winner")

        winner_nomination = self.nomination_repo.get_by_id(db=db, nomination_id=winner_nomination_id)
        if winner_nomination is None:
            raise NominationNotFoundError("All that voting only to realize that nomination doesn't exist...")

        book_selection = self.book_select_repo.get_by_id(db=db, selection_id=session.selection_id)
        if book_selection is None:
            raise BookSelectionNotFoundError("It shouldn't be possible, and yet...")

        meeting = self.meeting_repo.get_by_id(db=db, meeting_id=book_selection.meeting_id)
        if meeting is None:
            raise MeetingNotFoundError("Meeting for this selection was not found")

        book = self.book_repo.get_by_id(db=db, book_id=winner_nomination.book_id)
        if book is None:
            raise BookNotFoundError("There is no such book :<")

        try:
            self.book_select_repo.assign_winning_nomination_and_update_status_no_commit(
                db=db,
                selection=book_selection,
                winning_nomination_id=winner_nomination_id,
                target_status=BookSelectionStatus.WINNER_SELECTED,
            )
            self.meeting_repo.assign_book_no_commit(
                db=db,
                meeting=meeting,
                book_id=winner_nomination.book_id,
            )
            self.winner_selection_repo.update_status_no_commit(
                db=db,
                session=session,
                target_status=WinnerSelectionStatus.FINALIZED,
            )
            db.commit()

            db.refresh(book_selection)
            db.refresh(meeting)
            db.refresh(session)
        except Exception:
            db.rollback()
            raise

        winner_selected_data = {
            "selection_id": session.selection_id,
            "winning_nomination_id": winner_nomination_id,
            "book_id": winner_nomination.book_id,
            "title": book.title,
            "author": book.author,
            "description": book.description,
            "vote_count": len(self.vote_repo.get_votes_for_nomination(db=db, nomination=winner_nomination)),
        }

        return WinnerSelectRead.model_validate(winner_selected_data)