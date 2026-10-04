from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATA_DIR


DATABASE_URL = f"sqlite:///{DATA_DIR / 'app.db'}"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(engine)
Base = declarative_base()


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db() -> None:
    """Create tables from schema.sql. This is the schema the app runs."""

    schema = SCHEMA_PATH.read_text()
    connection = engine.raw_connection()
    try:
        connection.executescript(schema)
        connection.commit()
    finally:
        connection.close()