import pytest
from pydantic import ValidationError

from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.core.config import Settings, settings
from lit_club_app.backend.core.security import create_access_token, decode_access_token
from lit_club_app.backend.dev_user import prepare_dev_user
from lit_club_app.backend.users.models import User


@pytest.fixture
def dev_user(monkeypatch, db_session):
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "dev_auth_enabled", True)
    user = prepare_dev_user(db_session)
    monkeypatch.setattr(settings, "dev_auth_user_id", user.id)
    return user


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_dev_login_without_telegram(client, dev_user):
    response = client.post("/users/auth/dev")
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert decode_access_token(token)["auth_method"] == "dev"
    me = client.get("/users/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["id"] == dev_user.id
    assert me.json()["role"] == "admin"
    assert client.get("/users/", headers=auth_headers(token)).status_code == 200


@pytest.mark.parametrize("env,enabled", [("production", False), ("production", True), ("development", False)])
def test_disabled_dev_auth_rejects_login_and_token(client, dev_user, monkeypatch, env, enabled):
    token = client.post("/users/auth/dev").json()["access_token"]
    monkeypatch.setattr(settings, "app_env", env)
    monkeypatch.setattr(settings, "dev_auth_enabled", enabled)
    assert client.post("/users/auth/dev").status_code == 404
    assert client.get("/users/me", headers=auth_headers(token)).status_code == 401


def test_configuration_rejects_dev_auth_in_production():
    values = settings.model_dump()
    values.update(app_env="production", dev_auth_enabled=True)
    with pytest.raises(ValidationError, match="requires APP_ENV=development"):
        Settings.model_validate(values)


@pytest.mark.parametrize("user_id,expected", [(None, 503), (999999, 403)])
def test_missing_dev_user(client, dev_user, monkeypatch, user_id, expected):
    monkeypatch.setattr(settings, "dev_auth_user_id", user_id)
    assert client.post("/users/auth/dev").status_code == expected


def test_disabled_user_loses_login_and_session(client, dev_user, db_session):
    token = client.post("/users/auth/dev").json()["access_token"]
    dev_user.is_active = False
    db_session.commit()
    assert client.post("/users/auth/dev").status_code == 403
    assert client.get("/users/me", headers=auth_headers(token)).status_code == 403


def test_deleted_user_loses_session(client, dev_user, db_session):
    token = client.post("/users/auth/dev").json()["access_token"]
    db_session.delete(dev_user)
    db_session.commit()
    assert client.get("/users/me", headers=auth_headers(token)).status_code == 401


def test_only_configured_user_can_use_dev_token(client, dev_user, db_session, monkeypatch):
    token = client.post("/users/auth/dev").json()["access_token"]
    other = User(username="other")
    db_session.add(other)
    db_session.commit()
    other_token = create_access_token({"sub": str(other.id), "auth_method": "dev"})
    assert client.get("/users/me", headers=auth_headers(other_token)).status_code == 401
    monkeypatch.setattr(settings, "dev_auth_user_id", other.id)
    assert client.get("/users/me", headers=auth_headers(token)).status_code == 401


def test_dev_auth_preserves_role_checks(client, dev_user, db_session):
    dev_user.role = Roles.MEMBER
    db_session.commit()
    token = client.post("/users/auth/dev").json()["access_token"]
    assert client.get("/users/me", headers=auth_headers(token)).status_code == 200
    assert client.get("/users/", headers=auth_headers(token)).status_code == 403


def test_prepare_dev_user_is_repeatable(dev_user, db_session):
    assert prepare_dev_user(db_session).id == dev_user.id
    assert db_session.query(User).count() == 1
    assert dev_user.tg_id is None


def test_prepare_dev_user_does_not_overwrite_existing_account(dev_user, db_session):
    dev_user.role = Roles.MEMBER
    db_session.commit()
    with pytest.raises(ValueError, match="account was not changed"):
        prepare_dev_user(db_session)
    db_session.refresh(dev_user)
    assert dev_user.role == Roles.MEMBER


def test_prepare_dev_user_requires_dev_mode(monkeypatch, db_session):
    monkeypatch.setattr(settings, "dev_auth_enabled", False)
    with pytest.raises(ValueError, match="Set APP_ENV"):
        prepare_dev_user(db_session)
    assert db_session.query(User).count() == 0
