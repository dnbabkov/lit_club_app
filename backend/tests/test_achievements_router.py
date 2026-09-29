from io import BytesIO

from PIL import Image
import pytest
from sqlalchemy.orm import Session

from lit_club_app.backend.core.security import create_access_token
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.shark import service
from lit_club_app.backend.shark.models import Achievement
from lit_club_app.backend.shark.repository import AchievementRepository
from lit_club_app.backend.shark import router as achievements_router
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
    assert client.get("/users/owner/profile/achievements", headers=headers[1]).status_code == 200
    assert client.get("/achievements/10/image", headers=headers[1]).status_code == 200
    assert client.get("/users/owner/profile/achievements", headers=headers[0]).status_code == 200
    assert client.get("/achievements/10/image", headers=headers[0]).status_code == 200


def test_imported_filename_image(client, db_session, achievements):
    headers, data, _ = achievements
    db_session.get(Achievement, 10).path = "existing.png"
    db_session.commit()
    response = client.get("/achievements/10/image", headers=headers[0])
    assert response.status_code == 200
    assert response.content == data


def test_base_dir_relative_legacy_image_is_read(client, db_session, achievements, monkeypatch, tmp_path):
    headers, data, _ = achievements
    legacy_root = tmp_path / "tg_bot" / "achievements"
    legacy_root.mkdir(parents=True)
    image = legacy_root / "existing.png"
    image.write_bytes(data)
    monkeypatch.setattr(achievements_router, "BASE_DIR", tmp_path)
    monkeypatch.setattr(service, "achievements_path", legacy_root)
    db_session.get(Achievement, 10).path = "tg_bot/achievements/existing.png"
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


def test_achievement_directory_is_authenticated_exact_public_payload_and_includes_inactive_admins(
    client, db_session, achievements
):
    headers, _, _ = achievements
    owner = db_session.get(User, db_session.get(Achievement, 10).user_id)
    owner.role = Roles.ADMIN
    owner.is_active = False
    inactive = User(id=30, username="inactive", tg_id=333, is_active=False)
    db_session.add(inactive)
    db_session.commit()

    response = client.get("/users/achievement-directory", headers=headers[1])

    assert response.status_code == 200
    assert response.json() == [
        {"id": owner.id, "username": "owner"},
        {"id": db_session.get(User, 2).id, "username": "other"},
        {"id": inactive.id, "username": "inactive"},
    ]
    assert all(set(item) == {"id", "username"} for item in response.json())
    assert client.get("/users/owner/profile/achievements", headers=headers[1]).status_code == 200
    assert client.get("/achievements/10/image", headers=headers[1]).status_code == 200
    assert client.get("/users/achievement-directory").status_code == 401


def test_achievement_directory_excludes_dev_admin_for_dev_admin_and_other_callers(client, db_session, achievements):
    headers, _, _ = achievements
    dev_admin = User(id=30, username="dev_admin", tg_id=333, role=Roles.ADMIN)
    db_session.add(dev_admin)
    db_session.commit()
    dev_admin_header = {"Authorization": "Bearer " + create_access_token({
        "sub": str(dev_admin.id), "tg_id": str(dev_admin.tg_id), "auth_method": "telegram",
    })}

    for request_headers in (dev_admin_header, headers[0], headers[1]):
        response = client.get("/users/achievement-directory", headers=request_headers)
        assert response.status_code == 200
        assert "dev_admin" not in {user["username"] for user in response.json()}


def test_inactive_viewer_cannot_use_directory_or_achievement_routes(client, db_session, achievements):
    headers, _, _ = achievements
    viewer = db_session.get(User, db_session.get(Achievement, 10).giver_id)
    viewer.is_active = False
    db_session.commit()

    assert client.get("/users/achievement-directory", headers=headers[1]).status_code == 403
    assert client.get("/users/owner/profile/achievements", headers=headers[1]).status_code == 403
    assert client.get("/achievements/10/image", headers=headers[1]).status_code == 403


def test_achievement_directory_keeps_full_user_management_protected(client, achievements):
    headers, _, _ = achievements

    assert client.get("/users/", headers=headers[0]).status_code == 403
    assert client.get("/users/public", headers=headers[0]).status_code == 200


def _multipart_image(data=None, filename="badge.png", content_type="image/png"):
    if data is None:
        output = BytesIO()
        Image.new("RGBA", (3, 2), (10, 20, 30, 255)).save(output, "PNG")
        data = output.getvalue()
    return {"image": (filename, data, content_type)}


