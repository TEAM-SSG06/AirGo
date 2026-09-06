import os
import logging
import re
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from playwright.sync_api import sync_playwright
from airgo.scrapers.base import BaseScraper
from airgo.pipeline.models import RawQuoteSchema
from airgo.engine.dgca_weights import INDIAN_AIRLINES

logger = logging.getLogger("AirGoScraper.Playwright")


class PlaywrightFlightScraper(BaseScraper):
    """
    Real Visual Browser Scraper using Playwright.
    Captures live flight quotes and attaches original search links.
    """

    def __init__(self, headless: bool = False, rate_limit_secs: float = 1.0):
        self.headless = os.getenv("HEADLESS", "false").lower() == "true" if headless is False else headless
        super().__init__(name="PlaywrightVisual", rate_limit_secs=rate_limit_secs)

    def fetch_quotes(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        advance_window: str,
        advance_days: int
    ) -> List[RawQuoteSchema]:
        quotes: List[RawQuoteSchema] = []
        booking_today = date.today()
        formatted_date = departure_date.strftime("%Y-%m-%d")
        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{formatted_date}%20one%20way"

        try:
            with sync_playwright() as p:
                self.logger.info(f"[Playwright] 🖥️ Navigating to: {url}")
                browser = p.chromium.launch(
                    headless=self.headless,
                    slow_mo=50,
                    args=["--start-maximized", "--no-sandbox"]
                )
                context = browser.new_context(
                    no_viewport=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="en-IN"
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3500)

                flight_cards = page.query_selector_all("li.pIav2d, div.gws-flights-results__itinerary-card, div.h11v2, div[role='listitem']")

                for card in flight_cards[:15]:
                    card_text = card.inner_text()
                    if not card_text or "₹" not in card_text:
                        continue

                    price_match = re.search(r"₹\s*([0-9,]+)", card_text)
                    if not price_match:
                        continue
                    
                    price_str = price_match.group(1).replace(",", "")
                    try:
                        total_fare = float(price_str)
                    except ValueError:
                        continue

                    if total_fare < 1000 or total_fare > 60000:
                        continue

                    carrier_name = "IndiGo"
                    carrier_code = "6E"
                    for code, name in INDIAN_AIRLINES.items():
                        if name.lower() in card_text.lower():
                            carrier_name = name
                            carrier_code = code
                            break

                    time_match = re.search(r"(\d{1,2}:\d{2})\s*(?:AM|PM|am|pm)?", card_text)
                    dep_time_str = time_match.group(1) if time_match else "08:00"
                    
                    try:
                        dep_hour, dep_min = [int(x) for x in dep_time_str.split(":")[:2]]
                        dep_datetime = datetime.combine(departure_date, datetime.min.time()).replace(hour=dep_hour, minute=dep_min)
                    except Exception:
                        dep_datetime = datetime.combine(departure_date, datetime.min.time()).replace(hour=8, minute=0)

                    stops = 0
                    if "1 stop" in card_text.lower():
                        stops = 1
                    elif "2 stop" in card_text.lower():
                        stops = 2

                    duration = 130
                    dur_match = re.search(r"(\d+)\s*hr(?:\s*(\d+)\s*min)?", card_text)
                    if dur_match:
                        hrs = int(dur_match.group(1))
                        mins = int(dur_match.group(2)) if dur_match.group(2) else 0
                        duration = hrs * 60 + mins

                    flight_no = f"{carrier_code}-{dep_datetime.strftime('%H%M')}"
                    base_fare = round(total_fare * 0.74, 2)
                    taxes = round(total_fare - base_fare, 2)

                    quotes.append(RawQuoteSchema(
                        source="Google Flights Live",
                        carrier=carrier_name,
                        carrier_code=carrier_code,
                        flight_number=flight_no,
                        origin=origin,
                        destination=destination,
                        departure_datetime=dep_datetime,
                        duration_mins=duration,
                        stops=stops,
                        booking_date=booking_today,
                        advance_window=advance_window,
                        advance_days=advance_days,
                        fare_class="Economy",
                        base_fare=base_fare,
                        surcharges=0.0,
                        taxes=taxes,
                        convenience_fee=350.0,
                        total_fare=total_fare,
                        source_url=url,
                        is_sold_out=False,
                        seats_remaining=9,
                        metadata_json={"channel": "Chromium Live", "raw_snippet": card_text[:100]}
                    ))

                page.wait_for_timeout(500)
                browser.close()
        except Exception as e:
            self.logger.error(f"[Playwright] Scraper error: {e}")

        return quotes
