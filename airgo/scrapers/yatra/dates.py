"""
Advance-purchase window and travel date generator.
Dynamically calculates travel dates relative to search execution date.
Never hardcodes calendar dates.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field


STANDARD_HORIZONS: List[int] = [1, 7, 15, 30, 45]


class SearchWindow(BaseModel):
    """Encapsulates a search window observation point."""

    window_code: str
    advance_purchase_days: int
    search_date: date
    travel_date: date

    @property
    def iso_search_date(self) -> str:
        return self.search_date.isoformat()

    @property
    def iso_travel_date(self) -> str:
        return self.travel_date.isoformat()

    @property
    def yatra_formatted_date(self) -> str:
        """Formatted as DD/MM/YYYY for Yatra web UI / URL trigger."""
        return self.travel_date.strftime("%d/%m/%Y")


def get_travel_date(days_ahead: int, base_date: Optional[date] = None) -> date:
    """Computes a future travel date given advance purchase days offset."""
    if days_ahead < 0:
        raise ValueError(f"Advance purchase days cannot be negative, got: {days_ahead}")
    anchor = base_date or date.today()
    return anchor + timedelta(days=days_ahead)


def get_window_for_days(days_ahead: int, base_date: Optional[date] = None) -> SearchWindow:
    """Generates a single SearchWindow for a specific day offset."""
    anchor = base_date or date.today()
    travel_d = get_travel_date(days_ahead, base_date=anchor)
    return SearchWindow(
        window_code=f"T+{days_ahead}",
        advance_purchase_days=days_ahead,
        search_date=anchor,
        travel_date=travel_d,
    )


def generate_search_windows(
    base_date: Optional[date] = None,
    horizons: Optional[List[int]] = None,
) -> List[SearchWindow]:
    """
    Generates dynamic search windows for all configured advance-purchase horizons.
    Defaults to [1, 7, 15, 30, 45].
    """
    anchor = base_date or date.today()
    target_horizons = horizons if horizons is not None else STANDARD_HORIZONS
    return [get_window_for_days(h, base_date=anchor) for h in target_horizons]
