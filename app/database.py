from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()


DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR}/app.db"


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread":False})

SessionLocal = sessionmaker(engine)
Base = declarative_base()