def _users_and_headers(db_session):
    giver = User(id=101, username="giver", tg_id=1001)
    recipient = User(id=102, username="recipient", tg_id=1002, role=Roles.MODERATOR)
    admin = User(id=103, username="admin", tg_id=1003, role=Roles.ADMIN)
    db_session.add_all([giver, recipient, admin])
    db_session.commit()
    def header(user):
        return {"Authorization": "Bearer " + create_access_token({
            "sub": str(user.id), "tg_id": str(user.tg_id), "auth_method": "telegram",
        })}
    return giver, recipient, admin, header


def test_create_derives_giver_and_returns_exact_payload_for_any_existing_role(client, db_session, monkeypatch, tmp_path):
    giver, recipient, _, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)

    response = client.post(
        "/achievements", headers=header(giver),
        data={"recipient_id": str(recipient.id), "title": "  Title  ", "description": "\nDetails\t"},
        files=_multipart_image(),
    )

    assert response.status_code == 201
    assert response.json().keys() == {"id", "image_url", "giver", "title", "description"}
    assert response.json()["giver"] == {"id": giver.id, "username": "giver"}
    assert response.json()["title"] == "Title"
    assert response.json()["description"] == "Details"
    row = db_session.get(Achievement, response.json()["id"])
    assert row.giver_id == giver.id
    assert row.user_id == recipient.id
    assert not row.path.startswith("/")
    assert (tmp_path / row.path).is_file()


def test_create_stores_pillow_composite_with_supplied_metadata(client, db_session, monkeypatch, tmp_path):
    giver, recipient, _, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)

    first = client.post(
        "/achievements", headers=header(giver),
        data={"recipient_id": str(recipient.id), "title": "First title", "description": "First description"},
        files=_multipart_image(),
    )
    second = client.post(
        "/achievements", headers=header(giver),
        data={"recipient_id": str(recipient.id), "title": "Second title", "description": "Second description"},
        files=_multipart_image(),
    )

    assert first.status_code == second.status_code == 201
    first_path = tmp_path / db_session.get(Achievement, first.json()["id"]).path
    second_path = tmp_path / db_session.get(Achievement, second.json()["id"]).path
    with Image.open(first_path) as first_image, Image.open(second_path) as second_image:
        assert first_image.format == second_image.format == "PNG"
        assert first_image.size == second_image.size == (2094, 1076)
    assert first_path.read_bytes() != _multipart_image()["image"][1]
    assert first_path.read_bytes() != second_path.read_bytes()


def test_create_cleans_composite_when_pillow_generator_fails(client, db_session, monkeypatch, tmp_path):
    giver, recipient, _, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)

    def fail_after_writing(picture, title, description, output_path=None):
        output_path.write_bytes(b"partial composite")
        raise RuntimeError("generator failure")

    monkeypatch.setattr(service.achievement_service, "create_achievement", fail_after_writing)
    with pytest.raises(RuntimeError):
        client.post(
            "/achievements", headers=header(giver),
            data={"recipient_id": str(recipient.id), "title": "Title", "description": "Description"},
            files=_multipart_image(),
        )

    assert db_session.query(Achievement).count() == 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("field,value", [
    ("title", "   "), ("description", "\t\n"),
    ("title", "x" * 201), ("description", "x" * 5001),
])
def test_create_rejects_blank_or_oversized_trimmed_metadata_without_file(client, db_session, monkeypatch, tmp_path, field, value):
    giver, recipient, _, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)
    data = {"recipient_id": str(recipient.id), "title": "Title", "description": "Description"}
    data[field] = value

    response = client.post("/achievements", headers=header(giver), data=data, files=_multipart_image())

    assert response.status_code == 422
    assert list(tmp_path.iterdir()) == []
    assert db_session.query(Achievement).count() == 0


def test_create_rejects_missing_recipient_and_does_not_write_upload(client, db_session, monkeypatch, tmp_path):
    giver, _, _, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)
    response = client.post("/achievements", headers=header(giver), data={
        "recipient_id": "99999", "title": "Title", "description": "Description",
    }, files=_multipart_image())
    assert response.status_code == 404
    assert list(tmp_path.iterdir()) == []


def test_create_requires_active_authenticated_giver_and_ignores_spoofed_giver_field(client, db_session, monkeypatch, tmp_path):
    giver, recipient, admin, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)
    inactive = db_session.get(User, giver.id)
    inactive.is_active = False
    db_session.commit()
    denied = client.post("/achievements", headers=header(giver), data={
        "recipient_id": str(recipient.id), "giver_id": str(admin.id),
        "title": "Title", "description": "Description",
    }, files=_multipart_image())
    assert denied.status_code == 403
    assert list(tmp_path.iterdir()) == []

    inactive.is_active = True
    db_session.commit()
    created = client.post("/achievements", headers=header(giver), data={
        "recipient_id": str(recipient.id), "giver_id": str(admin.id),
        "title": "Title", "description": "Description",
    }, files=_multipart_image())
    assert created.status_code == 201
    assert created.json()["giver"]["id"] == giver.id


