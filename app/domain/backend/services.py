from models import (
    CreateRoomModel,
    Player,
    Room,
    Problem,
    ProblemTopic,
    Topic,
    RoomProblem,
    JoinRoomModel,
    GetRoomModel,
    RoomPlayer,
    StartRoomModel,
    Submission
)

import random
import string
from datetime import datetime, timezone, timedelta

import requests
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session


ROOM_STATUS_CREATED = "Created"
ROOM_STATUS_ACTIVE = "Active"
ROOM_STATUS_FINISHED = "Finished"

RESULT_IN_PROGRESS = "In_Progress"
RESULT_WINNER = "Winner"
RESULT_LOSER = "Loser"
FINAL_RESULTS = {RESULT_WINNER, RESULT_LOSER}


# Utilities

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_db_time(value: datetime) -> str:
    """Store timestamps as UTC ISO strings. Time columns are TEXT."""

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat()


def parse_db_time(value) -> datetime | None:
    """Read a TEXT timestamp back into a timezone-aware datetime."""

    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def submission_in_window(
    submission_time: datetime,
    start_time: datetime | None,
    end_time: datetime | None,
) -> bool:
    """Count a solve only after the match starts and before it ends."""

    if start_time is None or submission_time < start_time:
        return False

    if end_time is not None and submission_time > end_time:
        return False

    return True


def assign_match_results(room_players: list[RoomPlayer]) -> None:
    """Highest score wins. A tie at the top shares the win. Zero solves is a loss."""

    if not room_players:
        return

    top_score = max(player.score for player in room_players)

    for player in room_players:
        if top_score > 0 and player.score == top_score:
            player.result = RESULT_WINNER
        else:
            player.result = RESULT_LOSER


def generate_room_code(db: Session) -> str:
    """Generate a unique 6-character room code."""

    letters = string.ascii_uppercase

    while True:
        room_code = "".join(random.choice(letters) for _ in range(6))

        exists = (
            db.query(Room.id)
            .filter(Room.room_code == room_code)
            .first()
        )

        if exists is None:
            return room_code



def get_or_create_player(db: Session, username: str) -> Player:
    """Fetch player by username or create them."""

    player = (
        db.query(Player)
        .filter(Player.lc_user == username)
        .first()
    )

    if player is not None:
        return player

    new_player = Player(lc_user=username)
    db.add(new_player)
    db.flush()

    return new_player



def add_player_to_room(db: Session, player_id: int, room_id: int) -> RoomPlayer | None:
    """Add a player to a room if not already present."""

    existing = (
        db.query(RoomPlayer)
        .filter(
            RoomPlayer.room_id == room_id,
            RoomPlayer.player_id == player_id
        )
        .first()
    )

    if existing is not None:
        return None

    room_player = RoomPlayer(
        room_id=room_id,
        player_id=player_id,
        joined_at=to_db_time(utc_now()),
        score=0
    )

    db.add(room_player)
    return room_player



def add_problems_to_room(
    db: Session,
    count: int,
    topics: list[str],
    difficulty: str,
    room_id: int
) -> None:
    """Add random problems to a room."""

    problems = (
        db.query(Problem.id)
        .join(ProblemTopic, Problem.id == ProblemTopic.problem_id)
        .join(Topic, Topic.id == ProblemTopic.topic_id)
        .filter(
            Topic.topic_name.in_(topics),
            Problem.difficulty == difficulty
        )
        .distinct()
        .order_by(func.random())
        .limit(count)
        .all()
    )

    problem_ids = [problem[0] for problem in problems]

    if len(problem_ids) < count:
        raise ValueError("Not enough problems available for selection")

    room_problems = []

    for index, problem_id in enumerate(problem_ids):
        room_problems.append(
            RoomProblem(
                room_id=room_id,
                problem_id=problem_id,
                display_order=index
            )
        )

    db.add_all(room_problems)





