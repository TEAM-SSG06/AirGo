from __future__ import annotations

import argparse
import asyncio
import csv
import json
import random
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

# Ensure project root is in sys.path so script can be run from any directory
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from .config import IxigoConfig
except ImportError:
    from airgo.scrapers.ixigo.config import IxigoConfig


@dataclass
class FareCandidate:
    carrier: str
    flight_number: str
    departure_time: str
    fare_class: str
    listing_price: float
    flight_key: str | None = None
    airline: str = ""
    arrival_time: str = ""
    duration: str = ""
    stops: int = 0


def select_least_five(candidates: Iterable[FareCandidate | dict[str, Any]]) -> list[FareCandidate]:
    """Select up to five cheapest fare options independently for each flight."""
    groups: dict[str, list[FareCandidate]] = {}
    for item in candidates:
        fare = item if isinstance(item, FareCandidate) else FareCandidate(**item)
        key = fare.flight_key or "|".join((fare.carrier, fare.flight_number, fare.departure_time))
        groups.setdefault(key, []).append(fare)
    selected: list[FareCandidate] = []
    for fares in groups.values():
        selected.extend(sorted(fares, key=lambda fare: fare.listing_price)[:5])
    return selected


def price_mismatch(listing_price: float | None, confirmed_price: float | None) -> bool | None:
    if listing_price is None or confirmed_price is None:
        return None
    return round(listing_price, 2) != round(confirmed_price, 2)


def _money(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"\d+(?:[,.]\d+)*", str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def parse_result_payload(payload: list[dict[str, Any]]) -> list[FareCandidate]:
    """Normalize flight payload without inventing fake data."""
    result: list[FareCandidate] = []
    for row in payload:
        listing_price = _money(row.get("listing_price"))
        carrier = str(row.get("carrier") or "").strip()
        flight_number = str(row.get("flight_number") or "").strip()
        departure_time = str(row.get("departure_time") or "").strip()
        if not all((carrier, flight_number, departure_time)) or listing_price is None:
            continue
        result.append(FareCandidate(
            carrier=carrier,
            flight_number=flight_number,
            departure_time=departure_time,
            fare_class=str(row.get("fare_class") or "Economy").strip(),
            listing_price=listing_price,
            flight_key=str(row.get("flight_key") or "") or None,
            airline=str(row.get("airline") or carrier).strip(),
            arrival_time=str(row.get("arrival_time") or "").strip(),
            duration=str(row.get("duration") or "").strip(),
            stops=int(row.get("stops") or 0),
        ))
    return result


async def extract_result_payload(page: Any) -> tuple[int, list[dict[str, Any]]]:
    """Extract flight candidates and total flights count from live Ixigo DOM."""
    data = await page.evaluate(
        """() => {
            let flightsFound = 0;
            const bodyText = document.body.innerText;
            const countMatch = bodyText.match(/(\\d+)\\s+Flights?\\s+Available/i);
            if (countMatch) {
                flightsFound = parseInt(countMatch[1], 10);
            }

            // Check if explicit test attributes exist
            const explicit = [...document.querySelectorAll('[data-flight-number][data-departure-time][data-listing-price]')];
            if (explicit.length > 0) {
                const items = explicit.map(node => ({
                    carrier: node.getAttribute('data-carrier') || '',
                    flight_number: node.getAttribute('data-flight-number') || '',
                    departure_time: node.getAttribute('data-departure-time') || '',
                    fare_class: node.getAttribute('data-fare-class') || 'Economy',
                    listing_price: node.getAttribute('data-listing-price') || '',
                    flight_key: node.getAttribute('data-flight-key') || ''
                }));
                return { flightsFound: flightsFound || items.length, items };
            }

            // Live Ixigo React cards
            const items = [];
            const pricingNodes = document.querySelectorAll('[data-testid="pricing"]');
            for (const el of pricingNodes) {
                let card = el.closest('div[class*="Listing_listItem"]') || el.closest('div[class*="shadow-card"]');
                if (!card) {
                    let parent = el;
                    for (let j = 0; j < 8; j++) {
                        if (parent && parent.parentElement) parent = parent.parentElement;
                    }
                    card = parent;
                }

                const logo = card ? card.querySelector('img[data-testid="airline-logo"]') : null;
                const carrierCode = logo ? (logo.getAttribute('alt') || '').trim() : '';

                const airlineEl = card ? card.querySelector('.airlineTruncate, .airlineInfo p') : null;
                const airlineName = airlineEl ? airlineEl.innerText.trim() : (carrierCode || 'Unknown');

                const text = card ? card.innerText : '';
                const flightNumMatch = text.match(/[A-Z0-9]{2}\\s*\\d{3,4}/);
                const flightNum = flightNumMatch ? flightNumMatch[0].replace(/\\s+/, '') : '';

                const timeH6s = card ? [...card.querySelectorAll('.timeTile h6, .timeTileList h6')] : [];
                const depTime = timeH6s.length > 0 ? timeH6s[0].innerText.trim() : '';
                const arrTime = timeH6s.length > 1 ? timeH6s[1].innerText.trim() : '';

                let duration = '';
                let stops = 0;
                if (card) {
                    const durationMatch = text.match(/(\\d+h\\s*\\d+m|\\d+h|\\d+m)/);
                    if (durationMatch) duration = durationMatch[0];

                    if (/non-stop/i.test(text)) {
                        stops = 0;
                    } else {
                        const stopsMatch = text.match(/(\\d+)\\s*stop/i);
                        if (stopsMatch) stops = parseInt(stopsMatch[1], 10);
                    }
                }

                const priceText = el.innerText.replace(/[^0-9]/g, '');
                const price = priceText ? parseFloat(priceText) : null;

                if (flightNum && depTime && price !== null) {
                    items.push({
                        carrier: carrierCode || flightNum.slice(0, 2),
                        airline: airlineName,
                        flight_number: flightNum,
                        departure_time: depTime,
                        arrival_time: arrTime,
                        duration: duration,
                        stops: stops,
                        fare_class: 'Economy',
                        listing_price: price,
                        flight_key: `${carrierCode || flightNum.slice(0, 2)}|${flightNum}|${depTime}`
                    });
                }
            }

            return { flightsFound: flightsFound || items.length, items };
        }"""
    )
    return int(data.get("flightsFound") or 0), data.get("items") or []


def load_top_routes(path: Path, count: int = 3) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: int(row.get("rank") or 10**9))
    routes: list[dict[str, Any]] = []
    for row in rows[:count]:
        origin, destination = (part.strip().upper() for part in row["route"].split("-", 1))
        routes.append({"origin": origin, "destination": destination, "rank": int(row["rank"]), "route": row["route"]})
    return routes