@pytest.mark.parametrize("payload,filename,content_type", [
    (b"not an image", "bad.png", "image/png"),
    (b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", "bad.svg", "image/svg+xml"),
    (b"x" * (20 * 1024 * 1024 + 1), "huge.png", "image/png"),
])
def test_create_rejects_corrupt_svg_and_oversized_uploads(client, db_session, monkeypatch, tmp_path, payload, filename, content_type):
    giver, recipient, _, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)
    response = client.post("/achievements", headers=header(giver), data={
        "recipient_id": str(recipient.id), "title": "Title", "description": "Description",
    }, files=_multipart_image(payload, filename, content_type))
    assert response.status_code in {400, 413}
    assert list(tmp_path.iterdir()) == []


def test_create_rejects_decompression_bomb_without_writing_file(client, db_session, monkeypatch, tmp_path):
    giver, recipient, _, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)
    bomb = BytesIO()
    Image.new("RGB", (10001, 1), "red").save(bomb, "PNG")
    response = client.post("/achievements", headers=header(giver), data={
        "recipient_id": str(recipient.id), "title": "Title", "description": "Description",
    }, files=_multipart_image(bomb.getvalue()))
    assert response.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_create_rolls_back_database_and_cleans_upload_when_repository_fails(client, db_session, monkeypatch, tmp_path):
    giver, recipient, _, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)
    def fail(*args, **kwargs):
        raise RuntimeError("database failure")
    monkeypatch.setattr("lit_club_app.backend.shark.router.AchievementRepository.create", fail)

    with pytest.raises(RuntimeError):
        client.post("/achievements", headers=header(giver), data={
            "recipient_id": str(recipient.id), "title": "Title", "description": "Description",
        }, files=_multipart_image())
    assert db_session.query(Achievement).count() == 0
    assert list(tmp_path.iterdir()) == []


def test_delete_requires_creator_or_admin_and_cleans_only_private_unshared_file(client, db_session, achievements, monkeypatch):
    headers, data, directory = achievements
    private = directory.parent / "private-achievements"
    private.mkdir()
    monkeypatch.setattr(service, "private_achievements_path", lambda: private)
    private_image = private / "managed.png"
    private_image.write_bytes(data)
    db_session.get(Achievement, 10).path = str(private_image)
    creator = db_session.get(User, db_session.get(Achievement, 10).giver_id)
    recipient = db_session.get(User, db_session.get(Achievement, 10).user_id)
    recipient.role = Roles.MODERATOR
    db_session.commit()
    assert creator.id == db_session.get(User, 2).id
    assert client.delete("/achievements/10", headers=headers[1]).status_code == 204
    assert not private_image.exists()
    assert db_session.get(Achievement, 10) is None

    # The recipient and moderator are not granted delete rights by ownership.
    db_session.add(Achievement(id=30, user_id=recipient.id, giver_id=creator.id, path=str(directory / "shared.png")))
    (directory / "shared.png").write_bytes(data)
    db_session.commit()
    assert client.delete("/achievements/30", headers=headers[1]).status_code == 204


def test_delete_recipient_moderator_denied_admin_allowed_and_missing_is_404(client, db_session, achievements):
    headers, data, directory = achievements
    recipient = db_session.get(User, db_session.get(Achievement, 10).user_id)
    recipient.role = Roles.MODERATOR
    db_session.commit()
    # headers[0] is the recipient; receiving an achievement grants no delete rights.
    assert client.delete("/achievements/10", headers=headers[0]).status_code == 403
    assert client.delete("/achievements/20", headers=headers[0]).status_code == 403
    admin = User(id=40, username="delete-admin", tg_id=4040, role=Roles.ADMIN)
    db_session.add(admin)
    db_session.commit()
    admin_header = {"Authorization": "Bearer " + create_access_token({
        "sub": str(admin.id), "tg_id": str(admin.tg_id), "auth_method": "telegram",
    })}
    assert client.delete("/achievements/20", headers=admin_header).status_code == 204
    assert client.delete("/achievements/99999", headers=admin_header).status_code == 404


