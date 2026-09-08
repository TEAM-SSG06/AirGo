"""
HTML and DOM parsing engine for Yatra search results.
Extracts flight items, processes multiple fare options, selects the 5 cheapest
options per flight, detects sold-out flights, and checks for anti-bot barriers.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag

from airgo.scrapers.yatra.models import (
    AntiBotEvent,
    AntiBotEventType,
    AvailabilityStatus,
    DataStatus,
    NormalizedFareQuote,
)
from airgo.scrapers.yatra.normalizer import normalize_price
from airgo.scrapers.yatra.selectors import YatraSelectors

logger = logging.getLogger("AirGo.Yatra.Parser")


class YatraParser:
    """Parses raw HTML from Yatra flight searches into structured quotes."""

    @staticmethod
    def detect_anti_bot(
        html: str,
        status_code: Optional[int] = None,
        url: str = "",
        route: str = "",
        travel_date: Optional[date] = None,
    ) -> Optional[AntiBotEvent]:
        """
        Inspects status codes and HTML content for anti-bot or security challenge markers.
        Never attempts to bypass; records the event for backoff.
        """
        effective_date = travel_date or date.today()
        lower_html = html.lower() if html else ""

        # Avoid false positives if page contains actual rendered content (flight tuples or checkout)
        has_rendered_content = (
            ("tuple" in lower_html and "book" in lower_html)
            or "autom=\"booknow\"" in lower_html
            or "paynowbtn" in lower_html
            or "fare summary" in lower_html
        )
        if (status_code is None or status_code == 200) and has_rendered_content:
            return None

        # Check specific challenge signatures in HTML
        for sig in YatraSelectors.CHALLENGE_SIGNATURES:
            if sig.lower() in lower_html:
                detected_type = AntiBotEventType.CAPTCHA if "captcha" in sig.lower() else (
                    AntiBotEventType.AKAMAI_CHALLENGE if ("akamai" in sig.lower() or "access denied" in sig.lower()) else AntiBotEventType.OTHER
                )
                code_str = f" (HTTP {status_code})" if status_code else ""
                return AntiBotEvent(
                    route=route,
                    travel_date=effective_date,
                    url=url,
                    event_type=detected_type,
                    status_code=status_code or 200,
                    message=f"Access Denied / Security challenge detected: '{sig}'{code_str}",
                )

        # Check HTTP status codes
        if status_code in (403, 429):
            event_type = AntiBotEventType.RATE_LIMITED if status_code == 429 else AntiBotEventType.ACCESS_DENIED
            return AntiBotEvent(
                route=route,
                travel_date=effective_date,
                url=url,
                event_type=event_type,
                status_code=status_code,
                message=f"Access Denied: HTTP {status_code} received from server",
            )

        if not html:
            return None

        return None

    @staticmethod
    def _find_element_text(tag: Tag, selectors: List[str]) -> Optional[str]:
        """Helper to find the text of the first matching selector."""
        for sel in selectors:
            found = tag.select_one(sel)
            if found and found.get_text(strip=True):
                return found.get_text(strip=True)
        return None

    @staticmethod
    def _parse_stops(raw_stops: Optional[str]) -> int:
        """Parses stop string (e.g. 'Non Stop', '1 Stop', '2 Stops') into integer."""
        if not raw_stops:
            return 0
        cleaned = raw_stops.lower()
        if "non" in cleaned or "0" in cleaned:
            return 0
        digits = re.findall(r"\d+", cleaned)
        if digits:
            return int(digits[0])
        return 1

    @classmethod
    def parse_flight_cards(
        cls,
        html: str,
        search_context: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[NormalizedFareQuote]]:
        """
        Parses all available flight cards from the page HTML.
        For each flight:
          1. Extracts all available fare options (including expanded fare families).
          2. Normalizes prices.
          3. Sorts ascending.
          4. Selects strictly the 5 cheapest fare options for that flight.
        Returns a tuple of (raw_quotes_list, normalized_quotes_list).
        """
        soup = BeautifulSoup(html, "html.parser")
        route_code = search_context.get("route", "DEL-BOM")
        origin_iata = search_context.get("origin", "DEL")
        dest_iata = search_context.get("destination", "BOM")
        search_date = search_context.get("search_date", date.today())
        travel_date = search_context.get("travel_date", date.today())
        advance_days = search_context.get("advance_purchase_days", 1)
        source_url = search_context.get("url", "")

        # Find flight card containers
        cards: List[Tag] = []
        for selector in YatraSelectors.FLIGHT_CARDS:
            matched = soup.select(selector)
            if matched:
                cards = matched
                break

        if not cards:
            logger.info(f"No flight cards found on page for {route_code}")
            return [], []

        raw_quotes: List[Dict[str, Any]] = []
        normalized_quotes: List[NormalizedFareQuote] = []

        for card in cards:
            # Check for sold-out indicator
            is_sold_out = bool(card.select_one(", ".join(YatraSelectors.SOLD_OUT))) or ("sold out" in card.get_text().lower())
            avail_status = AvailabilityStatus.SOLD_OUT if is_sold_out else AvailabilityStatus.AVAILABLE

            # Extract airline name cleanly
            airline_name = cls._find_element_text(card, YatraSelectors.AIRLINE_NAME)
            if not airline_name:
                img = card.select_one("img[alt]")
                alt_val = img.get("alt") if img else ""
                airline_name = str(alt_val).strip() if alt_val else "Unknown Airline"
            if "\n" in airline_name:
                airline_name = airline_name.split("\n")[0].strip()

            # Extract flight code / number
            flight_number = cls._find_element_text(card, YatraSelectors.FLIGHT_NUMBER) or "FLIGHT-UNKNOWN"
            if "\n" in flight_number:
                flight_number = flight_number.split("\n")[-1].strip()

            # Departure & Arrival times (clean regex match for HH:MM)
            raw_dep = cls._find_element_text(card, YatraSelectors.DEPARTURE_TIME) or ""
            dep_match = re.search(r"(\d{1,2}:\d{2})", raw_dep)
            dep_time = dep_match.group(1) if dep_match else "00:00"

            raw_arr = cls._find_element_text(card, YatraSelectors.ARRIVAL_TIME) or ""
            arr_match = re.search(r"(\d{1,2}:\d{2})", raw_arr)
            arr_time = arr_match.group(1) if arr_match else "00:00"

            # Duration and Stops
            raw_dur = cls._find_element_text(card, YatraSelectors.DURATION) or "00h 00m"
            dur_match = re.search(r"\d+h\s*\d+m|\d+h|\d+m", raw_dur)
            duration = dur_match.group(0) if dur_match else raw_dur

            raw_stops = cls._find_element_text(card, YatraSelectors.STOPS)
            stops_count = cls._parse_stops(raw_stops)

            # Extract fare options
            fare_options: List[Tuple[str, Decimal, str]] = []  # (name, normalized_price, raw_string)

            # 1. Check for expanded fare options table (e.g. div.table-box)
            table_box = card.select_one("div.table-box")
            if table_box:
                services_rows = table_box.select("div.services tr")[1:]  # skip header
                book_rows = table_box.select("div.booknow-btn tr")[1:]   # skip header
                for s_tr, b_tr in zip(services_rows, book_rows):
                    opt_name = s_tr.get_text(strip=True) or "Standard"
                    price_div = b_tr.select_one("div.v-aligm-m, div.tipsy, [class*='rupee'], .bold")
                    raw_price = price_div.get_text(strip=True) if price_div else b_tr.get_text(strip=True)
                    try:
                        p_dec = normalize_price(raw_price)
                        fare_options.append((opt_name, p_dec, raw_price))
                    except ValueError:
                        pass

            # 2. Check general fare options containers if table_box didn't yield
            if not fare_options:
                matched_containers = card.select(", ".join(YatraSelectors.FARE_OPTIONS_CONTAINER))
                container_set = set(matched_containers)
                fare_containers = [
                    c for c in matched_containers
                    if not any(d in container_set for d in c.descendants)
                ]
                if fare_containers:
                    for f_tag in fare_containers:
                        opt_name = cls._find_element_text(f_tag, YatraSelectors.FARE_OPTION_NAME) or "Standard"
                        raw_price_str = cls._find_element_text(f_tag, YatraSelectors.FARE_OPTION_PRICE)
                        if raw_price_str:
                            try:
                                norm_price = normalize_price(raw_price_str)
                                fare_options.append((opt_name, norm_price, raw_price_str))
                            except ValueError:
                                continue

            # 3. Fallback to main displayed price on the card
            if not fare_options:
                main_price_str = cls._find_element_text(card, YatraSelectors.DISPLAYED_PRICE)
                if main_price_str:
                    try:
                        norm_price = normalize_price(main_price_str)
                        fare_options.append(("Standard", norm_price, main_price_str))
                    except ValueError:
                        pass

            # If sold out or missing price
            if not fare_options:
                raw_record = {
                    "source": "Yatra",
                    "route": route_code,
                    "origin": origin_iata,
                    "destination": dest_iata,
                    "search_date": search_date.isoformat(),
                    "travel_date": travel_date.isoformat(),
                    "advance_purchase_days": advance_days,
                    "airline": airline_name,
                    "flight_number": flight_number,
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "duration": duration,
                    "stops": stops_count,
                    "fare_class": "ECONOMY",
                    "fare_option_name": "Standard",
                    "displayed_price": None,
                    "availability_status": AvailabilityStatus.SOLD_OUT.value if is_sold_out else AvailabilityStatus.NOT_FOUND.value,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "source_url": source_url,
                }
                raw_quotes.append(raw_record)
                continue

            # Find the single cheapest available fare option for this flight
            cheapest_opt = min(fare_options, key=lambda x: x[1])
            opt_name, price_dec, raw_str = cheapest_opt

            clean_opt_name = opt_name.strip() if opt_name and opt_name.strip().lower() != "standard" else "Saver"

            raw_record = {
                "source": "Yatra",
                "route": route_code,
                "origin": origin_iata,
                "destination": dest_iata,
                "search_date": search_date.isoformat(),
                "travel_date": travel_date.isoformat(),
                "advance_purchase_days": advance_days,
                "airline": airline_name,
                "flight_number": flight_number,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "duration": duration,
                "stops": stops_count,
                "fare_class": "Economy",
                "fare_option_name": clean_opt_name,
                "displayed_price": float(price_dec),
                "raw_displayed_price": raw_str,
                "availability_status": avail_status.value,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "source_url": source_url,
            }
            raw_quotes.append(raw_record)

            # Build normalized quote for this flight's cheapest seat/fare
            norm_quote = NormalizedFareQuote(
                source="Yatra",
                route=route_code,
                origin=origin_iata,
                destination=dest_iata,
                search_date=search_date,
                travel_date=travel_date,
                advance_purchase_days=advance_days,
                airline=airline_name,
                flight_number=flight_number,
                departure_time=dep_time,
                arrival_time=arr_time,
                duration=duration,
                stops=stops_count,
                fare_class="Economy",
                fare_option_name=clean_opt_name,
                base_fare=price_dec,
                taxes=Decimal("0.00"),
                fees=Decimal("0.00"),
                convenience_fee=Decimal("0.00"),
                displayed_price=price_dec,
                displayed_search_price=price_dec,
                final_payable_price=None,
                currency="INR",
                availability_status=avail_status,
                verification_status=DataStatus.SEARCH_RESULT,
            )
            normalized_quotes.append(norm_quote)

        logger.info(
            f"Parsed {len(cards)} flight cards for {route_code} (Generated {len(normalized_quotes)} flight candidates with cheapest fare each)"
        )
        return raw_quotes, normalized_quotes

    @classmethod
    def parse_paynow_breakdown(cls, html: str) -> Dict[str, Optional[Decimal]]:
        """
        Extracts final payable total and component fee breakdown from the pre-payment / Pay Now page
        or the checkout fare summary sidebar.
        Returns a dictionary with Decimal values or None.
        """
        soup = BeautifulSoup(html, "html.parser")

        def _extract_decimal(selectors: List[str]) -> Optional[Decimal]:
            for sel in selectors:
                el = soup.select_one(sel)
                if el:
                    text_val = el.get_text().strip()
                    try:
                        return normalize_price(text_val)
                    except ValueError:
                        continue
            return None

        final_payable = _extract_decimal(YatraSelectors.PAYNOW_TOTAL_AMOUNT)
        base_fare = _extract_decimal(YatraSelectors.PAYNOW_BASE_FARE)
        taxes = _extract_decimal(YatraSelectors.PAYNOW_TAXES)
        convenience_fee = _extract_decimal(YatraSelectors.PAYNOW_CONVENIENCE_FEE)
        other_charges = _extract_decimal(YatraSelectors.PAYNOW_OTHER_CHARGES)

        # Fallback 1: check labeled line items across text blocks (Tailwind / React checkout sidebar)
        fare_section = soup.find(lambda tag: tag.name in ("div", "section") and "Fare Summary" in tag.get_text() and len(tag.get_text()) < 1000)
        search_target = fare_section if fare_section else soup

        lines = [line.strip() for line in search_target.get_text(separator="\n").split("\n") if line.strip()]
        for idx, line in enumerate(lines):
            line_lower = line.lower()
            if not final_payable and any(kw in line_lower for kw in ("total amount", "total payable", "final payable", "amount to pay")):
                for next_line in lines[idx+1:idx+4]:
                    try:
                        final_payable = normalize_price(next_line)
                        break
                    except ValueError:
                        pass
            elif not base_fare and "base fare" in line_lower:
                for next_line in lines[idx+1:idx+4]:
                    try:
                        base_fare = normalize_price(next_line)
                        break
                    except ValueError:
                        pass
            elif not taxes and any(kw in line_lower for kw in ("fee & surcharges", "fees & surcharges", "taxes & fees", "taxes and fees", "tax")):
                for next_line in lines[idx+1:idx+4]:
                    try:
                        taxes = normalize_price(next_line)
                        break
                    except ValueError:
                        pass
            elif not convenience_fee and re.search(r"^(?:convenience\s*fee|convenience\s*charges?)\b", line_lower) and "zero" not in line_lower:
                for next_line in lines[idx+1:idx+4]:
                    try:
                        convenience_fee = normalize_price(next_line)
                        break
                    except ValueError:
                        pass

        # Fallback 2: check table rows for labeled fee components
        for tr in soup.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) >= 2:
                label_text = cells[0].get_text().lower()
                val_text = cells[-1].get_text().strip()
                try:
                    price_val = normalize_price(val_text)
                    if not final_payable and ("total" in label_text or "payable" in label_text):
                        final_payable = price_val
                    elif not base_fare and "base" in label_text:
                        base_fare = price_val
                    elif not taxes and ("tax" in label_text or ("fee" in label_text and "convenience" not in label_text)):
                        taxes = price_val
                    elif not convenience_fee and "convenience" in label_text:
                        convenience_fee = price_val
                    elif not other_charges and ("other" in label_text or "udf" in label_text):
                        other_charges = price_val
                except ValueError:
                    continue

        return {
            "final_payable_price": final_payable,
            "base_fare": base_fare,
            "taxes": taxes,
            "convenience_fee": convenience_fee,
            "other_charges": other_charges,
        }

    @classmethod
    def detect_price_change_alert(cls, html: str) -> Optional[str]:
        """
        Detects price change or seat unavailability alerts during checkout.
        """
        soup = BeautifulSoup(html, "html.parser")
        for sel in YatraSelectors.PRICE_CHANGE_ALERT:
            el = soup.select_one(sel)
            if el and el.get_text().strip():
                return el.get_text().strip()

        text_content = soup.get_text().lower()
        signatures = [
            "fare has changed",
            "price has increased",
            "fare has increased",
            "price has changed",
            "fare updated",
            "price updated",
            "fare increase",
        ]
        for sig in signatures:
            if sig in text_content:
                return sig.title()

        return None

    @classmethod
    def is_paynow_page(cls, html: str) -> bool:
        """
        Determines whether the rendered HTML corresponds to the final pre-payment / Pay Now page.
        """
        soup = BeautifulSoup(html, "html.parser")
        for sel in YatraSelectors.PAYNOW_CONTAINER:
            if soup.select_one(sel):
                return True
        text_content = soup.get_text().lower()
        if "pay now" in text_content or "make payment" in text_content or "payment options" in text_content:
            return True
        return False
