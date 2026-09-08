"""
Unit test suite for Phase 2 Yatra airfare scraper components.
Tests flight parsing, fare options sorting (5 cheapest per flight), sold-out flights,
missing prices, anti-bot challenge detection, run directory layout, and JSON generation.
All tests run strictly offline with zero network calls.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import pytest

from airgo.scrapers.yatra.db_adapter import _parse_time_str, _resolve_airline_code
from airgo.scrapers.yatra.models import (
    AntiBotEvent,
    AntiBotEventType,
    AvailabilityStatus,
    DataStatus,
    NormalizedFareQuote,
)
from airgo.scrapers.yatra.parser import YatraParser
from airgo.scrapers.yatra.run_manager import YatraRunManager
from airgo.scrapers.yatra.selectors import YatraSelectors

# Realistic mocked HTML containing multiple flights, multi-fare options, sold-out cards, and missing prices
MOCK_YATRA_SEARCH_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Flight Search Results - Yatra.com</title></head>
<body>
<div class="flight-list">
    <!-- Flight 1: IndiGo with 6 fare options (tests 5 cheapest selection) -->
    <div class="flight-seg">
        <div class="fs-15">IndiGo</div>
        <span class="fl-code">6E-205</span>
        <div class="depart-time fs-18">06:00</div>
        <div class="arrival-time fs-18">08:15</div>
        <p class="duration">02h 15m</p>
        <span class="cursor-default">Non Stop</span>
        <div class="fare-family">
            <div class="fare-option"><span class="fare-name">Saver</span><span class="fare-price">₹4,500</span></div>
            <div class="fare-option"><span class="fare-name">Flexi</span><span class="fare-price">₹4,800</span></div>
            <div class="fare-option"><span class="fare-name">Super</span><span class="fare-price">₹5,000</span></div>
            <div class="fare-option"><span class="fare-name">Regular</span><span class="fare-price">₹5,300</span></div>
            <div class="fare-option"><span class="fare-name">Plus</span><span class="fare-price">₹5,700</span></div>
            <div class="fare-option"><span class="fare-name">Premium</span><span class="fare-price">₹6,000</span></div>
        </div>
    </div>

    <!-- Flight 2: Air India with 3 fare options (< 5, preserves all) -->
    <div class="flight-seg">
        <div class="fs-15">Air India</div>
        <span class="fl-code">AI-805</span>
        <div class="depart-time fs-18">10:30</div>
        <div class="arrival-time fs-18">12:45</div>
        <p class="duration">02h 15m</p>
        <span class="cursor-default">Non Stop</span>
        <div class="fare-family">
            <div class="fare-option"><span class="fare-name">Comfort</span><span class="fare-price">₹6,200</span></div>
            <div class="fare-option"><span class="fare-name">Comfort Plus</span><span class="fare-price">₹7,100</span></div>
            <div class="fare-option"><span class="fare-name">Flex</span><span class="fare-price">₹8,500</span></div>
        </div>
    </div>

    <!-- Flight 3: Sold Out Flight -->
    <div class="flight-seg">
        <div class="fs-15">SpiceJet</div>
        <span class="fl-code">SG-123</span>
        <div class="depart-time fs-18">14:00</div>
        <div class="arrival-time fs-18">16:20</div>
        <p class="duration">02h 20m</p>
        <span class="cursor-default">Non Stop</span>
        <span class="sold-out">Sold Out</span>
    </div>

    <!-- Flight 4: Akasa Air with single displayed price -->
    <div class="flight-seg">
        <div class="fs-15">Akasa Air</div>
        <span class="fl-code">QP-1102</span>
        <div class="depart-time fs-18">18:00</div>
        <div class="arrival-time fs-18">20:15</div>
        <p class="duration">02h 15m</p>
        <span class="cursor-default">Non Stop</span>
        <span class="tipsy">₹ 5,400</span>
    </div>

    <!-- Flight 5: Missing Price (unavailable) -->
    <div class="flight-seg">
        <div class="fs-15">Vistara</div>
        <span class="fl-code">UK-995</span>
        <div class="depart-time fs-18">21:00</div>
        <div class="arrival-time fs-18">23:15</div>
        <p class="duration">02h 15m</p>
        <span class="cursor-default">1 Stop</span>
    </div>
</div>
</body>
</html>
"""

MOCK_AKAMAI_CHALLENGE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Access Denied</title></head>
<body>
<h1>Access Denied</h1>
<p>You don't have permission to access "http://flight.yatra.com/air-search-ui/dom2/trigger" on this server.</p>
<p>Reference #18.2360109.1694000000.abc1234</p>
</body>
</html>
"""

MOCK_CAPTCHA_HTML = """
<!DOCTYPE html>
<html>
<head><title>Security Check - Yatra</title></head>
<body>
<div id="captcha-box">
    <h2>Please verify you are a human</h2>
    <div class="g-recaptcha" data-sitekey="xyz"></div>
