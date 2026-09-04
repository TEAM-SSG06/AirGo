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
