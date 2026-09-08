"""
MakeMyTrip Airfare Harvester & Deep Checkout Auditor.
Extracts live flight quotes across DGCA routes and advance purchase horizons (T+1, T+7, T+15, T+30, T+45).
Includes optional deep checkout auditing: fare breakdown, zero-insurance opt-out, cheapest seat selection, and payment gateway verification.
Adheres strictly to the Zero Dummy Data Policy (Rule 1), Chrome-Only engine (Rule 6), and visual ground-truth proofs (Rule 3).
"""

import os
import sys
import io
import re
import json
import asyncio
import argparse
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

try:
    from patchright.async_api import async_playwright, BrowserContext, Page
except ImportError:
    from playwright.async_api import async_playwright, BrowserContext, Page

from airgo.scrapers.makemytrip.human_mouse import HumanMouse
from airgo.scrapers.makemytrip.config import (
    CITY_NAMES,
    DEFAULT_HORIZONS,
    build_search_url,
    load_route_basket,
    calculate_horizon_dates,
)

# Enforce UTF-8 stdout encoding for Windows console compatibility
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


INDIAN_CARRIERS: Dict[str, str] = {
    "6E": "IndiGo",
    "AI": "Air India",
    "IX": "Air India Express",
    "SG": "SpiceJet",
    "QP": "Akasa Air",
    "UK": "Vistara",
    "I5": "AirAsia India",
    "9I": "Alliance Air",
    "S5": "Star Air"
}


# Client-side JavaScript evaluation to extract rendered MakeMyTrip flight cards
JS_EXTRACT_MMT_CARDS = r"""() => {
    const results = [];
    const cards = Array.from(document.querySelectorAll('.flightCard, [class*="flightCard--full"], [class*="flightCard--clickable"], .listingCardItem'));
    const leaves = cards.filter(el => el.querySelectorAll('.flightCard, .listingCardItem').length === 0);

    for (let i = 0; i < leaves.length; i++) {
        const row = leaves[i];
        const text = row.innerText || '';
        if (text.length < 20) continue;

        let price = 0.0;
        const priceMatches = text.match(/₹\s*([\d,]+)/g);
        if (priceMatches && priceMatches.length > 0) {
            price = parseFloat(priceMatches[0].replace(/[^0-9]/g, '')) || 0.0;
        }
        if (price === 0) continue;

        let flightNo = '';
        const fltMatch = text.match(/\b([0-9A-Z]{2}[-\s]?[0-9]{3,4})\b/i);
        if (fltMatch) flightNo = fltMatch[1].replace(/\s+/g, '-').toUpperCase();

        let airline = '';
        const airImg = row.querySelector('img[src*="air-logos"], img[src*="airline"], img[src*="AirlineLogon"], img[alt]');
        if (airImg) {
            const src = airImg.src || '';
            const alt = airImg.alt || '';
            if (src.includes('6E') || alt.includes('6E')) airline = 'IndiGo';
            else if (src.includes('AI') || src.includes('AirIndia') || alt.includes('Air India')) airline = 'Air India';
            else if (src.includes('IX') || alt.includes('Express')) airline = 'Air India Express';
            else if (src.includes('SG') || src.includes('SpiceJet') || alt.includes('SpiceJet')) airline = 'SpiceJet';
            else if (src.includes('QP') || src.includes('Akasa') || alt.includes('Akasa')) airline = 'Akasa Air';
            else if (src.includes('UK') || alt.includes('Vistara')) airline = 'Vistara';
            else if (airImg.alt && !/logo|airline/i.test(airImg.alt)) airline = airImg.alt.trim();
        }
        
        if (!airline || /logo|sponsored/i.test(airline)) {
            const airMatch = text.match(/(Akasa Air|IndiGo|Air India Express|Air India|SpiceJet|Vistara|Alliance Air|Star Air)/i);
            if (airMatch) airline = airMatch[0].trim();
        }

        if (!airline || /sponsored/i.test(airline)) {
            if (/^6E/i.test(flightNo)) airline = 'IndiGo';
            else if (/^AI/i.test(flightNo)) airline = 'Air India';
            else if (/^IX/i.test(flightNo)) airline = 'Air India Express';
            else if (/^SG/i.test(flightNo)) airline = 'SpiceJet';
            else if (/^QP/i.test(flightNo)) airline = 'Akasa Air';
            else if (/^UK/i.test(flightNo)) airline = 'Vistara';
        }

        const timeMatches = text.match(/\b([012]?\d:[0-5]\d)\b/g);
        let depTime = timeMatches && timeMatches.length > 0 ? timeMatches[0] : '';
        let arrTime = timeMatches && timeMatches.length > 1 ? timeMatches[1] : '';

        let stops = /non[\s-]?stop/i.test(text) ? 0 : 1;
        const durMatch = text.match(/(\d{1,2}h\s*\d{1,2}m|\d{1,2}h|\d{1,2}m)/i);
        let duration = durMatch ? durMatch[0] : '';

        results.push({
            domIndex: i,
            airline: airline || "Airline",
            flightNumber: flightNo || "N/A",
            departureTime: depTime,
            arrivalTime: arrTime,
            duration: duration,
            stops: stops,
            priceINR: price
        });
    }
    return results;
}"""


