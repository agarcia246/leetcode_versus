from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.domain.backend.models import RoomPlayer
from app.domain.backend.services import (
    add_player_to_room,
    assign_match_results,
    canonical_submission_status,
    expire_inactive_lobby,
    generate_room_code,
    get_or_create_player,
    parse_db_time,
    submission_in_window,
    to_db_time,
)
from tests.factories import add_player, add_room


def test_submission_inside_window():
    start = datetime.now(timezone.utc)
    end = start + timedelta(minutes=30)

    assert submission_in_window(start + timedelta(minutes=5), start, end) is True


def test_submission_before_start():
    start = datetime.now(timezone.utc)
    end = start + timedelta(minutes=30)

    assert submission_in_window(start - timedelta(seconds=1), start, end) is False


def test_submission_after_end_or_without_start():
    start = datetime.now(timezone.utc)
    end = start + timedelta(minutes=30)

    assert submission_in_window(end + timedelta(seconds=1), start, end) is False
    assert submission_in_window(start, None, end) is False


def test_status_mapping():
    assert canonical_submission_status("Accepted") == "Accepted"
    assert canonical_submission_status("Wrong Answer") == "Wrong_Answer"
    assert canonical_submission_status("Time Limit Exceeded") == "Time_Limit"
    assert canonical_submission_status("Runtime Error") == "Pending"
    assert canonical_submission_status(None) == "Pending"


def test_timestamp_round_trip():
    naive = datetime(2026, 10, 4, 12, 0, 0)
    aware = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)

    stored = to_db_time(naive)
    assert parse_db_time(stored) == naive.replace(tzinfo=timezone.utc)
    assert parse_db_time(aware).tzinfo == timezone.utc
    assert parse_db_time(None) is None
    assert parse_db_time(naive).tzinfo == timezone.utc
    assert parse_db_time("2026-10-04T12:00:00Z") == aware
    assert parse_db_time("2026-10-04T12:00:00") == aware


def test_assign_match_results():
    assign_match_results([])

    tied = [RoomPlayer(score=2, result="In_Progress"), RoomPlayer(score=2, result="In_Progress")]
    assign_match_results(tied)
    assert [player.result for player in tied] == ["Winner", "Winner"]

    scored = [RoomPlayer(score=0, result="In_Progress"), RoomPlayer(score=1, result="In_Progress")]
    assign_match_results(scored)
    assert [player.result for player in scored] == ["Loser", "Winner"]


def test_generate_room_code_skips_a_taken_code(db):
    host = add_player(db, "alex")
    add_room(db, host, code="AAAAAA")

    with patch("app.domain.backend.services.random.choice", side_effect=["A"] * 6 + ["B"] * 6):
        assert generate_room_code(db) == "BBBBBB"


def test_get_or_create_player_reuses_existing_name(db):
    add_player(db, "Alex")

    with patch("app.domain.backend.services.lookup_leetcode_user") as lookup:
        player = get_or_create_player(db, " alex ")

    lookup.assert_not_called()
    assert player.lc_user == "Alex"


def test_expire_inactive_lobby():
    created = datetime.now(timezone.utc) - timedelta(hours=2)
    room = type("Room", (), {})()
    room.current_status = "Active"
    room.creation_time = to_db_time(created)
    room.duration_min = 30
    expire_inactive_lobby(room)
    assert room.current_status == "Active"

    room.current_status = "Created"
    room.creation_time = None
    expire_inactive_lobby(room)
    assert room.current_status == "Created"

    room.creation_time = to_db_time(created)
    expire_inactive_lobby(room, now=datetime.now(timezone.utc))
    assert room.current_status == "Inactive"


def test_add_player_to_room_returns_none_when_already_seated(db):
    host = add_player(db, "alex")
    room = add_room(db, host)
    assert add_player_to_room(db, host.id, room.id) is not None
    assert add_player_to_room(db, host.id, room.id) is None