def test_creator_can_delete_record_even_when_image_is_missing(client, db_session, achievements):
    headers, _, _ = achievements

    assert client.delete("/achievements/20", headers=headers[1]).status_code == 204
    assert db_session.get(Achievement, 20) is None


def test_repository_delete_rolls_back_when_commit_fails(db_session, achievements, monkeypatch):
    _, _, _ = achievements
    repository = AchievementRepository()
    original_commit = db_session.commit

    def fail_commit():
        raise RuntimeError("database failure")

    monkeypatch.setattr(db_session, "commit", fail_commit)
    with pytest.raises(RuntimeError):
        repository.delete_achievement(db_session, 10)

    monkeypatch.setattr(db_session, "commit", original_commit)
    assert db_session.get(Achievement, 10) is not None


def test_delete_never_unlinks_legacy_outside_or_shared_paths(client, db_session, achievements):
    headers, data, directory = achievements
    giver = db_session.get(User, db_session.get(Achievement, 10).giver_id)
    legacy = directory / "legacy.png"
    outside = directory.parent / "outside.png"
    shared = directory / "shared.png"
    for path in (legacy, outside, shared):
        path.write_bytes(data)
    db_session.add_all([
        Achievement(id=31, user_id=1, giver_id=giver.id, path="legacy.png"),
        Achievement(id=32, user_id=1, giver_id=giver.id, path=str(outside)),
        Achievement(id=33, user_id=1, giver_id=giver.id, path=str(shared)),
        Achievement(id=34, user_id=1, giver_id=giver.id, path=str(shared)),
    ])
    db_session.commit()
    for achievement_id in (31, 32, 33):
        assert client.delete(f"/achievements/{achievement_id}", headers=headers[1]).status_code == 204
    assert legacy.exists() and outside.exists() and shared.exists()
    assert client.delete("/achievements/34", headers=headers[1]).status_code == 204
    assert shared.exists()


def test_delete_does_not_unlink_private_file_shared_by_absolute_and_relative_legacy_records(
    client, db_session, achievements, monkeypatch
):
    headers, data, directory = achievements
    private = directory.parent / "private-shared"
    private.mkdir()
    monkeypatch.setattr(service, "private_achievements_path", lambda: private)
    shared = private / "same.png"
    shared.write_bytes(data)
    giver = db_session.get(User, db_session.get(Achievement, 10).giver_id)
    db_session.add_all([
        Achievement(id=41, user_id=1, giver_id=giver.id, path=str(shared)),
        Achievement(id=42, user_id=1, giver_id=giver.id, path="same.png"),
    ])
    db_session.commit()

    assert client.delete("/achievements/41", headers=headers[1]).status_code == 204
    assert shared.exists()


def test_repository_flushes_and_refreshes_before_commit(db_session):
    events = []
    original_flush = db_session.flush
    original_refresh = db_session.refresh
    original_commit = db_session.commit

    def flush(*args, **kwargs):
        events.append("flush")
        return original_flush(*args, **kwargs)

    def refresh(*args, **kwargs):
        events.append("refresh")
        return original_refresh(*args, **kwargs)

    def commit(*args, **kwargs):
        events.append("commit")
        return original_commit(*args, **kwargs)

    db_session.flush = flush
    db_session.refresh = refresh
    db_session.commit = commit
    row = AchievementRepository().create(db_session, 1, "legacy.png", 2, "Title", "Description")

    assert row.id is not None
    assert events == ["flush", "refresh", "commit"]


def test_precommit_refresh_failure_rolls_back_and_cleans_uploaded_file(
    client, db_session, monkeypatch, tmp_path
):
    giver, recipient, _, header = _users_and_headers(db_session)
    monkeypatch.setattr(service, "private_achievements_path", lambda: tmp_path)
    events = []
    original_commit = Session.commit
    original_refresh = Session.refresh

    def commit(session, *args, **kwargs):
        events.append("commit")
        return original_commit(session, *args, **kwargs)

    def refresh(session, instance, *args, **kwargs):
        if isinstance(instance, Achievement):
            events.append("refresh")
            raise RuntimeError("refresh failed before commit")
        return original_refresh(session, instance, *args, **kwargs)

    monkeypatch.setattr(Session, "commit", commit)
    monkeypatch.setattr(Session, "refresh", refresh)

    with pytest.raises(RuntimeError):
        client.post("/achievements", headers=header(giver), data={
            "recipient_id": str(recipient.id), "title": "Title", "description": "Description",
        }, files=_multipart_image())

    assert events == ["refresh"]
    assert db_session.query(Achievement).count() == 0
    assert list(tmp_path.iterdir()) == []
