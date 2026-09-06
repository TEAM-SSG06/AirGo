"""
Unit and Integration Test Suite for EaseMyTrip Data Pipeline Integration.
Validates multi-platform ingestion, PostgreSQL persistence, canonical deduplication, and daily aggregate calculations.
"""

import os
import sys
import pytest
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from airgo.pipeline.models import RawObservationSchema, RawObservationDB, CanonicalFareDB, DailyAirfareAggregateDB, ScrapingRunDB
from airgo.pipeline.orchestrator import PipelineOrchestrator
from airgo.pipeline.migrations import run_migrations
from airgo.pipeline.db import engine as global_engine, init_db


@pytest.fixture(scope="module")
def db_engine():
    init_db()
    run_migrations()
    return global_engine


def test_easemytrip_observation_schema_validation():
    """Verify RawObservationSchema creation for EaseMyTrip observation DTO."""
    today = date.today()
    travel_dt = today + timedelta(days=7)

    obs = RawObservationSchema(
        scraping_run_id="run_emt_test_001",
        platform="EaseMyTrip",
        carrier="IndiGo",
        carrier_code="6E",
        flight_number="6E-201",
        origin="BOM",
        destination="DEL",
        route="BOM-DEL",
        observation_date=today,
        travel_date=travel_dt,
        departure_time="06:00",
        arrival_time="08:15",
        duration_mins=135,
        stops=0,
        advance_purchase_days=7,
        advance_purchase_window="T+7",
        fare_class="Economy",
        fare_family="Standard",
        base_fare=3700.0,
        taxes=1100.0,
        fees=0.0,
        convenience_fee=350.0,
        total_fare=4800.0,
        currency="INR",
        availability="AVAILABLE",
        source_url="https://flight.easemytrip.com/FlightList/Index?srch=BOM-DEL",
        raw_payload={"flight": "6E-201", "price": 4800.0}
    )

    assert obs.platform == "EaseMyTrip"
    assert obs.flight_number == "6E-201"
    assert obs.total_fare == 4800.0
    assert obs.route == "BOM-DEL"


def test_easemytrip_multi_platform_ingestion_and_deduplication(db_engine):
    """
    Test ingesting both Cleartrip and EaseMyTrip observations for the same flight.
    Verifies that canonical deduplication selects the cheapest total fare across platforms.
    """
    orchestrator = PipelineOrchestrator()
    today = date.today()
    travel_dt = today + timedelta(days=15)
    run_id = f"test_run_multi_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

    # Start scraping run
    orchestrator.start_scraping_run("MultiPlatformTest", routes_count=1, custom_run_id=run_id)

    # Observation 1: Cleartrip fare = 5200.0
    obs_cleartrip = RawObservationSchema(
        scraping_run_id=run_id,
        platform="Cleartrip",
        carrier="Air India Express",
        carrier_code="IX",
        flight_number="IX-105",
        origin="BOM",
        destination="DEL",
        route="BOM-DEL",
        observation_date=today,
        travel_date=travel_dt,
        departure_time="14:00",
        arrival_time="16:15",
        duration_mins=135,
        stops=0,
        advance_purchase_days=15,
        advance_purchase_window="T+15",
        fare_class="Economy",
        fare_family="Standard",
        base_fare=4000.0,
        taxes=1200.0,
        fees=0.0,
        convenience_fee=300.0,
        total_fare=5200.0,
        currency="INR",
        availability="AVAILABLE"
    )

    # Observation 2: EaseMyTrip fare = 4950.0 (Cheaper!)
    obs_easemytrip = RawObservationSchema(
        scraping_run_id=run_id,
        platform="EaseMyTrip",
        carrier="Air India Express",
        carrier_code="IX",
        flight_number="IX-105",
        origin="BOM",
        destination="DEL",
        route="BOM-DEL",
        observation_date=today,
        travel_date=travel_dt,
        departure_time="14:00",
        arrival_time="16:15",
        duration_mins=135,
        stops=0,
        advance_purchase_days=15,
        advance_purchase_window="T+15",
        fare_class="Economy",
        fare_family="Standard",
        base_fare=3800.0,
        taxes=1150.0,
        fees=0.0,
        convenience_fee=350.0,
        total_fare=4950.0,
        currency="INR",
        availability="AVAILABLE"
    )

    res = orchestrator.process_and_store_pipeline([obs_cleartrip, obs_easemytrip], run_id=run_id)

    assert res["status"] == "SUCCESS"
    assert res["raw_count"] == 2

    # Query canonical fare table to verify cheapest fare selection
    Session = sessionmaker(bind=db_engine)
    session = Session()

    canonical = session.query(CanonicalFareDB).filter(
        CanonicalFareDB.route == "BOM-DEL",
        CanonicalFareDB.flight_number == "IX-105",
        CanonicalFareDB.travel_date == travel_dt
    ).first()

    assert canonical is not None
    # EaseMyTrip (4950.0) should win over Cleartrip (5200.0) for canonical fare
    assert float(canonical.min_total_fare) == 4950.0
    assert canonical.cheapest_platform == "EaseMyTrip"

    # Query daily aggregates
    aggregate = session.query(DailyAirfareAggregateDB).filter(
        DailyAirfareAggregateDB.route == "BOM-DEL",
        DailyAirfareAggregateDB.observation_date == today,
        DailyAirfareAggregateDB.advance_purchase_window == "T+15"
    ).first()

    assert aggregate is not None
    assert aggregate.observation_count >= 1
    session.close()