def get_leetcode_player_submissions(lc_username: str) -> dict:
    """Fetch recent accepted LeetCode submissions."""

    url = "https://leetcode.com/graphql"

    query = """
    query recentSubmissions($username: String!, $limit: Int!) {
        recentAcSubmissionList(username: $username, limit: $limit) {
            title
            titleSlug
            timestamp
            statusDisplay
            lang
        }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "username": lc_username,
            "limit": 20
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "Origin": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0"
    }

    session = requests.Session()

    try:
        response = session.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if "data" not in data:
            raise ValueError("Invalid LeetCode response")

        return data

    except Exception as exc:
        raise RuntimeError(f"LeetCode API error: {exc}")



# API SERVICES

def create_room(db: Session, model: CreateRoomModel):
    """Create a room with problems and host."""

    try:
        code = generate_room_code(db)

        host = get_or_create_player(db, model.host_username)

        room = Room(
            room_code=code,
            host_id=host.id,
            current_status=ROOM_STATUS_CREATED,
            duration_min=model.duration,
            creation_time=to_db_time(utc_now()),
            start_time=None,
            end_time=None,
            last_polled_at=None,
            poll_error=None
        )

        db.add(room)
        db.flush()

        add_problems_to_room(
            db=db,
            count=model.problem_count,
            topics=model.topics,
            difficulty=model.difficulty,
            room_id=room.id
        )

        add_player_to_room(
            db=db,
            player_id=host.id,
            room_id=room.id
        )

        db.commit()

        return {
            "room_code": room.room_code,
            "room_id": room.id,
            "host_id": host.id
        }

    except Exception:
        db.rollback()
        raise




def join_room(db: Session, model: JoinRoomModel):
    """Join an existing room."""

    try:
        room = (
            db.query(Room)
            .filter(Room.room_code == model.room_code.upper())
            .first()
        )

        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.current_status == ROOM_STATUS_FINISHED:
            raise HTTPException(status_code=400, detail="Room already finished")

        player = get_or_create_player(db, model.username)

        existing = (
            db.query(RoomPlayer)
            .filter(
                RoomPlayer.room_id == room.id,
                RoomPlayer.player_id == player.id
            )
            .first()
        )

        if existing is not None:
            db.commit()
            return {
                "message": "Joined room",
                "room_code": room.room_code,
                "player_id": player.id
            }

        room_player = add_player_to_room(
            db,
            player_id=player.id,
            room_id=room.id
        )

        if room.current_status == ROOM_STATUS_ACTIVE and room_player is not None:
            room_player.result = RESULT_IN_PROGRESS

        db.commit()

        return {
            "message": "Joined room",
            "room_code": room.room_code,
            "player_id": player.id
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise





def start_room(db: Session, model: StartRoomModel):
    """Start a room if host is valid."""

    try:
        room = (
            db.query(Room)
            .filter(Room.room_code == model.room_code.upper())
            .first()
        )

        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")

        if room.host_id != model.player_id:
            raise HTTPException(status_code=400, detail="Host must start room")

        if room.current_status != ROOM_STATUS_CREATED:
            raise HTTPException(status_code=400, detail="Room already started")

        room_players = (
            db.query(RoomPlayer)
            .filter(RoomPlayer.room_id == room.id)
            .all()
        )

        room_problems = (
            db.query(RoomProblem)
            .filter(RoomProblem.room_id == room.id)
            .all()
        )

        if len(room_players) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 players")

        if len(room_problems) < 1:
            raise HTTPException(status_code=400, detail="No problems in room")

        start_time = utc_now()

        room.start_time = to_db_time(start_time)
        room.end_time = to_db_time(start_time + timedelta(minutes=room.duration_min))
        room.current_status = ROOM_STATUS_ACTIVE
        room.poll_error = None

        for room_player in room_players:
            room_player.result = RESULT_IN_PROGRESS

        db.commit()

        return {
            "message": "Room started",
            "room_code": room.room_code,
            "start_time": room.start_time,
            "end_time": room.end_time
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise




def get_room(db: Session, model: GetRoomModel):
    """Fetch room state and poll submissions that landed during the match."""

    room = None

    try:
        room_code = model.room_code.upper()

        room = (
            db.query(Room)
            .filter(Room.room_code == room_code)
            .first()
        )

        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")

        now = utc_now()
        start_time = parse_db_time(room.start_time)
        end_time = parse_db_time(room.end_time)
        time_up = end_time is not None and now >= end_time

        player_rows = (
            db.query(RoomPlayer, Player)
            .join(Player, Player.id == RoomPlayer.player_id)
            .filter(RoomPlayer.room_id == room.id)
            .all()
        )
        room_players = [room_player for room_player, _player in player_rows]

        results_pending = any(
            room_player.result not in FINAL_RESULTS
            for room_player in room_players
        )
        should_poll = room.current_status == ROOM_STATUS_ACTIVE or (
            room.current_status == ROOM_STATUS_FINISHED and results_pending
        )

        if should_poll:
            room_problem_slugs = set(
                db.query(Problem.lc_id)
                .join(RoomProblem, Problem.id == RoomProblem.problem_id)
                .filter(RoomProblem.room_id == room.id)
                .scalars()
                .all()
            )

            submissions_to_add = []

            for room_player, player in player_rows:
                player_submissions = get_leetcode_player_submissions(player.lc_user)
                recent_submissions = (
                    (player_submissions.get("data") or {}).get("recentAcSubmissionList")
                    or []
                )

                latest_submissions = {}

                for submission in recent_submissions:
                    slug = submission.get("titleSlug")

                    if (
                        slug
                        and slug not in latest_submissions
                        and slug in room_problem_slugs
                    ):
                        latest_submissions[slug] = submission

                for submission in latest_submissions.values():
                    submission_time = datetime.fromtimestamp(
                        int(submission["timestamp"]),
                        tz=timezone.utc
                    )

                    if not submission_in_window(submission_time, start_time, end_time):
                        continue

                    existing_submission = (
                        db.query(Submission)
                        .join(Problem, Problem.id == Submission.problem_id)
                        .filter(
                            Submission.room_id == room.id,
                            Submission.player_id == room_player.player_id,
                            Problem.lc_id == submission["titleSlug"]
                        )
                        .first()
                    )

                    if existing_submission is not None:
                        continue

                    problem_id = (
                        db.query(Problem.id)
                        .filter(Problem.lc_id == submission["titleSlug"])
                        .scalar()
                    )

                    if problem_id is None:
                        continue

                    submissions_to_add.append(
                        Submission(
                            room_id=room.id,
                            player_id=room_player.player_id,
                            problem_id=problem_id,
                            submitted_at=to_db_time(submission_time),
                            current_status="Accepted"
                        )
                    )

                    room_player.score += 1

            if submissions_to_add:
                db.add_all(submissions_to_add)

            room.last_polled_at = to_db_time(now)
            room.poll_error = None

        if time_up or room.current_status == ROOM_STATUS_FINISHED:
            room.current_status = ROOM_STATUS_FINISHED
            assign_match_results(room_players)

        problems = (
            db.query(Problem, RoomProblem.display_order)
            .join(RoomProblem, Problem.id == RoomProblem.problem_id)
            .filter(RoomProblem.room_id == room.id)
            .order_by(RoomProblem.display_order)
            .all()
        )

        db.commit()

        return {
            "room_code": room.room_code,
            "status": room.current_status,
            "start_time": room.start_time,
            "end_time": room.end_time,
            "players": [
                {
                    "player_id": room_player.player_id,
                    "username": player.lc_user,
                    "score": room_player.score,
                    "result": room_player.result
                }
                for room_player, player in player_rows
            ],
            "problems": [
                {
                    "title": problem.title,
                    "slug": problem.lc_id,
                    "url": problem.lc_url,
                    "difficulty": problem.difficulty,
                    "display_order": display_order
                }
                for problem, display_order in problems
            ]
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()

        if room is not None:
            room.poll_error = str(exc)
            db.commit()

        raise
