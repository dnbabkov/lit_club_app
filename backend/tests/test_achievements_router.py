from io import BytesIO

from PIL import Image
import pytest

from lit_club_app.backend.core.security import create_access_token
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.shark import service
from lit_club_app.backend.shark.models import Achievement
from lit_club_app.backend.users.models import User


@pytest.fixture
def achievements(db_session, tmp_path, monkeypatch):
    directory = tmp_path / "achievements"
    directory.mkdir()
    monkeypatch.setattr(service, "achievements_path", directory)
    users = [User(username="owner", tg_id=111), User(username="other", tg_id=222)]
    db_session.add_all(users)
    db_session.flush()
    headers = [{"Authorization": "Bearer " + create_access_token({
        "sub": str(user.id), "tg_id": str(user.tg_id), "auth_method": "telegram",
    })} for user in users]
    data = BytesIO()
    Image.new("RGB", (4, 4), "red").save(data, "PNG")
    image = directory / "existing.png"
    image.write_bytes(data.getvalue())
    # Explicit IDs: the production BigInteger PK does not autoincrement in SQLite.
    db_session.add_all([
        Achievement(id=10, user_id=users[0].id, giver_id=users[1].id, path=str(image)),
        Achievement(id=20, user_id=users[0].id, giver_id=users[1].id, path=str(directory / "missing.png")),
    ])
    db_session.commit()
    return headers, data.getvalue(), directory


def test_only_own_achievements_newest_first(client, db_session, achievements):
    headers, _, _ = achievements
    giver = db_session.get(User, db_session.get(Achievement, 10).giver_id)
    response = client.get("/achievements/me", headers=headers[0])
    assert response.status_code == 200
    assert response.json() == [
        {"id": 20, "image_url": "/achievements/20/image", "giver": {"id": giver.id, "username": "other"}},
        {"id": 10, "image_url": "/achievements/10/image", "giver": {"id": giver.id, "username": "other"}},
    ]
    assert client.get("/achievements/me", headers=headers[1]).json() == []
    assert client.get("/achievements/me").status_code == 401


def test_image_visible_to_authenticated_profile_viewers(client, achievements):
    headers, data, _ = achievements
    response = client.get("/achievements/10/image", headers=headers[0])
    assert response.status_code == 200
    assert response.content == data
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "private, no-store"
    assert client.get("/achievements/10/image", headers=headers[1]).content == data
    assert client.get("/achievements/10/image").status_code == 401


def test_profile_achievement_routes(client, achievements):
    headers, _, _ = achievements
    own = client.get("/users/me/profile/achievements", headers=headers[0])
    other = client.get("/users/owner/profile/achievements", headers=headers[1])
    assert own.status_code == other.status_code == 200
    assert own.json() == other.json()
    assert [item["id"] for item in own.json()] == [20, 10]
    assert client.get("/users/other/profile/achievements", headers=headers[0]).json() == []
    assert client.get("/users/unknown/profile/achievements", headers=headers[0]).status_code == 404
    assert client.get("/users/me/profile/achievements").status_code == 401
    assert client.get("/users/owner/profile/achievements").status_code == 401


def test_admin_profile_achievements_visibility(client, db_session, achievements):
    headers, _, _ = achievements
    owner = db_session.get(User, db_session.get(Achievement, 10).user_id)
    owner.role = Roles.ADMIN
    db_session.commit()
    assert client.get("/users/owner/profile/achievements", headers=headers[1]).status_code == 404
    assert client.get("/achievements/10/image", headers=headers[1]).status_code == 404
    assert client.get("/users/owner/profile/achievements", headers=headers[0]).status_code == 200
    assert client.get("/achievements/10/image", headers=headers[0]).status_code == 200


def test_imported_filename_image(client, db_session, achievements):
    headers, data, _ = achievements
    db_session.get(Achievement, 10).path = "existing.png"
    db_session.commit()
    response = client.get("/achievements/10/image", headers=headers[0])
    assert response.status_code == 200
    assert response.content == data


def test_missing_achievement_or_file_returns_404(client, achievements):
    headers, _, _ = achievements
    assert client.get("/achievements/20/image", headers=headers[0]).status_code == 404
    assert client.get("/achievements/999/image", headers=headers[0]).status_code == 404


def test_image_cannot_escape_achievement_directory(client, db_session, achievements):
    headers, data, directory = achievements
    outside = directory.parent / "private.png"
    outside.write_bytes(data)
    achievement = db_session.get(Achievement, 10)
    achievement.path = str(outside)
    db_session.commit()
    assert client.get("/achievements/10/image", headers=headers[0]).status_code == 404
    link = directory / "link.png"
    link.symlink_to(outside)
    achievement.path = str(link)
    db_session.commit()
    assert client.get("/achievements/10/image", headers=headers[0]).status_code == 404


def test_removed_achievement_is_no_longer_accessible(client, db_session, achievements):
    headers, _, _ = achievements
    db_session.delete(db_session.get(Achievement, 10))
    db_session.commit()
    assert client.get("/achievements/10/image", headers=headers[0]).status_code == 404
    assert [item["id"] for item in client.get("/achievements/me", headers=headers[0]).json()] == [20]