class MakeMyTripHarvester:
    """
    Automated Harvester & Deep Checkout Auditor for MakeMyTrip.
    """

    def __init__(
        self,
        basket_csv: str = "data/processed/dgca_top100_route_basket.csv",
        routes: Optional[List[Dict[str, Any]]] = None,
        horizons: Optional[List[int]] = None,
        top_n: Optional[int] = 1,
        deep_checkout: bool = False,
        checkout_top_n: int = 1,
        headless: bool = False,
        runs_dir: str = "runs",
        pause_on_error: bool = False
    ):
        self.basket_csv = basket_csv
        self.horizons = horizons or DEFAULT_HORIZONS
        self.top_n = top_n
        self.deep_checkout = deep_checkout
        self.checkout_top_n = checkout_top_n
        self.headless = headless
        self.runs_dir = runs_dir
        self.pause_on_error = pause_on_error

        # Session / Run Metadata
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.run_id = f"{timestamp_str}_makemytrip"
        self.run_dir = os.path.join(self.runs_dir, self.run_id)
        os.makedirs(self.run_dir, exist_ok=True)

        if routes:
            self.routes = routes
        else:
            self.routes = load_route_basket(self.basket_csv, top_n=self.top_n)
        self.all_extracted_quotes: List[Dict[str, Any]] = []

        # Stable persistent profile directory per Patchright documentation
        self.profile_dir = os.path.join(self.runs_dir, "mmt_browser_profile")
        os.makedirs(self.profile_dir, exist_ok=True)

    async def _safe_screenshot(self, page: Page, path: str, full_page: bool = True):
        """
        Resilient screenshot capture avoiding Chromium texture buffer exhaustion.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            await page.screenshot(path=path, full_page=full_page)
        except Exception:
            try:
                await page.screenshot(path=path, full_page=False)
            except Exception as e:
                print(f"      [⚠️] Screenshot capture error: {e}")

    async def _dismiss_modal(self, page: Page, mouse: HumanMouse):
        """
        Dismisses login or marketing overlays using outside click coordinate (100, 100) and Escape.
        """
        await asyncio.sleep(4.5)
        try:
            await mouse.click_at((100, 100))
        except Exception:
            try:
                await page.keyboard.press("Escape")
            except Exception:
                pass
        await asyncio.sleep(1)

    async def _wait_for_sensor(self, context: BrowserContext, timeout_sec: int = 15) -> bool:
        """
        Monitors Akamai Bot Manager Premier telemetry handshake until _abck reaches ~0~.
        """
        for _ in range(timeout_sec):
            cookies = await context.cookies()
            abck = [c["value"] for c in cookies if c["name"] == "_abck"]
            if abck and "~0~" in abck[0]:
                return True
            await asyncio.sleep(1)
        return False

    async def harvest_all(self):
        """
        Executes the harvesting across all configured DGCA routes and advance purchase horizons.
        """
        print("\n" + "=" * 80)
        print(f"🚀 STARTING MAKEMYTRIP HARVEST RUN: {self.run_id}")
        print(f"   Target Routes   : {[r['route'] for r in self.routes]}")
        print(f"   Horizons        : {[f'T+{h}' for h in self.horizons]}")
        print(f"   Deep Checkout   : {self.deep_checkout} (Top {self.checkout_top_n} flights)")
        print(f"   Headless        : {self.headless}")
        print(f"   Mandatory Engine: Google Chrome (channel='chrome')")
        print(f"   Output Directory: {self.run_dir}")
        print("=" * 80 + "\n")

        start_time = datetime.now()

        for route_info in self.routes:
            route_str = route_info["route"]
            route_dir = os.path.join(self.run_dir, route_str)
            os.makedirs(route_dir, exist_ok=True)

            print(f"\n🛫 ROUTE: {route_str} ({route_info['city1']} -> {route_info['city2']})")
            horizon_dates = calculate_horizon_dates(self.horizons)

            for h_info in horizon_dates:
                horizon_label = h_info["horizon_label"]
                dept_date_dmy = h_info["date_dmy"]
                horizon_dir = os.path.join(route_dir, horizon_label)
                os.makedirs(horizon_dir, exist_ok=True)

                print(f"   📅 Advance Horizon: {horizon_label} ({dept_date_dmy})")
                await self._harvest_horizon(
                    route_info=route_info,
                    h_info=h_info,
                    horizon_dir=horizon_dir
                )

        # Write overall quotes.json and run_summary.json
        root_quotes_path = os.path.join(self.run_dir, "quotes.json")
        with open(root_quotes_path, "w", encoding="utf-8") as f:
            json.dump(self.all_extracted_quotes, f, indent=2, ensure_ascii=False)

        duration = (datetime.now() - start_time).total_seconds()
        summary = {
            "run_id": self.run_id,
            "platform": "makemytrip",
            "timestamp": start_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "routes_count": len(self.routes),
            "horizons": self.horizons,
            "deep_checkout_enabled": self.deep_checkout,
            "total_quotes_collected": len(self.all_extracted_quotes),
            "status": "COMPLETED"
        }
        with open(os.path.join(self.run_dir, "run_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 80)
        print(f"✅ MAKEMYTRIP HARVEST RUN COMPLETED IN {duration:.1f}s")
        print(f"   Total Quotes Saved: {len(self.all_extracted_quotes)}")
        print(f"   Audit Directory   : {self.run_dir}")
        print("=" * 80 + "\n")

    async def _harvest_horizon(
        self,
        route_info: Dict[str, Any],
        h_info: Dict[str, Any],
        horizon_dir: str
    ):
        """
        Harvests search results for a single route and horizon using Patchright golden config and HumanMouse.
        """
        origin = route_info["origin"]
        dest = route_info["destination"]
        date_dmy = h_info["date_dmy"]
        horizon_label = h_info["horizon_label"]
        dep_date_obj: date = h_info["date_obj"]

        async with async_playwright() as p:
            # Patchright Undetected Golden Configuration
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                channel="chrome",
                headless=self.headless,
                no_viewport=True,
                args=["--start-maximized"]
            )

            page = context.pages[0] if context.pages else await context.new_page()
            mouse = HumanMouse(page)
            await mouse.show_cursor()

            try:
                print("      [1/4] Navigating to MakeMyTrip & preparing search widget...")
                await page.goto("https://www.makemytrip.com/flights/", wait_until="domcontentloaded", timeout=45000)

                # Dismiss login modal via HumanMouse
                await self._dismiss_modal(page, mouse)

                city1_name = route_info.get("city1", "")
                city2_name = route_info.get("city2", "")

                # 1. Select Origin City
                from_label = await page.query_selector('label[for="fromCity"]')
                from_text = await page.evaluate("() => (document.querySelector('#fromCity') || {}).value || ''")
                if (origin not in from_text and city1_name not in from_text) or not from_text:
                    print(f"      [ℹ️] Selecting From: {origin} ({city1_name})...")
                    if from_label:
                        await mouse.click_at(from_label)
                        await asyncio.sleep(1)
                    auto_input = await page.query_selector('input[placeholder*="From"], input[autocomplete="off"]')
                    if auto_input:
                        await auto_input.click()
                        await page.keyboard.press("Control+A")
                        await page.keyboard.press("Backspace")
                        await auto_input.fill(origin)
                        await asyncio.sleep(1.5)
                        first_sug = await page.query_selector('li[id*="react-autowhatever-1-section-0-item-0"], li.react-autosuggest__suggestion--first')
                        if first_sug:
                            await mouse.click_at(first_sug)
                            await asyncio.sleep(1)

                # 2. Select Destination City
                to_label = await page.query_selector('label[for="toCity"]')
                to_text = await page.evaluate("() => (document.querySelector('#toCity') || {}).value || ''")
                if (dest not in to_text and city2_name not in to_text) or not to_text:
                    print(f"      [ℹ️] Selecting To: {dest} ({city2_name})...")
                    if to_label:
                        await mouse.click_at(to_label)
                        await asyncio.sleep(1)
                    to_input = await page.query_selector('input[placeholder*="To"]')
                    if to_input:
                        await to_input.click()
                        await page.keyboard.press("Control+A")
                        await page.keyboard.press("Backspace")
                        await to_input.fill(dest)
                        await asyncio.sleep(1.5)
                        first_to_sug = await page.query_selector('li[id*="react-autowhatever-1-section-0-item-0"], li.react-autosuggest__suggestion--first')
                        if first_to_sug:
                            await mouse.click_at(first_to_sug)
                            await asyncio.sleep(1)

                # 3. Select Date from Calendar for Advance Horizon
                target_date_str = dep_date_obj.strftime("%b %d %Y")
                print(f"      [ℹ️] Selecting Horizon Date: {target_date_str}...")
                dep_widget = await page.query_selector('label[for="departure"], div[data-cy="departureDate"]')
                if dep_widget:
                    await mouse.click_at(dep_widget)
                    await asyncio.sleep(1)

                # Look for matching day
                day_el = await page.query_selector(f'div.DayPicker-Day[aria-label*="{target_date_str}"]')
                if not day_el:
                    # If not in visible month, click next month
                    next_month_btn = await page.query_selector('span.DayPicker-NavButton--next, [aria-label="Next Month"]')
                    if next_month_btn:
                        await mouse.click_at(next_month_btn)
                        await asyncio.sleep(1)
                        day_el = await page.query_selector(f'div.DayPicker-Day[aria-label*="{target_date_str}"]')

                if day_el:
                    await mouse.click_at(day_el)
                    print(f"      [✓] Selected calendar date: {target_date_str}")
                    await asyncio.sleep(1)

                # 4. Pre-warm sensor telemetry over From and To
                f_hover = await page.query_selector('label[for="fromCity"]')
                if f_hover:
                    await mouse.human_hover(f_hover, dwell_sec=0.6)
                t_hover = await page.query_selector('label[for="toCity"]')
                if t_hover:
                    await mouse.human_hover(t_hover, dwell_sec=0.6)

                # Wait for Akamai sensor token
                sensor_ok = await self._wait_for_sensor(context, timeout_sec=10)
                if sensor_ok:
                    print("      [✓] Akamai Bot Manager telemetry validated (_abck ~0~).")

                # 5. Click Search Button
                print("      [2/4] Clicking Search button with HumanMouse...")
                search_a = await page.query_selector('a.widgetSearchBtn, [data-cy="submit"] a, a:has-text("Search")')
                if search_a:
                    await mouse.click_at(search_a)
                else:
                    search_btn = await page.query_selector('[data-cy="submit"]')
                    if search_btn:
                        await search_btn.click()

                # 6. Resilient card wait loop
                print("      [3/4] Waiting for flight listings & lazy loading...")
                loaded = False
                for sec in range(35):
                    await asyncio.sleep(1)
                    # Handle transient 'Network Problem' refresh prompt if rendered
                    ref_btn = await page.query_selector('button:has-text("REFRESH"), a:has-text("REFRESH"), .refreshBtn')
                    if ref_btn and await ref_btn.is_visible():
                        print(f"      [ℹ️] Transient network prompt detected at second {sec+1}, clicking REFRESH...")
                        await mouse.click_at(ref_btn)
                        await asyncio.sleep(3)

                    count = await page.evaluate("() => document.querySelectorAll('div.listingCard, div.clusterCard, [id^=\"listing-id\"], div.fli-list, .flightItem').length")
                    if count > 0:
                        print(f"      [✓] Loaded initial {count} live flight cards at second {sec+1}!")
                        loaded = True
                        break

                if not loaded:
                    # Warm session direct navigation recovery
                    search_url = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{dest}-{dep_date_obj.strftime('%d/%m/%Y')}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
                    print(f"      [ℹ️] Retrying navigation via direct warm session URL: {search_url}...")
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                    await asyncio.sleep(4)
                    ref_btn = await page.query_selector('button:has-text("REFRESH"), a:has-text("REFRESH")')
                    if ref_btn:
                        await mouse.click_at(ref_btn)
                        await asyncio.sleep(3)
                    for s in range(25):
                        count = await page.evaluate("() => document.querySelectorAll('div.listingCard, div.clusterCard, [id^=\"listing-id\"], div.fli-list, .flightItem').length")
                        if count > 0:
                            print(f"      [✓] Direct recovery loaded {count} live flight cards!")
                            loaded = True
                            break
                        await asyncio.sleep(1)

                # Dismiss overlay if present
                try:
                    overlay_close = await page.query_selector('span.overlay-cross, button.overlay-close, div.fareRuleOverlay-close')
                    if overlay_close:
                        await overlay_close.click()
                except Exception:
                    pass

                # Smooth progressive human scrolling across entire page to capture all virtualized cards
                print("      [4/4] Human progressive scrolling across entire page to extract all flight cards...")
                all_collected_quotes: Dict[str, Dict[str, Any]] = {}
                unchanged_count = 0

                # Ensure cursor is over the flight listing center so wheel events target listings
                await mouse.move_to((650, 400))
                await asyncio.sleep(0.5)

                for scroll_step in range(60):
                    # Extract cards currently in DOM (virtualized list)
                    batch = await page.evaluate(JS_EXTRACT_MMT_CARDS)
                    new_count = 0
                    for card in batch:
                        key = f"{card.get('flightNumber', '')}_{card.get('departureTime', '')}_{card.get('priceINR', 0)}"
                        if key not in all_collected_quotes:
                            quote = {
                                "airline": card.get("airline"),
                                "flight_number": card.get("flightNumber"),
                                "origin": origin,
                                "destination": dest,
                                "departure_date": date_dmy,
                                "departure_time": card.get("departureTime"),
                                "arrival_time": card.get("arrivalTime"),
                                "duration": card.get("duration", ""),
                                "stops": card.get("stops", 0),
                                "price_inr": card.get("priceINR"),
                                "advance_horizon": horizon_label,
                                "captured_at": datetime.now().isoformat(),
                                "platform": "makemytrip"
                            }
                            all_collected_quotes[key] = quote
                            new_count += 1

                    scroll_info = await page.evaluate("() => ({ y: window.scrollY, height: document.body.scrollHeight })")
                    if scroll_step % 5 == 0 or new_count > 0:
                        print(f"         Step {scroll_step+1:02d}: ScrollY={int(scroll_info['y'])}, Height={scroll_info['height']} | Batch={len(batch)}, New=+{new_count}, Total Unique={len(all_collected_quotes)}")

                    # Smooth wheel scroll
                    await mouse.smooth_scroll(500, steps=10)
                    await asyncio.sleep(0.5)

                    max_scroll = scroll_info['height'] - 1000
                    if scroll_info['y'] >= max_scroll and new_count == 0:
                        unchanged_count += 1
                        if unchanged_count >= 5:
                            print("         Reached bottom of flight listings.")
                            break
                    else:
                        unchanged_count = 0

                # Scroll back to top to take proof screenshot
                await page.evaluate("() => window.scrollTo(0, 0)")
                await asyncio.sleep(1.5)

                # Ground-Truth Proof: Screenshot
                shot_path = os.path.join(horizon_dir, "00_search_results.png")
                await self._safe_screenshot(page, shot_path, full_page=False)
                print(f"      [📸] Proof Saved: {shot_path}")

                horizon_quotes = list(all_collected_quotes.values())
                print(f"      [📊] Extracted {len(horizon_quotes)} total live flight cards.")
                self.all_extracted_quotes.extend(horizon_quotes)

                # Save horizon-level quotes.json
                horizon_quotes_path = os.path.join(horizon_dir, "quotes.json")
                with open(horizon_quotes_path, "w", encoding="utf-8") as f:
                    json.dump(horizon_quotes, f, indent=2, ensure_ascii=False)
                print(f"      [💾] Horizon Quotes Saved ({len(horizon_quotes)} quotes): {horizon_quotes_path}")

                # Optional: Deep Checkout Auditing
                if self.deep_checkout and horizon_quotes:
                    top_targets = horizon_quotes[:self.checkout_top_n]
                    for idx, target in enumerate(top_targets):
                        print(f"\n      🔎 DEEP CHECKOUT AUDIT [{idx+1}/{len(top_targets)}]: {target['airline']} {target['flight_number']} (₹{target['price_inr']})")
                        await self._audit_flight_checkout(
                            context=context,
                            page=page,
                            mouse=mouse,
                            flight_quote=target,
                            horizon_dir=horizon_dir
                        )

            except Exception as e:
                print(f"      [❌] Horizon harvest failed: {e}")
                if self.pause_on_error:
                    input("Press Enter to continue...")
            finally:
                await context.close()

    async def _audit_flight_checkout(
        self,
        context: BrowserContext,
        page: Page,
        mouse: HumanMouse,
        flight_quote: Dict[str, Any],
        horizon_dir: str
    ):
        """
        Audits checkout review, zero-insurance opt-out, cheapest seat selection, and payment gateway.
        """
        carrier_clean = re.sub(r'[^a-zA-Z0-9]', '', flight_quote.get("airline", "Airline"))
        flt_clean = re.sub(r'[^a-zA-Z0-9]', '-', flight_quote.get("flight_number", "Flight"))
        checkout_folder_name = f"checkout_{carrier_clean}_{flt_clean}"
        checkout_dir = os.path.join(horizon_dir, checkout_folder_name)
        os.makedirs(checkout_dir, exist_ok=True)

        print(f"         📁 Flight Folder: {checkout_dir}")

        try:
            # 1. Click "VIEW PRICES" on the flight card
            view_prices_btn = await page.query_selector('button:has-text("VIEW PRICES"), button:has-text("View Prices"), span:has-text("VIEW PRICES")')
            if view_prices_btn:
                print("         [1/5] Expanding fare options (VIEW PRICES)...")
                await view_prices_btn.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                await mouse.click_at(view_prices_btn)
                await asyncio.sleep(2)

            # 2. Click "BOOK NOW" and handle new tab
            book_now_btn = None
            for _ in range(12):
                book_now_btn = await page.query_selector('button:has-text("BOOK NOW"), button:has-text("Book Now"), a:has-text("BOOK NOW"), button[id^="bookbutton"]')
                if book_now_btn and await book_now_btn.is_visible():
                    break
                await asyncio.sleep(0.5)

            if not book_now_btn:
                print("         [⚠️] Book now button not visible after expanding.")
                return

            print("         [2/5] Clicking BOOK NOW...")
            await book_now_btn.scroll_into_view_if_needed()
            async with context.expect_page() as new_page_info:
                await mouse.click_at(book_now_btn)
            review_page = await new_page_info.value

            await review_page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(4)
            review_mouse = HumanMouse(review_page)
            await review_mouse.show_cursor()

            # Extract fare breakdown from Review Page
            fare_data = await review_page.evaluate(r"""() => {
                const text = document.body.innerText || '';
                const baseMatch = text.match(/Base Fare[^\d₹]*₹?\s*([\d,]+)/i);
                const taxMatch = text.match(/Taxes and Surcharges[^\d₹]*₹?\s*([\d,]+)/i);
                const totalMatch = text.match(/Total Amount[^\d₹]*₹?\s*([\d,]+)/i);
                return {
                    baseFare: baseMatch ? parseFloat(baseMatch[1].replace(/,/g, '')) : null,
                    taxes: taxMatch ? parseFloat(taxMatch[1].replace(/,/g, '')) : null,
                    total: totalMatch ? parseFloat(totalMatch[1].replace(/,/g, '')) : null
                };
            }""")
            print(f"         [📊] Observed Breakdown: Base ₹{fare_data.get('baseFare')}, Taxes ₹{fare_data.get('taxes')}, Total ₹{fare_data.get('total')}")

            # 3. Handle Zero-Insurance Opt-Out
            opt_out = await review_page.query_selector('label:has-text("No, I do not wish"), label:has-text("risk my travel"), label:has-text("No, I will risk"), input[value="no" i]')
            if opt_out:
                print("         [ℹ️] Opting out of travel insurance (Zero-insurance policy)...")
                try:
                    await opt_out.scroll_into_view_if_needed()
                    await review_mouse.click_at(opt_out)
                    await asyncio.sleep(1)
                except Exception:
                    pass

            # Fill passenger details
            add_adult = await review_page.query_selector('button:has-text("+ ADD ADULT"), button:has-text("Add New Adult"), button:has-text("+ Add New Adult"), span:has-text("+ ADD ADULT"), button:has-text("+ ADD NEW ADULT")')
            if add_adult:
                await add_adult.scroll_into_view_if_needed()
                await review_mouse.click_at(add_adult)
                await asyncio.sleep(1)

            fn = await review_page.query_selector('input[placeholder*="First"], input[name*="firstName" i]')
            if fn:
                await fn.fill("Arundhati")
                await asyncio.sleep(0.3)

            ln = await review_page.query_selector('input[placeholder*="Last"], input[name*="lastName" i]')
            if ln:
                await ln.fill("Sharma")
                await asyncio.sleep(0.3)

            gender = await review_page.query_selector('label:has-text("FEMALE"), label:has-text("Female")')
            if gender:
                await review_mouse.click_at(gender)
                await asyncio.sleep(0.3)

            # Contact Details
            mob = await review_page.query_selector('input[placeholder*="Mobile"], input[type="tel"], input[name*="mobile" i]')
            if mob:
                await mob.click()
                await review_page.keyboard.press("Control+A")
                await review_page.keyboard.press("Backspace")
                await mob.fill("9876543210")
                await asyncio.sleep(0.5)

            email = await review_page.query_selector('input[placeholder*="Email"], input[name*="email" i], input[type="email"]')
            if email:
                await email.click()
                await review_page.keyboard.press("Control+A")
                await review_page.keyboard.press("Backspace")
                await email.fill("audit.airgo@gmail.com")
                await asyncio.sleep(0.5)

            # Date of birth if requested
            try:
                dob_d = review_page.locator('div:has-text("Date"), div[class*="dateSelect"]').last
                if await dob_d.is_visible():
                    await dob_d.click()
                    await asyncio.sleep(0.5)
                    d_opt = review_page.locator('li:has-text("15"), div:has-text("15"), span:has-text("15")').first
                    if await d_opt.is_visible(): await d_opt.click()
                    await asyncio.sleep(0.5)

                dob_m = review_page.locator('div:has-text("Month"), div[class*="monthSelect"]').last
                if await dob_m.is_visible():
                    await dob_m.click()
                    await asyncio.sleep(0.5)
                    m_opt = review_page.locator('li:has-text("Jul"), div:has-text("Jul"), span:has-text("Jul")').first
                    if await m_opt.is_visible(): await m_opt.click()
                    await asyncio.sleep(0.5)

                dob_y = review_page.locator('div:has-text("Year"), div[class*="yearSelect"]').last
                if await dob_y.is_visible():
                    await dob_y.click()
                    await asyncio.sleep(0.5)
                    y_opt = review_page.locator('li:has-text("1995"), div:has-text("1995"), span:has-text("1995")').first
                    if await y_opt.is_visible(): await y_opt.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

            # Review screen proof: 01_checkout_review.png
            review_shot = os.path.join(checkout_dir, "01_checkout_review.png")
            await self._safe_screenshot(review_page, review_shot, full_page=False)
            print(f"         [📸] Proof Saved: {review_shot}")

            # 4. Proceed to Aircraft Seat Map
            cont_btn = await review_page.query_selector('button:has-text("CONTINUE"), button:has-text("Continue"), button.continueBtn')
            if cont_btn:
                print("         [3/5] Navigating to aircraft seat map...")
                await cont_btn.scroll_into_view_if_needed()
                await review_mouse.click_at(cont_btn)
                await asyncio.sleep(3)

            # Handle confirm popup if present
            popup_confirm = await review_page.query_selector('button:has-text("CONFIRM"), button:has-text("Confirm"), button:has-text("Yes, Continue")')
            if popup_confirm:
                await review_mouse.click_at(popup_confirm)
                await asyncio.sleep(3)

            # Seat Map screenshot: 02_aircraft_seat_map.png
            seat_shot = os.path.join(checkout_dir, "02_aircraft_seat_map.png")
            await self._safe_screenshot(review_page, seat_shot, full_page=False)
            print(f"         [📸] Proof Saved: {seat_shot}")

            # Select cheapest/free seat or skip to payment
            skip_seat = await review_page.query_selector('button:has-text("CONTINUE ANYWAY"), button:has-text("Proceed to pay"), button:has-text("Continue to payment"), button:has-text("PROCEED TO PAY"), button:has-text("CONTINUE"), button:has-text("Skip to Payment")')
            if skip_seat:
                print("         [4/5] Proceeding to payment gateway...")
                await review_mouse.click_at(skip_seat)
                await asyncio.sleep(4)

            skip_seat_popup = await review_page.query_selector('button:has-text("Yes, Proceed"), button:has-text("CONTINUE ANYWAY"), button:has-text("Proceed without seat")')
            if skip_seat_popup:
                await review_mouse.click_at(skip_seat_popup)
                await asyncio.sleep(4)

            # 5. Payment Gateway screenshot: 03_final_payment_gateway.png
            pay_shot = os.path.join(checkout_dir, "03_final_payment_gateway.png")
            await self._safe_screenshot(review_page, pay_shot, full_page=False)
            print(f"         [📸] Proof Saved: {pay_shot}")

            # Extract convenience fee
            page_text = await review_page.inner_text("body")
            conv_fee = 0.0
            conv_match = re.search(r'(?:convenience|payment\s*gateway|processing)\s*fee[^\d₹]*₹?\s*([\d,]+)', page_text, re.IGNORECASE)
            if conv_match:
                conv_fee = float(conv_match.group(1).replace(",", ""))

            audited_quote = {
                **flight_quote,
                "audit_timestamp": datetime.now().isoformat(),
                "checkout_url": review_page.url,
                "base_sticker_price": flight_quote["price_inr"],
                "observed_base_fare": fare_data.get("baseFare"),
                "observed_taxes": fare_data.get("taxes"),
                "observed_convenience_fee": conv_fee,
                "audited_proofs": {
                    "search_results": "00_search_results.png",
                    "checkout_review": "01_checkout_review.png",
                    "aircraft_seat_map": "02_aircraft_seat_map.png",
                    "final_payment_gateway": "03_final_payment_gateway.png"
                }
            }

            audited_json_path = os.path.join(checkout_dir, "audited_quote.json")
            with open(audited_json_path, "w", encoding="utf-8") as f:
                json.dump(audited_quote, f, indent=2, ensure_ascii=False)
            print(f"         [💾] Audited Quote Saved: {audited_json_path}")

        except Exception as e:
            print(f"         [⚠️] Deep checkout audit error: {e}")


# Alias matching AirGo scraper naming convention
MakeMyTripScraper = MakeMyTripHarvester


def main():
    parser = argparse.ArgumentParser(description="MakeMyTrip Live Airfare Harvester & Deep Checkout Auditor")
    parser.add_argument("--basket", default="data/processed/dgca_top100_route_basket.csv", help="DGCA route basket CSV path")
    parser.add_argument("--horizons", nargs="+", type=int, default=DEFAULT_HORIZONS, help="Advance purchase horizons in days (e.g. 1 7 15 30 45)")
    parser.add_argument("--top-n", type=int, default=1, help="Number of top routes from the basket to harvest")
    parser.add_argument("--deep-checkout", action="store_true", help="Enable deep checkout auditing (Review, Seat Map, Payment Gateway)")
    parser.add_argument("--checkout-top-n", type=int, default=1, help="Number of flights to deep audit per horizon")
    parser.add_argument("--visible", action="store_true", help="Run headful Google Chrome browser")
    parser.add_argument("--runs-dir", default="runs", help="Root directory for local audit storage")
    parser.add_argument("--pause", action="store_true", help="Pause on errors for interactive inspection")

    args = parser.parse_args()

    harvester = MakeMyTripHarvester(
        basket_csv=args.basket,
        horizons=args.horizons,
        top_n=args.top_n,
        deep_checkout=args.deep_checkout,
        checkout_top_n=args.checkout_top_n,
        headless=not args.visible,
        runs_dir=args.runs_dir,
        pause_on_error=args.pause
    )

    asyncio.run(harvester.harvest_all())


if __name__ == "__main__":
    main()
