"""
FastAPI Server connected to Supabase PostgreSQL.
Provides a simple health API endpoint and database verification.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from airgo.db import check_db_connection, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup checks."""
    print("=======================================================")
    print("[AirGo] Launching FastAPI Server...")
    try:
        db_status = check_db_connection()
        ver = db_status["version"][:45]
        print(f"[AirGo] Supabase PostgreSQL Connected: {ver}... (Latency: {db_status['latency_ms']}ms)")
    except Exception as e:
        print(f"[AirGo] Warning: Supabase connection failed: {e}")
    print("=======================================================")
    yield
    print("[AirGo] FastAPI Server Shutting Down...")


app = FastAPI(
    title="AirGo APIx Server",
    description="FastAPI server connected to Supabase PostgreSQL with health verification.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    """
    Simple health check API endpoint verifying service and database status.
    """
    db_status = check_db_connection()

    # Verify tables in the database
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)).fetchall()
        tables = [r[0] for r in result]

    return {
        "status": "healthy",
        "service": "AirGo APIx",
        "database": db_status,
        "tables_count": len(tables),
        "tables": tables,
    }


@app.get("/", tags=["Root"])
def root():
    """Root entrypoint."""
    return {
        "service": "AirGo APIx Server",
        "version": "1.0.0",
        "status": "online",
        "health_endpoint": "/health",
        "scrapers_endpoint": "/api/scrapers",
        "scrape_trigger_endpoint": "/api/scrape",
        "docs": "/docs",
    }


# -----------------------------------------------------------------------------
# Scraper Dispatch Endpoints (Pure Single-Threaded Event Loop, Zero DB writes)
# -----------------------------------------------------------------------------
from pydantic import BaseModel, Field
from typing import List
from fastapi import HTTPException
from airgo.scrapers.registry import run_scraper, SUPPORTED_PLATFORMS


class ScrapeRequest(BaseModel):
    platform: str = Field(..., description="Target platform (e.g. 'makemytrip', 'easemytrip', 'cleartrip')", example="makemytrip")
    route: str = Field(default="BOM-DEL", description="Route sector 'ORIGIN-DEST'", example="BOM-DEL")
    horizons: List[int] = Field(default=[7], description="Advance purchase windows in days", example=[7])
    headless: bool = Field(default=False, description="Run headless or visible browser")
    deep_checkout: bool = Field(default=False, description="Whether to execute deep checkout audit")


@app.get("/api/scrapers", tags=["Scrapers"])
def get_supported_scrapers():
    """Returns the list of supported scrapers available in AirGo."""
    return {
        "supported_platforms": SUPPORTED_PLATFORMS,
        "count": len(SUPPORTED_PLATFORMS)
    }


@app.post("/api/scrape", tags=["Scrapers"])
async def trigger_scrape(req: ScrapeRequest):
    """
    Executes a scraper directly on FastAPI's single-threaded event loop.
    Returns the harvested flight cards in-memory without writing to the database.
    """
    try:
        quotes = await run_scraper(
            platform=req.platform,
            route=req.route,
            horizons=req.horizons,
            headless=req.headless,
            deep_checkout=req.deep_checkout
        )
        return {
            "status": "success",
            "platform": req.platform,
            "route": req.route,
            "horizons": req.horizons,
            "quotes_count": len(quotes),
            "quotes": quotes
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Scraper error: {str(e)}")

