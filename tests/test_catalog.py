from unittest.mock import patch

import pytest

from app.domain.backend.models import Problem, ProblemTopic, RoomProblem, Topic
from app.domain.backend.services import (
    add_problems_to_room,
    fetch_problems_for_topics,
    fetch_topic_tags,
    leetcode_graphql,
    list_match_filters,
    local_problem_ids,
    lookup_leetcode_user,
    resolve_topics,
    upsert_problem,
)
from tests.factories import add_player, add_problem, add_room


TWO_SUM = {
    "title": "Two Sum",
    "titleSlug": "two-sum",
    "difficulty": "EASY",
    "paidOnly": False,
    "topicTags": [
        {"name": "Array", "slug": "array"},
        {"name": " ", "slug": "blank"},
    ],
}

TAGS = {
    "data": {
        "questionTopicTags": {
            "edges": [
                {"node": {"name": "Array", "slug": "array"}},
                {"node": {"name": "", "slug": "blank"}},
            ]
        }
    }
}


def test_leetcode_graphql_success_and_failures():
    class Response:
        def __init__(self, payload, fail=False):
            self.payload = payload
            self.fail = fail

        def raise_for_status(self):
            if self.fail:
                raise RuntimeError("http down")

        def json(self):
            return self.payload

    with patch("app.domain.backend.services.requests.post", return_value=Response({"data": {}})):
        assert leetcode_graphql("query {}") == {"data": {}}

    with patch("app.domain.backend.services.requests.post", return_value=Response({}, fail=True)):
        with pytest.raises(RuntimeError, match="LeetCode API error"):
            leetcode_graphql("query {}")

    with patch(
        "app.domain.backend.services.requests.post",
        return_value=Response({"errors": [{"message": "bad query"}]}),
    ):
        with pytest.raises(RuntimeError, match="bad query"):
            leetcode_graphql("query {}")

    with patch(
        "app.domain.backend.services.requests.post",
        return_value=Response({"errors": [{}]}),
    ):
        with pytest.raises(RuntimeError, match="Invalid LeetCode response"):
            leetcode_graphql("query {}")


def test_lookup_leetcode_user():
    with patch(
        "app.domain.backend.services.leetcode_graphql",
        return_value={"data": {"matchedUser": {"username": "Alex"}}},
    ):
        assert lookup_leetcode_user("alex") == "Alex"

    with patch(
        "app.domain.backend.services.leetcode_graphql",
        return_value={"data": {"matchedUser": None}},
    ):
        with pytest.raises(ValueError, match="not found"):
            lookup_leetcode_user("missing")


def test_fetch_and_resolve_topics(db):
    with patch("app.domain.backend.services.leetcode_graphql", return_value=TAGS):
        tags = fetch_topic_tags()
    assert tags == [{"name": "Array", "slug": "array"}]

    with patch("app.domain.backend.services.leetcode_graphql", return_value={"data": {}}):
        with pytest.raises(RuntimeError, match="no topic tags"):
            fetch_topic_tags()

    with patch("app.domain.backend.services.fetch_topic_tags", return_value=[{"name": "Array", "slug": "array"}]):
        resolved = resolve_topics(db, ["Array", "array"])
        assert resolved == [{"name": "Array", "slug": "array"}]
        assert db.query(Topic).filter(Topic.topic_name == "Array").count() == 1

        with pytest.raises(ValueError, match="Unknown topic"):
            resolve_topics(db, ["Graphs"])


def test_list_match_filters_stores_topics(db):
    with patch("app.domain.backend.services.fetch_topic_tags", return_value=[{"name": "Array", "slug": "array"}]):
        filters = list_match_filters(db)

    assert filters["difficulties"] == ["Easy", "Medium", "Hard"]
    assert db.query(Topic).filter(Topic.topic_name == "Array").one()


def test_fetch_problems_skips_unusable_rows_and_pages():
    pages = [
        {
            "data": {
                "problemsetQuestionListV2": {
                    "questions": [
                        {"titleSlug": None, "difficulty": "EASY", "paidOnly": False},
                        {"titleSlug": "paid-only", "difficulty": "EASY", "paidOnly": True},
                        {"titleSlug": "hard-one", "difficulty": "HARD", "paidOnly": False},
                    ],
                    "hasMore": True,
                }
            }
        },
        {
            "data": {
                "problemsetQuestionListV2": {
                    "questions": [TWO_SUM, dict(TWO_SUM)],
                    "hasMore": False,
                }
            }
        },
    ]

    with patch("app.domain.backend.services.leetcode_graphql", side_effect=pages):
        found = fetch_problems_for_topics("Easy", ["array"], 1)

    assert [question["titleSlug"] for question in found] == ["two-sum"]

    with patch(
        "app.domain.backend.services.leetcode_graphql",
        return_value={"data": {"problemsetQuestionListV2": {"questions": [], "hasMore": False}}},
    ):
        assert fetch_problems_for_topics("Easy", ["array"], 1) == []


def test_upsert_problem_links_topics_once(db):
    first = upsert_problem(db, TWO_SUM)
    second = upsert_problem(db, TWO_SUM)

    assert first.id == second.id
    assert db.query(Problem).count() == 1
    assert db.query(ProblemTopic).count() == 1


def test_local_problem_ids_samples_when_there_are_extras(db):
    add_problem(db, slug="one")
    add_problem(db, slug="two")
    assert len(local_problem_ids(db, ["Array"], "Easy", 5)) == 2

    with patch("app.domain.backend.services.random.sample", return_value=[1]):
        assert local_problem_ids(db, ["Array"], "Easy", 1) == [1]


def test_add_problems_to_room_stores_a_sample_and_falls_back(db):
    host = add_player(db, "alex")
    room = add_room(db, host)
    questions = [
        TWO_SUM,
        {
            "title": "Valid Parentheses",
            "titleSlug": "valid-parentheses",
            "difficulty": "EASY",
            "paidOnly": False,
            "topicTags": [{"name": "Array", "slug": "array"}],
        },
    ]

    with patch("app.domain.backend.services.fetch_topic_tags", return_value=[{"name": "Array", "slug": "array"}]):
        with patch("app.domain.backend.services.fetch_problems_for_topics", return_value=questions):
            with patch("app.domain.backend.services.random.sample", side_effect=lambda ids, count: ids[:count]):
                add_problems_to_room(db, 1, ["Array"], "Easy", room.id)

    assert db.query(RoomProblem).filter(RoomProblem.room_id == room.id).count() == 1

    other = add_room(db, host, code="ROOM02")
    saved = add_problem(db, slug="local-only", topic="Hash Table")
    with patch("app.domain.backend.services.fetch_topic_tags", return_value=[{"name": "Hash Table", "slug": "hash-table"}]):
        with patch("app.domain.backend.services.fetch_problems_for_topics", side_effect=RuntimeError("down")):
            add_problems_to_room(db, 1, ["Hash Table"], "Easy", other.id)

    attached = db.query(RoomProblem).filter(RoomProblem.room_id == other.id).all()
    assert [row.problem_id for row in attached] == [saved.id]

    empty = add_room(db, host, code="ROOM03")
    with patch("app.domain.backend.services.fetch_topic_tags", return_value=[{"name": "Array", "slug": "array"}]):
        with patch("app.domain.backend.services.fetch_problems_for_topics", side_effect=RuntimeError("down")):
            with patch("app.domain.backend.services.local_problem_ids", return_value=[]):
                with pytest.raises(ValueError, match="Not enough problems"):
                    add_problems_to_room(db, 1, ["Array"], "Easy", empty.id)
