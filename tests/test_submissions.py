from datetime import datetime, timedelta, timezone

from unittest.mock import patch

from app.domain.backend.models import Submission
from app.domain.backend.services import get_leetcode_player_submissions, record_match_submissions
from tests.factories import add_player, add_problem, add_room, attach, seat


def open_match(db):
    start = datetime.now(timezone.utc) - timedelta(minutes=5)
    end = start + timedelta(minutes=30)
    host = add_player(db, "alex")
    room = add_room(db, host, status="Active", start=start, end=end)
    problem = add_problem(db)
    attach(db, room, problem)
    player = seat(db, room, host, result="In_Progress")
    return room, player, start, end


def submission(slug, when, status):
    return {
        "titleSlug": slug,
        "timestamp": int(when.timestamp()),
        "statusDisplay": status,
    }


def test_get_leetcode_player_submissions_merges_and_hides():
    payload = {
        "data": {
            "recentSubmissionList": [
                {"titleSlug": "two-sum", "timestamp": "10", "statusDisplay": "Accepted"},
                {"titleSlug": None, "timestamp": "11", "statusDisplay": "Accepted"},
            ],
            "recentAcSubmissionList": [
                {"titleSlug": "two-sum", "timestamp": "10", "statusDisplay": "Accepted"},
                {"titleSlug": "two-sum", "timestamp": "12", "statusDisplay": "Accepted"},
            ],
        }
    }
    with patch("app.domain.backend.services.leetcode_graphql", return_value=payload):
        merged = get_leetcode_player_submissions("alex")

    assert merged["hidden"] is False
    assert len(merged["submissions"]) == 2

    with patch(
        "app.domain.backend.services.leetcode_graphql",
        return_value={"data": {"recentSubmissionList": None, "recentAcSubmissionList": None}},
    ):
        hidden = get_leetcode_player_submissions("alex")

    assert hidden == {"submissions": [], "hidden": True}


def test_record_match_submissions_scores_a_new_accept_once(db):
    room, player, start, end = open_match(db)
    inside = start + timedelta(minutes=1)
    outside = start - timedelta(minutes=10)
    rows = record_match_submissions(
        db,
        room,
        player,
        [
            submission("other", inside, "Accepted"),
            {"titleSlug": "two-sum", "timestamp": "nope", "statusDisplay": "Accepted"},
            submission("two-sum", outside, "Accepted"),
            submission("two-sum", inside, "Wrong Answer"),
            submission("two-sum", inside + timedelta(seconds=30), "Accepted"),
        ],
        {"two-sum", "missing-problem"},
        start,
        end,
    )
    db.add_all(rows)
    db.flush()

    assert player.score == 1
    assert len(rows) == 1
    assert rows[0].current_status == "Accepted"

    again = record_match_submissions(
        db,
        room,
        player,
        [submission("two-sum", inside, "Accepted")],
        {"two-sum"},
        start,
        end,
    )
    assert again == []
    assert player.score == 1


def test_record_match_submissions_upgrades_a_wrong_answer(db):
    room, player, start, end = open_match(db)
    inside = start + timedelta(minutes=1)
    wrong = record_match_submissions(
        db,
        room,
        player,
        [submission("two-sum", inside, "Wrong Answer")],
        {"two-sum"},
        start,
        end,
    )
    db.add_all(wrong)
    db.flush()
    assert player.score == 0

    upgraded = record_match_submissions(
        db,
        room,
        player,
        [submission("two-sum", inside + timedelta(seconds=20), "Accepted")],
        {"two-sum"},
        start,
        end,
    )
    assert upgraded == []
    assert player.score == 1
    stored = db.query(Submission).one()
    assert stored.current_status == "Accepted"


def test_record_match_submissions_skips_a_slug_with_no_problem_row(db):
    room, player, start, end = open_match(db)
    rows = record_match_submissions(
        db,
        room,
        player,
        [submission("missing-problem", start + timedelta(minutes=1), "Accepted")],
        {"missing-problem"},
        start,
        end,
    )
    assert rows == []
    assert player.score == 0
