"""
Data models and status enums for Yatra airfare scraping.
Defines the canonical NormalizedFareQuote model, anti-bot event records,
and workflow status enumeration.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
import hashlib
from typing import Optional, Union
import uuid

from pydantic import BaseModel, Field, field_validator


class DataStatus(str, Enum):
    """Lifecycle and verification statuses for scraped observations."""

    SEARCH_RESULT = "SEARCH_RESULT"
    FARE_SELECTED = "FARE_SELECTED"
    FARE_VERIFIED = "FARE_VERIFIED"
    SOLD_OUT = "SOLD_OUT"
    CAPTCHA_BLOCKED = "CAPTCHA_BLOCKED"
    ACCESS_DENIED = "ACCESS_DENIED"
    PRICE_CHANGED = "PRICE_CHANGED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class AvailabilityStatus(str, Enum):
    """Flight seat inventory status."""

    AVAILABLE = "available"
    SOLD_OUT = "sold_out"
    CANCELLED = "cancelled"
    NOT_FOUND = "not_found"


class AntiBotEventType(str, Enum):
    """Anti-bot and access barrier event classifications."""

    CAPTCHA = "captcha"
    AKAMAI_CHALLENGE = "akamai_challenge"
    CLOUDFLARE_WAF = "cloudflare_waf"
    RATE_LIMITED = "rate_limited"
    IP_BLOCKED = "ip_blocked"
    ACCESS_DENIED = "access_denied"
    FINGERPRINT_CHECK = "fingerprint_check"
    OTHER = "other"


class AntiBotEvent(BaseModel):
    """Structure to record detection and challenge events without evasion."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    route: str
    travel_date: date
    url: str
    event_type: Union[AntiBotEventType, str]
    status_code: Optional[int] = None
    message: str
    retry_after: Optional[int] = None
    screenshot_path: Optional[str] = None


class NormalizedFareQuote(BaseModel):
    """
    Standardized airfare observation representation.
    Supports historical snapshots across routes, flights, and advance purchase windows.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "Yatra"
    route: str                                  # 'DEL-BOM'
    origin: str                                 # 'DEL'
    destination: str                            # 'BOM'
    search_date: date
    travel_date: date
    advance_purchase_days: int                  # 1, 7, 15, 30, 45
    airline: str                                # 'IndiGo', 'Air India'
    flight_number: str                          # '6E-2341'
    departure_time: str                         # '08:15'
    arrival_time: Optional[str] = None          # '10:30'
    duration: Optional[str] = None              # '02h 15m'
    stops: int = 0
    fare_class: Optional[str] = "ECONOMY"
    fare_option_name: Optional[str] = None      # 'Standard', 'Flexi Plus'

    # Fares and Fee Breakdown
    base_fare: Decimal
    taxes: Decimal = Decimal("0.00")
    fees: Decimal = Decimal("0.00")
    convenience_fee: Decimal = Decimal("0.00")
    other_charges: Decimal = Decimal("0.00")
    displayed_price: Decimal
    displayed_search_price: Optional[Decimal] = None
    final_payable_price: Optional[Decimal] = None
    price_difference: Optional[Decimal] = None
    currency: str = "INR"

    # Status & Audit Tracking
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verification_status: DataStatus = DataStatus.SEARCH_RESULT
    verification_timestamp: Optional[datetime] = None
    error_reason: Optional[str] = None
    paynow_screenshot_path: Optional[str] = None

    def model_post_init(self, __context) -> None:
        if self.displayed_search_price is None:
            self.displayed_search_price = self.displayed_price
        if self.final_payable_price is not None and self.price_difference is None:
            self.price_difference = (self.final_payable_price - self.displayed_search_price).quantize(Decimal("0.01"))

    @field_validator(
        "base_fare",
        "taxes",
        "fees",
        "convenience_fee",
        "other_charges",
        "displayed_price",
        "displayed_search_price",
        "final_payable_price",
        "price_difference",
        mode="before",
    )
    @classmethod
    def parse_decimals(cls, v):
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v)).quantize(Decimal("0.01"))

    @property
    def dedup_hash(self) -> str:
        """
        Deterministic unique hash identifying flight, date, and search timestamp minute.
        Ensures multiple historical runs can be captured without overwriting prior audits.
        """
        ts_minute = self.scraped_at.strftime("%Y%m%d%H%M")
        raw_key = f"{self.source}|{self.flight_number}|{self.route}|{self.travel_date.isoformat()}|{self.fare_class}|{ts_minute}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
