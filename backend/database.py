from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///meeting_hub.db")

# SQLite needs special handling for UUID columns and foreign keys
connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, connect_args=connect_args)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from backend.models.db_models import (
        Project, Transcript, ActionItem, SentimentSegment, ChatHistory
    )
    Base.metadata.create_all(bind=engine)
