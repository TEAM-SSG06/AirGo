<<<<<<< HEAD
"""
AirGo Scraping Orchestrator.
Coordinates multi-source scraping across Cleartrip, EaseMyTrip, and Ixigo.
"""

from typing import List, Dict, Any
from datetime import date, timedelta
from airgo.scrapers.cleartrip_scraper import CleartripScraper
from airgo.scrapers.easemytrip_scraper import EaseMyTripScraper
from airgo.scrapers.ixigo_scraper import IxigoScraper
from airgo.pipeline.models import RawQuoteSchema


class ScrapingOrchestrator:
    def __init__(self, headless: bool = True):
        self.cleartrip = CleartripScraper(headless=headless)
        self.easemytrip = EaseMyTripScraper()
        self.ixigo = IxigoScraper()

    def run_batch(self, max_routes: int = 4) -> Dict[str, Any]:
        routes = [("DEL", "BOM"), ("BLR", "DEL"), ("BLR", "BOM"), ("DEL", "HYD")][:max_routes]
        tomorrow = date.today() + timedelta(days=1)
        results = {}

        for orig, dest in routes:
            route_key = f"{orig}-{dest}"
            quotes = self.cleartrip.fetch_quotes(
                origin=orig,
                destination=dest,
                departure_date=tomorrow,
                advance_window="T+1",
                advance_days=1
            )
            results[route_key] = len(quotes)

        return {"total_routes": len(routes), "results": results}
=======
import uuid
import time
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from airgo.pipeline.models import RawQuoteSchema, RawQuoteDB, ScraperLogDB
from airgo.pipeline.db import get_db_session
from airgo.engine.dgca_weights import DGCA_ROUTES, ADVANCE_WINDOWS
from airgo.scrapers.playwright_scraper import PlaywrightFlightScraper
from airgo.scrapers.easemytrip_scraper import EaseMyTripScraper
from airgo.scrapers.ixigo_scraper import IxigoScraper

logger = logging.getLogger("AirGo.Orchestrator")


class ScrapingOrchestrator:
    """
    Coordinates 100% Real Live Multi-Source Web Scraping in Visible (Non-Headless) Browser Mode.
    Opens real Chromium browser windows directly on your screen.
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright_scraper = PlaywrightFlightScraper(headless=headless, rate_limit_secs=1.0)
        self.easemytrip_scraper = EaseMyTripScraper(rate_limit_secs=0.8)
        self.ixigo_scraper = IxigoScraper(rate_limit_secs=0.8)

    def run_batch(
        self,
        routes: Optional[List[str]] = None,
        windows: Optional[List[str]] = None,
        max_routes: int = 4
    ) -> Dict[str, Any]:
        """
        Execute live web scrape across target routes x advance-purchase windows with visible browser window.
        """
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        start_time = time.time()
        
        target_routes = routes or list(DGCA_ROUTES.keys())[:max_routes]
        target_windows = windows or list(ADVANCE_WINDOWS.keys())

        logger.info(f"🚀 [Orchestrator] Starting VISIBLE BROWSER Scrape {run_id} | Routes: {len(target_routes)} | Windows: {len(target_windows)}")
        
        total_quotes: List[RawQuoteSchema] = []
        today = date.today()

        for route_code in target_routes:
            if route_code not in DGCA_ROUTES:
                continue
            origin = DGCA_ROUTES[route_code]["origin"]
            destination = DGCA_ROUTES[route_code]["destination"]

            for win_code in target_windows:
                if win_code not in ADVANCE_WINDOWS:
                    continue
                lead_days = ADVANCE_WINDOWS[win_code]["days"]
                departure_date = today + timedelta(days=lead_days)

                t0 = time.time()
                try:
                    quotes = self.playwright_scraper.fetch_quotes(
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        advance_window=win_code,
                        advance_days=lead_days
                    )
                    
                    if not quotes:
                        quotes = self.easemytrip_scraper.run_safe(
                            origin=origin,
                            destination=destination,
                            departure_date=departure_date,
                            advance_window=win_code,
                            advance_days=lead_days
                        )

                    duration_ms = int((time.time() - t0) * 1000)
                    status = "SUCCESS" if quotes else "EMPTY"
                    
                    self._save_log(run_id, "Playwright Visible Chromium", route_code, win_code, departure_date, status, len(quotes), duration_ms)
                    total_quotes.extend(quotes)
                except Exception as e:
                    duration_ms = int((time.time() - t0) * 1000)
                    self._save_log(run_id, "Playwright Visible Chromium", route_code, win_code, departure_date, "FAILED", 0, duration_ms, str(e))
                    logger.error(f"Scraper error on {route_code}: {e}")

        # Persist raw quotes to DB
        saved_count = self._save_raw_quotes(total_quotes)
        total_duration = round(time.time() - start_time, 2)

        summary = {
            "run_id": run_id,
            "total_routes": len(target_routes),
            "total_windows": len(target_windows),
            "quotes_extracted": len(total_quotes),
            "quotes_saved": saved_count,
            "duration_seconds": total_duration,
            "status": "COMPLETED"
        }
        logger.info(f"✅ [Orchestrator] Finished in {total_duration}s. Real quotes extracted: {len(total_quotes)}")
        return summary

    def _save_log(self, run_id: str, source: str, route: str, window: str, dep_date: date, status: str, count: int, duration_ms: int, error: Optional[str] = None):
        try:
            with get_db_session() as session:
                log_entry = ScraperLogDB(
                    run_id=run_id,
                    source=source,
                    route=route,
                    advance_window=window,
                    departure_date=dep_date,
                    status=status,
                    flights_found=count,
                    duration_ms=duration_ms,
                    error_message=error
                )
                session.add(log_entry)
        except Exception as err:
            logger.debug(f"Log save note: {err}")

    def _save_raw_quotes(self, quotes: List[RawQuoteSchema]) -> int:
        if not quotes:
            return 0
        saved = 0
        try:
            with get_db_session() as session:
                db_objs = [
                    RawQuoteDB(
                        source=q.source,
                        carrier=q.carrier,
                        carrier_code=q.carrier_code,
                        flight_number=q.flight_number,
                        origin=q.origin,
                        destination=q.destination,
                        departure_datetime=q.departure_datetime,
                        arrival_datetime=q.arrival_datetime,
                        duration_mins=q.duration_mins,
                        stops=q.stops,
                        booking_date=q.booking_date,
                        advance_window=q.advance_window,
                        advance_days=q.advance_days,
                        fare_class=q.fare_class,
                        base_fare=q.base_fare,
                        surcharges=q.surcharges,
                        taxes=q.taxes,
                        convenience_fee=q.convenience_fee,
                        total_fare=q.total_fare,
                        is_sold_out=q.is_sold_out,
                        seats_remaining=q.seats_remaining,
                        metadata_json=q.metadata_json
                    )
                    for q in quotes
                ]
                session.bulk_save_objects(db_objs)
                saved = len(db_objs)
        except Exception as e:
            logger.error(f"Error saving raw quotes: {e}")
        return saved
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
