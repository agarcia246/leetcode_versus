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
import string
import random
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
import requests

def generate_room_code(db:Session) -> str:
    room_code = ""

    letters = string.ascii_uppercase

    for i in range(6):
        room_code = room_code + random.choice(letters)


    if db.query(Room).filter(Room.room_code==room_code).all():
        return generate_room_code(db)

    return room_code




def add_problems_to_room(db: Session, count:int, topics: list[str], difficulty:str, room_id:int) -> None:


    problems = db.query(Problem.id).join(ProblemTopic, Problem.id == ProblemTopic.problem_id).join(Topic, Topic.id == ProblemTopic.topic_id).filter(Topic.topic_name.in_(topics), Problem.difficulty == difficulty).order_by(func.random()).distinct().limit(count).all().scalars()

    new_rows = []

    for id in range(len(problems)):
        new_rows.append(RoomProblem(
            room_id=room_id,
            problem_id=problems[id],
            display_order=id
        ))

    db.add_all(new_rows)
    db.commit()



def add_player_to_room(db: Session, player_id:int, room_id:int) -> None:


    player = RoomPlayer(
        room_id=room_id,
        player_id=player_id,
        joined_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )

    db.add(player)
    db.commit()




def get_leetcode_player_submissions(lc_username:str) -> dict:
    url = "https://leetcode.com/graphql"

    query = """
    query recentSubmissions($username: String!) {
        recentSubmissionList(username: $username) {
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
            "username": f"{lc_username}"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "Origin": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0"
    }

    session = requests.Session()

    response = session.post(
        url,
        json=payload,
        headers=headers
    )

    return response.json()






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
def create_room(db: Session, model: CreateRoomModel):
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
    db.flush()




    add_problems_to_room(db=db, count=model.problem_count, topics=model.topics, difficulty=model.difficulty, room_id=room.id)
    add_player_to_room(db,player_id=host_id,room_id=room.id)





    db.commit()


    return {

    }







# Related_tables: Players, Rooms, Room_Players
# This function is going to add a player to an active room.
# It does the following:
    # 1. checks to see if the player exists in the players table and if not adds them
    # 2. gets the player's Id
    # 3. gets the rooms id using the room code
    # 3. adds that player's id to the room_players table



def join_room(db: Session, model: JoinRoomModel):
    
    player_id = db.query(Player.id).filter(Player.lc_user == model.username).scalar()

    if player_id is None:
        new_user = Player(lc_user=model.host_username)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        player_id = db.query(Player.id).filter(Player.lc_user == model.host_username).scalar()


    room_id = db.query(Room.id).filter(Room.room_code == model.room_code).scalar()

    add_player_to_room(db, player_id=player_id, room_id=room_id)




# The start
def start_room(db: Session, model: StartRoomModel):

    room = db.query(Room).filter(Room.room_code == model.room_code)

    if room.id is None:
        return {404:"Room not Found"}
    
    if room.host_id != model.player_id:
        return {400:"Host must start room"}

    if room.current_status != "Created":
        return {400:"This room already started"}

    room_players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()
    room_problems = db.query(RoomProblem).filter(RoomProblem.room_id == room.id).all()
    
    if len(room_players) == 0:
        return {400:"Wait for at least one player to join before starting"}
    
    if len(room_problems) == 0:
        return {400:"This room has no problems"}



    start_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    room.start_time = start_time
    room.end_time = start_time + timedelta(minutes=room.duration_min)
    room.current_status = "Active"
    room.poll_error = None


    db.commit()
    return {200:"Started Room"}





def get_room(db: Session, model: JoinRoomModel):

    room_code = model.room_code.upper()

    room = db.query(Room).filter(Room.room_code == room_code)

    if room is None:
        return {404: "room does not exist"}




    # MATCH FINISHED
    now = datetime.now(timezone.utc)

    if now >= datetime.fromtimestamp(room.end_time):
        room.current_status = "finished"



    # Match is live

    room_problems = db.query(RoomProblem).filter(RoomProblem.room_id == room.id).all()
    room_players = db.query(RoomPlayer).filter(RoomPlayer.room_id == room.id).all()



    new_submissions = []
    for player in room_players:
        player_submissions = get_leetcode_player_submissions()

        for submission in player_submissions["data"]["recentSubmissionList"]:
            if submission["statusDisplay"] == "Accepted" and datetime.fromtimestamp(submission["timestamp"] >= datetime.fromtimestamp(room.start_time)):
                problem_id = db.query(Problem.id).filter(Problem.lc_id == submission["titleSlug"]).scalar() 
                new_submissions.append(
                    Submission(
                        room_id=room.id,
                        player_id=player.id,
                        problem_id=problem_id
                    )
                )



        















    


    # MATCH LIVE



    











