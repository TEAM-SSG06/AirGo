"""
Configuration settings for the Yatra scraper module.
Reuses central AirGo configuration and provides safe defaults.
"""

from pathlib import Path
from pydantic import BaseModel, Field
from airgo.config import (
    HEADLESS,
    RUNS_DIR,
    YATRA_MAX_CONCURRENCY,
    YATRA_REQUEST_DELAY,
    YATRA_MAX_RETRIES,
    YATRA_BACKOFF_FACTOR,
    HEADED_SLOW_MO_MS,
    HEADED_OBSERVATION_DELAY,
)


class YatraScraperConfig(BaseModel):
    """Configuration schema for Yatra scraping runs."""

    platform_name: str = "Yatra"
    base_url: str = "https://flight.yatra.com/air-search-ui/dom2/trigger"
    headless: bool = Field(default_factory=lambda: HEADLESS)
    max_concurrency: int = Field(default_factory=lambda: YATRA_MAX_CONCURRENCY)
    request_delay: float = Field(default_factory=lambda: YATRA_REQUEST_DELAY)
    max_retries: int = Field(default_factory=lambda: YATRA_MAX_RETRIES)
    backoff_factor: float = Field(default_factory=lambda: YATRA_BACKOFF_FACTOR)
    browser_timeout_ms: int = 30000
    slow_mo_ms: int = Field(default_factory=lambda: HEADED_SLOW_MO_MS if not HEADLESS else 0)
    observation_delay: float = Field(default_factory=lambda: HEADED_OBSERVATION_DELAY if not HEADLESS else 0.0)
    runs_dir: Path = Field(default_factory=lambda: RUNS_DIR)

    model_config = {"arbitrary_types_allowed": True}


# Default singleton configuration instance
DEFAULT_YATRA_CONFIG = YatraScraperConfig()
