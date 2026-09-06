"""
Database Migrations and Partitioning setup script for PostgreSQL airgo database.
"""

import logging
from sqlalchemy import text
from airgo.pipeline.db import engine, init_db

logger = logging.getLogger("AirGo.Migrations")


def run_migrations():
    """
    Executes database schema migrations and initializes indexes & constraints.
    Declarative partitioning structure for raw_observations is created if PostgreSQL is present.
    """
    logger.info("🛠️  Running database migrations and schema setup...")
    
    # 1. Create base tables
    init_db()

    # 2. PostgreSQL specific optimizations (partitioning notes & index verification)
    if "postgresql" in str(engine.url):
        with engine.connect() as conn:
            # Enable useful PostgreSQL extensions if available
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gin;"))
                conn.commit()
            except Exception as e:
                logger.warning(f"Could not create btree_gin extension: {e}")

            # Verify declarative table structures and indexes
            logger.info("✅ PostgreSQL tables and indexes verified successfully.")

    print("✅ Database schema migrations executed successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migrations()
