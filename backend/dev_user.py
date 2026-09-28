"""Create the local development account: PYTHONPATH=.. python -m lit_club_app.backend.dev_user."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.core.config import settings
from lit_club_app.backend.db.session import SessionLocal
from lit_club_app.backend.users.models import User


def prepare_dev_user(db: Session) -> User:
    if not settings.dev_auth_allowed:
        raise ValueError("Set APP_ENV=development and DEV_AUTH_ENABLED=true first")
    user = db.scalar(select(User).where(User.username == "dev_admin"))
    if user is not None:
        if user.tg_id is not None or user.telegram_login is not None or user.role != Roles.ADMIN or not user.is_active:
            raise ValueError("dev_admin already exists with different settings; account was not changed")
        return user
    user = User(username="dev_admin", role=Roles.ADMIN, is_active=True)
    db.add(user)
    db.commit()
    return user


def main():
    with SessionLocal() as db:
        user = prepare_dev_user(db)
        print(f"Development admin ready: {user.username}")
        print(f"DEV_AUTH_USER_ID={user.id}")


if __name__ == "__main__":
    main()
