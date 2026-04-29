from datetime import datetime, timedelta
from sqlalchemy import select

from lit_club_app.backend.users.models import User
from lit_club_app.backend.meetings.models import Meeting
from lit_club_app.backend.selections.models import BookSelection
from lit_club_app.backend.common.enums import Roles, MeetingStatus


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_user(client, username: str, telegram_login: str, password: str = "1234") -> str:
    response = client.post(
        "/users/register",
        json={
            "username": username,
            "telegram_login": telegram_login,
            "password": password,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def promote_to_moderator(db_session, telegram_login: str) -> None:
    user = db_session.execute(
        select(User).where(User.telegram_login == telegram_login)
    ).scalar_one()
    user.role = Roles.MODERATOR
    db_session.commit()


def create_meeting_direct(
    db_session,
    status: MeetingStatus = MeetingStatus.BOOK_SELECTION,
    scheduled_for: datetime | None = None,
    book_id: int | None = None,
) -> Meeting:
    meeting = Meeting(
        status=status,
        scheduled_for=scheduled_for,
        book_id=book_id,
    )
    db_session.add(meeting)
    db_session.commit()
    db_session.refresh(meeting)
    return meeting


def test_create_meeting_requires_moderator(client):
    user_token = register_user(client, "user", "user_login")

    response = client.post(
        "/meetings/",
        json={},
        headers=auth_headers(user_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Moderator access required"


def test_create_first_meeting_success(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    response = client.post(
        "/meetings/",
        json={},
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["status"] == "book_selection"
    assert data["book_id"] is None
    assert data["scheduled_for"] is None


def test_create_meeting_fails_if_latest_not_finished(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    create_meeting_direct(db_session, status=MeetingStatus.BOOK_SELECTION)

    response = client.post(
        "/meetings/",
        json={},
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Last meeting is not finished"


def test_get_latest_meeting_404_when_empty(client):
    user_token = register_user(client, "user", "user_login")

    response = client.get(
        "/meetings/latest",
        headers=auth_headers(user_token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Meeting not found"


def test_get_meeting_by_id_404(client):
    user_token = register_user(client, "user", "user_login")

    response = client.get(
        "/meetings/9999",
        headers=auth_headers(user_token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Meeting not found"


def test_get_all_meetings_returns_created_meetings(client, db_session):
    user_token = register_user(client, "user", "user_login")

    create_meeting_direct(db_session, status=MeetingStatus.FINISHED)
    create_meeting_direct(db_session, status=MeetingStatus.BOOK_SELECTION)

    response = client.get(
        "/meetings/",
        headers=auth_headers(user_token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 2
    # порядок по id desc
    assert data[0]["status"] == "book_selection"
    assert data[1]["status"] == "finished"


def test_get_meetings_by_year_filters_correctly(client, db_session):
    user_token = register_user(client, "user", "user_login")

    create_meeting_direct(
        db_session,
        status=MeetingStatus.SCHEDULED,
        scheduled_for=datetime(2025, 6, 10, 12, 0, 0),
    )
    create_meeting_direct(
        db_session,
        status=MeetingStatus.SCHEDULED,
        scheduled_for=datetime(2026, 7, 15, 18, 0, 0),
    )
    create_meeting_direct(
        db_session,
        status=MeetingStatus.SCHEDULED,
        scheduled_for=datetime(2026, 12, 25, 20, 0, 0),
    )

    response = client.get(
        "/meetings/year/2026",
        headers=auth_headers(user_token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 2
    assert all(item["status"] == "scheduled" for item in data)


def test_schedule_meeting_requires_moderator(client, db_session):
    user_token = register_user(client, "user", "user_login")
    meeting = create_meeting_direct(db_session, status=MeetingStatus.BOOK_SELECTION)

    future_dt = (datetime.now() + timedelta(days=7)).isoformat()

    response = client.patch(
        f"/meetings/{meeting.id}/schedule",
        json={"scheduled_for": future_dt},
        headers=auth_headers(user_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Moderator access required"


def test_schedule_meeting_404_when_missing(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    future_dt = (datetime.now() + timedelta(days=7)).isoformat()

    response = client.patch(
        "/meetings/9999/schedule",
        json={"scheduled_for": future_dt},
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Meeting not found"


def test_schedule_meeting_rejects_past_datetime(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    meeting = create_meeting_direct(db_session, status=MeetingStatus.BOOK_SELECTION)

    past_dt = (datetime.now() - timedelta(days=1)).isoformat()

    response = client.patch(
        f"/meetings/{meeting.id}/schedule",
        json={"scheduled_for": past_dt},
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Can't schedule before current date"


def test_schedule_meeting_success_sets_status_scheduled(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    meeting = create_meeting_direct(db_session, status=MeetingStatus.BOOK_SELECTION)

    future_dt = datetime.now() + timedelta(days=10)

    response = client.patch(
        f"/meetings/{meeting.id}/schedule",
        json={"scheduled_for": future_dt.isoformat()},
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "scheduled"
    assert data["scheduled_for"] is not None


def test_finish_meeting_requires_moderator(client, db_session):
    user_token = register_user(client, "user", "user_login")
    meeting = create_meeting_direct(db_session, status=MeetingStatus.SCHEDULED)

    response = client.post(
        f"/meetings/{meeting.id}/finish",
        headers=auth_headers(user_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Moderator access required"


def test_finish_meeting_wrong_status(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    meeting = create_meeting_direct(db_session, status=MeetingStatus.BOOK_SELECTION)

    response = client.post(
        f"/meetings/{meeting.id}/finish",
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Wrong meeting status"


def test_finish_meeting_success(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    meeting = create_meeting_direct(db_session, status=MeetingStatus.SCHEDULED)

    response = client.post(
        f"/meetings/{meeting.id}/finish",
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "finished"


def test_start_next_requires_moderator(client):
    user_token = register_user(client, "user", "user_login")

    response = client.post(
        "/meetings/start-next",
        headers=auth_headers(user_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Moderator access required"


def test_start_next_with_no_meetings_creates_meeting_and_selection(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    response = client.post(
        "/meetings/start-next",
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert "meeting" in data
    assert "selection_id" in data
    assert data["meeting"]["status"] == "book_selection"
    assert data["selection_id"] is not None

    selection = db_session.execute(
        select(BookSelection).where(BookSelection.id == data["selection_id"])
    ).scalar_one()
    assert selection.meeting_id == data["meeting"]["id"]


def test_start_next_fails_if_latest_meeting_not_started(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    create_meeting_direct(db_session, status=MeetingStatus.BOOK_SELECTION)

    response = client.post(
        "/meetings/start-next",
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Can't start next before last one is scheduled"


def test_start_next_finishes_scheduled_meeting_and_creates_new_one(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    old_meeting = create_meeting_direct(
        db_session,
        status=MeetingStatus.SCHEDULED,
        scheduled_for=datetime.now() + timedelta(days=2),
    )

    response = client.post(
        "/meetings/start-next",
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 200, response.text
    data = response.json()

    new_meeting_id = data["meeting"]["id"]
    selection_id = data["selection_id"]

    assert data["meeting"]["status"] == "book_selection"
    assert new_meeting_id != old_meeting.id
    assert selection_id is not None

    db_session.expire_all()

    refreshed_old = db_session.execute(
        select(Meeting).where(Meeting.id == old_meeting.id)
    ).scalar_one()
    refreshed_new = db_session.execute(
        select(Meeting).where(Meeting.id == new_meeting_id)
    ).scalar_one()
    selection = db_session.execute(
        select(BookSelection).where(BookSelection.id == selection_id)
    ).scalar_one()

    assert refreshed_old.status == MeetingStatus.FINISHED
    assert refreshed_new.status == MeetingStatus.BOOK_SELECTION
    assert selection.meeting_id == refreshed_new.id