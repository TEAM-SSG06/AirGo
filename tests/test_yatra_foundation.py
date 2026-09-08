"""
Unit test suite for Yatra Scraper Phase 1 Foundation.
Tests route configurations, dynamic date generators, price normalizers,
and data models strictly offline without hitting live network endpoints.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from airgo.scrapers.yatra.routes import (
    INITIAL_ROUTES,
    RouteDefinition,
    RouteRegistry,
    get_route,
    list_routes,
    validate_route,
)
from airgo.scrapers.yatra.dates import (
    STANDARD_HORIZONS,
    SearchWindow,
    generate_search_windows,
    get_travel_date,
    get_window_for_days,
)
from airgo.scrapers.yatra.normalizer import (
    normalize_price,
    normalize_price_float,
)
from airgo.scrapers.yatra.models import (
    DataStatus,
    AvailabilityStatus,
    AntiBotEventType,
    AntiBotEvent,
    NormalizedFareQuote,
)
from airgo.scrapers.yatra.browser import (
    PlaywrightBrowserManager,
    BROWSER_MANAGER,
)
from airgo.scrapers.yatra.config import (
    DEFAULT_YATRA_CONFIG,
    YatraScraperConfig,
)


class TestRouteConfiguration:
    """Tests configuration-driven routes and route validation."""

    def test_initial_routes_count_and_corridors(self):
        """Verifies exactly 3 initial corridors exist: BOM-DEL, BLR-DEL, BLR-BOM."""
        routes = list_routes()
        assert len(routes) == 3
        codes = [r.route_code for r in routes]
        assert "BOM-DEL" in codes
        assert "BLR-DEL" in codes
        assert "BLR-BOM" in codes

    def test_route_attributes_and_display_name(self):
        """Verifies route properties are structured with IATA codes and names."""
        del_bom = get_route("DEL-BOM")
        assert del_bom is not None
        assert del_bom.origin_iata == "DEL"
        assert del_bom.dest_iata == "BOM"
        assert del_bom.origin_name == "New Delhi"
        assert del_bom.dest_name == "Mumbai"
        assert "DEL" in del_bom.display_name
        assert "BOM" in del_bom.display_name

    def test_route_validation_helpers(self):
        """Tests route existence checking."""
        assert validate_route("DEL", "BOM") is True
        assert validate_route("DEL", "BLR") is True
        assert validate_route("BOM", "BLR") is True
        assert validate_route("DEL", "XYZ") is False
        assert validate_route("AAA", "BBB") is False

    def test_case_insensitivity_and_lookup(self):
        """Tests lookup by code handles case variations and whitespace."""
        route = get_route("del-bom ")
        assert route is not None
        assert route.route_code == "DEL-BOM"

    def test_route_registration_extensibility(self):
        """Tests adding new corridors without modifying scraper logic."""
        registry = RouteRegistry()
        new_route = RouteDefinition(
            route_code="HYD-DEL",
            origin_iata="HYD",
            dest_iata="DEL",
            origin_name="Hyderabad",
            dest_name="New Delhi",
        )
        registry.register(new_route)
        assert registry.validate_route_code("HYD-DEL") is True
        assert registry.get("HYD-DEL").origin_name == "Hyderabad"

    def test_invalid_route_definition_raises(self):
        """Validates that malformed IATA or route codes raise validation errors."""
        with pytest.raises(ValidationError):
            RouteDefinition(
                route_code="INVALID",
                origin_iata="DELHI",  # Must be 3 chars
                dest_iata="BOM",
                origin_name="Delhi",
                dest_name="Mumbai",
            )


class TestAdvancePurchaseWindows:
    """Tests dynamic travel date generation across T+1..T+45 horizons."""

    def test_standard_horizons_definition(self):
        """Verifies exactly T+1, T+7, T+15, T+30, T+45 are defined."""
        assert STANDARD_HORIZONS == [1, 7, 15, 30, 45]

    def test_dynamic_date_calculation_relative_to_anchor(self):
        """Tests offsets are computed dynamically without hardcoding calendar dates."""
        anchor = date(2026, 10, 1)
        windows = generate_search_windows(base_date=anchor)
        assert len(windows) == 5

        w_map = {w.window_code: w for w in windows}
        assert w_map["T+1"].travel_date == date(2026, 10, 2)
        assert w_map["T+7"].travel_date == date(2026, 10, 8)
        assert w_map["T+15"].travel_date == date(2026, 10, 16)
        assert w_map["T+30"].travel_date == date(2026, 10, 31)
        assert w_map["T+45"].travel_date == date(2026, 11, 15)

    def test_window_metadata_stored(self):
        """Verifies search_date, travel_date, and advance_purchase_days are stored."""
        anchor = date(2026, 5, 10)
        win = get_window_for_days(7, base_date=anchor)
        assert win.search_date == anchor
        assert win.travel_date == date(2026, 5, 17)
        assert win.advance_purchase_days == 7
        assert win.window_code == "T+7"
        assert win.yatra_formatted_date == "17/05/2026"
        assert win.iso_travel_date == "2026-05-17"

    def test_month_and_year_rollover(self):
        """Tests that date generator correctly rolls over months and years."""
        anchor = date(2026, 12, 25)
        travel = get_travel_date(15, base_date=anchor)
        assert travel == date(2027, 1, 9)

    def test_negative_days_raises_error(self):
        """Ensures negative advance purchase days are rejected."""
        with pytest.raises(ValueError):
            get_travel_date(-5)


class TestPriceNormalization:
    """Tests the price normalization utility across various currency and string formats."""

    @pytest.mark.parametrize("raw_input,expected", [
        ("₹4,999", Decimal("4999.00")),
        ("₹ 4,999", Decimal("4999.00")),
        ("4,999", Decimal("4999.00")),
        (4999, Decimal("4999.00")),
        (4999.0, Decimal("4999.00")),
        ("4999.50", Decimal("4999.50")),
        ("Rs. 4,999/-", Decimal("4999.00")),
        ("INR 12,450.75", Decimal("12450.75")),
        ("  5,600  ", Decimal("5600.00")),
    ])
    def test_normalize_price_valid_formats(self, raw_input, expected):
        """Verifies standard and decorated airfare string formats normalize correctly."""
        result = normalize_price(raw_input)
        assert result == expected
        assert isinstance(result, Decimal)

    def test_normalize_price_float_helper(self):
        """Tests normalize_price_float helper."""
        assert normalize_price_float("₹4,999") == 4999.0
        assert normalize_price_float("4999.75") == 4999.75

    def test_normalize_price_invalid_inputs(self):
        """Tests error handling on invalid strings without digits."""
        with pytest.raises(ValueError):
            normalize_price("FREE")
        with pytest.raises(ValueError):
            normalize_price("")
        with pytest.raises(ValueError):
            normalize_price(None)

    def test_normalize_price_with_default_fallback(self):
        """Tests fallback behavior when a default is supplied."""
        assert normalize_price("N/A", default=Decimal("0.00")) == Decimal("0.00")
        assert normalize_price(None, default=Decimal("100.00")) == Decimal("100.00")


class TestDataModelsAndStatuses:
    """Tests Pydantic models for normalized fare quotes, anti-bot events, and status enums."""

    def test_all_data_statuses_supported(self):
        """Ensures all requested status enum values are present."""
        expected_statuses = [
            "SEARCH_RESULT",
            "FARE_SELECTED",
            "FARE_VERIFIED",
            "SOLD_OUT",
            "CAPTCHA_BLOCKED",
            "ACCESS_DENIED",
            "PRICE_CHANGED",
            "VERIFICATION_FAILED",
        ]
        for s in expected_statuses:
            assert hasattr(DataStatus, s)
            assert DataStatus[s].value == s

    def test_normalized_fare_quote_creation_and_defaults(self):
        """Verifies full NormalizedFareQuote creation, decimal coercion, and dedup_hash."""
        quote = NormalizedFareQuote(
            route="DEL-BOM",
            origin="DEL",
            destination="BOM",
            search_date=date(2026, 9, 7),
            travel_date=date(2026, 9, 14),
            advance_purchase_days=7,
            airline="IndiGo",
            flight_number="6E-205",
            departure_time="06:00",
            arrival_time="08:15",
            duration="02h 15m",
            stops=0,
            base_fare="4500",
            taxes=750,
            convenience_fee="350",
            displayed_price=5600,
            final_payable_price="5600.00",
            currency="INR",
            verification_status=DataStatus.SEARCH_RESULT,
        )

        assert quote.source == "Yatra"
        assert quote.base_fare == Decimal("4500.00")
        assert quote.taxes == Decimal("750.00")
        assert quote.convenience_fee == Decimal("350.00")
        assert quote.displayed_price == Decimal("5600.00")
        assert quote.availability_status == AvailabilityStatus.AVAILABLE
        assert len(quote.dedup_hash) == 64  # SHA-256 hash length

    def test_anti_bot_event_model(self):
        """Verifies AntiBotEvent model structure for capturing challenges without evasion."""
        event = AntiBotEvent(
            route="DEL-BOM",
            travel_date=date(2026, 9, 14),
            url="https://flight.yatra.com/air-search-ui/dom2/trigger",
            event_type=AntiBotEventType.CAPTCHA,
            status_code=403,
            message="Cloudflare Turnstile challenge detected",
            retry_after=60,
            screenshot_path="/runs/2026-09-07_antibot/captcha.png",
        )

        assert event.event_type == AntiBotEventType.CAPTCHA
        assert event.status_code == 403
        assert event.route == "DEL-BOM"
        assert event.retry_after == 60


class TestBrowserAndConfiguration:
    """Tests centralized Playwright browser manager configuration and settings."""

    def test_default_yatra_config(self):
        """Verifies safe defaults in Yatra configuration."""
        assert DEFAULT_YATRA_CONFIG.platform_name == "Yatra"
        assert DEFAULT_YATRA_CONFIG.max_concurrency >= 1
        assert DEFAULT_YATRA_CONFIG.request_delay >= 0.5
        assert DEFAULT_YATRA_CONFIG.max_retries >= 1
        assert DEFAULT_YATRA_CONFIG.backoff_factor >= 1.0

    def test_browser_manager_initialization(self):
        """Verifies browser manager defaults to configured headless mode."""
        manager = PlaywrightBrowserManager(headless=True)
        assert manager.headless is True

        manager_headed = PlaywrightBrowserManager(headless=False)
        assert manager_headed.headless is False
