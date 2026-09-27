from contextlib import closing

from lit_club_app.backend.api.dependencies import get_db
from lit_club_app.backend.core.security import create_access_token
from lit_club_app.backend.users.models import User


def register_user(client, username: str, telegram_login: str) -> str:
    """Provision a member directly; public registration no longer exists.

    Domain router tests use a valid application JWT. Telegram signature and
    login behavior are exercised separately in test_telegram_auth.py.
    """
    with closing(client.app.dependency_overrides[get_db]()) as sessions:
        db = next(sessions)
        user = User(username=username, telegram_login=telegram_login)
        db.add(user)
        db.flush()
        user.tg_id = 5_000_000_000 + user.id
        db.commit()
        return create_access_token({
            "sub": str(user.id), "auth_method": "telegram", "tg_id": str(user.tg_id),
        })
