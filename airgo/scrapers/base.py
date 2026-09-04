"""
AirGo Base Scraper Class.
"""

import time
import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from airgo.pipeline.models import RawQuoteSchema


class BaseScraper(ABC):
    """
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

    @abstractmethod
    def fetch_quotes(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        advance_window: str,
        advance_days: int,
        **kwargs
    ) -> List[RawQuoteSchema]:
        """
        Extract flight quotes from live platform.
        """
        pass
