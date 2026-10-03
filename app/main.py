from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.domain.backend.router import router as backend_router


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(router=backend_router, prefix="/backend")


app.mount("/static", StaticFiles(directory="app/static"), name="static")