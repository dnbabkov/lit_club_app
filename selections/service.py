from collections import Counter
from random import choices
from sqlalchemy.orm import Session

from lit_club_app.books.repository import BookRepository
from lit_club_app.meetings.repository import MeetingRepository
from lit_club_app.selections.repository import (
    BookSelectionRepository,
    NominationRepository,
    VoteRepository,
)
from lit_club_app.common.enums import BookSelectionStatus, MeetingStatus
from lit_club_app.core.exceptions import (
    MeetingNotFoundError,
    BookSelectionNotFoundError,
    BookSelectionExistsError,
    NominationsNotOpenError,
    VotingNotOpenError,
    WinnerAlreadySelectedError,
    WinnerCannotBeSelectedBeforeVotingClosedError,
    NoNominationsError,
    NoVotesError,
    NominationNotFoundError,
    UserAlreadyNominatedError,
    NominationUpdateForbiddenError,
    DuplicateVoteError,
    VotingAlreadyClosedError,
    IncorrectVotingStatus,
    WrongNominationError, NoNominationVotesError,
)
from lit_club_app.selections.schemas import (
    BookSelectionCreate,
    NominationCreate,
    NominationUpdate,
    VoteCreate,
)
from lit_club_app.books.models import Book
from lit_club_app.meetings.models import Meeting
from lit_club_app.selections.models import BookSelection, Nomination, Vote
from lit_club_app.users.models import User

class SelectionService:
    def __init__(self):
        self.meeting_repo = MeetingRepository()
        self.book_select_repo = BookSelectionRepository()
        self.nomination_repo = NominationRepository()
        self.vote_repo = VoteRepository()
        self.book_repo = BookRepository()

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
    def start_winner_selection(self):
        ...
    def advance_winner_selection_step(self):
        ...
    def get_winner_selection_state(self):
        ...
    def finalize_winner_selection(self):
        ...