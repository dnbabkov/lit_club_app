from sqlalchemy import select, Sequence
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

    def get_by_tg_id(self, db: Session, tg_id: int) -> User | None:
        statement = select(User).where(User.tg_id == tg_id)
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

    def get_all_users(self, db: Session) -> Sequence[User]:
        statement = select(User).order_by(User.username)
        result = db.execute(statement)
        return result.scalars().all()

    def get_all_non_admin_users(self, db: Session) -> Sequence[User]:
        statement = (
            select(User)
            .where(User.role != Roles.ADMIN)
            .order_by(User.username)
        )
        result = db.execute(statement)
        return result.scalars().all()

    def update_user_password(self, db: Session, user: User, password_hash: str) -> User:
        try:
            user.password_hash = password_hash
            db.commit()
            db.refresh(user)
            return user
        except Exception:
            db.rollback()
            raise

    def get_user_role(self, db: Session, tg_id: str):
        statement = select(User.role).where(User.tg_id == tg_id)
        result = db.execute(statement)
        return result.scalars().all()

    def get_user_id_by_tg_id(self, db: Session, tg_id: str):
        statement = select(User.id).where(User.tg_id == tg_id)
        result = db.execute(statement)
        return result.scalars().all()[0]
