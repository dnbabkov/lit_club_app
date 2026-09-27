from io import BytesIO
import json

from PIL import Image
import pytest

from lit_club_app.backend.comics import service
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.core.security import create_access_token
from lit_club_app.backend.users.models import User


@pytest.fixture
def actors(db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(service, "storage_dir", lambda: tmp_path)
    result = {}
    for index, role in enumerate([Roles.ADMIN, Roles.MEMBER, Roles.MODERATOR], 1):
        user = User(username=role.value, tg_id=index, role=role)
        db_session.add(user)
        db_session.flush()
        token = create_access_token({"sub": str(user.id), "tg_id": str(user.tg_id), "auth_method": "telegram"})
        result[role.value] = {"Authorization": f"Bearer {token}"}
    db_session.commit()
    return result


def image(color="red"):
    data = BytesIO()
    Image.new("RGB", (8, 8), color).save(data, "PNG")
    return ("page.png", data.getvalue(), "image/png")


def save(client, auth, payload=None, files=None, chapter_id=None):
    return client.post(
        "/comics/chapters" + (f"/{chapter_id}" if chapter_id else ""), headers=auth,
        data={"payload": json.dumps(payload or {"title": "Глава", "number": 1})}, files=files,
    )


def test_visibility_includes_images_and_changes_immediately(client, actors):
    response = save(client, actors["admin"], {"title": "Тайная глава", "number": 2,
        "pages": [{"number": 1, "file_index": 0}]}, [("cover", image()), ("files", image())])
    assert response.status_code == 201, response.text
    chapter = response.json()
    path = f'/comics/chapters/{chapter["id"]}'
    urls = [path, chapter["cover_url"], chapter["pages"][0]["image_url"]]
    for url in urls:
        assert client.get(url).status_code == 401
        assert client.get(url, headers=actors["member"]).status_code == 404
        assert client.get(url, headers=actors["moderator"]).status_code == 404
        assert client.get(url, headers=actors["admin"]).status_code == 200
    assert client.get("/comics/chapters", headers=actors["member"]).json() == []
    assert len(client.get("/comics/chapters", headers=actors["admin"]).json()) == 1
    payload = {"title": chapter["title"], "number": 2, "is_public": True,
               "pages": [{"id": chapter["pages"][0]["id"], "number": 1}]}
    assert save(client, actors["admin"], payload, chapter_id=chapter["id"]).status_code == 200
    for url in urls:
        response = client.get(url, headers=actors["member"])
        assert response.status_code == 200
        if url != path:
            assert response.headers["cache-control"] == "private, no-store"
    payload["is_public"] = False
    save(client, actors["admin"], payload, chapter_id=chapter["id"])
    assert client.get(urls[-1], headers=actors["member"]).status_code == 404


@pytest.mark.parametrize("actor,status", [("member", 403), ("moderator", 403), (None, 401)])
def test_only_admin_can_write(client, actors, actor, status):
    auth = actors[actor] if actor else {}
    assert save(client, auth).status_code == status
    assert save(client, auth, chapter_id=999).status_code == status


def test_reorder_replace_append_and_remove_pages(client, actors, tmp_path):
    chapter = save(client, actors["admin"], {"title": "First", "number": 5,
        "pages": [{"number": 2, "file_index": 0}, {"number": 1, "file_index": 1}]},
        [("files", image("red")), ("files", image("blue"))]).json()
    first, second = chapter["pages"]
    payload = {"title": "Renamed", "number": 1, "pages": [
        {"id": first["id"], "number": 3},
        {"id": second["id"], "number": 1, "file_index": 0},
        {"number": 2, "file_index": 1},
    ]}
    response = save(client, actors["admin"], payload, [("files", image("green")), ("files", image())], chapter["id"])
    assert response.status_code == 200, response.text
    updated = response.json()
    assert [page["number"] for page in updated["pages"]] == [1, 2, 3]
    assert updated["pages"][0]["id"] == second["id"]
    assert updated["pages"][0]["image_url"] != second["image_url"]
    assert len(list(tmp_path.iterdir())) == 3
    assert updated["title"] == "Renamed" and updated["number"] == 1
    assert save(client, actors["admin"], chapter_id=chapter["id"]).json()["pages"] == []
    assert list(tmp_path.iterdir()) == []


def test_failed_upload_rolls_back_database_and_files(client, actors, tmp_path):
    chapter = save(client, actors["admin"]).json()
    response = save(client, actors["admin"], {"title": "Changed", "number": 2,
        "pages": [{"number": 1, "file_index": 0}, {"number": 2, "file_index": 1}]},
        [("cover", image()), ("files", image()), ("files", ("bad.png", b"invalid", "image/png"))], chapter["id"])
    assert response.status_code == 400
    assert list(tmp_path.iterdir()) == []
    persisted = client.get(f'/comics/chapters/{chapter["id"]}', headers=actors["admin"]).json()
    assert persisted == chapter


@pytest.mark.parametrize("payload", [
    {"title": " ", "number": 1}, {"title": "A", "number": 0},
    {"title": "A", "number": 1, "pages": [{"number": 1}, {"number": 1}]},
])
def test_invalid_metadata(client, actors, payload):
    assert save(client, actors["admin"], payload).status_code == 422


def test_foreign_page_and_missing_upload_are_rejected(client, actors):
    first = save(client, actors["admin"], {"title": "A", "number": 2,
        "pages": [{"number": 1, "file_index": 0}]}, [("files", image())]).json()
    second = save(client, actors["admin"]).json()
    for page in [{"id": first["pages"][0]["id"], "number": 1}, {"number": 1}, {"number": 1, "file_index": 0}]:
        assert save(client, actors["admin"], {"title": "B", "number": 1, "pages": [page]}, chapter_id=second["id"]).status_code == 400
    chapters = client.get("/comics/chapters", headers=actors["admin"]).json()
    assert [chapter["number"] for chapter in chapters] == [1, 2]
    assert client.get(f'/comics/chapters/{second["id"]}/pages/{first["pages"][0]["id"]}/image', headers=actors["admin"]).status_code == 404
