"""
<<<<<<< HEAD
AirGo Data Pipeline Pydantic Schemas and Database Models.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class RawQuoteSchema(BaseModel):
    source: str = "Cleartrip"
    platform: Optional[str] = None
=======
SQLAlchemy ORM Models and Pydantic Schemas for AirGo Data Pipeline.
Supports PostgreSQL (with declarative partitioning readiness) and SQLite fallback.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean, JSON, Index, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ==========================================
# 1. Scraping Run Metadata Table
# ==========================================

class ScrapingRunDB(Base):
    """Execution metadata tracking each pipeline scraping run."""
    __tablename__ = "scraping_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraping_run_id = Column(String(100), nullable=False, unique=True, index=True)
    platform = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="RUNNING", index=True)  # RUNNING, SUCCESS, FAILED
    routes_count = Column(Integer, default=0)
    total_raw_records = Column(Integer, default=0)
    total_clean_records = Column(Integer, default=0)
    notes = Column(String(500), nullable=True)

    raw_observations = relationship("RawObservationDB", back_populates="scraping_run")


# ==========================================
# 2. Raw Observations Table (High Volume)
# ==========================================

class RawObservationDB(Base):
    """
    Raw scraped airfare observation directly captured from platform/OTA.
    Preserves exact un-mutated source fields.
    Supports declarative time-based partitioning on observation_date in PostgreSQL.
    """
    __tablename__ = "raw_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraping_run_id = Column(String(100), ForeignKey("scraping_runs.scraping_run_id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    carrier = Column(String(50), nullable=False, index=True)
    carrier_code = Column(String(10), nullable=True)
    flight_number = Column(String(20), nullable=False, index=True)
    
    origin = Column(String(10), nullable=False, index=True)
    destination = Column(String(10), nullable=False, index=True)
    route = Column(String(20), nullable=False, index=True)
    
    observation_date = Column(Date, nullable=False, index=True)
    travel_date = Column(Date, nullable=False, index=True)
    departure_time = Column(String(10), nullable=False)
    arrival_time = Column(String(10), nullable=True)
    duration_mins = Column(Integer, nullable=True)
    stops = Column(Integer, default=0)
    
    advance_purchase_days = Column(Integer, nullable=False, index=True)
    advance_purchase_window = Column(String(10), nullable=False, index=True)  # e.g., T+0, T+1, T+7, T+15, T+30, T+45
    
    fare_class = Column(String(30), default="Economy")
    fare_family = Column(String(50), default="Standard")
    
    base_fare = Column(Float, nullable=True)
    taxes = Column(Float, nullable=True)
    fees = Column(Float, nullable=True)
    convenience_fee = Column(Float, default=0.0)
    total_fare = Column(Float, nullable=False, index=True)
    currency = Column(String(10), default="INR")
    availability = Column(String(20), default="AVAILABLE")
    
    source_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    raw_payload = Column(JSON, nullable=True)

    scraping_run = relationship("ScrapingRunDB", back_populates="raw_observations")

    __table_args__ = (
        Index("ix_raw_route_obs_travel", "route", "observation_date", "travel_date"),
        Index("ix_raw_obs_window", "observation_date", "advance_purchase_window"),
    )


# ==========================================
# 3. Canonical Clean Airfares Table
# ==========================================

class CanonicalFareDB(Base):
    """
    Normalized, deduplicated canonical airfare records across platforms.
    Deduplicated by: (origin, destination, travel_date, carrier, flight_number, departure_time, fare_class).
    """
    __tablename__ = "canonical_fares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_id = Column(String(150), nullable=False, unique=True, index=True)
    
    route = Column(String(20), nullable=False, index=True)
    origin = Column(String(10), nullable=False, index=True)
    destination = Column(String(10), nullable=False, index=True)
    carrier = Column(String(50), nullable=False, index=True)
    flight_number = Column(String(20), nullable=False, index=True)
    
    observation_date = Column(Date, nullable=False, index=True)
    travel_date = Column(Date, nullable=False, index=True)
    departure_time = Column(String(10), nullable=False)
    arrival_time = Column(String(10), nullable=True)
    
    advance_purchase_days = Column(Integer, nullable=False, index=True)
    advance_purchase_window = Column(String(10), nullable=False, index=True)
    
    fare_class = Column(String(30), default="Economy")
    fare_family = Column(String(50), default="Standard")
    stops = Column(Integer, default=0)
    
    min_total_fare = Column(Float, nullable=False, index=True)
    avg_total_fare = Column(Float, nullable=False)
    max_total_fare = Column(Float, nullable=False)
    
    base_fare = Column(Float, nullable=False)
    taxes = Column(Float, nullable=False)
    fees = Column(Float, nullable=False)
    convenience_fee = Column(Float, default=0.0)
    
    cheapest_platform = Column(String(50), nullable=False)
    platform_count = Column(Integer, default=1)
    observed_platforms = Column(String(200), nullable=False)  # Comma-separated list of OTAs/Airlines
    
    is_outlier = Column(Boolean, default=False, index=True)
    outlier_reason = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_canon_route_travel_adv", "route", "travel_date", "advance_purchase_window"),
    )


# ==========================================
# 4. Daily Airfare Aggregates Table
# ==========================================

class DailyAirfareAggregateDB(Base):
    """
    Analytics-ready daily aggregates by route, observation_date, advance_purchase_window, carrier, platform.
    Used for Airfare Price Index (APIx) and market load metrics.
    """
    __tablename__ = "daily_airfare_aggregates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aggregate_key = Column(String(150), nullable=False, unique=True, index=True)
    
    route = Column(String(20), nullable=False, index=True)
    observation_date = Column(Date, nullable=False, index=True)
    advance_purchase_window = Column(String(10), nullable=False, index=True)
    carrier = Column(String(50), default="ALL", index=True)
    platform = Column(String(50), default="ALL", index=True)
    
    observation_count = Column(Integer, nullable=False)
    unique_flights = Column(Integer, nullable=False)
    
    average_fare = Column(Float, nullable=False)
    median_fare = Column(Float, nullable=False)
    min_fare = Column(Float, nullable=False)
    max_fare = Column(Float, nullable=False)
    
    average_base_fare = Column(Float, nullable=False)
    average_taxes = Column(Float, nullable=False)
    average_fees = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_daily_agg_query", "route", "observation_date", "advance_purchase_window"),
    )


# ==========================================
# 5. Scraper Log Table
# ==========================================

class ScraperLogDB(Base):
    """Execution logs for scraper worker tasks."""
    __tablename__ = "scraper_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraping_run_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    route = Column(String(20), nullable=False)
    advance_purchase_window = Column(String(10), nullable=False)
    travel_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)  # SUCCESS, WARNING, FAILED
    flights_found = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==========================================
# Pydantic Schemas / DTOs
# ==========================================

class RawObservationSchema(BaseModel):
    scraping_run_id: str
    platform: str
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
    carrier: str
    carrier_code: Optional[str] = None
    flight_number: str
    origin: str
    destination: str
<<<<<<< HEAD
    departure_date: Optional[date] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    duration_mins: Optional[int] = None
    stops: int = 0
    booking_date: Optional[date] = None
    audit_timestamp: Optional[str] = None
    advance_window: str
    advance_days: int
    fare_class: str = "Economy"
    base_fare: float = 0.0
    surcharges: float = 0.0
    taxes: float = 0.0
    seat_surcharge: float = 0.0
    convenience_fee: float = 0.0
    total_fare: float = 0.0
    final_payable_fare: float = 0.0
    search_url: Optional[str] = None
    source_url: Optional[str] = None
    is_sold_out: bool = False
    seats_remaining: Optional[int] = None
    has_zero_dummy_proof: bool = True
    metadata_json: Optional[Dict[str, Any]] = None
    screenshots: Optional[Dict[str, str]] = None
    seat_matrix: Optional[Dict[str, Any]] = None

    @model_validator(mode='before')
    @classmethod
    def populate_defaults(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if not values.get("platform"):
                values["platform"] = values.get("source", "Cleartrip")
            if not values.get("source"):
                values["source"] = values.get("platform", "Cleartrip")
            if not values.get("audit_timestamp"):
                values["audit_timestamp"] = datetime.utcnow().isoformat() + "Z"
            if not values.get("search_url"):
                values["search_url"] = values.get("source_url", "")
            if not values.get("source_url"):
                values["source_url"] = values.get("search_url", "")
            if not values.get("final_payable_fare"):
                values["final_payable_fare"] = values.get("total_fare", 0.0)
            if not values.get("total_fare"):
                values["total_fare"] = values.get("final_payable_fare", 0.0)
        return values


class RawQuoteDB(BaseModel):
    id: Optional[int] = None
    platform: str
    audit_timestamp: str
    search_url: str
    origin: str
    destination: str
    departure_date: str
    advance_window: str
    advance_days: int
    carrier: str
    flight_number: str
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    stops: int = 0
    base_fare: float = 0.0
    taxes: float = 0.0
    seat_surcharge: float = 0.0
    final_payable_fare: float = 0.0
    has_zero_dummy_proof: bool = True
=======
    route: str
    observation_date: date
    travel_date: date
    departure_time: str
    arrival_time: Optional[str] = None
    duration_mins: Optional[int] = None
    stops: int = 0
    advance_purchase_days: int
    advance_purchase_window: str
    fare_class: str = "Economy"
    fare_family: str = "Standard"
    base_fare: Optional[float] = None
    taxes: Optional[float] = None
    fees: Optional[float] = None
    convenience_fee: float = 0.0
    total_fare: float
    currency: str = "INR"
    availability: str = "AVAILABLE"
    source_url: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None


class CanonicalFareSchema(BaseModel):
    canonical_id: str
    route: str
    origin: str
    destination: str
    carrier: str
    flight_number: str
    observation_date: date
    travel_date: date
    departure_time: str
    arrival_time: Optional[str] = None
    advance_purchase_days: int
    advance_purchase_window: str
    fare_class: str = "Economy"
    fare_family: str = "Standard"
    stops: int = 0
    min_total_fare: float
    avg_total_fare: float
    max_total_fare: float
    base_fare: float
    taxes: float
    fees: float
    convenience_fee: float = 0.0
    cheapest_platform: str
    platform_count: int = 1
    observed_platforms: str


class DailyAirfareAggregateSchema(BaseModel):
    aggregate_key: str
    route: str
    observation_date: date
    advance_purchase_window: str
    carrier: str = "ALL"
    platform: str = "ALL"
    observation_count: int
    unique_flights: int
    average_fare: float
    median_fare: float
    min_fare: float
    max_fare: float
    average_base_fare: float
    average_taxes: float
    average_fees: float
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
