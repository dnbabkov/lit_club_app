import pytest
from sqlalchemy.exc import IntegrityError

from lit_club_app.backend.core.security import verify_password
from lit_club_app.backend.users.models import User
from lit_club_app.backend.users.repository import UserRepository
from lit_club_app.backend.users.schemas import UserRead


def test_unlinked_accounts_can_coexist_without_telegram_names_or_passwords(db_session):
    users = [User(username="first"), User(username="second")]
    db_session.add_all(users)
    db_session.commit()

    for user in users:
        db_session.refresh(user)
        assert user.tg_id is None
        assert user.password_hash is None
        assert user.is_active is True
        assert UserRead.model_validate(user).telegram_login is None
        assert verify_password("anything", user.password_hash) is False


def test_linking_large_telegram_id_preserves_account(db_session):
    user = User(username="existing", telegram_login="reader", password_hash="legacy")
    db_session.add(user)
    db_session.commit()
    original_id = user.id
    original_role = user.role

    user.tg_id = 5_000_000_000
    db_session.commit()
    db_session.expire_all()

    linked = UserRepository().get_by_tg_id(db_session, 5_000_000_000)
    assert linked.id == original_id
    assert linked.role == original_role
    assert linked.password_hash == "legacy"
    assert linked.telegram_login == "reader"


def test_telegram_identity_cannot_belong_to_two_accounts(db_session):
    db_session.add(User(username="first", tg_id=5_000_000_000))
    db_session.commit()
    db_session.add(User(username="second", tg_id=5_000_000_000))

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert db_session.query(User).count() == 1


def test_inactive_account_flag_is_persisted(db_session):
    user = User(username="inactive", is_active=False)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.is_active is False
