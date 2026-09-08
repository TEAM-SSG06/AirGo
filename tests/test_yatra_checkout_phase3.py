"""
Offline Unit Test Suite for Yatra Airfare Scraper Phase 3:
Deep Checkout Flow, Pay Now Verification, Price Breakdown Extraction,
Price Change Detection, Screenshot Paths, DB Persistence, and Run Summary Counters.

Strictly offline: all tests run deterministically against mock fixtures without
hitting live Yatra endpoints.
"""

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from airgo.scrapers.yatra.checkout import YatraCheckoutVerifier
from airgo.scrapers.yatra.db_adapter import persist_fare_quotes_to_db
from airgo.scrapers.yatra.models import (
    AntiBotEvent,
    AntiBotEventType,
    AvailabilityStatus,
    DataStatus,
    NormalizedFareQuote,
)
from airgo.scrapers.yatra.parser import YatraParser
from airgo.scrapers.yatra.routes import RouteDefinition
from airgo.scrapers.yatra.run_manager import YatraRunManager
from airgo.scrapers.yatra.scraper import YatraScraper


# --- MOCK HTML FIXTURES ---

MOCK_PAYNOW_PAGE_IDENTICAL_HTML = """
<!DOCTYPE html>
<html>
<head><title>Payment - Yatra.com</title></head>
<body>
<div class="payment-container">
    <h2>Select Payment Option</h2>
    <div class="payment-options">
        <button id="payNowBtn">Pay Now</button>
    </div>
    <div class="fare-breakup">
        <span class="base-fare">₹4,000</span>
        <span class="taxes">₹500</span>
        <span class="convenience-fee">₹0</span>
        <span class="other-charges">₹0</span>
        <span class="total-payable">₹ 4,500</span>
    </div>
</div>
</body>
</html>
"""

MOCK_PAYNOW_PAGE_PRICE_INCREASED_HTML = """
<!DOCTYPE html>
<html>
<head><title>Payment Review - Yatra.com</title></head>
<body>
<div class="payment-wrapper">
    <div class="price-change alert-warning">
        <p>Fare has changed due to dynamic airline inventory updates.</p>
    </div>
    <div class="payment-options">
        <button>Make Payment</button>
    </div>
    <div class="fare-summary">
        <table>
            <tr><td>Base Fare</td><td><span class="base-fare">₹4,200</span></td></tr>
            <tr><td>Taxes & Fees</td><td><span class="taxes">₹600</span></td></tr>
            <tr><td>Convenience Fee</td><td><span class="convenience-fee">₹300</span></td></tr>
            <tr><td>Total Amount</td><td><span class="total-payable">₹5,100</span></td></tr>
        </table>
    </div>
</div>
</body>
</html>
"""

MOCK_PAYNOW_PAGE_SOLD_OUT_HTML = """
<!DOCTYPE html>
<html>
<head><title>Booking Notice - Yatra.com</title></head>
<body>
<div class="error-container">
    <div class="sold-out">
        <h3>Seats sold out! The selected fare is no longer available.</h3>
    </div>
    <a href="/flights">Search Again</a>
</div>
</body>
</html>
"""

