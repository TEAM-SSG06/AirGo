"""
AirGo Data Pipeline Pydantic Schemas and Database Models.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class RawQuoteSchema(BaseModel):
    source: str = "Cleartrip"
    platform: Optional[str] = None
    carrier: str
    carrier_code: Optional[str] = None
    flight_number: str
    origin: str
    destination: str
    departure_date: Optional[date] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    duration_mins: Optional[int] = None
    stops: int = 0
    booking_date: Optional[date] = None
    audit_timestamp: Optional[str] = None
    advance_window: str
    advance_days: int
    fare_class: str = "Economy"
    base_fare: float = 0.0
    surcharges: float = 0.0
    taxes: float = 0.0
    seat_surcharge: float = 0.0
    convenience_fee: float = 0.0
    total_fare: float = 0.0
    final_payable_fare: float = 0.0
    search_url: Optional[str] = None
    source_url: Optional[str] = None
    is_sold_out: bool = False
    seats_remaining: Optional[int] = None
    has_zero_dummy_proof: bool = True
    metadata_json: Optional[Dict[str, Any]] = None
    screenshots: Optional[Dict[str, str]] = None
    seat_matrix: Optional[Dict[str, Any]] = None

    @model_validator(mode='before')
    @classmethod
    def populate_defaults(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if not values.get("platform"):
                values["platform"] = values.get("source", "Cleartrip")
            if not values.get("source"):
                values["source"] = values.get("platform", "Cleartrip")
            if not values.get("audit_timestamp"):
                values["audit_timestamp"] = datetime.utcnow().isoformat() + "Z"
            if not values.get("search_url"):
                values["search_url"] = values.get("source_url", "")
            if not values.get("source_url"):
                values["source_url"] = values.get("search_url", "")
            if not values.get("final_payable_fare"):
                values["final_payable_fare"] = values.get("total_fare", 0.0)
            if not values.get("total_fare"):
                values["total_fare"] = values.get("final_payable_fare", 0.0)
        return values


class RawQuoteDB(BaseModel):
    id: Optional[int] = None
    platform: str
    audit_timestamp: str
    search_url: str
    origin: str
    destination: str
    departure_date: str
    advance_window: str
    advance_days: int
    carrier: str
    flight_number: str
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    stops: int = 0
    base_fare: float = 0.0
    taxes: float = 0.0
    seat_surcharge: float = 0.0
    final_payable_fare: float = 0.0
    has_zero_dummy_proof: bool = True
