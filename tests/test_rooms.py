from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.domain.backend.models import CreateRoomModel, GetRoomModel, JoinRoomModel, Room, RoomPlayer, StartRoomModel
from app.domain.backend.services import create_room, get_room, join_room, start_room
from tests.factories import add_player, add_problem, add_room, attach, seat


def host_model(username="alex"):
    return CreateRoomModel(
        host_username=username,
        duration=30,
        difficulty="Easy",
        topics=["Array"],
        problem_count=2,
    )


@patch("app.domain.backend.services.lookup_leetcode_user")
@patch("app.domain.backend.services.add_problems_to_room")
def test_create_room(mock_add_problems, mock_lookup, db):
    mock_lookup.return_value = "alex"

    result = create_room(db, host_model())

    assert result["room_code"] is not None
    assert result["host_id"] is not None


@patch("app.domain.backend.services.add_problems_to_room", side_effect=ValueError("Not enough problems"))
@patch("app.domain.backend.services.lookup_leetcode_user", return_value="alex")
def test_create_room_rolls_back_when_problems_cannot_be_chosen(mock_lookup, mock_add_problems, db):
    with pytest.raises(ValueError, match="Not enough problems"):
        create_room(db, host_model())

    assert db.query(Room).count() == 0


def test_join_room_paths(db):
    host = add_player(db, "alex")
    created = datetime.now(timezone.utc) - timedelta(hours=2)
    room = add_room(db, host, created=created)
    seat(db, room, host)

    with patch("app.domain.backend.services.lookup_leetcode_user", return_value="sam"):
        with pytest.raises(HTTPException) as inactive:
            join_room(db, JoinRoomModel(username="sam", room_code="room01"))
    assert inactive.value.status_code == 400
    assert inactive.value.detail == "Room is inactive"

    fresh = add_room(db, host, code="FRESH1")
    seat(db, fresh, host)
    with patch("app.domain.backend.services.lookup_leetcode_user", return_value="sam"):
        joined = join_room(db, JoinRoomModel(username="sam", room_code="fresh1"))
    assert joined["player_id"] is not None

    with patch("app.domain.backend.services.lookup_leetcode_user", return_value="sam"):
        again = join_room(db, JoinRoomModel(username="sam", room_code="FRESH1"))
    assert again["player_id"] == joined["player_id"]

    with pytest.raises(HTTPException) as missing:
        join_room(db, JoinRoomModel(username="sam", room_code="NOPE00"))
    assert missing.value.status_code == 404

    finished = add_room(db, host, code="DONE01", status="Finished")
    with pytest.raises(HTTPException) as done:
        join_room(db, JoinRoomModel(username="sam", room_code="DONE01"))
    assert done.value.detail == "Room already finished"

    live = add_room(db, host, code="LIVE01", status="Active")
    with patch("app.domain.backend.services.lookup_leetcode_user", return_value="late"):
        late = join_room(db, JoinRoomModel(username="late", room_code="LIVE01"))
    seated = db.query(RoomPlayer).filter(RoomPlayer.player_id == late["player_id"]).one()
    assert seated.result == "In_Progress"

    with patch("app.domain.backend.services.get_or_create_player", side_effect=RuntimeError("db down")):
        with pytest.raises(RuntimeError, match="db down"):
            join_room(db, JoinRoomModel(username="sam", room_code="FRESH1"))


def test_start_room_paths(db):
    host = add_player(db, "alex")
    guest = add_player(db, "sam")
    created = datetime.now(timezone.utc) - timedelta(hours=2)
    expired = add_room(db, host, code="OLD001", created=created)
    seat(db, expired, host)
    seat(db, expired, guest)
    db.commit()

    with pytest.raises(HTTPException) as inactive:
        start_room(db, StartRoomModel(player_id=host.id, room_code="OLD001"))
    assert inactive.value.detail == "Room is inactive"

    waiting = add_room(db, host, code="WAIT01")
    seat(db, waiting, host)
    db.commit()
    with pytest.raises(HTTPException) as alone:
        start_room(db, StartRoomModel(player_id=host.id, room_code="WAIT01"))
    assert alone.value.detail == "Need at least 2 players"

    seat(db, waiting, guest)
    db.commit()
    with pytest.raises(HTTPException) as empty:
        start_room(db, StartRoomModel(player_id=host.id, room_code="WAIT01"))
    assert empty.value.detail == "No problems in room"

    with pytest.raises(HTTPException) as stranger:
        start_room(db, StartRoomModel(player_id=guest.id, room_code="WAIT01"))
    assert stranger.value.detail == "Host must start room"

    problem = add_problem(db)
    attach(db, waiting, problem)
    db.commit()
    started = start_room(db, StartRoomModel(player_id=host.id, room_code="wait01"))
    assert started["message"] == "Room started"
    assert db.get(Room, waiting.id).current_status == "Active"

    with pytest.raises(HTTPException) as twice:
        start_room(db, StartRoomModel(player_id=host.id, room_code="WAIT01"))
    assert twice.value.detail == "Room already started"

    with pytest.raises(HTTPException) as missing:
        start_room(db, StartRoomModel(player_id=host.id, room_code="NOPE00"))
    assert missing.value.status_code == 404

    boom = add_room(db, host, code="BOOM01")
    seat(db, boom, host)
    seat(db, boom, guest)
    attach(db, boom, problem)
    db.commit()
    with patch("app.domain.backend.services.utc_now", side_effect=[datetime.now(timezone.utc), RuntimeError("clock")]):
        with pytest.raises(RuntimeError, match="clock"):
            start_room(db, StartRoomModel(player_id=host.id, room_code="BOOM01"))


