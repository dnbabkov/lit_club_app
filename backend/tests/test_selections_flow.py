from sqlalchemy import select

from lit_club_app.users.models import User
from lit_club_app.books.models import Book
from lit_club_app.meetings.models import Meeting
from lit_club_app.selections.models import BookSelection, WinnerSelectionSession
from lit_club_app.common.enums import Roles, MeetingStatus, BookSelectionStatus, WinnerSelectionStatus

import pytest


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


def create_meeting(db_session) -> int:
    meeting = Meeting(
        status=MeetingStatus.BOOK_SELECTION,
        book_id=None,
        scheduled_for=None,
    )
    db_session.add(meeting)
    db_session.commit()
    db_session.refresh(meeting)
    return meeting.id


def ensure_books_have_descriptions(db_session) -> None:
    books = db_session.execute(select(Book)).scalars().all()
    for book in books:
        if book.description is None:
            book.description = f"Description for {book.title}"
    db_session.commit()


def get_selection_id_from_response(response_json: dict) -> int:
    return response_json["id"]


def get_session_id_from_state(response_json: dict) -> int:
    return response_json["session_id"]


def get_nomination_ids(client, selection_id: int, token: str) -> list[int]:
    response = client.get(
        f"/selections/{selection_id}/nominations",
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()]


