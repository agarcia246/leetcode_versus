from datetime import datetime, timezone

from app.domain.backend.models import Player, Problem, ProblemTopic, Room, RoomPlayer, RoomProblem, Topic
from app.domain.backend.services import to_db_time


def add_player(db, username):
    player = Player(lc_user=username)
    db.add(player)
    db.flush()
    return player


def add_room(db, host, code="ROOM01", status="Created", minutes=30, created=None, start=None, end=None):
    room = Room(
        room_code=code,
        host_id=host.id,
        current_status=status,
        duration_min=minutes,
        creation_time=to_db_time(created or datetime.now(timezone.utc)),
        start_time=to_db_time(start) if start else None,
        end_time=to_db_time(end) if end else None,
    )
    db.add(room)
    db.flush()
    return room


def add_problem(db, slug="two-sum", title="Two Sum", difficulty="Easy", topic="Array"):
    problem = Problem(
        title=title,
        lc_id=slug,
        lc_url=f"https://leetcode.com/problems/{slug}/",
        difficulty=difficulty,
    )
    db.add(problem)
    db.flush()

    topic_row = db.query(Topic).filter(Topic.topic_name == topic).first()
    if topic_row is None:
        topic_row = Topic(topic_name=topic)
        db.add(topic_row)
        db.flush()

    db.add(ProblemTopic(problem_id=problem.id, topic_id=topic_row.id))
    db.flush()
    return problem


def seat(db, room, player, score=0, result="Created"):
    link = RoomPlayer(
        room_id=room.id,
        player_id=player.id,
        joined_at=to_db_time(datetime.now(timezone.utc)),
        score=score,
        result=result,
    )
    db.add(link)
    db.flush()
    return link


def attach(db, room, problem, order=0):
    link = RoomProblem(room_id=room.id, problem_id=problem.id, display_order=order)
    db.add(link)
    db.flush()
    return link