def test_get_room_polls_scores_and_finishes(db):
    with pytest.raises(HTTPException) as missing:
        get_room(db, GetRoomModel(room_code="NOPE00"))
    assert missing.value.status_code == 404

    now = datetime.now(timezone.utc)
    host = add_player(db, "alex")
    guest = add_player(db, "sam")
    problem = add_problem(db)
    room = add_room(
        db,
        host,
        code="LIVE01",
        status="Active",
        start=now - timedelta(minutes=5),
        end=now + timedelta(minutes=25),
    )
    host_seat = seat(db, room, host, result="In_Progress")
    seat(db, room, guest, result="In_Progress")
    attach(db, room, problem)
    db.commit()

    accepted = {
        "titleSlug": "two-sum",
        "timestamp": int((now - timedelta(minutes=1)).timestamp()),
        "statusDisplay": "Accepted",
    }

    def submissions(username):
        if username == "alex":
            return {"submissions": [accepted], "hidden": False}
        raise RuntimeError("timeout")

    with patch("app.domain.backend.services.get_leetcode_player_submissions", side_effect=submissions):
        state = get_room(db, GetRoomModel(room_code="live01"))

    assert state["status"] == "Active"
    assert state["problems"][0]["slug"] == "two-sum"
    scores = {player["username"]: player["score"] for player in state["players"]}
    assert scores["alex"] == 1
    assert "sam: timeout" in db.get(Room, room.id).poll_error

    hidden = add_room(db, host, code="HIDE01", status="Active", start=now - timedelta(minutes=5), end=now + timedelta(minutes=10))
    seat(db, hidden, host, result="In_Progress")
    with patch(
        "app.domain.backend.services.get_leetcode_player_submissions",
        return_value={"submissions": [], "hidden": True},
    ):
        get_room(db, GetRoomModel(room_code="HIDE01"))
    assert "private" in db.get(Room, hidden.id).poll_error

    over = add_room(
        db,
        host,
        code="OVER01",
        status="Active",
        start=now - timedelta(minutes=40),
        end=now - timedelta(minutes=1),
    )
    seat(db, over, host, score=2, result="In_Progress")
    seat(db, over, guest, score=2, result="In_Progress")
    with patch(
        "app.domain.backend.services.get_leetcode_player_submissions",
        return_value={"submissions": [], "hidden": False},
    ):
        finished = get_room(db, GetRoomModel(room_code="OVER01"))
    assert finished["status"] == "Finished"
    assert {player["result"] for player in finished["players"]} == {"Winner"}

    pending = add_room(db, host, code="PEND01", status="Finished", end=now - timedelta(minutes=1))
    seat(db, pending, host, score=0, result="In_Progress")
    with patch(
        "app.domain.backend.services.get_leetcode_player_submissions",
        return_value={"submissions": [], "hidden": False},
    ):
        closed = get_room(db, GetRoomModel(room_code="PEND01"))
    assert closed["players"][0]["result"] == "Loser"

    stale = add_room(db, host, code="STALE1", created=now - timedelta(hours=2))
    seat(db, stale, host)
    stale_state = get_room(db, GetRoomModel(room_code="STALE1"))
    assert stale_state["status"] == "Inactive"

    broken = add_room(db, host, code="BROKE1", status="Active", start=now - timedelta(minutes=5), end=now + timedelta(minutes=10))
    seat(db, broken, host, result="In_Progress")
    db.commit()
    with patch("app.domain.backend.services.get_leetcode_player_submissions", side_effect=ValueError("boom")):
        with pytest.raises(ValueError, match="boom"):
            get_room(db, GetRoomModel(room_code="BROKE1"))
    assert db.get(Room, broken.id).poll_error == "boom"
    assert host_seat.score == 1
