"""
Automated Unit Tests for AirGo Data Pipeline.
Tests:
- Schema validation & model instantiation
- Advance purchase window calculations
- Multi-platform canonical deduplication logic
- Daily market aggregation calculations
- Idempotent database pipeline execution
"""

import unittest
from datetime import date, timedelta
from airgo.pipeline.models import (
    RawObservationSchema, CanonicalFareSchema, DailyAirfareAggregateSchema
)
from airgo.pipeline.deduplicator import AirfareDeduplicator
from airgo.pipeline.aggregator import AirfareAggregator
from airgo.pipeline.orchestrator import PipelineOrchestrator
from airgo.pipeline.db import get_db_session, init_db


class TestDataPipeline(unittest.TestCase):

    def setUp(self):
        init_db()
        self.deduplicator = AirfareDeduplicator()
        self.aggregator = AirfareAggregator()
        self.orchestrator = PipelineOrchestrator()

        self.today = date.today()
        self.travel_date_t7 = self.today + timedelta(days=7)

        # Sample raw observations representing the same underlying flight from 2 OTAs
        self.raw_obs_cleartrip = RawObservationSchema(
            scraping_run_id="test_run_001",
            platform="Cleartrip",
            carrier="IndiGo",
            carrier_code="6E",
            flight_number="6E-201",
            origin="DEL",
            destination="BOM",
            route="DEL-BOM",
            observation_date=self.today,
            travel_date=self.travel_date_t7,
            departure_time="06:00",
            arrival_time="08:15",
            duration_mins=135,
            stops=0,
            advance_purchase_days=7,
            advance_purchase_window="T+7",
            fare_class="Economy",
            fare_family="Standard",
            base_fare=3750.0,
            taxes=1250.0,
            fees=0.0,
            convenience_fee=0.0,
            total_fare=5000.0,
            currency="INR",
            availability="AVAILABLE"
        )

        self.raw_obs_easemytrip = RawObservationSchema(
            scraping_run_id="test_run_001",
            platform="EaseMyTrip",
            carrier="IndiGo",
            carrier_code="6E",
            flight_number="6E-201",
            origin="DEL",
            destination="BOM",
            route="DEL-BOM",
            observation_date=self.today,
            travel_date=self.travel_date_t7,
            departure_time="06:00",
            arrival_time="08:15",
            duration_mins=135,
            stops=0,
            advance_purchase_days=7,
            advance_purchase_window="T+7",
            fare_class="Economy",
            fare_family="Standard",
            base_fare=3600.0,
            taxes=1200.0,
            fees=0.0,
            convenience_fee=0.0,
            total_fare=4800.0,
            currency="INR",
            availability="AVAILABLE"
        )

        self.raw_obs_flight_b = RawObservationSchema(
            scraping_run_id="test_run_001",
            platform="Cleartrip",
            carrier="Air India",
            carrier_code="AI",
            flight_number="AI-805",
            origin="DEL",
            destination="BOM",
            route="DEL-BOM",
            observation_date=self.today,
            travel_date=self.travel_date_t7,
            departure_time="09:30",
            arrival_time="11:45",
            duration_mins=135,
            stops=0,
            advance_purchase_days=7,
            advance_purchase_window="T+7",
            fare_class="Economy",
            fare_family="Standard",
            base_fare=4500.0,
            taxes=1500.0,
            fees=0.0,
            convenience_fee=0.0,
            total_fare=6000.0,
            currency="INR",
            availability="AVAILABLE"
        )

    def test_advance_purchase_days_calculation(self):
        days = (self.travel_date_t7 - self.today).days
        self.assertEqual(days, 7)
        self.assertEqual(self.raw_obs_cleartrip.advance_purchase_window, "T+7")

    def test_deduplication_combines_platforms(self):
        raw_list = [self.raw_obs_cleartrip, self.raw_obs_easemytrip, self.raw_obs_flight_b]
        canonical_fares = self.deduplicator.deduplicate(raw_list)

        # 3 raw quotes from 2 distinct flights -> 2 canonical fare products
        self.assertEqual(len(canonical_fares), 2)
        
        # Flight 6E-201 should be deduplicated
        indigo_canonical = next(c for c in canonical_fares if c.flight_number == "6E-201")
        self.assertEqual(indigo_canonical.platform_count, 2)
        self.assertEqual(indigo_canonical.min_total_fare, 4800.0)
        self.assertEqual(indigo_canonical.max_total_fare, 5000.0)
        self.assertEqual(indigo_canonical.cheapest_platform, "EaseMyTrip")
        self.assertIn("Cleartrip", indigo_canonical.observed_platforms)
        self.assertIn("EaseMyTrip", indigo_canonical.observed_platforms)

    def test_aggregation_metrics(self):
        raw_list = [self.raw_obs_cleartrip, self.raw_obs_easemytrip, self.raw_obs_flight_b]
        aggregates = self.aggregator.compute_daily_aggregates(raw_list)

        self.assertTrue(len(aggregates) > 0)
        overall_agg = next(a for a in aggregates if a.carrier == "ALL" and a.platform == "ALL")
        
        self.assertEqual(overall_agg.observation_count, 3)
        self.assertEqual(overall_agg.unique_flights, 2)
        self.assertEqual(overall_agg.min_fare, 4800.0)
        self.assertEqual(overall_agg.max_fare, 6000.0)
        self.assertEqual(overall_agg.median_fare, 5000.0)

    def test_pipeline_orchestrator_idempotency(self):
        raw_list = [self.raw_obs_cleartrip, self.raw_obs_easemytrip, self.raw_obs_flight_b]
        run_id = "test_run_idempotency_123"
        
        # First execution
        res1 = self.orchestrator.process_and_store_pipeline(raw_list, run_id=run_id)
        self.assertEqual(res1["status"], "SUCCESS")
        self.assertEqual(res1["raw_count"], 3)
        self.assertEqual(res1["canonical_count"], 2)

        # Second execution (Idempotent update)
        res2 = self.orchestrator.process_and_store_pipeline(raw_list, run_id=run_id)
        self.assertEqual(res2["status"], "SUCCESS")
        self.assertEqual(res2["canonical_count"], 2)


if __name__ == "__main__":
    unittest.main()
