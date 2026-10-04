from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.backend.models import (
    CreateRoomModel,
    GetRoomModel,
    JoinRoomModel,
    StartRoomModel,
)
from app.domain.backend.services import (
    create_room,
    get_room,
    join_room,
    list_match_filters,
    start_room,
)


router = APIRouter()


class JoinRoomBody(BaseModel):
    username: str


class StartRoomBody(BaseModel):
    player_id: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/filters")
def list_filters_route(db: Session = Depends(get_db)):
    try:
        return list_match_filters(db)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/rooms/create")
def create_room_route(model: CreateRoomModel, db: Session = Depends(get_db)):
    try:
        return create_room(db, model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/rooms/{room_code}/join")
def join_room_route(
    room_code: str,
    body: JoinRoomBody,
    db: Session = Depends(get_db),
):
    model = JoinRoomModel(username=body.username, room_code=room_code)
    try:
        return join_room(db, model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/rooms/{room_code}/start")
def start_room_route(
    room_code: str,
    body: StartRoomBody,
    db: Session = Depends(get_db),
):
    model = StartRoomModel(player_id=body.player_id, room_code=room_code)
    return start_room(db, model)


@router.get("/rooms/{room_code}")
def get_room_route(room_code: str, db: Session = Depends(get_db)):
    return get_room(db, GetRoomModel(room_code=room_code))