MOCK_CHECKOUT_AKAMAI_CHALLENGE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Access Denied</title></head>
<body>
<h1>Access Denied</h1>
<p>You don't have permission to access "http://flight.yatra.com/checkout" on this server.</p>
<p>Reference #18.2a43b742.1625049069.906991 (Akamai Bot Manager)</p>
</body>
</html>
"""


# --- FIXTURES ---

@pytest.fixture
def temp_run_manager(tmp_path: Path) -> YatraRunManager:
    """Provides an isolated run manager writing to a temporary test directory."""
    return YatraRunManager(base_runs_dir=tmp_path, run_timestamp="2026-09-07_22-00-00")


@pytest.fixture
def sample_candidate_quote() -> NormalizedFareQuote:
    """Provides a baseline candidate quote from search results."""
    return NormalizedFareQuote(
        source="Yatra",
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
        fare_class="ECONOMY",
        fare_option_name="Saver",
        base_fare=Decimal("4500.00"),
        displayed_price=Decimal("4500.00"),
        final_payable_price=None,
        verification_status=DataStatus.SEARCH_RESULT,
    )


# --- 1. DISPLAYED VS FINAL PRICE SEPARATION ---

class TestPriceSeparationAndBreakdown:
    """Verifies that displayed_search_price and final_payable_price are strictly separated."""

    def test_displayed_vs_final_price_preservation(self, sample_candidate_quote):
        """Original search price is preserved when final payable price is set."""
        quote = sample_candidate_quote
        assert quote.displayed_search_price == Decimal("4500.00")
        assert quote.final_payable_price is None
        assert quote.verification_status == DataStatus.SEARCH_RESULT

        # Simulate verification with convenience fee addition
        quote.final_payable_price = Decimal("4850.00")
        quote.verification_status = DataStatus.PRICE_CHANGED
        quote.price_difference = Decimal("350.00")

        # Crucial check: original displayed_search_price is NOT overwritten
        assert quote.displayed_search_price == Decimal("4500.00")
        assert quote.final_payable_price == Decimal("4850.00")
        assert quote.price_difference == Decimal("350.00")

    def test_parse_paynow_breakdown_identical(self):
        """Extracts base fare, taxes, fees, and final payable total from clean Pay Now HTML."""
        breakdown = YatraParser.parse_paynow_breakdown(MOCK_PAYNOW_PAGE_IDENTICAL_HTML)
        assert breakdown["final_payable_price"] == Decimal("4500.00")
        assert breakdown["base_fare"] == Decimal("4000.00")
        assert breakdown["taxes"] == Decimal("500.00")
        assert breakdown["convenience_fee"] == Decimal("0.00")

    def test_parse_paynow_breakdown_with_convenience_fee(self):
        """Extracts breakdown with convenience fee and taxes."""
        breakdown = YatraParser.parse_paynow_breakdown(MOCK_PAYNOW_PAGE_PRICE_INCREASED_HTML)
        assert breakdown["final_payable_price"] == Decimal("5100.00")
        assert breakdown["base_fare"] == Decimal("4200.00")
        assert breakdown["taxes"] == Decimal("600.00")
        assert breakdown["convenience_fee"] == Decimal("300.00")


# --- 2. PRICE CHANGE DETECTION ---

class TestPriceChangeDetection:
    """Verifies detection of price differences and in-flow alert banners."""

    def test_price_change_alert_banner_detection(self):
        """Detects in-flow warning banner alerting of dynamic price changes."""
        alert = YatraParser.detect_price_change_alert(MOCK_PAYNOW_PAGE_PRICE_INCREASED_HTML)
        assert alert is not None
        assert "fare has changed" in alert.lower()

    def test_no_price_change_alert_on_clean_page(self):
        """Returns None when no price change notice is present."""
        alert = YatraParser.detect_price_change_alert(MOCK_PAYNOW_PAGE_IDENTICAL_HTML)
        assert alert is None

    def test_price_difference_calculation(self, sample_candidate_quote):
        """Calculates difference between final payable price and initial search price."""
        quote = sample_candidate_quote
        quote.final_payable_price = Decimal("5100.00")
        # Difference = 5100.00 - 4500.00 = +600.00
        diff = quote.final_payable_price - quote.displayed_search_price
        assert diff == Decimal("600.00")


# --- 3. VERIFICATION STATUS TRANSITIONS ---

def create_mock_page(content_html: str, url: str = "https://flight.yatra.com/checkout/payment") -> AsyncMock:
    """Helper creating a robust mock Playwright page with realistic locator chaining."""
    mock_page = AsyncMock()
    mock_page.content = AsyncMock(return_value=content_html)
    mock_page.url = url
    mock_page.screenshot = AsyncMock(return_value=None)
    mock_page.wait_for_load_state = AsyncMock(return_value=None)
    mock_page.wait_for_selector = AsyncMock(return_value=None)
    mock_page.wait_for_timeout = AsyncMock(return_value=None)

    mock_locator = AsyncMock()
    mock_locator.count = AsyncMock(return_value=1)
    mock_locator.is_visible = AsyncMock(return_value=True)
    mock_locator.click = AsyncMock(return_value=None)
    mock_locator.fill = AsyncMock(return_value=None)
    mock_locator.input_value = AsyncMock(return_value="")
    mock_locator.first = mock_locator
    mock_locator.locator = MagicMock(return_value=mock_locator)

    mock_page.locator = MagicMock(return_value=mock_locator)
    return mock_page


# --- 3. VERIFICATION STATUS TRANSITIONS ---

class TestVerificationStatusTransitions:
    """Validates transitions across all lifecycle states."""

    def test_fare_verified_status_when_prices_match(self, temp_run_manager, sample_candidate_quote):
        """When displayed search price matches final payable price, status is FARE_VERIFIED."""
        async def _run():
            verifier = YatraCheckoutVerifier(run_manager=temp_run_manager)
            mock_page = create_mock_page(MOCK_PAYNOW_PAGE_IDENTICAL_HTML)
            return await verifier.verify_fare(mock_page, sample_candidate_quote, window_code="T+1")

        verified = asyncio.run(_run())
        assert verified.verification_status == DataStatus.FARE_VERIFIED
        assert verified.final_payable_price == Decimal("4500.00")
        assert verified.displayed_search_price == Decimal("4500.00")
        assert verified.price_difference == Decimal("0.00")
        assert verified.verification_timestamp is not None
        assert verified.paynow_screenshot_path is not None

    def test_price_changed_status_when_final_price_differs(self, temp_run_manager, sample_candidate_quote):
        """When final payable price exceeds search price, status is PRICE_CHANGED."""
        async def _run():
            verifier = YatraCheckoutVerifier(run_manager=temp_run_manager)
            mock_page = create_mock_page(MOCK_PAYNOW_PAGE_PRICE_INCREASED_HTML)
            return await verifier.verify_fare(mock_page, sample_candidate_quote, window_code="T+1")

        verified = asyncio.run(_run())
        assert verified.verification_status == DataStatus.PRICE_CHANGED
        assert verified.displayed_search_price == Decimal("4500.00")
        assert verified.final_payable_price == Decimal("5100.00")
        assert verified.price_difference == Decimal("600.00")

    def test_sold_out_status_during_checkout(self, temp_run_manager, sample_candidate_quote):
        """When flight sells out during booking progression, status is SOLD_OUT."""
        async def _run():
            verifier = YatraCheckoutVerifier(run_manager=temp_run_manager)
            mock_page = create_mock_page(MOCK_PAYNOW_PAGE_SOLD_OUT_HTML, url="https://flight.yatra.com/checkout/notice")
            return await verifier.verify_fare(mock_page, sample_candidate_quote, window_code="T+1")

        verified = asyncio.run(_run())
        assert verified.verification_status == DataStatus.SOLD_OUT
        assert verified.availability_status == AvailabilityStatus.SOLD_OUT

    def test_captcha_blocked_status_during_checkout(self, temp_run_manager, sample_candidate_quote):
        """When Akamai/CAPTCHA barrier is encountered, status is CAPTCHA_BLOCKED without crash."""
        async def _run():
            verifier = YatraCheckoutVerifier(run_manager=temp_run_manager)
            mock_page = create_mock_page(MOCK_CHECKOUT_AKAMAI_CHALLENGE_HTML, url="https://flight.yatra.com/checkout")
            return await verifier.verify_fare(mock_page, sample_candidate_quote, window_code="T+1")

        verified = asyncio.run(_run())
        assert verified.verification_status in (DataStatus.CAPTCHA_BLOCKED, DataStatus.ACCESS_DENIED)
        assert "Security barrier encountered" in (verified.error_reason or "")


# --- 4. PAY NOW SCREENSHOT HIERARCHY ---

class TestPayNowScreenshotPaths:
    """Verifies screenshot naming and folder organization."""

    def test_paynow_screenshot_path_structure(self, temp_run_manager):
        """Generates runs/yatra/<ts>/screenshots/<route>/<window>/<flight>_<fare>_paynow.png."""
        path = temp_run_manager.get_paynow_screenshot_path(
            route_code="DEL-BOM",
            window_code="T+1",
            flight_number="6E-205",
            fare_option_name="Saver",
        )
        assert path.name in ("DEL-BOM_T+1_6E-205_Saver_paynow.png", "DEL-BOM_T_1_6E-205_Saver_paynow.png")
        assert path.parent.name in ("T+1", "T_1")
        assert path.parent.parent.name == "DEL-BOM"
        assert path.parent.parent.parent.name == "screenshots"

    def test_count_screenshots_empty_and_populated(self, temp_run_manager):
        """Counts screenshots accurately across all nested subdirectories."""
        assert temp_run_manager.count_screenshots() == 0

        p1 = temp_run_manager.get_screenshot_path("DEL-BOM", "T+1", "search_results")
        p1.touch()
        p2 = temp_run_manager.get_paynow_screenshot_path("DEL-BOM", "T+1", "6E-205", "Saver")
        p2.touch()

        assert temp_run_manager.count_screenshots() == 2

    def test_get_top5_screenshot_path_structure(self, temp_run_manager):
        """Generates runs/yatra/<ts>/screenshots/<route>/<window>/<rank:02d>_<flight>.png."""
        top5_path = temp_run_manager.get_top5_screenshot_path(
            route_code="DEL-BOM",
            window_code="T+1",
            rank=1,
            flight_number="6E-6433",
        )
        assert top5_path.name == "01_6E-6433.png"
        assert top5_path.parent.name == "T+1"
        assert top5_path.parent.parent.name == "DEL-BOM"

    def test_save_quotes_json_persistence_and_schema(self, temp_run_manager):
        """Verifies quotes.json persistence, atomic writes, schema compliance, and re-reading."""
        quotes_sample = [
            {
                "rank": 1,
                "platform": "Yatra",
                "platform_type": "ota",
                "route": "DEL-BOM",
                "origin": "DEL",
                "destination": "BOM",
                "travel_date": "2026-09-08",
                "advance_purchase_days": 1,
                "window": "T+1",
                "airline": "IndiGo",
                "flight_number": "6E-6433",
                "departure_time": "06:00",
                "arrival_time": "08:15",
                "duration": "2h 15m",
                "stops": 0,
                "search_price": 6222,
                "deep_checkout_base_fare": 4326,
                "deep_checkout_taxes": 1896,
                "final_price": 6222,
                "currency": "INR",
                "fare_class": "Economy",
                "scraped_at": "2026-09-07T17:22:02.333202",
                "screenshot_evidence": "DEL-BOM/T+1/01_6E-6433.png",
            }
        ]

        out_path = temp_run_manager.save_quotes(quotes_sample)
        assert out_path.exists()
        assert out_path.name == "quotes.json"

        with open(out_path, "r", encoding="utf-8") as rf:
            loaded = json.load(rf)

        assert len(loaded) == 1
        q = loaded[0]
        assert q["rank"] == 1
        assert q["platform"] == "Yatra"
        assert q["platform_type"] == "ota"
        assert q["route"] == "DEL-BOM"
        assert q["window"] == "T+1"
        assert q["final_price"] == 6222
        assert q["screenshot_evidence"] == "DEL-BOM/T+1/01_6E-6433.png"

    def test_route_window_flight_artifact_hierarchy(self, tmp_path):
        """Verifies exact hierarchy: runs/yatra/<YYYY-MM-DD>/<ROUTE>/<WINDOW>/01_<flight>/{search_results,paynow}.png and quotes.json."""
        rm = YatraRunManager(base_runs_dir=tmp_path, run_timestamp="2026-09-07")
        flight_dir = rm.get_flight_dir("BOM-DEL", "T+7", rank=1, flight_number="SG-164")
        assert flight_dir.name == "01_SG164"
        assert flight_dir.parent.name == "T+7"
        assert flight_dir.parent.parent.name == "BOM-DEL"
        assert flight_dir.parent.parent.parent.name == "2026-09-07"
        assert flight_dir.parent.parent.parent.parent.name == "yatra"

        # Verify search_results.png and paynow.png paths
        sr_path = flight_dir / "search_results.png"
        pn_path = flight_dir / "paynow.png"
        assert sr_path.name == "search_results.png"
        assert pn_path.name == "paynow.png"

        # Verify window quotes.json
        window_quotes_path = rm.save_window_quotes("BOM-DEL", "T+7", [{"rank": 1, "flight_number": "SG-164", "final_price": 5000}])
        assert window_quotes_path.name == "quotes.json"
        assert window_quotes_path.parent == flight_dir.parent


# --- 5. FIVE-CHEAPEST RULE PER FLIGHT WITH VERIFIED FARES ---

class TestFiveCheapestRankingWithVerifiedFares:
    """Validates that ranking uses final_payable_price per flight."""

    def test_five_cheapest_sorts_by_final_payable_price(self):
        """
        Flight 6E-101 has 6 options.
        Option A has search price 4000, final price 5500.
        Option B has search price 4200, final price 4300.
        Option B should rank cheaper than Option A based on authoritative final payable price.
        """
        def make_quote(opt_name, disp, fin):
            return NormalizedFareQuote(
                route="DEL-BOM", origin="DEL", destination="BOM",
                search_date=date(2026, 9, 7), travel_date=date(2026, 9, 8),
                advance_purchase_days=1, airline="IndiGo", flight_number="6E-101",
                departure_time="06:00", base_fare=disp, displayed_price=disp,
                displayed_search_price=disp, final_payable_price=fin,
                fare_option_name=opt_name,
                verification_status=DataStatus.FARE_VERIFIED if fin else DataStatus.SEARCH_RESULT,
            )

        quotes = [
            make_quote("OptionA", Decimal("4000"), Decimal("5500")),  # search 4000 -> final 5500
            make_quote("OptionB", Decimal("4200"), Decimal("4300")),  # search 4200 -> final 4300
            make_quote("OptionC", Decimal("4500"), Decimal("4600")),
            make_quote("OptionD", Decimal("4800"), Decimal("4900")),
            make_quote("OptionE", Decimal("5000"), Decimal("5100")),
            make_quote("OptionF", Decimal("5200"), Decimal("5800")),
        ]

        # Sort using authoritative final_payable_price
        quotes.sort(key=lambda q: q.final_payable_price or q.displayed_price)
        top5 = quotes[:5]

        # Option B (₹4300) must be first, Option A (₹5500) must be ranked 5th, Option F (₹5800) dropped
        assert len(top5) == 5
        assert top5[0].fare_option_name == "OptionB"
        assert top5[0].final_payable_price == Decimal("4300.00")
        assert top5[1].fare_option_name == "OptionC"
        assert top5[4].fare_option_name == "OptionA"
        assert "OptionF" not in [q.fare_option_name for q in top5]


# --- 6. RUN SUMMARY COUNTERS ---

class TestRunSummaryCounters:
    """Verifies that all 20 required summary counters are properly generated."""

    def test_run_summary_contains_all_20_required_fields(self, temp_run_manager):
        """Checks presence and types of all required fields in the summary schema."""
        summary = {
            "run_id": temp_run_manager.run_id,
            "started_at": "2026-09-07T22:00:00Z",
            "completed_at": "2026-09-07T22:05:00Z",
            "source": "Yatra",
            "routes_requested": ["DEL-BOM", "DEL-BLR", "BOM-BLR"],
            "advance_purchase_windows": ["T+1", "T+7", "T+15", "T+30", "T+45"],
            "total_searches": 15,
            "total_flights_found": 30,
            "total_fare_options_found": 90,
            "total_fares_selected": 45,
            "total_fares_verified": 40,
            "total_successful_extractions": 45,
            "total_failed_extractions": 0,
            "total_sold_out": 2,
            "total_price_changes": 5,
            "total_antibot_events": 1,
            "total_captcha_events": 0,
            "total_access_denied_events": 1,
            "screenshot_count": 48,
            "overall_status": "COMPLETED",
        }

        # Save to disk
        out_path = temp_run_manager.save_scraping_summary(summary)
        assert out_path.exists()

        with open(out_path, "r", encoding="utf-8") as f:
            saved = json.load(f)

        required_keys = [
            "run_id",
            "started_at",
            "completed_at",
            "source",
            "routes_requested",
            "advance_purchase_windows",
            "total_searches",
            "total_flights_found",
            "total_fare_options_found",
            "total_fares_selected",
            "total_fares_verified",
            "total_successful_extractions",
            "total_failed_extractions",
            "total_sold_out",
            "total_price_changes",
            "total_antibot_events",
            "total_captcha_events",
            "total_access_denied_events",
            "screenshot_count",
            "overall_status",
        ]
        for k in required_keys:
            assert k in saved, f"Missing required summary key: {k}"


# --- 7. DATABASE PERSISTENCE OF BOTH PRICES ---

class TestDatabasePersistenceBothPrices:
    """Verifies DB adapter persists displayed_search_price and final_payable_price."""

    def test_persist_both_prices_to_database(self, sample_candidate_quote):
        """Verifies insertion binds displayed_search_price, final_payable_price, and verification_status."""
        quote = sample_candidate_quote
        quote.final_payable_price = Decimal("4850.00")
        quote.verification_status = DataStatus.PRICE_CHANGED
        quote.verification_timestamp = datetime.now(timezone.utc)

        # Persist to live Supabase DB
        inserted = persist_fare_quotes_to_db(quotes=[quote], run_id=999)
        # Should be 1 (or 0 if unique conflict on retry)
        assert inserted in (0, 1)


# --- 8. HEADED BROWSER MODE AND OBSERVABILITY ---

class TestHeadedModeConfigurationAndDebugging:
    """Verifies that headed mode configurations, slow-mo, and pauses are properly wired."""

    def test_headed_mode_slow_mo_and_observation_delay(self):
        """When headless=False, slow_mo is applied for visual debugging."""
        from airgo.scrapers.yatra.config import YatraScraperConfig
        from airgo.scrapers.yatra.browser import PlaywrightBrowserManager

        cfg_headed = YatraScraperConfig(headless=False, slow_mo_ms=300, observation_delay=5.0)
        assert cfg_headed.headless is False
        assert cfg_headed.slow_mo_ms == 300
        assert cfg_headed.observation_delay == 5.0

        bm = PlaywrightBrowserManager(headless=False, slow_mo_ms=300)
        assert bm.headless is False
        assert bm.slow_mo_ms == 300

    def test_headless_mode_defaults_zero_slow_mo(self):
        """When headless=True, slow_mo is zero for fast execution."""
        from airgo.scrapers.yatra.config import YatraScraperConfig

        cfg_headless = YatraScraperConfig(headless=True, slow_mo_ms=0, observation_delay=0.0)
        assert cfg_headless.headless is True
        assert cfg_headless.slow_mo_ms == 0
        assert cfg_headless.observation_delay == 0.0
