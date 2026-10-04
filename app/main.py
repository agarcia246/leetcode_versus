from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import HOST, PORT, STATIC_DIR
from app.database import Base, engine, init_db
from app.domain.backend.router import router as backend_router
from app.domain.frontend.router import router as frontend_router


init_db()
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(frontend_router)
app.include_router(router=backend_router, prefix="/backend")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
