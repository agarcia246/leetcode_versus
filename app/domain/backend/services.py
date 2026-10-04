from models import (
    CreateRoomModel,
    Player,
    Room,
    Problem,
    ProblemTopic,
    Topic,
    RoomProblem,
    JoinRoomModel,
    RoomPlayer,
    StartRoomModel,
    Submission
)

import random
import string
from datetime import datetime, timezone, timedelta

import requests
from sqlalchemy import func
from sqlalchemy.orm import Session


ROOM_STATUS_CREATED = "Created"
ROOM_STATUS_ACTIVE = "Active"
ROOM_STATUS_FINISHED = "Finished"


# =========================
# Utility Functions
# =========================


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



def add_player_to_room(db: Session, player_id: int, room_id: int) -> None:
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
        return

    room_player = RoomPlayer(
        room_id=room_id,
        player_id=player_id,
        joined_at=datetime.now(timezone.utc),
        score=0
    )

    db.add(room_player)



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


# =========================
# LeetCode API
# =========================


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


# =========================
# Room Creation
# =========================


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
            creation_time=datetime.now(timezone.utc),
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


# =========================
# Join Room
# =========================


def join_room(db: Session, model: JoinRoomModel):
    """Join an existing room."""

    try:
        room = (
            db.query(Room)
            .filter(Room.room_code == model.room_code.upper())
            .first()
        )

        if room is None:
            return {404: "Room not found"}

        if room.current_status == ROOM_STATUS_FINISHED:
            return {400: "Room already finished"}

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
            return {400: "Player already joined room"}

        add_player_to_room(
            db,
            player_id=player.id,
            room_id=room.id
        )

        db.commit()

        return {
            "message": "Joined room",
            "room_code": room.room_code,
            "player_id": player.id
        }

    except Exception:
        db.rollback()
        raise


# =========================
# Start Room
# =========================


def start_room(db: Session, model: StartRoomModel):
    """Start a room if host is valid."""

    try:
        room = (
            db.query(Room)
            .filter(Room.room_code == model.room_code)
            .first()
        )

        if room is None:
            return {404: "Room not found"}

        if room.host_id != model.player_id:
            return {400: "Host must start room"}

        if room.current_status != ROOM_STATUS_CREATED:
            return {400: "Room already started"}

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

        if len(room_players) < 1:
            return {400: "No players in room"}

        if len(room_problems) < 1:
            return {400: "No problems in room"}

        start_time = datetime.now(timezone.utc)

        room.start_time = start_time
        room.end_time = start_time + timedelta(minutes=room.duration_min)
        room.current_status = ROOM_STATUS_ACTIVE
        room.poll_error = None

        db.commit()

        return {200: "Room started"}

    except Exception:
        db.rollback()
        raise


# =========================
# Get Room / Poll Submissions
# =========================


def get_room(db: Session, model: JoinRoomModel):
    """Fetch room state and poll submissions."""

    try:
        room_code = model.room_code.upper()

        room = (
            db.query(Room)
            .filter(Room.room_code == room_code)
            .first()
        )

        if room is None:
            return None

        now = datetime.now(timezone.utc)

        if room.end_time is not None and now >= room.end_time:
            room.current_status = ROOM_STATUS_FINISHED

        room_players = (
            db.query(RoomPlayer)
            .filter(RoomPlayer.room_id == room.id)
            .all()
        )

        room_problem_slugs = set(
            db.query(Problem.lc_id)
            .join(RoomProblem, Problem.id == RoomProblem.problem_id)
            .filter(RoomProblem.room_id == room.id)
            .scalars()
            .all()
        )

        submissions_to_add = []

        for room_player in room_players:
            username = (
                db.query(Player.lc_user)
                .filter(Player.id == room_player.player_id)
                .scalar()
            )

            player_submissions = get_leetcode_player_submissions(username)

            latest_submissions = {}

            for submission in player_submissions["data"]["recentAcSubmissionList"]:
                slug = submission["titleSlug"]

                if (
                    slug not in latest_submissions
                    and slug in room_problem_slugs
                ):
                    latest_submissions[slug] = submission

            for submission in latest_submissions.values():
                submission_time = datetime.fromtimestamp(
                    int(submission["timestamp"]),
                    tz=timezone.utc
                )

                if room.end_time is not None and submission_time > room.end_time:
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
                        submitted_at=submission_time,
                        current_status="Accepted"
                    )
                )

                room_player.score += 1

        if submissions_to_add:
            db.add_all(submissions_to_add)

        room.last_polled_at = now

        db.commit()

        return {
            "room_code": room.room_code,
            "status": room.current_status,
            "players": [
                {
                    "player_id": player.player_id,
                    "score": player.score
                }
                for player in room_players
            ]
        }

    except Exception as exc:
        db.rollback()

        if 'room' in locals() and room is not None:
            room.poll_error = str(exc)
            db.commit()

        raise