def test_create_selection_requires_moderator(client, db_session):
    user_token = register_user(client, "user", "user_login")
    meeting_id = create_meeting(db_session)

    response = client.post(
        "/selections/",
        json={"meeting_id": meeting_id},
        headers=auth_headers(user_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Moderator access required"


def test_user_cannot_nominate_twice(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    user_token = register_user(client, "user1", "user1_login")
    meeting_id = create_meeting(db_session)

    selection_response = client.post(
        "/selections/",
        json={"meeting_id": meeting_id},
        headers=auth_headers(moderator_token),
    )
    assert selection_response.status_code == 201, selection_response.text
    selection_id = get_selection_id_from_response(selection_response.json())

    first_nomination = client.post(
        f"/selections/{selection_id}/nominations",
        json={
            "selection_id": selection_id,
            "title": "Dune",
            "author": "Frank Herbert",
            "comment": "first",
        },
        headers=auth_headers(user_token),
    )
    assert first_nomination.status_code == 201, first_nomination.text

    second_nomination = client.post(
        f"/selections/{selection_id}/nominations",
        json={
            "selection_id": selection_id,
            "title": "1984",
            "author": "George Orwell",
            "comment": "second",
        },
        headers=auth_headers(user_token),
    )
    assert second_nomination.status_code == 409
    assert second_nomination.json()["detail"] == "User already has a nomination"


def test_vote_replaces_previous_votes(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    user1_token = register_user(client, "user1", "user1_login")
    user2_token = register_user(client, "user2", "user2_login")

    meeting_id = create_meeting(db_session)

    selection_response = client.post(
        "/selections/",
        json={"meeting_id": meeting_id},
        headers=auth_headers(moderator_token),
    )
    assert selection_response.status_code == 201, selection_response.text
    selection_id = get_selection_id_from_response(selection_response.json())

    r1 = client.post(
        f"/selections/{selection_id}/nominations",
        json={
            "selection_id": selection_id,
            "title": "Dune",
            "author": "Frank Herbert",
            "comment": "classic",
        },
        headers=auth_headers(user1_token),
    )
    assert r1.status_code == 201, r1.text

    r2 = client.post(
        f"/selections/{selection_id}/nominations",
        json={
            "selection_id": selection_id,
            "title": "1984",
            "author": "George Orwell",
            "comment": "dystopia",
        },
        headers=auth_headers(user2_token),
    )
    assert r2.status_code == 201, r2.text

    open_response = client.post(
        f"/selections/{selection_id}/open_voting",
        headers=auth_headers(moderator_token),
    )
    assert open_response.status_code == 200, open_response.text

    nomination_ids = get_nomination_ids(client, selection_id, user1_token)
    assert len(nomination_ids) == 2

    first_vote = client.post(
        f"/selections/{selection_id}/votes",
        json={
            "selection_id": selection_id,
            "nomination_ids": [nomination_ids[0]],
        },
        headers=auth_headers(user1_token),
    )
    assert first_vote.status_code == 200, first_vote.text

    second_vote = client.post(
        f"/selections/{selection_id}/votes",
        json={
            "selection_id": selection_id,
            "nomination_ids": [nomination_ids[1]],
        },
        headers=auth_headers(user1_token),
    )
    assert second_vote.status_code == 200, second_vote.text

    counts_response = client.get(
        f"/selections/{selection_id}/votes",
        headers=auth_headers(user1_token),
    )
    assert counts_response.status_code == 200, counts_response.text

    counts = {
        item["nomination_id"]: item["vote_count"]
        for item in counts_response.json()
    }

    assert counts[nomination_ids[0]] == 0
    assert counts[nomination_ids[1]] == 1


def test_full_selection_flow(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    user1_token = register_user(client, "user1", "user1_login")
    user2_token = register_user(client, "user2", "user2_login")

    meeting_id = create_meeting(db_session)

    create_selection_response = client.post(
        "/selections/",
        json={"meeting_id": meeting_id},
        headers=auth_headers(moderator_token),
    )
    assert create_selection_response.status_code == 201, create_selection_response.text
    selection_id = get_selection_id_from_response(create_selection_response.json())

    nomination_1 = client.post(
        f"/selections/{selection_id}/nominations",
        json={
            "selection_id": selection_id,
            "title": "Dune",
            "author": "Frank Herbert",
            "comment": "classic",
        },
        headers=auth_headers(user1_token),
    )
    assert nomination_1.status_code == 201, nomination_1.text

    nomination_2 = client.post(
        f"/selections/{selection_id}/nominations",
        json={
            "selection_id": selection_id,
            "title": "1984",
            "author": "George Orwell",
            "comment": "dystopia",
        },
        headers=auth_headers(user2_token),
    )
    assert nomination_2.status_code == 201, nomination_2.text

    nominations_response = client.get(
        f"/selections/{selection_id}/nominations",
        headers=auth_headers(user1_token),
    )
    assert nominations_response.status_code == 200, nominations_response.text
    nomination_ids = [item["id"] for item in nominations_response.json()]
    assert len(nomination_ids) == 2

    open_response = client.post(
        f"/selections/{selection_id}/open_voting",
        headers=auth_headers(moderator_token),
    )
    assert open_response.status_code == 200, open_response.text
    assert open_response.json()["status"] == "voting_open"

    vote_1 = client.post(
        f"/selections/{selection_id}/votes",
        json={
            "selection_id": selection_id,
            "nomination_ids": [nomination_ids[0]],
        },
        headers=auth_headers(user1_token),
    )
    assert vote_1.status_code == 200, vote_1.text

    vote_2 = client.post(
        f"/selections/{selection_id}/votes",
        json={
            "selection_id": selection_id,
            "nomination_ids": [nomination_ids[0], nomination_ids[1]],
        },
        headers=auth_headers(user2_token),
    )
    assert vote_2.status_code == 200, vote_2.text

    counts_response = client.get(
        f"/selections/{selection_id}/votes",
        headers=auth_headers(user1_token),
    )
    assert counts_response.status_code == 200, counts_response.text
    counts = {
        item["nomination_id"]: item["vote_count"]
        for item in counts_response.json()
    }
    assert counts[nomination_ids[0]] == 2
    assert counts[nomination_ids[1]] == 1

    close_response = client.post(
        f"/selections/{selection_id}/close_voting",
        headers=auth_headers(moderator_token),
    )
    assert close_response.status_code == 200, close_response.text
    assert close_response.json()["status"] == "voting_closed"

    start_winner_response = client.post(
        f"/selections/{selection_id}/winner-selection/start",
        headers=auth_headers(moderator_token),
    )
    assert start_winner_response.status_code == 200, start_winner_response.text
    session_id = get_session_id_from_state(start_winner_response.json())

    state = start_winner_response.json()
    guard = 0
    while state["status"] != "ready_to_finalize":
        guard += 1
        assert guard < 10, "winner selection should finish in a few steps"

        advance_response = client.post(
            f"/selections/winner-selection/{session_id}/advance",
            headers=auth_headers(moderator_token),
        )
        assert advance_response.status_code == 200, advance_response.text
        state = advance_response.json()

    assert state["winner_nomination_id"] is not None

    ensure_books_have_descriptions(db_session)

    finalize_response = client.post(
        f"/selections/winner-selection/{session_id}/finalize",
        headers=auth_headers(moderator_token),
    )
    assert finalize_response.status_code == 200, finalize_response.text

    final_data = finalize_response.json()
    assert final_data["selection_id"] == selection_id
    assert final_data["winning_nomination_id"] is not None
    assert final_data["book_id"] is not None
    assert final_data["title"] in {"Dune", "1984"}
    assert final_data["author"] in {"Frank Herbert", "George Orwell"}
    assert isinstance(final_data["vote_count"], int)

    refreshed_selection = db_session.execute(
        select(BookSelection).where(BookSelection.id == selection_id)
    ).scalar_one()
    refreshed_meeting = db_session.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    ).scalar_one()
    refreshed_session = db_session.execute(
        select(WinnerSelectionSession).where(WinnerSelectionSession.id == session_id)
    ).scalar_one()

    assert refreshed_selection.status == BookSelectionStatus.WINNER_SELECTED
    assert refreshed_selection.winning_nomination_id is not None
    assert refreshed_meeting.book_id is not None
    assert refreshed_session.status == WinnerSelectionStatus.FINALIZED

def create_selection_as_moderator(client, db_session, moderator_token: str) -> int:
    meeting_id = create_meeting(db_session)
    response = client.post(
        "/selections/",
        json={"meeting_id": meeting_id},
        headers=auth_headers(moderator_token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_nomination_for_user(client, selection_id: int, token: str, title: str, author: str, comment: str):
    response = client.post(
        f"/selections/{selection_id}/nominations",
        json={
            "selection_id": selection_id,
            "title": title,
            "author": author,
            "comment": comment,
        },
        headers=auth_headers(token),
    )
    return response


@pytest.mark.parametrize(
    "method,path_builder",
    [
        ("post", lambda selection_id: "/selections/"),
        ("post", lambda selection_id: f"/selections/{selection_id}/open_voting"),
        ("post", lambda selection_id: f"/selections/{selection_id}/close_voting"),
        ("post", lambda selection_id: f"/selections/{selection_id}/winner-selection/start"),
    ],
)
def test_moderator_only_endpoints_require_moderator(client, db_session, method, path_builder):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "user", "user_login")

    selection_id = create_selection_as_moderator(client, db_session, moderator_token)

    path = path_builder(selection_id)
    if path == "/selections/":
        response = client.post(
            path,
            json={"meeting_id": create_meeting(db_session)},
            headers=auth_headers(user_token),
        )
    else:
        response = getattr(client, method)(
            path,
            headers=auth_headers(user_token),
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Moderator access required"


def test_cannot_open_voting_without_nominations(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    selection_id = create_selection_as_moderator(client, db_session, moderator_token)

    response = client.post(
        f"/selections/{selection_id}/open_voting",
        headers=auth_headers(moderator_token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Can't start an empty vote"


def test_cannot_nominate_twice_in_same_selection(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "user1", "user1_login")

    selection_id = create_selection_as_moderator(client, db_session, moderator_token)

    first = create_nomination_for_user(
        client, selection_id, user_token, "Dune", "Frank Herbert", "first"
    )
    assert first.status_code == 201, first.text

    second = create_nomination_for_user(
        client, selection_id, user_token, "1984", "George Orwell", "second"
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "User already has a nomination"


def test_cannot_edit_nomination_after_voting_open(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "user1", "user1_login")

    selection_id = create_selection_as_moderator(client, db_session, moderator_token)

    create_response = create_nomination_for_user(
        client, selection_id, user_token, "Dune", "Frank Herbert", "first"
    )
    assert create_response.status_code == 201, create_response.text

    open_response = client.post(
        f"/selections/{selection_id}/open_voting",
        headers=auth_headers(moderator_token),
    )
    assert open_response.status_code == 200, open_response.text

    edit_response = client.patch(
        f"/selections/{selection_id}/nominations/me",
        json={
            "title": "Foundation",
            "author": "Isaac Asimov",
            "comment": "changed",
        },
        headers=auth_headers(user_token),
    )
    assert edit_response.status_code == 409
    assert edit_response.json()["detail"] == "Nominations not open"

    comment_response = client.patch(
        f"/selections/{selection_id}/nominations/me/comment",
        json={"comment": "new comment"},
        headers=auth_headers(user_token),
    )
    assert comment_response.status_code == 409
    assert comment_response.json()["detail"] == "Nominations not open"


def test_cannot_vote_when_voting_not_open(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "user1", "user1_login")

    selection_id = create_selection_as_moderator(client, db_session, moderator_token)

    create_response = create_nomination_for_user(
        client, selection_id, user_token, "Dune", "Frank Herbert", "first"
    )
    assert create_response.status_code == 201, create_response.text
    nomination_id = create_response.json()["id"]

    vote_response = client.post(
        f"/selections/{selection_id}/votes",
        json={
            "selection_id": selection_id,
            "nomination_ids": [nomination_id],
        },
        headers=auth_headers(user_token),
    )
    assert vote_response.status_code == 409
    assert vote_response.json()["detail"] == "Voting is not open"


def test_cannot_vote_with_empty_nomination_ids(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "user1", "user1_login")

    selection_id = create_selection_as_moderator(client, db_session, moderator_token)

    create_response = create_nomination_for_user(
        client, selection_id, user_token, "Dune", "Frank Herbert", "first"
    )
    assert create_response.status_code == 201, create_response.text

    open_response = client.post(
        f"/selections/{selection_id}/open_voting",
        headers=auth_headers(moderator_token),
    )
    assert open_response.status_code == 200, open_response.text

    vote_response = client.post(
        f"/selections/{selection_id}/votes",
        json={
            "selection_id": selection_id,
            "nomination_ids": [],
        },
        headers=auth_headers(user_token),
    )
    assert vote_response.status_code == 400
    assert vote_response.json()["detail"] == "No nominations selected for voting"


def test_cannot_vote_for_nomination_from_other_selection(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user1_token = register_user(client, "user1", "user1_login")
    user2_token = register_user(client, "user2", "user2_login")

    selection_1 = create_selection_as_moderator(client, db_session, moderator_token)
    selection_2 = create_selection_as_moderator(client, db_session, moderator_token)

    nomination_1 = create_nomination_for_user(
        client, selection_1, user1_token, "Dune", "Frank Herbert", "first"
    )
    assert nomination_1.status_code == 201, nomination_1.text

    nomination_2 = create_nomination_for_user(
        client, selection_2, user2_token, "1984", "George Orwell", "second"
    )
    assert nomination_2.status_code == 201, nomination_2.text

    open_response = client.post(
        f"/selections/{selection_1}/open_voting",
        headers=auth_headers(moderator_token),
    )
    assert open_response.status_code == 200, open_response.text

    foreign_nomination_id = nomination_2.json()["id"]

    vote_response = client.post(
        f"/selections/{selection_1}/votes",
        json={
            "selection_id": selection_1,
            "nomination_ids": [foreign_nomination_id],
        },
        headers=auth_headers(user1_token),
    )
    assert vote_response.status_code == 400
    assert vote_response.json()["detail"] == "Nomination does not belong to this selection"


def test_cannot_close_voting_without_votes(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "user1", "user1_login")

    selection_id = create_selection_as_moderator(client, db_session, moderator_token)

    nomination_response = create_nomination_for_user(
        client, selection_id, user_token, "Dune", "Frank Herbert", "first"
    )
    assert nomination_response.status_code == 201, nomination_response.text

    open_response = client.post(
        f"/selections/{selection_id}/open_voting",
        headers=auth_headers(moderator_token),
    )
    assert open_response.status_code == 200, open_response.text

    close_response = client.post(
        f"/selections/{selection_id}/close_voting",
        headers=auth_headers(moderator_token),
    )
    assert close_response.status_code == 409
    assert close_response.json()["detail"] == "Selection has no votes"


def test_cannot_start_winner_selection_before_voting_closed(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    selection_id = create_selection_as_moderator(client, db_session, moderator_token)

    start_response = client.post(
        f"/selections/{selection_id}/winner-selection/start",
        headers=auth_headers(moderator_token),
    )
    assert start_response.status_code == 409
    assert start_response.json()["detail"] == "Winner selection can start only after voting is closed"


def test_cannot_advance_nonexistent_session(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")

    response = client.post(
        "/selections/winner-selection/9999/advance",
        headers=auth_headers(moderator_token),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Winner selection session not found"


def test_cannot_finalize_before_ready_to_finalize(client, db_session):
    moderator_token = register_user(client, "moderator", "moderator_login")
    promote_to_moderator(db_session, "moderator_login")
    user_token = register_user(client, "user1", "user1_login")

    selection_id = create_selection_as_moderator(client, db_session, moderator_token)

    nomination_response = create_nomination_for_user(
        client, selection_id, user_token, "Dune", "Frank Herbert", "first"
    )
    assert nomination_response.status_code == 201, nomination_response.text

    open_response = client.post(
        f"/selections/{selection_id}/open_voting",
        headers=auth_headers(moderator_token),
    )
    assert open_response.status_code == 200, open_response.text

    vote_response = client.post(
        f"/selections/{selection_id}/votes",
        json={
            "selection_id": selection_id,
            "nomination_ids": [nomination_response.json()["id"]],
        },
        headers=auth_headers(user_token),
    )
    assert vote_response.status_code == 200, vote_response.text

    close_response = client.post(
        f"/selections/{selection_id}/close_voting",
        headers=auth_headers(moderator_token),
    )
    assert close_response.status_code == 200, close_response.text

    start_response = client.post(
        f"/selections/{selection_id}/winner-selection/start",
        headers=auth_headers(moderator_token),
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["session_id"]

    finalize_response = client.post(
        f"/selections/winner-selection/{session_id}/finalize",
        headers=auth_headers(moderator_token),
    )
    assert finalize_response.status_code == 409
    assert finalize_response.json()["detail"] == "Winner selection session is not ready to finalize"