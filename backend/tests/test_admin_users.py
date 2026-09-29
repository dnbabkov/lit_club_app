import pytest

from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.core.security import create_access_token
from lit_club_app.backend.users.models import User


def account(db, name, tg_id, role=Roles.MEMBER):
    user = User(username=name, tg_id=tg_id, role=role)
    db.add(user)
    db.commit()
    return user


def headers(user):
    token = create_access_token({"sub": str(user.id), "tg_id": str(user.tg_id), "auth_method": "telegram"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("role", [Roles.MEMBER, Roles.MODERATOR, None])
def test_admin_operations_are_protected(client, db_session, role):
    auth = headers(account(db_session, "actor", 11, role)) if role else {}
    for method, path, kwargs in [
        ("get", "/users/", {}),
        ("post", "/users/", {"json": {"username": "new", "tg_id": "12"}}),
        ("patch", "/users/999", {"json": {"username": "new", "tg_id": "12"}}),
    ]:
        assert getattr(client, method)(path, headers=auth, **kwargs).status_code == (403 if role else 401)


def test_create_and_edit_preserve_identity_role_and_revoke_old_binding(client, db_session):
    admin = account(db_session, "admin", 11, Roles.ADMIN)
    response = client.post("/users/", headers=headers(admin), json={
        "username": " New member ", "tg_id": "9007199254740993", "telegram_login": " @Reader "})
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["tg_id"] == "9007199254740993"
    assert data["telegram_login"] == "reader"
    assert data["username"] == "New member"
    user = db_session.get(User, data["id"])
    assert user.password_hash is None
    assert user.role == Roles.MEMBER
    old_headers = headers(user)
    response = client.patch(f"/users/{user.id}", headers=headers(admin), json={
        "username": "Renamed", "tg_id": "123456", "telegram_login": None})
    assert response.status_code == 200, response.text
    assert response.json()["id"] == user.id
    assert response.json()["role"] == "member"
    assert client.get("/users/me", headers=old_headers).status_code == 401
    assert len(client.get("/users/", headers=headers(admin)).json()) == 2


@pytest.mark.parametrize("field,value", [("username", "taken"), ("tg_id", "22"), ("telegram_login", "@READER")])
def test_conflicts_do_not_modify_existing_account(client, db_session, field, value):
    admin = account(db_session, "admin", 11, Roles.ADMIN)
    taken = account(db_session, "taken", 22)
    taken.telegram_login = "Reader"
    db_session.commit()
    target = account(db_session, "target", 33)
    payload = {"username": "changed", "tg_id": "44", "telegram_login": "another", field: value}
    for method, path in [("post", "/users/"), ("patch", f"/users/{target.id}")]:
        assert getattr(client, method)(path, headers=headers(admin), json=payload).status_code == 409
    db_session.refresh(target)
    assert target.username == "target" and target.tg_id == 33


@pytest.mark.parametrize("changes", [
    {"username": "   "}, {"tg_id": True}, {"tg_id": 1.5}, {"tg_id": "-1"},
    {"tg_id": "9223372036854775808"}, {"role": "admin"}, {"is_active": False},
    {"telegram_login": "invalid name"},
])
def test_invalid_fields_and_role_injection(client, db_session, changes):
    admin = account(db_session, "admin", 11, Roles.ADMIN)
    response = client.post("/users/", headers=headers(admin), json={"username": "new", "tg_id": "22", **changes})
    assert response.status_code == 422


def test_unbound_accounts_and_missing_target(client, db_session):
    admin = account(db_session, "admin", 11, Roles.ADMIN)
    payload = {"username": "unbound", "tg_id": None, "telegram_login": ""}
    response = client.post("/users/", headers=headers(admin), json=payload)
    assert response.status_code == 201
    assert response.json()["tg_id"] is None
    assert response.json()["telegram_login"] is None
    assert client.patch("/users/9999", headers=headers(admin), json=payload).status_code == 404


def test_user_can_rename_self(client, db_session):
    user = account(db_session, "old", 11)
    response = client.patch("/users/me", headers=headers(user), json={"username": "  new name  "})
    assert response.status_code == 200, response.text
    assert response.json()["username"] == "new name"
    db_session.refresh(user)
    assert user.username == "new name"


def test_user_cannot_rename_self_to_existing_username(client, db_session):
    account(db_session, "taken", 11)
    user = account(db_session, "old", 22)
    response = client.patch("/users/me", headers=headers(user), json={"username": "taken"})
    assert response.status_code == 409
    db_session.refresh(user)
    assert user.username == "old"
