"""
Run storage and artifact manager for Yatra scraper executions.
Ensures every execution writes into an isolated, timestamped folder under /runs/yatra/
and preserves raw quotes, normalized JSON, screenshot proofs, and logs.
"""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from airgo.config import RUNS_DIR
from airgo.scrapers.yatra.models import AntiBotEvent, NormalizedFareQuote

logger = logging.getLogger("AirGo.Yatra.RunManager")


class YatraRunManager:
    """Manages creation, layout, and artifact saving for Yatra scraping executions."""

    def __init__(
        self,
        base_runs_dir: Optional[Path] = None,
        run_timestamp: Optional[str] = None,
    ):
        base_dir = base_runs_dir or RUNS_DIR
        raw_ts = run_timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.scrape_date = raw_ts.split("_")[0]
        self.run_id = f"yatra_{raw_ts}"
        self.run_dir = base_dir / "yatra" / raw_ts

        # Subdirectories for backward-compatibility
        self.data_dir = self.run_dir / "data"
        self.screenshots_dir = self.run_dir / "screenshots"
        self.logs_dir = self.run_dir / "logs"

        # Initialize folders
        self._initialize_directories()

    def _initialize_directories(self) -> None:
        """Creates the run directory and required subdirectories."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        if "_" in self.run_id:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.screenshots_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized Yatra run directory: {self.run_dir}")

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Removes or replaces invalid characters for safe cross-platform filenames, preserving + in T+1."""
        cleaned = re.sub(r"[^\w\-_+.]", "_", name.strip())
        return cleaned

    @staticmethod
    def clean_flight_number(name: str) -> str:
        """Strips non-alphanumeric characters (e.g. 'SG-164' -> 'SG164', '6E 1234' -> '6E1234')."""
        if not name:
            return "UNKNOWN"
        clean = name.split("/")[0].strip()
        clean = re.sub(r"[^A-Za-z0-9]", "", clean).upper()
        return clean or "UNKNOWN"

    def get_route_dir(self, route_code: str) -> Path:
        """Returns runs/yatra/<scrape-date>/<ROUTE>/."""
        clean_route = self._sanitize_filename(route_code.strip().upper())
        route_dir = self.run_dir / clean_route
        route_dir.mkdir(parents=True, exist_ok=True)
        return route_dir

    def get_window_dir(self, route_code: str, window_code: str) -> Path:
        """Returns runs/yatra/<scrape-date>/<ROUTE>/<WINDOW>/."""
        clean_window = self._sanitize_filename(window_code.strip().upper())
        window_dir = self.get_route_dir(route_code) / clean_window
        window_dir.mkdir(parents=True, exist_ok=True)
        return window_dir

    def get_flight_dir(
        self,
        route_code: str,
        window_code: str,
        rank: int,
        flight_number: str,
    ) -> Path:
        """Returns runs/yatra/<scrape-date>/<ROUTE>/<WINDOW>/<rank:02d>_<flight>/."""
        window_dir = self.get_window_dir(route_code, window_code)
        clean_fn = self.clean_flight_number(flight_number)
        flight_dir = window_dir / f"{rank:02d}_{clean_fn}"
        flight_dir.mkdir(parents=True, exist_ok=True)
        return flight_dir

    def get_flight_screenshot_path(
        self,
        route_code: str,
        window_code: str,
        rank: int,
        flight_number: str,
        filename: str,
    ) -> Path:
        """Returns path for a screenshot inside runs/yatra/<scrape-date>/<ROUTE>/<WINDOW>/<rank:02d>_<flight>/."""
        flight_dir = self.get_flight_dir(route_code, window_code, rank, flight_number)
        return flight_dir / filename

    def save_window_quotes(
        self,
        route_code: str,
        window_code: str,
        quotes: List[Dict[str, Any]],
    ) -> Path:
        """
        Saves quotes.json for a single route + window combination.
        Must contain ONLY the selected flights (maximum 5).
        Also prunes any excess flight directories in the window folder so maximum 5 flight directories exist.
        """
        window_dir = self.get_window_dir(route_code, window_code)
        out_path = window_dir / "quotes.json"
        limited_quotes = quotes[:5]

        try:
            temp_path = out_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(limited_quotes, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            temp_path.replace(out_path)

            # Ensure at most 5 flight directories exist in window_dir
            valid_dirs = {
                f"{q.get('rank', i+1):02d}_{self.clean_flight_number(q.get('flight_number', ''))}"
                for i, q in enumerate(limited_quotes)
            }
            for sub in window_dir.iterdir():
                if sub.is_dir() and re.match(r"^\d{2}_", sub.name):
                    if sub.name not in valid_dirs and len(valid_dirs) >= 5:
                        import shutil
                        shutil.rmtree(sub, ignore_errors=True)

            print(f"[Yatra][JSON] Saved:\n{out_path}\n")
            print(f"[Yatra] Records written: {len(limited_quotes)}\n")
            logger.info(f"Saved window quotes to {out_path} ({len(limited_quotes)} records)")
            return out_path
        except Exception as e:
            print(f"[Yatra][JSON][ERROR] Failed to write window quotes.json: {e}")
            logger.error(f"Failed to write window quotes to {out_path}: {e}", exc_info=True)
            raise

    def get_screenshot_path(
        self,
        route_code: str,
        window_code: str,
        label: str,
        ext: str = ".png",
    ) -> Path:
        """
        Computes and creates target path for a screenshot within route and window folder.
        Example: runs/yatra/<ts>/screenshots/DEL-BOM/T+1/DEL-BOM_T+1_search_results.png
        """
        route_dir = self.screenshots_dir / self._sanitize_filename(route_code)
        window_dir = route_dir / self._sanitize_filename(window_code)
        window_dir.mkdir(parents=True, exist_ok=True)

        clean_label = self._sanitize_filename(label)
        if not clean_label.endswith(ext):
            clean_label += ext

        clean_route = self._sanitize_filename(route_code)
        clean_window = self._sanitize_filename(window_code)
        prefix = f"{clean_route}_{clean_window}_"

        # Avoid duplicating route and window prefix if already present
        if clean_label.startswith(prefix):
            filename = clean_label
        else:
            filename = f"{prefix}{clean_label}"

        return window_dir / filename

    def get_top5_screenshot_path(
        self,
        route_code: str,
        window_code: str,
        rank: int,
        flight_number: str,
    ) -> Path:
        """
        Computes target path for a Top 5 flight screenshot.
        Supports both new flight directory structure and backward-compatible path.
        """
        clean_fn = self._sanitize_filename(flight_number)
        route_dir = self.screenshots_dir / self._sanitize_filename(route_code)
        window_dir = route_dir / self._sanitize_filename(window_code)
        window_dir.mkdir(parents=True, exist_ok=True)
        return window_dir / f"{rank:02d}_{clean_fn}.png"

    def get_paynow_screenshot_path(
        self,
        route_code: str,
        window_code: str,
        flight_number: str,
        fare_option_name: str = "fare_1",
    ) -> Path:
        """
        Computes target path for a Pay Now / pre-payment verification screenshot.
        """
        clean_flight = self._sanitize_filename(flight_number)
        clean_fare = self._sanitize_filename(fare_option_name or "fare_1")
        label = f"{clean_flight}_{clean_fare}_paynow.png"
        return self.get_screenshot_path(route_code, window_code, label)

    def count_screenshots(self) -> int:
        """Counts all screenshot images stored across the run directory."""
        if not self.run_dir.exists():
            return 0
        return len(list(self.run_dir.glob("**/*.png")))

    def save_quotes(self, quotes: List[Dict[str, Any]]) -> Path:
        """
        Persists the primary airfare quotes array to runs/yatra/<run_id>/data/quotes.json.
        Ensures reliable serialization, disk flushing, existence validation, and re-read verification.
        Logs status explicitly matching Section 9.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.data_dir / "quotes.json"
        print(f"[Yatra][JSON] Writing quotes...")
        print(f"[Yatra][JSON] Records: {len(quotes)}")
        print(f"[Yatra][JSON] Path:\n{out_path}")

        try:
            temp_path = out_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(quotes, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename to prevent partial writes
            temp_path.replace(out_path)

            # Verify file exists on disk
            if not out_path.exists():
                raise FileNotFoundError(f"quotes.json was not created at {out_path}")

            # Verify readability and record count
            with open(out_path, "r", encoding="utf-8") as rf:
                verified_data = json.load(rf)

            if len(verified_data) != len(quotes):
                raise ValueError(
                    f"Integrity check failed: wrote {len(quotes)} quotes, verified {len(verified_data)}"
                )

            print(f"[Yatra][JSON] Successfully persisted {len(quotes)} records.\n")
            logger.info(f"Successfully saved and verified {len(quotes)} quotes in {out_path}")
            return out_path
        except Exception as e:
            print(f"[Yatra][JSON][ERROR] Failed to write quotes.json: {e}")
            logger.error(f"Failed to write quotes.json to {out_path}: {e}", exc_info=True)
            raise

    def save_raw_quotes(self, raw_quotes: List[Dict[str, Any]]) -> Path:
        """Saves raw scraped airfare observations to data/raw_quotes.json."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.data_dir / "raw_quotes.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(raw_quotes, f, indent=2, default=str)
        logger.info(f"Saved {len(raw_quotes)} raw quotes to {out_path}")
        return out_path

    def save_normalized_quotes(self, normalized_quotes: List[NormalizedFareQuote]) -> Path:
        """Saves validated normalized quotes to data/normalized_quotes.json."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.data_dir / "normalized_quotes.json"
        serialized = [q.model_dump(mode="json") for q in normalized_quotes]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, default=str)
        logger.info(f"Saved {len(normalized_quotes)} normalized quotes to {out_path}")
        return out_path

    def save_scraping_summary(self, summary: Dict[str, Any]) -> Path:
        """
        Saves overall execution statistics and metrics to data/scraping_summary.json
        and dual-writes data/run_summary.json for backward compatibility.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.data_dir / "scraping_summary.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        compat_path = self.data_dir / "run_summary.json"
        with open(compat_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Saved scraping summary to {out_path}")
        return out_path

    def record_anti_bot_event(self, event: AntiBotEvent) -> Path:
        """Appends an anti-bot challenge event to data/antibot_events.json."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.data_dir / "antibot_events.json"
        existing = []
        if out_path.exists():
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        existing.append(event.model_dump(mode="json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, default=str)
        logger.warning(f"Recorded anti-bot event to {out_path}: {event.event_type}")
        return out_path
