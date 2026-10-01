from fastapi import APIRouter, Request
from pydantic import BaseModel
from backend.models import CreateRoomModel



router = APIRouter()



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


@router.post("/rooms/create")
def create_room(model:CreateRoomModel):
    room_id = 



@router.get("/room/{room_code}")
def join_room(room_code:str):
    return {
        "room_code":room_code
    } 


