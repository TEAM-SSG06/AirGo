"""
AirGo Crawlee Multi-Platform Flight Harvesting Engine.
Leverages Apify Crawlee for Python with:
- PlaywrightCrawler and SessionPool management
- BrowserForge anti-fingerprinting & stealth launch options
- Concurrency scaling & automated request retry handling
- Zero Dummy Data policy (raw DOM extraction and timestamped screenshot audits)
"""

import os
import sys
import io
import re
import csv
import json
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

from crawlee import Request, ConcurrencySettings
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

from airgo.utils.run_manager import create_run_directory, save_run_artifact

# Fix Windows terminal UTF-8 encoding
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

CITY_NAMES = {
    "DEL": "Delhi", "BOM": "Mumbai", "BLR": "Bengaluru", "HYD": "Hyderabad",
    "CCU": "Kolkata", "MAA": "Chennai", "GOI": "Goa", "GOX": "Goa",
    "PNQ": "Pune", "AMD": "Ahmedabad", "COK": "Kochi", "GAU": "Guwahati",
    "LKO": "Lucknow", "PAT": "Patna", "JAI": "Jaipur", "SXR": "Srinagar",
    "BBI": "Bhubaneswar", "IXC": "Chandigarh", "IXR": "Ranchi", "VTZ": "Visakhapatnam",
    "TRV": "Thiruvananthapuram", "VNS": "Varanasi", "IDR": "Indore", "NAG": "Nagpur",
    "ATQ": "Amritsar", "IXB": "Bagdogra", "BDQ": "Vadodara", "UDR": "Udaipur"
}


