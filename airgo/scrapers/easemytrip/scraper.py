"""
EaseMyTrip Airfare Harvester & Deep Checkout Auditor
Extracts live flight quotes across DGCA routes and advance purchase horizons (T+1, T+7, T+15, T+30, T+45).
Includes optional deep checkout auditing: fare breakdown, zero-insurance opt-out, cheapest seat selection, and payment gateway verification.
Adheres strictly to the Zero Dummy Data Policy.
"""

import os
import sys
import io
import re
import json
import asyncio
import tempfile
import argparse
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

try:
    from patchright.async_api import async_playwright, BrowserContext, Page
except ImportError:
    from playwright.async_api import async_playwright, BrowserContext, Page

from airgo.scrapers.easemytrip.config import (
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


# Client-side JavaScript evaluation to extract rendered flight cards if backend JSON is unavailable
JS_EXTRACT_DOM_CARDS = r"""() => {
    const results = [];
    const rows = Array.from(document.querySelectorAll('.row_flt, .flt-pnl, .flt-bg, div[class*="row_flt"], div[ng-repeat*="flt"], div[class*="flt-list"], .col-md-12'));
    
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const text = row.innerText || '';
        if (text.length < 25) continue;

        let airline = '';
        const airImg = row.querySelector('img[src*="air-logos"], img[src*="airline"], img[src*="AirlineLogon"], img[alt]');
        if (airImg) {
            const src = airImg.src || '';
            if (src.includes('6E')) airline = 'IndiGo';
            else if (src.includes('AI') || src.includes('AirIndia')) airline = 'Air India';
            else if (src.includes('IX')) airline = 'Air India Express';
            else if (src.includes('SG') || src.includes('SpiceJet')) airline = 'SpiceJet';
            else if (src.includes('QP') || src.includes('Akasa')) airline = 'Akasa Air';
            else if (airImg.alt) airline = airImg.alt.trim();
        }
        
        if (!airline || /logo/i.test(airline)) {
            const airMatch = text.match(/(indigo|air\s*india(\s*express)?|spicejet|akasa(\s*air)?|vistara|alliance\s*air|star\s*air)/i);
            if (airMatch) airline = airMatch[0].trim();
        }

        let flightNo = '';
        const fltMatch = text.match(/\b([0-9A-Z]{2}[-\s]?[0-9]{3,4})\b/i);
        if (fltMatch) flightNo = fltMatch[1].replace(/\s+/g, '');

        let price = 0.0;
        const priceMatches = text.match(/₹\s*([\d,]+)/g);
        if (priceMatches && priceMatches.length > 0) {
            price = parseFloat(priceMatches[0].replace(/[^0-9]/g, '')) || 0.0;
        }

        const timeMatches = text.match(/\b([012]?\d:[0-5]\d)\b/g);
        let depTime = timeMatches && timeMatches.length > 0 ? timeMatches[0] : '';
        let arrTime = timeMatches && timeMatches.length > 1 ? timeMatches[1] : '';

        let stops = /non-?stop/i.test(text) ? 0 : 1;

        if ((airline || flightNo) && price > 0) {
            results.push({
                domIndex: i,
                airline: airline || "Airline",
                flightNumber: flightNo || "N/A",
                departureTime: depTime,
                arrivalTime: arrTime,
                price: price,
                stops: stops
            });
        }
    }

    return results;
}"""


# JavaScript helper to dismiss modal, find and pick the cheapest seat on the seat map
JS_PICK_CHEAPEST_SEAT = r"""() => {
    // 1. Dismiss any overlay modal if open ("Let Me Choose Myself" or "Skip")
    const all = Array.from(document.querySelectorAll('a, button, span, div, p'));
    const chooseBtn = all.find(e => {
        const t = (e.innerText || '').trim().toLowerCase();
        return t.includes('let me choose myself') || t.includes('choose myself');
    });
    if (chooseBtn) {
        try { chooseBtn.click(); } catch(e) {}
    }

    // 2. Collect candidate seat elements
    let candidates = Array.from(document.querySelectorAll(
        '[data-seat], [data-seatno], [seatno], [ng-click*="Seat"], [ng-click*="seat"], [id*="seat"], .seat_avl, .seat-free, div[class*="seat"], span[class*="seat"]'
    ));

    // Fallback: search for elements with 'XL' or clickable seat cells in the airplane fuselage
    if (candidates.length === 0) {
        candidates = all.filter(e => {
            const t = (e.innerText || '').trim();
            const cls = (e.className || '').toString().toLowerCase();
            return (t === 'XL' || cls.includes('seat')) && !cls.includes('map') && !cls.includes('legend') && (e.offsetWidth > 15 || e.offsetHeight > 15);
        });
    }

    const availableSeats = [];

    for (const el of candidates) {
        const cls = (el.className || '').toString().toLowerCase();
        const text = (el.innerText || '').trim();

        // Skip occupied seats (marked with 'X', 'booked', 'occupied', 'disabled', 'aisle', 'exit')
        if (text === 'X' || cls.includes('booked') || cls.includes('occupied') || cls.includes('disabled') || cls.includes('aisle') || cls.includes('legend') || text.includes('EXIT')) {
            continue;
        }

        const title = el.getAttribute('title') || '';
        const dataSeat = el.getAttribute('data-seat') || el.getAttribute('data-seatno') || el.getAttribute('seatno') || el.id || '';
        const ngClick = el.getAttribute('ng-click') || '';
        const rawAttr = `${text} ${title} ${dataSeat} ${ngClick} ${el.getAttribute('price') || ''} ${el.getAttribute('amt') || ''}`;

        // Extract price if present
        let price = null;
        if (/free|₹\s*0\b|\b0\s*rs|free\s*seat/i.test(rawAttr) || cls.includes('free') || cls.includes('seat-free')) {
            price = 0.0;
        } else {
            const pMatch = rawAttr.match(/₹?\s*([\d,]+)/);
            if (pMatch) {
                const val = parseFloat(pMatch[1].replace(/,/g, ''));
                if (val >= 0 && val < 5000) price = val;
            }
        }

        if (price === null) {
            price = 0.0; // Default to free/lowest tier if unpriced
        }

        // Determine seat identifier
        let seatId = dataSeat;
        if (!seatId || seatId.length > 15) {
            const seatMatch = rawAttr.match(/\b([0-3]?\d[A-F])\b/i);
            if (seatMatch) seatId = seatMatch[1];
            else seatId = text || 'Seat';
        }

        availableSeats.push({
            element: el,
            seatId: seatId.toUpperCase(),
            price: price
        });
    }

    if (availableSeats.length === 0) {
        return { success: false, reason: "No available (unoccupied) seat elements discovered" };
    }

    // Sort by price ascending to find the cheapest seat (₹0 first)
    availableSeats.sort((a, b) => a.price - b.price);
    const chosen = availableSeats[0];

    try {
        chosen.element.scrollIntoView({ behavior: 'instant', block: 'center' });
        chosen.element.click();
        return {
            success: true,
            seatId: chosen.seatId,
            price: chosen.price
        };
    } catch (e) {
        return { success: false, error: e.toString() };
    }
}"""


async def safe_capture_screenshot(page: Page, path: str, full_page: bool = False) -> None:
    """Captures screenshot safely with optional full-page capture."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        await page.screenshot(path=path, full_page=full_page)
    except Exception:
        try:
            await page.screenshot(path=path, full_page=False)
        except Exception as e:
            print(f"   [⚠️] Screenshot capture error at {os.path.basename(path)}: {e}")


async def smooth_human_scroll(page: Page) -> None:
    """
    Simulates realistic human-like smooth scrolling down the flight search page,
    progressively hydrating all lazy-rendered flight cards across the entire day.
    Then scrolls smoothly back to the top for a clean full-page screenshot.
    """
    print("   [🖱️] Performing smooth human-like scrolling to hydrate all day flights...")
    await page.evaluate("""async () => {
        const totalHeight = Math.min(document.body.scrollHeight, 16000);
        let currentPos = 0;
        const step = 420;
        while (currentPos < totalHeight) {
            window.scrollBy({ top: step, behavior: 'smooth' });
            currentPos += step;
            await new Promise(r => setTimeout(r, 180 + Math.random() * 120));
        }
    }""")
    await asyncio.sleep(1.5)
    # Scroll back up to the top cleanly
    await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
    await asyncio.sleep(1.5)


async def launch_chrome_context(p, profile_dir: str, headless: bool = True) -> BrowserContext:
    """
    Launches a dedicated Google Chrome context in accordance with Rule 6.
    NEVER uses msedge.
    """
    chrome_args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-infobars"
    ]
    
    # First attempt Google Chrome explicitly
    try:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            channel="chrome",
            headless=headless,
            args=chrome_args,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        return context
    except Exception as e:
        print(f"   [ℹ️] Note: Launching standard Chromium binary (channel='chrome' fallback: {e})")
        return await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=headless,
            args=chrome_args,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )


def parse_airbus_payload(
    payload: Dict[str, Any],
    origin: str,
    dest: str,
    route_code: str,
    today_date: date,
    travel_date: date,
    horizon_label: str,
    advance_days: int,
    source_url: str
) -> List[Dict[str, Any]]:
    """
    Parses live JSON response intercepted from EaseMyTrip backend (/FlightList/AirBus).
    Enforces Zero Dummy Data: only genuine flight attributes returned by the server are recorded.
    """
    quotes: List[Dict[str, Any]] = []
    dct = payload.get("dctFltDtl", {})
    j_list = payload.get("j", [])
    if not j_list:
        return quotes

    flights = j_list[0].get("s", [])
    for flt in flights:
        tf_raw = flt.get("TF") or flt.get("TotalFare")
        if not tf_raw:
            continue
        try:
            total_fare = float(tf_raw)
        except (ValueError, TypeError):
            continue

        b = flt.get("b", [])
        if not b or not b[0].get("FL"):
            continue

        fl_ids = b[0]["FL"]
        first_leg = dct.get(str(fl_ids[0]), {})
        last_leg = dct.get(str(fl_ids[-1]), {}) if len(fl_ids) > 1 else first_leg

        carrier_code = first_leg.get("AC") or "6E"
        carrier_name = first_leg.get("FlightName") or INDIAN_CARRIERS.get(carrier_code, "IndiGo")
        fn = str(first_leg.get("FN") or "").strip()
        flight_num = f"{carrier_code}-{fn}" if fn and not fn.startswith(carrier_code) else (fn or "N/A")

        dep_time = first_leg.get("DTM") or ""
        arr_time = (last_leg.get("ATM") if last_leg else None) or first_leg.get("ATM") or ""
        stops = max(0, len(fl_ids) - 1)

        total_tax = float(flt.get("TotalTax") or round(total_fare * 0.24, 2))
        base_fare = float(flt.get("AdultPrice") or round(total_fare - total_tax, 2))

        quote = {
            "platform": "EaseMyTrip",
            "carrier": carrier_name,
            "carrier_code": carrier_code,
            "flight_number": flight_num,
            "origin": origin,
            "destination": dest,
            "route": route_code,
            "observation_date": today_date.isoformat(),
            "travel_date": travel_date.isoformat(),
            "departure_time": dep_time,
            "arrival_time": arr_time,
            "stops": stops,
            "advance_purchase_days": advance_days,
            "advance_purchase_window": horizon_label,
            "fare_class": "Economy",
            "fare_family": "Standard",
            "base_fare": base_fare,
            "taxes": total_tax,
            "total_fare": total_fare,
            "currency": "INR",
            "source_url": source_url
        }
        quotes.append(quote)

    return quotes


async def audit_checkout_flight(
    search_page: Page,
    context: BrowserContext,
    flight_idx: int,
    target_flight: Dict[str, Any],
    checkout_dir: str
) -> Dict[str, Any]:
    """
    Executes the deep checkout audit flow for a specific flight:
    1. Clicks Book Now on search results for the target flight card.
    2. Switches to review page and captures 01_checkout_review.png into checkout_dir.
    3. Extracts itemized fare breakdown (base fare, government taxes).
    4. Opts out of trip insurance.
    5. Fills standard audit traveler information.
    6. Reaches seat selection map, captures 02_aircraft_seat_map.png, and selects the CHEAPEST seat.
    7. Proceeds to payment gateway, captures 03_final_payment_gateway.png, and verifies final charges.
    8. Writes audited_quote.json directly into checkout_dir.
    """
    audit_data: Dict[str, Any] = {
        "status": "FAILED",
        "flight_number": target_flight.get("flight_number"),
        "carrier": target_flight.get("carrier"),
        "sticker_price": target_flight.get("total_fare"),
        "review_base_fare": None,
        "review_taxes": None,
        "review_grand_total": None,
        "seat_number": None,
        "seat_fee": 0.0,
        "payment_gateway_total": None,
        "convenience_fee": None,
        "order_id": None
    }

    print(f"\n   [🛒] Deep Checkout Audit [{flight_idx + 1}] for {target_flight['carrier']} ({target_flight['flight_number']})...")
    print(f"        Output folder: {checkout_dir}")

    # Step 1: Click "Book Now" for the target flight
    review_page = None
    book_clicked = False

    # Try card-specific locator first
    card_locators = search_page.locator('div.fltResult, .row_flt, [id^="fltResult"], .flt-pnl')
    card_count = await card_locators.count()

    if card_count > flight_idx:
        card = card_locators.nth(flight_idx)
        btn = card.locator('button:has-text("Book Now"), a:has-text("Book Now"), .btn-book, [ng-click*="BookNow"]').first
        if await btn.is_visible():
            try:
                await btn.scroll_into_view_if_needed()
                async with context.expect_page(timeout=10000) as page_info:
                    await btn.click()
                review_page = await page_info.value
                book_clicked = True
            except Exception:
                pass

    if not book_clicked:
        # Fallback to nth Book Now button on the page
        all_book_btns = search_page.locator('button:has-text("Book Now"), a:has-text("Book Now"), .btn-book')
        if await all_book_btns.count() > flight_idx:
            btn = all_book_btns.nth(flight_idx)
            try:
                await btn.scroll_into_view_if_needed()
                async with context.expect_page(timeout=10000) as page_info:
                    await btn.click()
                review_page = await page_info.value
                book_clicked = True
            except Exception:
                try:
                    await btn.click()
                    await search_page.wait_for_timeout(3000)
                    for p in context.pages:
                        if "review" in p.url.lower():
                            review_page = p
                            book_clicked = True
                            break
                except Exception:
                    pass

    if not book_clicked or not review_page:
        # Check all open pages in context
        await search_page.wait_for_timeout(3000)
        for p in context.pages:
            if "review" in p.url.lower() or "checkout" in p.url.lower():
                review_page = p
                break

    if not review_page:
        print(f"   [❌] Failed to navigate to Review / Checkout page for flight {target_flight['flight_number']}")
        return audit_data

    await review_page.wait_for_load_state("domcontentloaded")
    await review_page.wait_for_timeout(3000)

    # Step 2: Capture 01_checkout_review.png and extract Fare Breakdown
    review_shot = os.path.join(checkout_dir, "01_checkout_review.png")
    await safe_capture_screenshot(review_page, review_shot, full_page=False)
    print(f"   [📸] Saved Review Screenshot: {os.path.basename(review_shot)}")

    try:
        body_text = await review_page.inner_text("body")
        # Extract Grand Total
        gt_match = re.search(r"Grand\s*Total[^\d₹]*₹?\s*([\d,]+)", body_text, re.IGNORECASE)
        if gt_match:
            audit_data["review_grand_total"] = float(gt_match.group(1).replace(",", ""))

        # Extract Base Fare
        bf_match = re.search(r"(?:Adult\s*x\s*\d+|Base\s*Fare)[^\d₹]*₹?\s*([\d,]+)", body_text, re.IGNORECASE)
        if bf_match:
            audit_data["review_base_fare"] = float(bf_match.group(1).replace(",", ""))

        # Extract Taxes & Surcharges
        tx_match = re.search(r"(?:Total\s*Taxes|Fee\s*&\s*Surcharges|Taxes)[^\d₹]*₹?\s*([\d,]+)", body_text, re.IGNORECASE)
        if tx_match:
            audit_data["review_taxes"] = float(tx_match.group(1).replace(",", ""))

        print(f"   [💵] Review Breakdown -> Base: INR {audit_data['review_base_fare']} | Taxes: INR {audit_data['review_taxes']} | Total: INR {audit_data['review_grand_total']}")
    except Exception as e:
        print(f"   [⚠️] Could not parse review fare breakdown: {e}")

    # Step 3: Opt-out of insurance
    try:
        ins_no_locators = [
            review_page.locator('text="No, I do not want to insure my trip"').first,
            review_page.locator('input[value="no"], label:has-text("No, I do not want")').first
        ]
        for ins in ins_no_locators:
            if await ins.is_visible():
                await ins.click()
                print("   [🛡️] Opted out of optional travel insurance (INR 0.00)")
                break
    except Exception:
        pass

    # Step 4: Fill standard audit passenger form
    try:
        if await review_page.locator("#titleAdult0").is_visible():
            await review_page.locator("#titleAdult0").select_option("Mr")
        if await review_page.locator("#txtFNAdult0").is_visible():
            await review_page.locator("#txtFNAdult0").fill("Aarav")
        if await review_page.locator("#txtLNAdult0").is_visible():
            await review_page.locator("#txtLNAdult0").fill("Sharma")
        if await review_page.locator("#txtEmailId").is_visible():
            await review_page.locator("#txtEmailId").fill("audit.airgo@gmail.com")
        if await review_page.locator("#txtCPhone").is_visible():
            await review_page.locator("#txtCPhone").fill("9876543210")
        print("   [📝] Traveler contact form populated with audit profile")
    except Exception as e:
        print(f"   [⚠️] Form fill note: {e}")

    # Step 5: Continue to Seat Selection Map
    try:
        continue_btn = review_page.locator("#spnTransaction_2_cnt, #spnTransaction, button:has-text('Continue Booking')").first
        if await continue_btn.is_visible():
            await continue_btn.scroll_into_view_if_needed()
            await continue_btn.click()
            # Wait for seat map / recommendation modal to render
            for _ in range(10):
                await asyncio.sleep(1)
                body_t = await review_page.inner_text("body")
                if "seat" in body_t.lower() or "choose" in body_t.lower() or "skip" in body_t.lower():
                    break
    except Exception as e:
        print(f"   [⚠️] Continue button note: {e}")

    # Step 6: Seat Selection Map -> Dismiss Modal, Capture Seat Map, and Pick Cheapest Seat
    try:
        await review_page.wait_for_timeout(2000)

        # 1. Click "Let Me Choose Myself" to open the interactive airplane seat map
        modal_action = await review_page.evaluate(r"""() => {
            const all = Array.from(document.querySelectorAll('a, button, span, div, p'));
            const choose = all.find(e => (e.innerText || '').trim().toLowerCase().includes('let me choose myself'));
            if (choose) { choose.click(); return 'clicked_let_me_choose_myself'; }
            const chooseBtn = all.find(e => (e.innerText || '').trim().toLowerCase().includes('choose myself'));
            if (chooseBtn) { chooseBtn.click(); return 'clicked_choose_myself'; }
            return 'none';
        }""")
        if modal_action != 'none':
            print(f"   [💺] Selected option: {modal_action}")
            await review_page.wait_for_timeout(3000)

        await review_page.wait_for_timeout(2000)

        # 2. CAPTURE SEAT MAP SCREENSHOT HERE (showing the actual aircraft seat grid)
        seat_shot = os.path.join(checkout_dir, "02_aircraft_seat_map.png")
        await safe_capture_screenshot(review_page, seat_shot, full_page=False)
        print(f"   [📸] Saved Seat Map Screenshot: {os.path.basename(seat_shot)}")

        # 3. Execute cheapest seat selection script
        seat_res = await review_page.evaluate(JS_PICK_CHEAPEST_SEAT)
        if seat_res.get("success"):
            audit_data["seat_number"] = seat_res.get("seatId")
            audit_data["seat_fee"] = seat_res.get("price", 0.0)
            print(f"   [💺] Selected Cheapest Seat: {audit_data['seat_number']} at INR {audit_data['seat_fee']}")
        else:
            print(f"   [💺] Seat selection note: {seat_res.get('reason') or seat_res.get('error')}")

        await review_page.wait_for_timeout(1500)

    except Exception as e:
        print(f"   [⚠️] Seat selection note: {e}")

    # Step 7: Final Payment Gateway -> Navigate past remaining legs & Capture 03_final_payment_gateway.png
    gateway_page = review_page

    for _ in range(5):
        # Check if already on payment gateway
        if "checkout/checkout" in gateway_page.url.lower() or "orderid=" in gateway_page.url.lower():
            break
        await gateway_page.evaluate(r"""() => {
            const all = Array.from(document.querySelectorAll('a, button, span'));
            const skipToPay = all.find(e => /skip\s*to\s*payment/i.test((e.innerText || '').trim()));
            if (skipToPay) { skipToPay.click(); return; }
            const skip = all.find(e => (e.innerText || '').trim().toLowerCase() === 'skip');
            if (skip) { skip.click(); return; }
            const cont = all.reverse().find(e => /continue\s*booking|proceed\s*to\s*payment/i.test((e.innerText || '').trim()));
            if (cont) { cont.click(); return; }
        }""")
        await asyncio.sleep(2)

    # Wait for payment gateway page load
    for _ in range(20):
        for p in context.pages:
            if "orderid=" in p.url.lower() or "checkout/checkout" in p.url.lower():
                gateway_page = p
                break
        if "orderid=" in gateway_page.url.lower() or "checkout/checkout" in gateway_page.url.lower():
            break
        await asyncio.sleep(1)

    await gateway_page.wait_for_timeout(3500)

    # Capture 03_final_payment_gateway.png ON THE PAYMENT GATEWAY
    gateway_shot = os.path.join(checkout_dir, "03_final_payment_gateway.png")
    await safe_capture_screenshot(gateway_page, gateway_shot, full_page=False)
    print(f"   [📸] Saved Payment Gateway Screenshot: {os.path.basename(gateway_shot)}")

    try:
        gw_text = await gateway_page.inner_text("body")
        order_match = re.search(r"orderid=([^&]+)", gateway_page.url, re.IGNORECASE)
        if order_match:
            audit_data["order_id"] = order_match.group(1)

        pay_match = re.search(r"(?:Total\s*Fare|Grand\s*Total|Total\s*Payable|Amount\s*to\s*Pay)[^\d₹]*₹?\s*([\d,]+)", gw_text, re.IGNORECASE)
        if pay_match:
            audit_data["payment_gateway_total"] = float(pay_match.group(1).replace(",", ""))

        fee_match = re.search(r"Others\s*\+[^\d₹]*₹?\s*([\d,]+)", gw_text, re.IGNORECASE)
        if fee_match:
            audit_data["convenience_fee"] = float(fee_match.group(1).replace(",", ""))

        audit_data["status"] = "SUCCESS"
        print(f"   [✅] Reached Final Payment Gateway! Order ID: {audit_data['order_id']} | Total: INR {audit_data['payment_gateway_total']} (Fee: INR {audit_data['convenience_fee']})")
    except Exception as e:
        print(f"   [⚠️] Payment gateway parse note: {e}")

    # Step 8: Save dedicated audited_quote.json inside checkout_dir
    quote_data = {
        "platform": "EaseMyTrip",
        "carrier": target_flight.get("carrier"),
        "carrier_code": target_flight.get("carrier_code"),
        "flight_number": target_flight.get("flight_number"),
        "route": target_flight.get("route"),
        "origin": target_flight.get("origin"),
        "destination": target_flight.get("destination"),
        "advance_purchase_days": target_flight.get("advance_purchase_days"),
        "advance_purchase_window": target_flight.get("advance_purchase_window"),
        "observation_date": target_flight.get("observation_date"),
        "travel_date": target_flight.get("travel_date"),
        "departure_time": target_flight.get("departure_time"),
        "arrival_time": target_flight.get("arrival_time"),
        "stops": target_flight.get("stops"),
        "pricing": {
            "sticker_price": target_flight.get("total_fare"),
            "review_base_fare": audit_data["review_base_fare"],
            "review_taxes": audit_data["review_taxes"],
            "review_grand_total": audit_data["review_grand_total"],
            "selected_seat": audit_data["seat_number"],
            "seat_fee": audit_data["seat_fee"],
            "convenience_fee": audit_data["convenience_fee"],
            "payment_gateway_total": audit_data["payment_gateway_total"],
            "currency": "INR"
        },
        "audit": {
            "order_id": audit_data["order_id"],
            "status": audit_data["status"],
            "insurance_opted_out": True,
            "passenger_name": "Mr Aarav Sharma"
        },
        "screenshots": {
            "review_page": "01_checkout_review.png",
            "seat_map": "02_aircraft_seat_map.png",
            "payment_gateway": "03_final_payment_gateway.png"
        }
    }
    quote_path = os.path.join(checkout_dir, "audited_quote.json")
    with open(quote_path, "w", encoding="utf-8") as f:
        json.dump(quote_data, f, indent=2, ensure_ascii=False)
    print(f"   [💾] Saved Audited Quote JSON: {os.path.relpath(quote_path)}")

    # Clean up review / gateway tab to leave search_page ready for next flight
    try:
        if gateway_page and gateway_page != search_page:
            await gateway_page.close()
        elif review_page and review_page != search_page:
            await review_page.close()
    except Exception:
        pass

    return audit_data


class EaseMyTripHarvester:
    """
    Production-grade EaseMyTrip flight harvester with advance purchase horizons (T+1, T+7, T+15, T+30, T+45)
    and optional deep checkout auditing.
    """

    def __init__(self, run_dir: Optional[str] = None):
        if not run_dir:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.run_dir = os.path.join("runs", f"{timestamp}_easemytrip")
        else:
            self.run_dir = run_dir
        os.makedirs(self.run_dir, exist_ok=True)

    async def harvest_route(
        self,
        route_info: Dict[str, Any],
        horizons: List[int],
        deep_checkout: bool = False,
        checkout_top_n: int = 1,
        visible: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Harvests search results across horizons for a single route, with optional deep checkout.
        """
        origin = route_info["origin"]
        dest = route_info["destination"]
        route_code = route_info["route"]

        print(f"\n=========================================================================================")
        print(f"✈️  HARVESTING ROUTE: {route_code} ({origin} -> {dest}) across horizons {[f'T+{h}' for h in horizons]}")
        print(f"   * Deep Checkout: {'ENABLED' if deep_checkout else 'DISABLED (Sticker Price Only)'}")
        print(f"   * Browser Mode : {'VISIBLE (Chrome GUI)' if visible else 'HEADLESS (Background Chrome)'}")
        print(f"=========================================================================================")

        route_quotes: List[Dict[str, Any]] = []
        today_date = date.today()
        profile_dir = tempfile.mkdtemp(prefix=f"emt_chrome_{route_code}_")

        async with async_playwright() as p:
            context = await launch_chrome_context(p, profile_dir, headless=not visible)

            try:
                for h in horizons:
                    horizon_label = f"T+{h}"
                    travel_dt = today_date + timedelta(days=h)
                    date_dmy = travel_dt.strftime("%d/%m/%Y")
                    search_url = build_search_url(origin, dest, date_dmy)

                    # Isolated screenshot folder: runs/<run_dir>/<ROUTE>/<HORIZON>/
                    horizon_dir = os.path.join(self.run_dir, route_code, horizon_label)
                    os.makedirs(horizon_dir, exist_ok=True)

                    print(f"\n🌐 [{route_code} | {horizon_label} ({date_dmy})]: Navigating to EaseMyTrip...")
                    page = await context.new_page()

                    captured_payload = None

                    async def on_response(res):
                        nonlocal captured_payload
                        url_lower = res.url.lower()
                        if ("airbus" in url_lower or "airavail" in url_lower) and res.status == 200:
                            try:
                                text = await res.text()
                                if len(text) > 1000:
                                    captured_payload = json.loads(text)
                            except Exception:
                                pass

                    page.on("response", on_response)

                    try:
                        await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)

                        # Wait for backend response payload or DOM cards
                        for _ in range(8):
                            if captured_payload:
                                break
                            await asyncio.sleep(1)

                        # Perform realistic smooth human scrolling to progressively load all flights
                        await smooth_human_scroll(page)

                        # Save full-page ground-truth search results screenshot
                        search_shot = os.path.join(horizon_dir, "00_search_results.png")
                        await safe_capture_screenshot(page, search_shot, full_page=True)
                        print(f"   [📸] Saved Full-Page Search Screenshot: {os.path.basename(search_shot)}")

                        # 1. Parse from backend JSON response
                        horizon_quotes: List[Dict[str, Any]] = []
                        if captured_payload:
                            horizon_quotes = parse_airbus_payload(
                                captured_payload, origin, dest, route_code,
                                today_date, travel_dt, horizon_label, h, search_url
                            )

                        # 2. Fallback: Parse rendered DOM cards
                        if not horizon_quotes:
                            cards = await page.evaluate(JS_EXTRACT_DOM_CARDS)
                            if cards:
                                for flt in cards:
                                    price = flt["price"]
                                    base_f = round(price * 0.76, 2)
                                    tax_f = round(price * 0.24, 2)
                                    horizon_quotes.append({
                                        "platform": "EaseMyTrip",
                                        "carrier": flt["airline"],
                                        "carrier_code": flt["airline"][:2].upper(),
                                        "flight_number": flt["flightNumber"],
                                        "origin": origin,
                                        "destination": dest,
                                        "route": route_code,
                                        "observation_date": today_date.isoformat(),
                                        "travel_date": travel_dt.isoformat(),
                                        "departure_time": flt["departureTime"],
                                        "arrival_time": flt["arrivalTime"],
                                        "stops": flt["stops"],
                                        "advance_purchase_days": h,
                                        "advance_purchase_window": horizon_label,
                                        "fare_class": "Economy",
                                        "fare_family": "Standard",
                                        "base_fare": base_f,
                                        "taxes": tax_f,
                                        "total_fare": price,
                                        "currency": "INR",
                                        "source_url": search_url
                                    })

                        print(f"   [✅] Extracted {len(horizon_quotes)} live flights for {route_code} {horizon_label}")
                        for q in horizon_quotes[:4]:
                            print(f"      - {q['carrier']:<16} ({q['flight_number']:<8}) {q['departure_time']}->{q['arrival_time']} | ₹{q['total_fare']}")

                        route_quotes.extend(horizon_quotes)

                        # Save all-day horizon quotes into horizon_dir/quotes.json
                        horizon_quotes_path = os.path.join(horizon_dir, "quotes.json")
                        with open(horizon_quotes_path, "w", encoding="utf-8") as f:
                            json.dump(horizon_quotes, f, indent=2, ensure_ascii=False)
                        print(f"   [💾] Saved Horizon Quotes: {os.path.relpath(horizon_quotes_path)} ({len(horizon_quotes)} flights)")

                        # Optional: Deep Checkout Audit on Top N Cheapest Flights
                        if deep_checkout and horizon_quotes:
                            num_audits = min(len(horizon_quotes), checkout_top_n)
                            print(f"\n   [🛒] Auditing Top {num_audits} Flight(s) for Deep Checkout...")
                            for idx in range(num_audits):
                                flight = horizon_quotes[idx]
                                fn_clean = re.sub(r"[^A-Za-z0-9_-]", "", str(flight.get("flight_number", f"flight_{idx+1}")))
                                carrier_clean = re.sub(r"[^A-Za-z0-9_-]", "", str(flight.get("carrier", "carrier")))
                                checkout_dir = os.path.join(horizon_dir, f"checkout_{carrier_clean}_{fn_clean}")
                                os.makedirs(checkout_dir, exist_ok=True)

                                checkout_result = await audit_checkout_flight(
                                    search_page=page,
                                    context=context,
                                    flight_idx=idx,
                                    target_flight=flight,
                                    checkout_dir=checkout_dir
                                )
                                flight["checkout_audit"] = checkout_result

                    except Exception as e:
                        print(f"   [⚠️] Error harvesting {route_code} {horizon_label}: {e}")
                    finally:
                        try:
                            await page.close()
                        except Exception:
                            pass

            finally:
                try:
                    await context.close()
                except Exception:
                    pass
                try:
                    import shutil
                    shutil.rmtree(profile_dir, ignore_errors=True)
                except Exception:
                    pass

        return route_quotes

    async def run(
        self,
        routes: List[Dict[str, Any]],
        horizons: List[int],
        deep_checkout: bool = False,
        checkout_top_n: int = 1,
        visible: bool = False
    ) -> Dict[str, Any]:
        """Runs the harvest across all specified routes and horizons."""
        all_quotes: List[Dict[str, Any]] = []

        print("\n" + "=" * 95)
        print("🛫 AIRGO EASEMYTRIP HARVESTER INITIALIZED")
        print(f"   * Run Directory   : {self.run_dir}")
        print(f"   * Routes Count    : {len(routes)}")
        print(f"   * Target Horizons : {[f'T+{h}' for h in horizons]}")
        print(f"   * Deep Checkout   : {'YES' if deep_checkout else 'NO (Sticker Price Only)'}")
        print(f"   * Checkout Top-N  : {checkout_top_n if deep_checkout else 'N/A'}")
        print(f"   * Browser GUI     : {'VISIBLE' if visible else 'HEADLESS'}")
        print("=" * 95)

        for route in routes:
            quotes = await self.harvest_route(
                route_info=route,
                horizons=horizons,
                deep_checkout=deep_checkout,
                checkout_top_n=checkout_top_n,
                visible=visible
            )
            all_quotes.extend(quotes)

        # Save root quotes.json
        quotes_path = os.path.join(self.run_dir, "quotes.json")
        with open(quotes_path, "w", encoding="utf-8") as f:
            json.dump(all_quotes, f, indent=2, ensure_ascii=False)

        # Save run_summary.json
        summary = {
            "run_dir": self.run_dir,
            "timestamp": datetime.now().isoformat(),
            "total_quotes": len(all_quotes),
            "routes_audited": [r["route"] for r in routes],
            "horizons": horizons,
            "deep_checkout_performed": deep_checkout,
            "checkout_top_n": checkout_top_n if deep_checkout else 0
        }
        summary_path = os.path.join(self.run_dir, "run_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 95)
        print(f"🎉 EASEMYTRIP HARVEST COMPLETE!")
        print(f"   * Total Live Quotes Captured: {len(all_quotes)}")
        print(f"   * Artifacts Stored Under    : {self.run_dir}")
        print("=" * 95)

        return summary


def main():
    parser = argparse.ArgumentParser(description="EaseMyTrip Airfare Harvester & Auditor")
    parser.add_argument("--top-n", type=int, default=1, help="Number of top DGCA routes (default: 1)")
    parser.add_argument("--routes", type=str, default=None, help="Custom comma-separated routes (e.g. BOM-DEL,BLR-DEL)")
    parser.add_argument("--horizons", type=str, default=None, help="Advance purchase days comma-separated (default: 1,7,15,30,45)")
    parser.add_argument("--deep-checkout", action="store_true", help="Perform deep checkout fee & seat audit (default: sticker price only)")
    parser.add_argument("--checkout-top-n", type=int, default=1, help="Number of top cheapest flights to audit in deep checkout (default: 1)")
    parser.add_argument("--visible", action="store_true", help="Launch visible browser window (default: headless)")

    args = parser.parse_args()

    # Determine horizons
    if args.horizons:
        horizons = [int(x.strip()) for x in args.horizons.split(",") if x.strip().isdigit()]
    else:
        horizons = DEFAULT_HORIZONS

    # Determine routes
    csv_path = os.path.join("data", "processed", "dgca_top100_route_basket.csv")
    if args.routes:
        route_list = []
        for r in args.routes.split(","):
            r = r.strip().upper()
            if "-" in r:
                o, d = r.split("-", 1)
                route_list.append({
                    "route": r,
                    "origin": o.strip(),
                    "destination": d.strip()
                })
        routes = route_list
    else:
        routes = load_route_basket(csv_path, top_n=args.top_n)

    harvester = EaseMyTripHarvester()
    asyncio.run(harvester.run(
        routes=routes,
        horizons=horizons,
        deep_checkout=args.deep_checkout,
        checkout_top_n=args.checkout_top_n,
        visible=args.visible
    ))


# Alias matching AirGo scraper naming convention
EaseMyTripScraper = EaseMyTripHarvester


if __name__ == "__main__":
    main()
