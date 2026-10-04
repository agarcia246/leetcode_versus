from fastapi import APIRouter, Request
from pydantic import BaseModel
from backend.models import CreateRoomModel
from database import SessionLocal


router = APIRouter()



@router.post("/rooms/create")
def create_room(model:CreateRoomModel):










@router.get("/room/{room_code}")
def join_room(room_code:str):
    return {
        "room_code":room_code
    } 





@router.get("/room/{room_code}")
def join_room(room_code:str):
    return {
        "room_code":room_code
    } 


@router.get("/room/{room_code}")
def join_room(room_code:str):
    return {
        "room_code":room_code
    } 