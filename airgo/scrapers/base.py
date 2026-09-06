<<<<<<< HEAD
"""
AirGo Base Scraper Class.
"""

import time
import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from airgo.pipeline.models import RawQuoteSchema
=======
import time
import random
import logging
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import requests
from airgo.pipeline.models import RawObservationSchema

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AirGoScraper")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15


class BaseScraper(ABC):
    """
<<<<<<< HEAD
    Abstract Base Class for all AirGo Flight Scrapers.
    """

    def __init__(self, name: str, rate_limit_secs: float = 1.0):
        self.name = name
        self.rate_limit_secs = rate_limit_secs
        self.last_request_time = 0.0
        self.logger = logging.getLogger(f"AirGoScraper.{name}")

    def enforce_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_secs:
            time.sleep(self.rate_limit_secs - elapsed)
        self.last_request_time = time.time()
=======
    Abstract base class for all airline and OTA scrapers.
    Implements ethical scraping controls, rate limiting, and standard parsing interfaces.
    """

    def __init__(self, name: str, rate_limit_secs: float = 1.0, max_retries: int = 3):
        self.name = name
        self.rate_limit_secs = rate_limit_secs
        self.max_retries = max_retries
        self.session = requests.Session()
        self.logger = logging.getLogger(f"AirGoScraper.{self.name}")

    def get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Connection": "keep-alive"
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def throttle(self):
        jitter = random.uniform(0.1, 0.4)
        time.sleep(self.rate_limit_secs + jitter)
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15

    @abstractmethod
    def fetch_quotes(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        advance_window: str,
        advance_days: int,
<<<<<<< HEAD
        **kwargs
    ) -> List[RawQuoteSchema]:
        """
        Extract flight quotes from live platform.
        """
        pass
=======
        run_id: str = "run_default"
    ) -> List[RawObservationSchema]:
        pass

    def run_safe(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        advance_window: str,
        advance_days: int,
        run_id: str = "run_default"
    ) -> List[RawObservationSchema]:
        retries = 0
        while retries < self.max_retries:
            try:
                self.throttle()
                start_time = time.time()
                quotes = self.fetch_quotes(origin, destination, departure_date, advance_window, advance_days, run_id=run_id)
                elapsed_ms = int((time.time() - start_time) * 1000)
                self.logger.info(
                    f"[{self.name}] {origin}->{destination} ({advance_window}, {departure_date}): "
                    f"Captured {len(quotes)} quotes in {elapsed_ms}ms"
                )
                return quotes
            except Exception as e:
                retries += 1
                backoff_wait = (2 ** retries) + random.uniform(0.2, 0.8)
                self.logger.warning(f"[{self.name}] Attempt {retries}/{self.max_retries} failed for {origin}->{destination}: {e}")
                time.sleep(backoff_wait)
        return []
>>>>>>> d7c1d6567af5b775241f0d2d708476c05b75ed15