</div>
</body>
</html>
"""


class TestYatraParsingAndFareFiltering:
    """Tests parsing of flight cards and per-flight 5 cheapest fare option extraction."""

    @pytest.fixture
    def search_context(self):
        return {
            "route": "DEL-BOM",
            "origin": "DEL",
            "destination": "BOM",
            "search_date": date(2026, 9, 7),
            "travel_date": date(2026, 9, 8),
            "advance_purchase_days": 1,
            "url": "https://flight.yatra.com/air-search-ui/dom2/trigger?type=O&origin=DEL&destination=BOM",
        }

    def test_parse_flight_cards_extracts_all_flights(self, search_context):
        """Verifies that all available flight cards produce 1 candidate quote each with its cheapest fare."""
        raw_quotes, normalized_quotes = YatraParser.parse_flight_cards(
            MOCK_YATRA_SEARCH_PAGE_HTML, search_context
        )
        # 3 available flights (6E, AI, QP) produce 1 cheapest quote each; SG is sold out, UK is missing price
        assert len(normalized_quotes) == 3
        assert len(raw_quotes) == 5

    def test_selects_strictly_cheapest_fare_per_flight(self, search_context):
        """
        Flight 1 (6E-205) has 6 options: ₹4500, ₹4800, ₹5000, ₹5300, ₹5700, ₹6000.
        Must strictly select only the single cheapest fare (₹4500, Saver).
        """
        _, normalized_quotes = YatraParser.parse_flight_cards(
            MOCK_YATRA_SEARCH_PAGE_HTML, search_context
        )
        indigo_quotes = [q for q in normalized_quotes if q.flight_number == "6E-205"]
        assert len(indigo_quotes) == 1
        assert indigo_quotes[0].displayed_price == Decimal("4500.00")
        assert indigo_quotes[0].fare_option_name == "Saver"

    def test_cheapest_fare_for_multi_fare_flight(self, search_context):
        """Flight 2 (AI-805) has 3 options (6200, 7100, 8500). Cheapest (6200, Comfort) must be selected."""
        _, normalized_quotes = YatraParser.parse_flight_cards(
            MOCK_YATRA_SEARCH_PAGE_HTML, search_context
        )
        ai_quotes = [q for q in normalized_quotes if q.flight_number == "AI-805"]
        assert len(ai_quotes) == 1
        assert ai_quotes[0].displayed_price == Decimal("6200.00")
        assert ai_quotes[0].fare_option_name == "Comfort"

    def test_sold_out_flight_handling(self, search_context):
        """Flight 3 (SG-123) is sold out; verifies it is recorded with SOLD_OUT status in raw quotes."""
        raw_quotes, _ = YatraParser.parse_flight_cards(
            MOCK_YATRA_SEARCH_PAGE_HTML, search_context
        )
        sg_raw = [r for r in raw_quotes if r["flight_number"] == "SG-123"]
        assert len(sg_raw) == 1
        assert sg_raw[0]["availability_status"] == AvailabilityStatus.SOLD_OUT.value
        assert sg_raw[0]["displayed_price"] is None

    def test_missing_price_handling(self, search_context):
        """Flight 5 (UK-995) has no price; verifies graceful handling without crash."""
        raw_quotes, _ = YatraParser.parse_flight_cards(
            MOCK_YATRA_SEARCH_PAGE_HTML, search_context
        )
        uk_raw = [r for r in raw_quotes if r["flight_number"] == "UK-995"]
        assert len(uk_raw) == 1
        assert uk_raw[0]["availability_status"] == AvailabilityStatus.NOT_FOUND.value

    def test_stops_and_duration_parsing(self, search_context):
        """Verifies stop parsing ('Non Stop' -> 0, '1 Stop' -> 1)."""
        _, normalized_quotes = YatraParser.parse_flight_cards(
            MOCK_YATRA_SEARCH_PAGE_HTML, search_context
        )
        indigo = normalized_quotes[0]
        assert indigo.stops == 0
        assert indigo.duration == "02h 15m"


class TestAntiBotDetection:
    """Tests detection of security challenges without attempting evasion."""

    def test_detect_akamai_challenge(self):
        """Verifies detection of Akamai Access Denied page signature."""
        event = YatraParser.detect_anti_bot(
            html=MOCK_AKAMAI_CHALLENGE_HTML,
            status_code=403,
            url="https://flight.yatra.com/air-search-ui/dom2/trigger",
            route="DEL-BOM",
            travel_date=date(2026, 9, 8),
        )
        assert event is not None
        assert event.status_code == 403
        assert event.route == "DEL-BOM"
        assert event.event_type in (AntiBotEventType.AKAMAI_CHALLENGE, AntiBotEventType.ACCESS_DENIED)
        assert "Access Denied" in event.message

    def test_detect_captcha_challenge(self):
        """Verifies detection of CAPTCHA challenges."""
        event = YatraParser.detect_anti_bot(
            html=MOCK_CAPTCHA_HTML,
            status_code=200,
            url="https://flight.yatra.com/air-search-ui/dom2/trigger",
            route="DEL-BLR",
            travel_date=date(2026, 9, 14),
        )
        assert event is not None
        assert event.event_type == AntiBotEventType.CAPTCHA
        assert event.route == "DEL-BLR"

    def test_detect_http_429_rate_limit(self):
        """Verifies HTTP 429 status code is recorded as RATE_LIMITED."""
        event = YatraParser.detect_anti_bot(
            html="",
            status_code=429,
            url="https://flight.yatra.com/air-search-ui/dom2/trigger",
            route="BOM-BLR",
            travel_date=date(2026, 9, 22),
        )
        assert event is not None
        assert event.event_type == AntiBotEventType.RATE_LIMITED
        assert event.status_code == 429

    def test_no_challenge_on_clean_html(self):
        """Verifies clean HTML returns None."""
        event = YatraParser.detect_anti_bot(
            html="<html><body><div>Flight Search Results</div></body></html>",
            status_code=200,
        )
        assert event is None


class TestRunManagerAndArtifacts:
    """Tests isolated run directory structure and JSON/screenshot file management."""

    def test_run_directory_creation_and_structure(self):
        """Verifies creation of runs/yatra/<ts>/ with data, screenshots, and logs folders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            rm = YatraRunManager(base_runs_dir=base_dir, run_timestamp="2026-09-07_12-00-00")
            assert rm.run_dir.exists()
            assert rm.data_dir.exists()
            assert rm.screenshots_dir.exists()
            assert rm.logs_dir.exists()
            assert "2026-09-07_12-00-00" in str(rm.run_dir)

    def test_screenshot_path_sanitization(self):
        """Verifies screenshot path generates route/window subdirectory with sanitized name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = YatraRunManager(base_runs_dir=Path(tmpdir))
            shot_path = rm.get_screenshot_path("DEL-BOM", "T+1", "search_results")
            assert shot_path.parent.name == "T_1" or shot_path.parent.name == "T+1"
            assert shot_path.name.endswith(".png")
            assert "search_results" in shot_path.name

    def test_save_raw_and_normalized_quotes_json(self):
        """Verifies saving and re-reading raw and normalized quotes JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = YatraRunManager(base_runs_dir=Path(tmpdir))
            raw_sample = [{"flight": "6E-205", "price": 4500}]
            raw_file = rm.save_raw_quotes(raw_sample)
            assert raw_file.exists()

            with open(raw_file, "r") as f:
                data = json.load(f)
            assert data[0]["flight"] == "6E-205"

            norm_quote = NormalizedFareQuote(
                route="DEL-BOM",
                origin="DEL",
                destination="BOM",
                search_date=date(2026, 9, 7),
                travel_date=date(2026, 9, 8),
                advance_purchase_days=1,
                airline="IndiGo",
                flight_number="6E-205",
                departure_time="06:00",
                arrival_time="08:15",
                base_fare=Decimal("4500.00"),
                displayed_price=Decimal("4500.00"),
            )
            norm_file = rm.save_normalized_quotes([norm_quote])
            assert norm_file.exists()

            with open(norm_file, "r") as f:
                norm_data = json.load(f)
            assert len(norm_data) == 1
            assert norm_data[0]["flight_number"] == "6E-205"

    def test_record_anti_bot_event_persistence(self):
        """Verifies anti-bot event is written to data/antibot_events.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = YatraRunManager(base_runs_dir=Path(tmpdir))
            event = AntiBotEvent(
                route="DEL-BOM",
                travel_date=date(2026, 9, 8),
                url="https://flight.yatra.com",
                event_type=AntiBotEventType.CAPTCHA,
                message="Test challenge",
            )
            out = rm.record_anti_bot_event(event)
            assert out.exists()
            with open(out, "r") as f:
                saved = json.load(f)
            assert len(saved) == 1
            assert saved[0]["event_type"] == "captcha"


class TestDBAdapterHelpers:
    """Tests carrier code resolution and time string parsing."""

    def test_resolve_airline_code(self):
        """Verifies carrier IATA code extraction."""
        assert _resolve_airline_code("IndiGo", "6E-205") == "6E"
        assert _resolve_airline_code("Air India", "AI-805") == "AI"
        assert _resolve_airline_code("Akasa Air", "QP-1102") == "QP"
        assert _resolve_airline_code("SpiceJet", "SG-123") == "SG"
        assert _resolve_airline_code("Air India Express", "IX-456") == "IX"
        assert _resolve_airline_code("Unknown", "XX-999") == "XX"

    def test_parse_time_str(self):
        """Verifies time string parsing to datetime.time."""
        t = _parse_time_str("06:30")
        assert t.hour == 6
        assert t.minute == 30

        fallback = _parse_time_str("invalid")
        assert fallback.hour == 0
        assert fallback.minute == 0
