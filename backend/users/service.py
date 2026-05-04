from collections import defaultdict

from sqlalchemy.orm import Session

from lit_club_app.backend.books.repository import BookRepository
from lit_club_app.backend.meetings.repository import MeetingRepository
from lit_club_app.backend.reviews.repository import ReviewRepository
from lit_club_app.backend.selections.models import Nomination
from lit_club_app.backend.selections.repository import NominationRepository, BookSelectionRepository
from lit_club_app.backend.users.models import User
from lit_club_app.backend.users.schemas import UserRegister, UserLogin, UserProfileRead, UserProfileBookRead, \
    UserProfileBookRatingRead

from lit_club_app.backend.common.enums import Roles

from lit_club_app.backend.users.repository import UserRepository

from lit_club_app.backend.core.security import hash_password, verify_password
from lit_club_app.backend.core.exceptions import (
    UsernameAlreadyExistsError,
    TelegramLoginAlreadyExistsError,
    UserNotFoundError,
    InvalidPasswordError, EmptyTelegramLoginError, BookNotFoundError, BookSelectionNotFoundError, MeetingNotFoundError,
)

class UserService:
    def __init__(self):
        self.repo = UserRepository()
        self.nomination_repo = NominationRepository()
        self.book_repo = BookRepository()
        self.book_selection_repo = BookSelectionRepository()
        self.meeting_repo = MeetingRepository()
        self.review_repo = ReviewRepository()

    def _normalize_telegram_login(self, telegram_login: str) -> str:
        telegram_login = telegram_login.strip().lstrip("@")

        return telegram_login

    def register_user(self, db: Session, user_data: UserRegister) -> User:

        username = user_data.username.strip()
        telegram_login = user_data.telegram_login.strip().lower()
        password = user_data.password

        telegram_login = self._normalize_telegram_login(telegram_login)
        if not telegram_login:
            raise EmptyTelegramLoginError()

        if self.repo.get_by_username(db=db, username=username):
            raise UsernameAlreadyExistsError("Username is already taken")
        if self.repo.get_by_telegram_login(db=db, telegram_login=telegram_login):
            raise TelegramLoginAlreadyExistsError("User with this tag already exists")

        password_hash = hash_password(password)

        user = self.repo.create(
            db=db,
            username=username,
            telegram_login=telegram_login,
            password_hash=password_hash,
            role=Roles.MEMBER,
        )

        return user

    def authenticate_user(self, db: Session, login_data: UserLogin) -> User:

        telegram_login = login_data.telegram_login.strip().lower()
        password = login_data.password

        telegram_login = self._normalize_telegram_login(telegram_login)
        if not telegram_login:
            raise EmptyTelegramLoginError()

        user = self.repo.get_by_telegram_login(db=db, telegram_login=telegram_login)

        if not user:
            raise UserNotFoundError("No user with this tag exists")

        if not verify_password(password=password, password_hash=user.password_hash):
            raise InvalidPasswordError("Incorrect password")

        return user

    def get_user_profile(self, db: Session, user_id) -> UserProfileRead:
        user = self.repo.get_by_id(db=db, user_id=user_id)
        if user is None:
            raise UserNotFoundError("No user fround")

        nominations = self.nomination_repo.get_all_user_nominations(db=db, user=user)

        nominations_by_book_id: dict[int, list] = defaultdict(list)
        for nomination in nominations:
            nominations_by_book_id[nomination.book_id].append(nomination)

        nominated_books: list[UserProfileBookRead] = []

        for book_id, book_nominations in nominations_by_book_id.items():
            book = self.book_repo.get_by_id(db=db, book_id=book_id)
            if book is None:
                raise BookNotFoundError()

            meeting_dates: list[str] = []
            has_won = False

            for nomination in book_nominations:
                selection = self.book_selection_repo.get_by_id(db=db, selection_id=nomination.selection_id)
                if selection is None:
                    raise BookSelectionNotFoundError()

                meeting = self.meeting_repo.get_by_id(db=db, meeting_id=selection.meeting_id)
                if meeting is None:
                    raise MeetingNotFoundError()

                if meeting.scheduled_for is not None:
                    meeting_dates.append(meeting.scheduled_for.isoformat())
                else:
                    meeting_dates.append("Дата не назначена")

                if selection.winning_nomination_id == nomination.id:
                    has_won = True

            unique_meeting_dates = list(dict.fromkeys(meeting_dates))

            ratings: list[UserProfileBookRatingRead] = []
            if has_won:
                reviews = self.review_repo.get_all_for_book(db=db, book_id=book_id)

                for review in reviews:
                    if review.anonymous:
                        username = None
                    else:
                        username = self.repo.get_username_by_id(db=db, user_id=review.user_id)

                    ratings.append(UserProfileBookRatingRead(username=username, rating=review.rating))

            nominated_books.append(
                UserProfileBookRead(
                    book_id=book.id,
                    title=book.title,
                    author=book.author,
                    nomination_count=len(book_nominations),
                    meeting_dates=unique_meeting_dates,
                    has_won=has_won,
                    ratings=ratings,
                )
            )
        return UserProfileRead(
            id=user.id,
            username=user.username,
            telegram_login=user.telegram_login,
            role=user.role,
            nominated_books=nominated_books,
        )

    def get_all_users(self, db: Session):
        return self.repo.get_all_users(db=db)

user_service = UserService()