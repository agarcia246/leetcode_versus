from models import CreateRoomModel, Player, Room, Problem, ProblemTopic, Topic, RoomProblem
import string
import random
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

def generate_room_code() -> str:
    room_code = ""

    letters = string.ascii_uppercase

    for i in range(6):
        room_code = room_code + random.choice(letters)

    return room_code




def add_problems_to_room(db: Session, count:int, topics: list[str], difficulty:str, room_id:int) -> None:


    problems = db.query(Problem.id).join(ProblemTopic, Problem.id == ProblemTopic.problem_id).join(Topic, Topic.id == ProblemTopic.topic_id).filter(Topic.topic_name in topics, Problem.difficulty == difficulty).order_by(func.random()).limit(count).all()

    new_rows = []

    for id in range(len(problems)):
        new_rows.append(RoomProblem(
            room_id=room_id,
            problem_id=problems[id],
            display_order=id+1
        ))

    db.add_all(new_rows)
    db.commit()













# related tables: rooms, players, room_players, problems, problems, problem_topics, topics
# Input: host_username:str, duration:int, problem_count:int, difficulty:str, 
# This is the request that creates the room. It is called when the user submits the create room form fromm the home page. It does the following:
    # generates room_id 6 character string

    # check to see if the host username exists in leetcode. if not return exception
    # checks to see if the host_username already exists in the players table:
        # If no it adds that username to the players table   
    # adds the host to the room_players table with the following
        # {room_id:"{room_id}", player_id:"{host_username}", joined_at:"{current datetime}", score:0, result:"Created"}

    # obtain 3 random problems from the problem_topics table which have the difficulty and topics that the user submitted.
    # add those problems to the room_problems table

    # create a new entry in the rooms table with:
        # room_code = the already generated room_id : str
        # host_id = host_username (foreign key for the players table): str
        # current_status = "created" : str
        # duration_min = duration : int
        # creation_time = "{current datetime}" : str
        # start_time = None : Null
        # end_time = None : Null
        # last_polled_at = None : Null
        # poll_error = None : Null


# API call return {room_id, host_username}
def CreateRoom(db: Session, model: CreateRoomModel):
    code = generate_room_code()

    host_id = db.query(Player.id).filter(Player.lc_user == model.host_username).scalar()

    if host_id is None:
        new_user = Player(lc_user=model.host_username)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        host_id = db.query(Player.id).filter(Player.lc_user == model.host_username).scalar()

    room = Room(
        room_code=code,
        host_id=host_id,
        duration_min=model.duration,
        creation_time=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )

    db.add(room)
    db.commit()
    db.refresh(room)





    add_problems_to_room(db=db, count=model.problem_count, topics=model.topics, difficulty=model.difficulty, room_id=room.id)






