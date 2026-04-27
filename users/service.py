from sqlalchemy.orm import Session

from lit_club_app.users.models import User
from lit_club_app.users.schemas import UserRegister, UserLogin

from lit_club_app.common.enums import Roles

from lit_club_app.users.repository import UserRepository

from lit_club_app.core.security import hash_password, verify_password
from lit_club_app.core.exceptions import (
    UsernameAlreadyExistsError,
    TelegramLoginAlreadyExistsError,
    UserNotFoundError,
    InvalidPasswordError, EmptyTelegramLoginError,
)

class UserService:
    def __init__(self):
        self.repo = UserRepository()

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

user_service = UserService()