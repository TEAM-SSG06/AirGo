"""
AirGo Configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

SUPABASE_DB_URI = os.getenv(
    "SUPABASE_DB_URI",
    os.getenv("DATABASE_URL", "postgresql://postgres.hhmcoffljphnzfrlkewe:Teamssg%402026@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
)
DATABASE_URL = SUPABASE_DB_URI

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Scraper & Runtime Configuration
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
RUNS_DIR = BASE_DIR / "runs"

# Yatra Specific Configuration
YATRA_MAX_CONCURRENCY = int(os.getenv("YATRA_MAX_CONCURRENCY", "2"))
YATRA_REQUEST_DELAY = float(os.getenv("YATRA_REQUEST_DELAY", "2.0"))
YATRA_MAX_RETRIES = int(os.getenv("YATRA_MAX_RETRIES", "3"))
YATRA_BACKOFF_FACTOR = float(os.getenv("YATRA_BACKOFF_FACTOR", "1.5"))

# Headed Mode Observability Settings
HEADED_SLOW_MO_MS = int(os.getenv("HEADED_SLOW_MO_MS", "250"))
HEADED_OBSERVATION_DELAY = float(os.getenv("HEADED_OBSERVATION_DELAY", "3.0"))

