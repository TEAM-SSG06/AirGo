"""
AirGo Data Pipeline Master Orchestrator.
Manages end-to-end flow:
Scraper Workers -> Raw Observations -> Validation -> Deduplication -> Daily Aggregations -> Idempotent PostgreSQL Writes.
"""

import os
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy import select, delete

from airgo.pipeline.models import (
    ScrapingRunDB, RawObservationDB, CanonicalFareDB, DailyAirfareAggregateDB, ScraperLogDB,
    RawObservationSchema, CanonicalFareSchema, DailyAirfareAggregateSchema
)
from airgo.pipeline.db import get_db_session
from airgo.pipeline.deduplicator import AirfareDeduplicator
from airgo.pipeline.aggregator import AirfareAggregator

logger = logging.getLogger("AirGo.Orchestrator")


class PipelineOrchestrator:
    """
    Coordinates execution of scraping jobs, data transformation, deduplication,
    aggregation, and idempotent batch database transactions into PostgreSQL.
    """

    def __init__(self):
        self.deduplicator = AirfareDeduplicator()
        self.aggregator = AirfareAggregator()

    def start_scraping_run(self, platform: str, routes_count: int = 0, custom_run_id: Optional[str] = None) -> str:
        """Initializes a new scraping run metadata entry."""
        run_id = custom_run_id or f"run_{platform.lower()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        with get_db_session() as session:
            run_entry = ScrapingRunDB(
                scraping_run_id=run_id,
                platform=platform,
                started_at=datetime.utcnow(),
                status="RUNNING",
                routes_count=routes_count
            )
            session.add(run_entry)
        logger.info(f"🚀 Initialized scraping run: {run_id}")
        return run_id

    def ingest_raw_observations(self, raw_schemas: List[RawObservationSchema]) -> int:
        """
        Idempotently inserts raw airfare observations into PostgreSQL database.
        Ensures foreign key parent scraping_runs entry exists.
        """
        if not raw_schemas:
            return 0

        with get_db_session() as session:
            # Ensure referenced scraping_run_ids exist in scraping_runs table
            run_ids = set(r.scraping_run_id for r in raw_schemas)
            for r_id in run_ids:
                existing_run = session.scalars(
                    select(ScrapingRunDB).where(ScrapingRunDB.scraping_run_id == r_id)
                ).first()
                if not existing_run:
                    sample_platform = next(r.platform for r in raw_schemas if r.scraping_run_id == r_id)
                    session.add(ScrapingRunDB(
                        scraping_run_id=r_id,
                        platform=sample_platform,
                        started_at=datetime.utcnow(),
                        status="RUNNING"
                    ))
            
            # Flush parent scraping_runs rows to PostgreSQL before bulk_save_objects
            session.flush()

            raw_db_objects = [
                RawObservationDB(
                    scraping_run_id=r.scraping_run_id,
                    platform=r.platform,
                    carrier=r.carrier,
                    carrier_code=r.carrier_code,
                    flight_number=r.flight_number,
                    origin=r.origin,
                    destination=r.destination,
                    route=r.route,
                    observation_date=r.observation_date,
                    travel_date=r.travel_date,
                    departure_time=r.departure_time,
                    arrival_time=r.arrival_time,
                    duration_mins=r.duration_mins,
                    stops=r.stops,
                    advance_purchase_days=r.advance_purchase_days,
                    advance_purchase_window=r.advance_purchase_window,
                    fare_class=r.fare_class,
                    fare_family=r.fare_family,
                    base_fare=r.base_fare,
                    taxes=r.taxes,
                    fees=r.fees,
                    convenience_fee=r.convenience_fee,
                    total_fare=r.total_fare,
                    currency=r.currency,
                    availability=r.availability,
                    source_url=r.source_url,
                    raw_payload=r.raw_payload
                )
                for r in raw_schemas
            ]
            session.bulk_save_objects(raw_db_objects)

        logger.info(f"📥 Saved {len(raw_schemas)} raw observations to PostgreSQL.")
        return len(raw_schemas)

    def process_and_store_pipeline(self, raw_schemas: List[RawObservationSchema], run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes full downstream pipeline:
        Raw Ingestion -> Deduplication -> Aggregation -> PostgreSQL Commit.
        """
        if not raw_schemas:
            logger.warning("Empty raw observation payload provided to pipeline.")
            return {"raw_count": 0, "canonical_count": 0, "aggregate_count": 0, "status": "EMPTY"}

        active_run_id = run_id or raw_schemas[0].scraping_run_id

        # 1. Ingest raw observations
        raw_count = self.ingest_raw_observations(raw_schemas)

        # 2. Canonical Deduplication
        canonical_schemas = self.deduplicator.deduplicate(raw_schemas)
        
        # 3. Daily Aggregations
        aggregate_schemas = self.aggregator.compute_daily_aggregates(raw_schemas)

        # 4. Idempotent Writes for Canonical & Aggregate tables
        with get_db_session() as session:
            # Canonical fares upsert logic
            for c in canonical_schemas:
                existing = session.scalars(
                    select(CanonicalFareDB).where(CanonicalFareDB.canonical_id == c.canonical_id)
                ).first()
                
                if existing:
                    existing.min_total_fare = c.min_total_fare
                    existing.avg_total_fare = c.avg_total_fare
                    existing.max_total_fare = c.max_total_fare
                    existing.platform_count = c.platform_count
                    existing.observed_platforms = c.observed_platforms
                else:
                    session.add(CanonicalFareDB(
                        canonical_id=c.canonical_id,
                        route=c.route,
                        origin=c.origin,
                        destination=c.destination,
                        carrier=c.carrier,
                        flight_number=c.flight_number,
                        observation_date=c.observation_date,
                        travel_date=c.travel_date,
                        departure_time=c.departure_time,
                        arrival_time=c.arrival_time,
                        advance_purchase_days=c.advance_purchase_days,
                        advance_purchase_window=c.advance_purchase_window,
                        fare_class=c.fare_class,
                        fare_family=c.fare_family,
                        stops=c.stops,
                        min_total_fare=c.min_total_fare,
                        avg_total_fare=c.avg_total_fare,
                        max_total_fare=c.max_total_fare,
                        base_fare=c.base_fare,
                        taxes=c.taxes,
                        fees=c.fees,
                        convenience_fee=c.convenience_fee,
                        cheapest_platform=c.cheapest_platform,
                        platform_count=c.platform_count,
                        observed_platforms=c.observed_platforms
                    ))

            # Daily Aggregates upsert logic
            for a in aggregate_schemas:
                existing_agg = session.scalars(
                    select(DailyAirfareAggregateDB).where(DailyAirfareAggregateDB.aggregate_key == a.aggregate_key)
                ).first()
                
                if existing_agg:
                    existing_agg.observation_count = a.observation_count
                    existing_agg.unique_flights = a.unique_flights
                    existing_agg.average_fare = a.average_fare
                    existing_agg.median_fare = a.median_fare
                    existing_agg.min_fare = a.min_fare
                    existing_agg.max_fare = a.max_fare
                    existing_agg.average_base_fare = a.average_base_fare
                    existing_agg.average_taxes = a.average_taxes
                    existing_agg.average_fees = a.average_fees
                else:
                    session.add(DailyAirfareAggregateDB(
                        aggregate_key=a.aggregate_key,
                        route=a.route,
                        observation_date=a.observation_date,
                        advance_purchase_window=a.advance_purchase_window,
                        carrier=a.carrier,
                        platform=a.platform,
                        observation_count=a.observation_count,
                        unique_flights=a.unique_flights,
                        average_fare=a.average_fare,
                        median_fare=a.median_fare,
                        min_fare=a.min_fare,
                        max_fare=a.max_fare,
                        average_base_fare=a.average_base_fare,
                        average_taxes=a.average_taxes,
                        average_fees=a.average_fees
                    ))

            # Update Scraping Run Metadata
            run_entry = session.scalars(
                select(ScrapingRunDB).where(ScrapingRunDB.scraping_run_id == active_run_id)
            ).first()
            if run_entry:
                run_entry.status = "SUCCESS"
                run_entry.completed_at = datetime.utcnow()
                run_entry.total_raw_records = raw_count
                run_entry.total_clean_records = len(canonical_schemas)

        summary = {
            "run_id": active_run_id,
            "raw_count": raw_count,
            "canonical_count": len(canonical_schemas),
            "aggregate_count": len(aggregate_schemas),
            "status": "SUCCESS"
        }
        logger.info(f"✨ [Pipeline Orchestrator] Complete! Summary: {summary}")
        return summary
