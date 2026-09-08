"""Configuration for the Ixigo-only collector."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[3]
DEFAULT_ROUTES_FILE = PACKAGE_DIR / "data" / "processed" / "dgca_top100_route_basket.csv"
DEFAULT_RUNS_DIR = PACKAGE_DIR / "runs"


@dataclass(frozen=True)
class IxigoConfig:
    routes_file: Path = DEFAULT_ROUTES_FILE
    runs_dir: Path = DEFAULT_RUNS_DIR
    lead_times: tuple[int, ...] = (1, 7, 15, 30, 45)
    top_routes: int = 3
    min_delay_seconds: float = 2.0
    max_jitter_seconds: float = 1.5
    retry_backoff_seconds: float = 3.0
    timeout_ms: int = 30_000
    headless: bool = True
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    locale: str = "en-IN"
    viewport: dict[str, int] = field(default_factory=lambda: {"width": 1440, "height": 1000})
    search_url_template: str = (
        "https://www.ixigo.com/search/result/flight/{origin}/{destination}/{travel_date}/1/0/0/e"
    )
    robots_url: str = "https://www.ixigo.com/robots.txt"
    ignore_robots: bool = False

    @classmethod
    def from_environment(
        cls,
        headed: bool = False,
        ignore_robots: bool = False,
        top_routes: int | None = None,
        lead_times: tuple[int, ...] | None = None,
    ) -> "IxigoConfig":
        routes_file = Path(os.getenv("IXIGO_ROUTES_FILE", str(DEFAULT_ROUTES_FILE)))
        runs_dir = Path(os.getenv("IXIGO_RUNS_DIR", str(DEFAULT_RUNS_DIR)))
        resolved_top_routes = top_routes if top_routes is not None else int(os.getenv("IXIGO_TOP_ROUTES", "3"))
        return cls(
            routes_file=routes_file,
            runs_dir=runs_dir,
            lead_times=lead_times or cls.lead_times,
            top_routes=resolved_top_routes,
            min_delay_seconds=float(os.getenv("IXIGO_MIN_DELAY", "2.0")),
            max_jitter_seconds=float(os.getenv("IXIGO_MAX_JITTER", "1.5")),
            timeout_ms=int(os.getenv("IXIGO_TIMEOUT_MS", "30000")),
            headless=not headed and os.getenv("IXIGO_HEADLESS", "true").lower() not in {"0", "false", "no"},
            ignore_robots=ignore_robots or os.getenv("IXIGO_IGNORE_ROBOTS", "false").lower() in {"1", "true", "yes"},
        )
