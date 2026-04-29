from sqlalchemy import select
from sqlalchemy.orm import Session

from lit_club_app.backend.users.models import User
from lit_club_app.backend.common.enums import Roles

class UserRepository:
    def get_by_id(self, db: Session, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def get_username_by_id(self, db: Session, user_id: int) -> str | None:
        statement = select(User.username).where(User.id == user_id)
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def get_by_username(self, db: Session, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def get_by_telegram_login(self, db: Session, telegram_login: str) -> User | None:
        statement = select(User).where(User.telegram_login == telegram_login)
        result = db.execute(statement)
        return result.scalar_one_or_none()
    def create(self, db: Session, username: str, telegram_login: str, password_hash: str, role: Roles = Roles.MEMBER) -> User:

        user = User(username=username, telegram_login=telegram_login, password_hash=password_hash, role=role)
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception:
            db.rollback()
            raise