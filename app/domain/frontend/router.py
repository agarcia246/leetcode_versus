from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import STATIC_DIR


router = APIRouter()


@router.get("/")
def serve_home():
    return FileResponse(STATIC_DIR / "index.html")
