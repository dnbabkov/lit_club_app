import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from pydantic import SecretStr

from lit_club_app.backend.core.config import settings
from lit_club_app.backend.core.security import create_access_token, decode_access_token
from lit_club_app.backend.users.models import User


BOT_TOKEN = "123456:test-bot-token"
TG_ID = 5_000_000_000


def signed_data(*, user=None, age=0, bot_token=BOT_TOKEN, **extra):
    fields = {
        "auth_date": str(int(time.time()) - age),
        "user": json.dumps(user if user is not None else {"id": TG_ID, "first_name": "Иван"}),
        **extra,
    }
    secret = hmac.digest(b"WebAppData", bot_token.encode(), "sha256")
    message = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    fields["hash"] = hmac.new(secret, message.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


@pytest.fixture(autouse=True)
def telegram_settings(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", SecretStr(BOT_TOKEN))
    monkeypatch.setattr(settings, "telegram_init_data_max_age_seconds", 300)


@pytest.fixture
def member(db_session):
    user = User(username="existing", telegram_login="old_name", tg_id=TG_ID)
    db_session.add(user)
    db_session.commit()
    return user


def login(client, init_data=None):
    return client.post("/users/auth/telegram", json={
        "init_data": signed_data() if init_data is None else init_data,
    })


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_preserves_existing_account_and_ignores_username(client, member, db_session):
    response = login(client, signed_data(user={"id": TG_ID, "username": "new_name"}, signature="extra-signature"))
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    payload = decode_access_token(token)
    assert payload["sub"] == str(member.id)
    assert payload["tg_id"] == str(TG_ID)
    assert payload["auth_method"] == "telegram"
    me = client.get("/users/me", headers=headers(token))
    assert me.status_code == 200
    assert me.json()["id"] == member.id
    assert db_session.query(User).count() == 1
    db_session.refresh(member)
    assert member.telegram_login == "old_name"


def test_unknown_user_is_not_created_even_with_matching_username(client, member, db_session):
    response = login(client, signed_data(user={"id": TG_ID + 1, "username": member.telegram_login}))
    assert response.status_code == 403
    assert db_session.query(User).count() == 1


def test_unknown_user_leaves_empty_database(client, db_session):
    assert login(client).status_code == 403
    assert db_session.query(User).count() == 0


def test_no_username_required(client, member):
    assert login(client).status_code == 200


@pytest.mark.parametrize("data", [
    lambda: signed_data(bot_token="different-bot"),
    lambda: signed_data(age=301),
    lambda: signed_data(age=-120),
    lambda: signed_data() + "&auth_date=1",
    lambda: signed_data() + "&hash=" + "0" * 64,
    lambda: signed_data() + "&user=%ZZ",
    lambda: signed_data().replace("5000000000", "5000000001"),
    lambda: "user=%7B%7D&auth_date=1",
    lambda: "hash=invalid&auth_date=not-a-number&user=null",
    lambda: signed_data(user={"id": True}),
    lambda: signed_data(user={"id": "5000000000"}),
    lambda: signed_data(user={"id": -1}),
    lambda: signed_data(user={"id": 2**63}),
    lambda: signed_data(user=[]),
    lambda: signed_data(auth_date="not-a-number"),
])
def test_invalid_data_is_rejected(client, member, data):
    assert login(client, data()).status_code == 401


def test_payload_limits(client):
    assert login(client, "").status_code == 422
    assert login(client, "x" * 16385).status_code == 422


@pytest.mark.parametrize("kwargs,reason", [
    ({"bot_token": "different-bot"}, "signature_mismatch"),
    ({"age": 301}, "expired"),
    ({"age": -120}, "auth_date_in_future"),
    ({"auth_date": "not-a-number"}, "malformed_data"),
])
def test_rejection_log_contains_safe_diagnostic_only(client, caplog, kwargs, reason):
    data = signed_data(**kwargs)
    assert login(client, data).status_code == 401
    assert f"reason={reason}" in caplog.text
    assert BOT_TOKEN not in caplog.text
    assert data not in caplog.text
    assert str(TG_ID) not in caplog.text


def test_missing_bot_token_fails_closed(client, member, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    assert login(client).status_code == 503


def test_disabling_account_revokes_session_and_login(client, member, db_session):
    token = login(client).json()["access_token"]
    member.is_active = False
    db_session.commit()
    assert login(client).status_code == 403
    assert client.get("/users/me", headers=headers(token)).status_code == 403


@pytest.mark.parametrize("new_id", [None, TG_ID + 1])
def test_changing_binding_revokes_session(client, member, db_session, new_id):
    token = login(client).json()["access_token"]
    member.tg_id = new_id
    db_session.commit()
    assert client.get("/users/me", headers=headers(token)).status_code == 401
    assert login(client).status_code == 403


def test_deleted_account_loses_access(client, member, db_session):
    token = login(client).json()["access_token"]
    db_session.delete(member)
    db_session.commit()
    assert client.get("/users/me", headers=headers(token)).status_code == 401


def test_legacy_and_unbound_tokens_are_rejected(client, member):
    for claims in [{"sub": str(member.id)}, {"sub": str(member.id), "auth_method": "telegram"}]:
        token = create_access_token(claims)
        assert client.get("/users/me", headers=headers(token)).status_code == 401


@pytest.mark.parametrize("method,path", [
    ("post", "/users/register"),
    ("post", "/users/login"),
    ("patch", "/users/me/profile/password"),
    ("patch", "/users/1/profile/password"),
])
def test_password_endpoints_are_removed(client, method, path):
    assert getattr(client, method)(path, json={}).status_code in (404, 405)
