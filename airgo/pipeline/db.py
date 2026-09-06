<<<<<<< HEAD
"""
AirGo Database Connection & SQLite/SQLAlchemy Pipeline Init.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = os.path.join(os.getcwd(), "data", "airgo.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
=======
import os
from urllib.parse import quote_plus
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from airgo.pipeline.models import Base

# Read credentials from Environment Variables with defaults provided by User
DB_USER = os.getenv("POSTGRES_USER", "rithish")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "Rithish@2006")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "airgo")

# Safe URL encoding for passwords containing special characters (e.g. @, #, %)
ENCODED_PASS = quote_plus(DB_PASS)
DEFAULT_POSTGRES_URL = f"postgresql://{DB_USER}:{ENCODED_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_POSTGRES_URL)

# Configure robust connection pooling for high-throughput batch writes
if "postgresql" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800
    )
else:
    # SQLite fallback for local unit tests if PostgreSQL is unreachable
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes schema tables in PostgreSQL/SQLite."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for DB transactional sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency generator for FastAPI / CLI DB sessions."""
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
<<<<<<< HEAD


def get_db_session():
    return SessionLocal()
=======
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