def load_route_basket(csv_path: str, top_n: Optional[int] = None) -> List[Dict[str, Any]]:
    """Loads top domestic routes from the DGCA route basket CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Route basket CSV not found at: {csv_path}")

    routes = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pair = row.get("route", "").strip().upper()
            if "-" in pair:
                origin, dest = pair.split("-", 1)
                routes.append({
                    "rank": int(row.get("rank", len(routes) + 1)),
                    "route": pair,
                    "origin": origin.strip(),
                    "destination": dest.strip(),
                    "city1": row.get("city1", ""),
                    "city2": row.get("city2", "")
                })

    if top_n and top_n > 0:
        routes = routes[:top_n]

    return routes


async def safe_capture_screenshot(page, file_path: str):
    """Resilient screenshot capture avoiding chromium texture buffer limits."""
    try:
        await page.screenshot(path=file_path, full_page=False, timeout=10000)
    except Exception as e:
        print(f"  [⚠️ ] Screenshot capture warning for {os.path.basename(file_path)}: {e}")


async def extract_cleartrip_cards(page) -> List[Dict[str, Any]]:
    """Extracts raw flight records from Cleartrip search DOM without synthetic mock data."""
    return await page.evaluate(r"""() => {
        const results = [];
        const bookButtons = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.trim() === 'Book');

        function findCardForButton(btn) {
            let cur = btn.parentElement;
            let card = null;
            while (cur && cur !== document.body) {
                const logos = cur.querySelectorAll('img[src*="air-logos"]');
                const books = Array.from(cur.querySelectorAll('button')).filter(b => b.innerText.trim() === 'Book');
                if (books.length === 1 && logos.length >= 1) {
                    card = cur;
                }
                if (books.length > 1) break;
                cur = cur.parentElement;
            }
            return card || btn.closest('div');
        }

        for (let i = 0; i < bookButtons.length; i++) {
            const btn = bookButtons[i];
            const container = findCardForButton(btn);
            if (!container) continue;

            const text = container.innerText || '';

            const imgEl = container.querySelector('img[alt], img[src*="air-logos"]');
            let airlineName = '';
            let flightNumber = '';

            if (imgEl && imgEl.parentElement && imgEl.parentElement.parentElement) {
                const nameContainer = imgEl.parentElement.parentElement;
                const pTags = Array.from(nameContainer.querySelectorAll('p')).map(p => p.innerText.trim()).filter(Boolean);
                if (pTags.length >= 1) airlineName = pTags[0];
                if (pTags.length >= 2) flightNumber = pTags[1];
            }

            if (!airlineName || /refundable/i.test(airlineName)) {
                const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
                for (const line of lines) {
                    if (/^(indigo|air\s*india(\s*express)?|spicejet|akasa(\s*air)?|vistara|alliance\s*air|star\s*air)$/i.test(line)) {
                        airlineName = line;
                    }
                    if (/^[0-9A-Z]{2}[-\s]?[0-9]{3,4}$/i.test(line)) {
                        flightNumber = line;
                    }
                }
            }

            let price = 0.0;
            const priceMatches = text.match(/₹\s*([\d,]+)/g);
            if (priceMatches && priceMatches.length > 0) {
                const cleanPrice = priceMatches[0].replace(/[₹,\s]/g, '');
                price = parseFloat(cleanPrice) || 0.0;
            }

            const timeMatches = text.match(/\b([012]?\d:[0-5]\d)\b/g);
            let depTime = timeMatches && timeMatches.length > 0 ? timeMatches[0] : '';
            let arrTime = timeMatches && timeMatches.length > 1 ? timeMatches[1] : '';

            const durMatch = text.match(/\b(\d+h\s*\d*m?|\d+m)\b/i);
            let duration = durMatch ? durMatch[1] : '';

            if (airlineName && !/refundable/i.test(airlineName) && flightNumber && price > 0) {
                results.push({
                    domIndex: i,
                    airline: airlineName,
                    flightNumber: flightNumber.replace(/\s+/g, ''),
                    departureTime: depTime,
                    arrivalTime: arrTime,
                    duration: duration,
                    price: price,
                    stops: /non-?stop/i.test(text) ? 0 : 1
                });
            }
        }

        return results;
    }""")


async def extract_easemytrip_cards(page) -> List[Dict[str, Any]]:
    """Extracts raw flight records from EaseMyTrip search DOM without synthetic mock data."""
    return await page.evaluate(r"""() => {
        const cards = Array.from(document.querySelectorAll('div.fltResult, div[class*="fltResult"]'));
        const results = [];

        cards.forEach((card, idx) => {
            const priceEl = card.querySelector("span[id*='spnPrice']") || card.querySelector("div.col-md-2 span[price]") || card.querySelector("span[price]");
            let price = null;
            if (priceEl) {
                const attr = priceEl.getAttribute('price');
                if (attr) price = parseFloat(attr);
                if (!price) {
                    const clean = priceEl.innerText.replace(/[^0-9.]/g, '');
                    if (clean) price = parseFloat(clean);
                }
            }

            const airEl = card.querySelector("span.txt-r4") || card.querySelector("span.air-name") || card.querySelector("span[class*='airl-name']");
            const fltEl = card.querySelector("span.txt-r5") || card.querySelector("span.flt-num") || card.querySelector("span[class*='flt-num']");
            const times = Array.from(card.querySelectorAll("span.txt-r2-n, span[class*='txt-r2']")).map(t => t.innerText.trim());
            const durEl = card.querySelector("span.dura_md") || card.querySelector("span.non-stop") || card.querySelector("span[class*='dura']");

            let airline = airEl ? airEl.innerText.trim() : '';
            let flightNumber = fltEl ? fltEl.innerText.trim() : '';

            if (!airline) {
                const m = card.innerText.match(/(IndiGo|Air India|SpiceJet|Akasa Air|Air India Express|Vistara)/i);
                if (m) airline = m[0];
            }
            if (!flightNumber) {
                const m = card.innerText.match(/\b([0-9A-Z]{2}[-\s]?[0-9]{3,4})\b/);
                if (m) flightNumber = m[1];
            }

            if (price && price > 0 && airline) {
                results.push({
                    domIndex: idx,
                    airline: airline,
                    flightNumber: flightNumber.replace(/\s+/g, ''),
                    departureTime: times.length > 0 ? times[0] : '',
                    arrivalTime: times.length > 1 ? times[1] : '',
                    duration: durEl ? durEl.innerText.trim() : '',
                    price: price,
                    stops: /non-?stop/i.test(card.innerText) ? 0 : 1
                });
            }
        });

        return results;
    }""")


class CrawleeFlightHarvester:
    """
    Crawlee-driven flight harvester managing session rotation, stealth fingerprinting,
    and concurrent search page extraction across DGCA routes.
    """

    def __init__(
        self,
        platform: str = "cleartrip",
        flights_per_route: int = 3,
        max_concurrency: int = 1,
        headless: bool = True
    ):
        self.platform = platform.lower()
        self.flights_per_route = flights_per_route
        self.max_concurrency = max_concurrency
        self.headless = headless
        self.audited_quotes: List[Dict[str, Any]] = []
        self.run_dir: str = ""

    def build_requests(
        self,
        routes: List[Dict[str, Any]],
        horizons: List[int]
    ) -> List[Request]:
        """Builds Crawlee Request objects with route and horizon metadata."""
        requests = []
        for route in routes:
            origin = route["origin"]
            dest = route["destination"]
            route_code = route["route"]

            for h in horizons:
                horizon_label = f"T+{h}"
                dept_date = (date.today() + timedelta(days=h)).strftime("%d/%m/%Y")

                if self.platform == "cleartrip":
                    url = f"https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&class=Economy&depart_date={dept_date}&from={origin}&to={dest}&intl=n&page=loaded"
                elif self.platform == "easemytrip":
                    city1 = CITY_NAMES.get(origin, origin)
                    city2 = CITY_NAMES.get(dest, dest)
                    url = (
                        f"https://flight.easemytrip.com/FlightList/Index?"
                        f"srch={origin}-{city1}-India|{dest}-{city2}-India|{dept_date}"
                        f"&px=1-0-0&cbn=0&ar=undefined&isDM=true&IsDoubleSeat=false&C=IN"
                    )
                else:
                    raise ValueError(f"Unsupported platform: {self.platform}")

                req = Request.from_url(
                    url=url,
                    user_data={
                        "platform": self.platform,
                        "route_code": route_code,
                        "origin": origin,
                        "destination": dest,
                        "horizon_label": horizon_label,
                        "advance_days": h,
                        "dept_date": dept_date
                    }
                )
                requests.append(req)

        return requests

    async def run(
        self,
        csv_path: str,
        top_n: int = 1,
        horizons: List[int] = [1],
    ) -> str:
        """Executes Crawlee-managed flight harvest."""
        routes = load_route_basket(csv_path, top_n=top_n)
        self.run_dir = create_run_directory(f"crawlee_{self.platform}_top{top_n}")

        print("=" * 95)
        print(f"🚀 AIRGO CRAWLEE HARVESTER [{self.platform.upper()}]")
        print(f"   * Concurrency: Max {self.max_concurrency}")
        print(f"   * Routes: {len(routes)} Top DGCA Routes")
        print(f"   * Horizons: {[f'T+{h}' for h in horizons]}")
        print(f"   * Audit Dir: {self.run_dir}")
        print("=" * 95)

        requests = self.build_requests(routes, horizons)

        concurrency_settings = ConcurrencySettings(
            min_concurrency=1,
            max_concurrency=self.max_concurrency,
            desired_concurrency=self.max_concurrency
        )

        crawler = PlaywrightCrawler(
            headless=self.headless,
            use_session_pool=True,
            max_request_retries=3,
            concurrency_settings=concurrency_settings,
            browser_launch_options={
                "channel": "msedge",
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            }
        )

        @crawler.router.default_handler
        async def handle_flight_search(context: PlaywrightCrawlingContext) -> None:
            req = context.request
            user_data = req.user_data
            route_code = user_data["route_code"]
            horizon_label = user_data["horizon_label"]
            platform = user_data["platform"]

            page = context.page
            rh_dir = os.path.join(self.run_dir, route_code, horizon_label)
            os.makedirs(rh_dir, exist_ok=True)

            print(f"\n✈️  [{route_code}_{horizon_label}] Crawlee processing {platform.title()} URL...")

            try:
                if platform == "cleartrip":
                    await page.wait_for_selector("button:has-text('Book')", timeout=35000)
                    await page.wait_for_timeout(2500)
                    cards = await extract_cleartrip_cards(page)
                elif platform == "easemytrip":
                    await page.wait_for_selector("div.fltResult, .fltResult, button:has-text('BOOK NOW')", timeout=35000)
                    await page.wait_for_timeout(2500)
                    cards = await extract_easemytrip_cards(page)
                else:
                    cards = []

                if not cards:
                    print(f"  [⚠️ ] {route_code}_{horizon_label}: No live flight cards found in DOM.")
                    if context.session:
                        context.session.retire()
                    return

                # Capture ground-truth screenshot proof
                search_shot = os.path.join(rh_dir, "search_results.png")
                await safe_capture_screenshot(page, search_shot)

                print(f"  [🔍] Found {len(cards)} live flights on {platform.title()}. Filtering top {self.flights_per_route} diverse carriers...")

                # Apply carrier diversity filter
                seen_carriers = set()
                selected = []
                for c in cards:
                    carrier = c["airline"]
                    if carrier not in seen_carriers:
                        seen_carriers.add(carrier)
                        selected.append(c)
                    if len(selected) >= self.flights_per_route:
                        break

                if len(selected) < self.flights_per_route:
                    for c in cards:
                        if c not in selected:
                            selected.append(c)
                            if len(selected) >= self.flights_per_route:
                                break

                for idx, flt in enumerate(selected):
                    carrier_slug = re.sub(r'[^a-zA-Z0-9]', '', flt['airline'])
                    flight_slug = re.sub(r'[^a-zA-Z0-9]', '', flt['flightNumber'])
                    flt_dir = os.path.join(rh_dir, f"{idx+1:02d}_{carrier_slug}_{flight_slug}")
                    os.makedirs(flt_dir, exist_ok=True)

                    quote = {
                        "platform": platform.title(),
                        "audit_timestamp": datetime.utcnow().isoformat() + "Z",
                        "route": route_code,
                        "advance_horizon": horizon_label,
                        "airline": flt["airline"],
                        "flight_number": flt["flightNumber"],
                        "departure_time": flt["departureTime"],
                        "arrival_time": flt["arrivalTime"],
                        "duration": flt["duration"],
                        "total_fare_inr": flt["price"],
                        "stops": flt["stops"],
                        "screenshot": os.path.relpath(search_shot, self.run_dir)
                    }

                    self.audited_quotes.append(quote)
                    save_run_artifact(flt_dir, "quote.json", quote)
                    await context.push_data(quote)
                    print(f"    [✅] Extracted {flt['airline']:<20} ({flt['flightNumber']:<8}) | {flt['departureTime']}->{flt['arrivalTime']} | Fare: INR {flt['price']}")

            except Exception as e:
                print(f"  [❌] Error processing {route_code}_{horizon_label}: {e}")
                if context.session:
                    context.session.retire()
                raise e

        await crawler.run(requests)

        save_run_artifact(self.run_dir, "crawlee_audited_quotes.json", self.audited_quotes)
        print(f"\n🎉 Crawlee Harvest Complete! Total Quotes Saved: {len(self.audited_quotes)}")
        return self.run_dir