def robots_allows(url: str, config: IxigoConfig) -> bool:
    """Fetch robots.txt once per search path and refuse disallowed paths."""
    request = urllib.request.Request(config.robots_url, headers={"User-Agent": config.user_agent})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            robots = response.read().decode("utf-8", errors="replace")
        from urllib.robotparser import RobotFileParser
        parser = RobotFileParser()
        parser.parse(robots.splitlines())
        return parser.can_fetch(config.user_agent, url)
    except (OSError, urllib.error.URLError):
        return False


class IxigoScraper:
    def __init__(self, config: IxigoConfig | None = None) -> None:
        self.config = config or IxigoConfig.from_environment()
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_dir = self.config.runs_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_ixigo"
        self.quotes: list[dict[str, Any]] = []
        self.horizon_details: list[dict[str, Any]] = []

    async def _context(self, browser: Any) -> Any:
        return await browser.new_context(
            user_agent=self.config.user_agent,
            locale=self.config.locale,
            viewport=self.config.viewport,
        )

    async def _search(self, browser: Any, route: dict[str, Any], lead_time: int) -> None:
        search_date = date.today()
        travel_date = search_date + timedelta(days=lead_time)
        travel_date_str = travel_date.strftime("%d%m%Y")
        window_name = f"T+{lead_time}"
        horizon_dir = self.run_dir / route["route"] / window_name
        horizon_dir.mkdir(parents=True, exist_ok=True)

        url = self.config.search_url_template.format(
            origin=route["origin"], destination=route["destination"], travel_date=travel_date_str
        )

        if not self.config.ignore_robots and not robots_allows(url, self.config):
            self.horizon_details.append({
                "horizon": window_name,
                "travel_date": travel_date.isoformat(),
                "flights_found": 0,
                "top_5_extracted": 0,
                "min_price": None,
                "max_price": None,
                "deep_checkout_audit": {
                    "checkout_successful": False,
                    "base_fare": None,
                    "taxes": None,
                    "convenience_fee": None,
                    "total_fare": None,
                    "notes": "robots.txt disallows path or is unavailable"
                }
            })
            return

        for attempt in range(2):
            context = await self._context(browser)
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_ms)
                try:
                    await page.wait_for_selector('[data-testid="pricing"], div[class*="Listing_listItem"]', timeout=15000)
                except Exception:
                    pass
                await page.wait_for_timeout(2000)

                # Scroll down with mouse wheel to load enough flight cards from Ixigo's virtual list
                raw_items_dict: dict[str, dict[str, Any]] = {}
                flights_found = 0
                for scroll_step in range(4):
                    ff, batch = await extract_result_payload(page)
                    if ff:
                        flights_found = max(flights_found, ff)
                    for item in batch:
                        k = item.get("flight_key") or f"{item.get('carrier')}|{item.get('flight_number')}|{item.get('departure_time')}"
                        if k not in raw_items_dict:
                            raw_items_dict[k] = item
                    if len(raw_items_dict) >= 15:
                        break
                    await page.mouse.wheel(0, 1200)
                    await page.wait_for_timeout(1000)

                # Scroll back to top for screenshot and booking
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(500)

                # Capture 00_search_results.png
                try:
                    await page.screenshot(path=str(horizon_dir / "00_search_results.png"), full_page=False)
                except Exception:
                    pass

                parsed_candidates = parse_result_payload(list(raw_items_dict.values()))

                # Deduplicate by carrier + flight number + departure time and sort by price
                seen_keys: set[str] = set()
                unique_candidates: list[FareCandidate] = []
                for cand in parsed_candidates:
                    key = f"{cand.carrier}|{cand.flight_number}|{cand.departure_time}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        unique_candidates.append(cand)

                unique_candidates.sort(key=lambda c: c.listing_price)
                top_5 = unique_candidates[:5]

                # Deep Checkout Audit on rank-1 flight
                checkout_success = False
                base_fare: float | None = None
                taxes: float | None = None
                convenience_fee: float | None = None
                total_fare: float | None = None
                checkout_notes = "Checkout review step not reached"

                book_btn = page.locator('button:has-text("Book")').first
                if await book_btn.count() > 0:
                    try:
                        await book_btn.click(timeout=10000)
                        await page.wait_for_timeout(4000)
                        try:
                            await page.screenshot(path=str(horizon_dir / "01_checkout_review.png"), full_page=False)
                        except Exception:
                            pass

                        fare_summary = await page.evaluate(
                            """() => {
                                const text = document.body.innerText;
                                const baseMatch = text.match(/Base\\s*Fare[^\\d]*([\\d,]+)/i);
                                const taxesMatch = text.match(/Taxes\\s*&\\s*Fees[^\\d]*([\\d,]+)/i);
                                const totalMatch = text.match(/Total\\s*Amount[^\\d]*([\\d,]+)/i);
                                return {
                                    baseFare: baseMatch ? parseInt(baseMatch[1].replace(/,/g, ''), 10) : null,
                                    taxes: taxesMatch ? parseInt(taxesMatch[1].replace(/,/g, ''), 10) : null,
                                    total: totalMatch ? parseInt(totalMatch[1].replace(/,/g, ''), 10) : null
                                };
                            }"""
                        )
                        base_fare = fare_summary.get("baseFare")
                        taxes = fare_summary.get("taxes")
                        total_fare = fare_summary.get("total")
                        if base_fare is not None or total_fare is not None:
                            checkout_success = True
                            checkout_notes = "Verified at review step; stopped before payment"
                    except Exception as e:
                        checkout_notes = f"Checkout traversal error: {type(e).__name__}"

                # Format quotes for quotes.json
                evidence_rel = f"{route['route']}/{window_name}/00_search_results.png"
                for rank, fare in enumerate(top_5, start=1):
                    price_val = int(fare.listing_price) if fare.listing_price.is_integer() else fare.listing_price
                    quote_obj = {
                        "rank": rank,
                        "platform": "Ixigo",
                        "platform_type": "ota",
                        "route": route["route"],
                        "origin": route["origin"],
                        "destination": route["destination"],
                        "travel_date": travel_date.isoformat(),
                        "advance_purchase_days": lead_time,
                        "window": window_name,
                        "airline": fare.airline or fare.carrier,
                        "flight_number": fare.flight_number,
                        "departure_time": fare.departure_time,
                        "arrival_time": fare.arrival_time,
                        "duration": fare.duration,
                        "stops": fare.stops,
                        "search_price": price_val,
                        "deep_checkout_base_fare": base_fare if rank == 1 else None,
                        "deep_checkout_taxes": taxes if rank == 1 else None,
                        "final_price": price_val,
                        "currency": "INR",
                        "fare_class": fare.fare_class or "Economy",
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                        "screenshot_evidence": evidence_rel,
                    }
                    self.quotes.append(quote_obj)

                min_price = int(top_5[0].listing_price) if top_5 else None
                max_price = int(top_5[-1].listing_price) if top_5 else None

                self.horizon_details.append({
                    "horizon": window_name,
                    "travel_date": travel_date.isoformat(),
                    "flights_found": flights_found or len(raw_items_dict),
                    "top_5_extracted": len(top_5),
                    "min_price": min_price,
                    "max_price": max_price,
                    "deep_checkout_audit": {
                        "checkout_successful": checkout_success,
                        "base_fare": base_fare,
                        "taxes": taxes,
                        "convenience_fee": convenience_fee,
                        "total_fare": total_fare or min_price,
                        "notes": checkout_notes,
                    }
                })
                break
            except Exception as exc:
                if attempt == 0:
                    await asyncio.sleep(self.config.retry_backoff_seconds)
                    continue
                self.horizon_details.append({
                    "horizon": window_name,
                    "travel_date": travel_date.isoformat(),
                    "flights_found": 0,
                    "top_5_extracted": 0,
                    "min_price": None,
                    "max_price": None,
                    "deep_checkout_audit": {
                        "checkout_successful": False,
                        "base_fare": None,
                        "taxes": None,
                        "convenience_fee": None,
                        "total_fare": None,
                        "notes": f"Search error: {type(exc).__name__}: {exc}"
                    }
                })
            finally:
                await context.close()

        await asyncio.sleep(self.config.min_delay_seconds + random.uniform(0, self.config.max_jitter_seconds))

    async def run(self) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=False)
        routes = load_top_routes(self.config.routes_file, self.config.top_routes)
        from playwright.async_api import async_playwright
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.config.headless)
            try:
                for route in routes:
                    for lead_time in self.config.lead_times:
                        await self._search(browser, route, lead_time)
            finally:
                await browser.close()

        # Write quotes.json at root of run folder
        quotes_path = self.run_dir / "quotes.json"
        quotes_path.write_text(json.dumps(self.quotes, indent=2), encoding="utf-8")

        # Write run_summary.json at root of run folder
        routes_label = ", ".join(r["route"] for r in routes) if len(routes) > 1 else routes[0]["route"]
        summary = {
            "scraper": "Ixigo",
            "channel": "chrome",
            "route": routes_label,
            "horizons": [f"T+{lt}" for lt in self.config.lead_times],
            "total_quotes_captured": len(self.quotes),
            "run_completed_at": datetime.now(timezone.utc).isoformat(),
            "horizon_details": self.horizon_details,
            "run_folder": str(self.run_dir),
        }
        summary_path = self.run_dir / "run_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        return self.run_dir


async def _main_async(args: argparse.Namespace) -> None:
    lead_times = tuple(int(x.strip()) for x in args.lead_times.split(",")) if args.lead_times else None
    config = IxigoConfig.from_environment(
        headed=args.headed,
        ignore_robots=args.ignore_robots,
        top_routes=args.top_n,
        lead_times=lead_times,
    )
    scraper = IxigoScraper(config)
    print(f"Ixigo run artifacts: {await scraper.run()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ixigo airfare scraper with structured JSON output and screenshot evidence")
    parser.add_argument("--headed", action="store_true", help="Show Chromium for local debugging")
    parser.add_argument("--ignore-robots", action="store_true", help="Bypass robots.txt check for headed debugging / inspection")
    parser.add_argument("--top-n", type=int, default=None, help="Number of top DGCA routes to audit (default: 3)")
    parser.add_argument("--lead-times", type=str, default=None, help="Comma-separated lead times in days, e.g. 7 or 1,7,15")
    asyncio.run(_main_async(parser.parse_args()))


if __name__ == "__main__":
    main()
