"""
Database connection and session management for Supabase PostgreSQL.
"""

import time
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from airgo.config import SUPABASE_DB_URI

engine = create_engine(
    SUPABASE_DB_URI,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> dict:
    """Verifies live database connection and returns latency and PostgreSQL version."""
    start = time.perf_counter()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();")).fetchone()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        version = result[0] if result else "Unknown"
        return {
            "status": "connected",
            "version": version,
            "latency_ms": latency_ms
        }

def init_db():
    """Initializes and verifies the database connection and schema."""
    print("[AirGo] Connecting to Supabase PostgreSQL...")
    try:
        db_status = check_db_connection()
        ver = db_status["version"][:45]
        print(f"[AirGo] Connected to PostgreSQL: {ver}... (Latency: {db_status['latency_ms']}ms)")

        schema_file = Path(__file__).resolve().parent.parent / "schema.sql"
        if schema_file.exists():
            with open(schema_file, mode="r", encoding="utf-8") as f:
                ddl = f.read()
            with engine.connect() as conn:
                conn.execute(text(ddl))
                conn.commit()
            print("[AirGo] Database schema verified and active.")
        else:
            print(f"[AirGo] Warning: {schema_file} not found.")
    except Exception as e:
        print(f"[AirGo] Warning: Database connection check failed: {e}")
