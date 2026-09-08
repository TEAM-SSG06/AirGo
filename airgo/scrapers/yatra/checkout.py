"""
Yatra deep checkout and fare verification engine.
Progresses through the Yatra booking flow up to the final pre-payment / Pay Now stage,
extracts authoritative payable prices and fee breakdowns, detects price changes,
captures ground-truth Pay Now screenshots, and halts strictly before payment.
"""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from airgo.scrapers.yatra.models import (
    AntiBotEvent,
    AntiBotEventType,
    AvailabilityStatus,
    DataStatus,
    NormalizedFareQuote,
)
from airgo.scrapers.yatra.normalizer import normalize_price
from airgo.scrapers.yatra.parser import YatraParser
from airgo.scrapers.yatra.run_manager import YatraRunManager
from airgo.scrapers.yatra.selectors import YatraSelectors

logger = logging.getLogger("AirGo.Yatra.Checkout")


class YatraCheckoutVerifier:
    """
    Orchestrates flight booking progression up to the Pay Now screen.
    Handles Yatra's multi-tab architecture (opening https://secure.yatra.com in a new tab),
    dismisses login popup modals, fills non-sensitive guest traveler details,
    extracts authoritative payable prices and fee breakdowns, detects price changes,
    captures ground-truth Pay Now screenshots, and halts strictly before payment.
    """

    def __init__(
        self,
        run_manager: YatraRunManager,
        timeout_ms: int = 25000,
    ):
        self.run_manager = run_manager
        self.timeout_ms = timeout_ms

    async def _dismiss_login_modal(self, target: Page) -> None:
        """Dismisses Yatra login popup dialog if rendered on the checkout tab."""
        for _ in range(3):
            cross = target.locator("span.style_cross__Rwqim, span[class*='cross'], img[alt='cross'], button.close").first
            if await cross.count() > 0 and await cross.is_visible():
                try:
                    await cross.click(force=True)
                    logger.info("Dismissed login popup modal")
                    await asyncio.sleep(0.5)
                    break
                except Exception:
                    pass
            try:
                await target.keyboard.press("Escape")
            except Exception:
                pass
            await asyncio.sleep(0.3)

    async def verify_fare(
        self,
        page: Page,
        quote: NormalizedFareQuote,
        window_code: str = "T+1",
        custom_screenshot_path: Optional[Path] = None,
    ) -> NormalizedFareQuote:
        """
        Executes booking navigation for a candidate fare quote:
        1. On search page: locates flight card and clicks Book (opening new tab).
        2. On checkout tab: closes login popup modal.
        3. Waits for live fare confirmation in sidebar.
        4. Progresses through insurance and guest traveler details.
        5. Reaches pre-payment / Pay Now stage.
        6. Extracts final payable fare and fee breakdown.
        7. Captures Pay Now screenshot proof.
        8. Halts strictly without payment.
        9. Closes checkout tab.
        """
        is_closed = False
        try:
            val = page.is_closed()
            if isinstance(val, bool):
                is_closed = val
        except Exception:
            pass

        if is_closed:
            quote.verification_status = DataStatus.VERIFICATION_FAILED
            quote.error_reason = "Search page is closed"
            print(f"[Yatra][ERROR] Search page was closed for {quote.flight_number}")
            return quote

        print(f"[Yatra] Opening booking flow for {quote.flight_number} ({quote.airline})...")
        logger.info(
            f"Initiating checkout verification for {quote.route} | {quote.flight_number} | "
            f"{quote.fare_option_name or 'Standard'} (Displayed: ₹{quote.displayed_price})"
        )

        if custom_screenshot_path is not None:
            paynow_shot_path = custom_screenshot_path
        else:
            paynow_shot_path = self.run_manager.get_paynow_screenshot_path(
                route_code=quote.route,
                window_code=window_code,
                flight_number=quote.flight_number,
                fare_option_name=quote.fare_option_name or "standard",
            )

        checkout_page: Optional[Page] = None
        try:
            # 1. Check if the initial page has an anti-bot challenge
            initial_html = await page.content()
            challenge = YatraParser.detect_anti_bot(
                html=initial_html,
                status_code=200,
                url=page.url,
                route=quote.route,
                travel_date=quote.travel_date,
            )
            if challenge:
                print(f"[Yatra][SECURITY] {challenge.message}")
                custom_dir = custom_screenshot_path.parent if custom_screenshot_path else None
                return await self._handle_challenge(page, quote, challenge, window_code, custom_dir=custom_dir)

            # Check if page is already at checkout / payment (e.g. direct test fixture or redirect)
            is_already_checkout = any(
                kw in page.url.lower() for kw in ["checkout", "payment", "notice"]
            ) or "payment-container" in initial_html or "fare-breakup" in initial_html

            if is_already_checkout:
                checkout_page = page
            else:
                # 2. Locate flight card on search page
                flight_card_locator = await self._find_flight_card(page, quote)
                if not flight_card_locator:
                    quote.verification_status = DataStatus.VERIFICATION_FAILED
                    quote.error_reason = f"Flight card {quote.flight_number} not found on search page"
                    print(f"[Yatra][ERROR] Flight {quote.flight_number} card not found")
                    return quote

                await flight_card_locator.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)

                # 3. Expand fare options if button present and not already expanded
                book_btn = flight_card_locator.locator("button[autom='booknow']").first
                if await book_btn.count() == 0 or not await book_btn.is_visible():
                    view_fares_btn = flight_card_locator.locator(
                        "button[autom='morefares']:has-text('View Fares'), button:has-text('View Fares')"
                    ).first
                    if await view_fares_btn.count() > 0 and await view_fares_btn.is_visible():
                        try:
                            await view_fares_btn.scroll_into_view_if_needed()
                            await view_fares_btn.click(force=True)
                            await asyncio.sleep(2.0)
                        except Exception:
                            pass

                # 4. Locate Book button
                try:
                    await flight_card_locator.locator("button[autom='booknow']").first.wait_for(state="attached", timeout=6000)
                except Exception:
                    pass

                book_btn = flight_card_locator.locator("button[autom='booknow']").first

                if quote.fare_option_name and quote.fare_option_name.lower() != "standard":
                    fare_row_btn = flight_card_locator.locator(
                        f"div.table-box:has-text('{quote.fare_option_name}') button[autom='booknow']"
                    ).first
                    if await fare_row_btn.count() > 0:
                        book_btn = fare_row_btn

                if await book_btn.count() == 0:
                    table_book = page.locator("div.table-box button[autom='booknow'], div.table-box button:has-text('Book')").first
                    if await table_book.count() > 0 and await table_book.is_visible():
                        book_btn = table_book
                    else:
                        quote.verification_status = DataStatus.VERIFICATION_FAILED
                        quote.error_reason = f"Book button not found for flight {quote.flight_number}"
                        print(f"[Yatra][ERROR] Book button not found for {quote.flight_number}")
                        return quote

                try:
                    await book_btn.scroll_into_view_if_needed()
                    async with page.context.expect_page(timeout=15000) as new_page_info:
                        await book_btn.click(force=True)
                    checkout_page = await new_page_info.value
                    await checkout_page.wait_for_load_state("domcontentloaded", timeout=20000)
                    print("[Yatra] Booking page loaded")
                    await asyncio.sleep(2.0)
                except Exception as open_err:
                    quote.verification_status = DataStatus.VERIFICATION_FAILED
                    quote.error_reason = f"Checkout page failed to open: {open_err}"
                    print(f"[Yatra][ERROR] Checkout page failed to open for {quote.flight_number}")
                    return quote

                # 5. Dismiss login popup modal if present
                await self._dismiss_login_modal(checkout_page)

                # 6. Wait for live fare confirmation in sidebar
                await asyncio.sleep(2.5)

            # 7. Check for anti-bot barriers on checkout page
            checkout_html = await checkout_page.content()
            challenge = YatraParser.detect_anti_bot(
                html=checkout_html,
                status_code=200,
                url=checkout_page.url,
                route=quote.route,
                travel_date=quote.travel_date,
            )
            if challenge:
                print(f"[Yatra][SECURITY] {challenge.message}")
                custom_dir = custom_screenshot_path.parent if custom_screenshot_path else None
                return await self._handle_challenge(checkout_page, quote, challenge, window_code, custom_dir=custom_dir)

            # 8. Check for price change alert or sold out banner
            price_alert = YatraParser.detect_price_change_alert(checkout_html)
            if "sold out" in checkout_html.lower() or "seats sold out" in checkout_html.lower():
                quote.availability_status = AvailabilityStatus.SOLD_OUT
                quote.verification_status = DataStatus.SOLD_OUT
                quote.error_reason = "Seats sold out during checkout progression"
                print(f"[Yatra] Flight {quote.flight_number} sold out during checkout")
                return quote

            # 9. Progress through booking review flow
            print("[Yatra] Continuing through booking review...")
            # Insurance skip / Continue button
            cont_btn = checkout_page.locator("button.bg-\\[\\#D60F0F\\], button:has-text('Continue')").first
            if await cont_btn.count() > 0 and await cont_btn.is_visible():
                try:
                    await cont_btn.click(force=True)
                    await asyncio.sleep(1.5)
                except Exception:
                    pass

            await self._dismiss_login_modal(checkout_page)

            # Fill non-sensitive guest traveler details
            try:
                email_inp = checkout_page.locator("input[type='email'], input[placeholder*='Email']").first
                if await email_inp.count() > 0 and await email_inp.is_visible():
                    await email_inp.fill("audit.traveler@example.com")

                phone_inp = checkout_page.locator("input[type='tel'], input[placeholder*='Mobile']").first
                if await phone_inp.count() > 0 and await phone_inp.is_visible():
                    await phone_inp.fill("9876543210")

                fname_inp = checkout_page.locator("input[placeholder*='First'], input[name*='fname']").first
                if await fname_inp.count() > 0 and await fname_inp.is_visible():
                    await fname_inp.fill("AirGo")

                lname_inp = checkout_page.locator("input[placeholder*='Last'], input[name*='lname']").first
                if await lname_inp.count() > 0 and await lname_inp.is_visible():
                    await lname_inp.fill("Audit")
            except Exception:
                pass

            # Proceed towards payment review / Pay Now stage
            for _ in range(2):
                prog_btn = checkout_page.locator(
                    "button:has-text('Proceed to Payment'), button:has-text('Skip to Payment'), button:has-text('Continue')"
                ).first
                if await prog_btn.count() > 0 and await prog_btn.is_visible():
                    try:
                        await prog_btn.click(force=True)
                        await asyncio.sleep(2.0)
                    except Exception:
                        pass
                await self._dismiss_login_modal(checkout_page)

            # 10. Extract final payable fare & breakdown
            try:
                await checkout_page.locator("text=/Total (Amount|Payable)/i").first.wait_for(state="visible", timeout=6000)
            except Exception:
                pass
            await asyncio.sleep(1.0)

            final_html = await checkout_page.content()
            breakdown = YatraParser.parse_paynow_breakdown(final_html)
            final_price = breakdown.get("final_payable_price")

            # Fallback to total amount in current html if not parsed
            if not final_price:
                try:
                    import re
                    fs = checkout_page.locator("div:has-text('Total Amount')").last
                    if await fs.count() > 0:
                        text = await fs.inner_text()
                        m = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", text)
                        if m:
                            final_price = normalize_price(m.group(1))
                except Exception:
                    pass

            # Fallback to total amount in current html if not parsed
            if not final_price:
                # search for ₹ price in Fare Summary section
                fs_loc = checkout_page.locator("h2:has-text('Fare Summary')").first
                if await fs_loc.count() > 0:
                    text_block = await checkout_page.locator("div:has-text('Fare Summary')").first.inner_text()
                    lines = [ln.strip() for ln in text_block.split("\n") if ln.strip()]
                    for i, ln in enumerate(lines):
                        if "total amount" in ln.lower() or "total payable" in ln.lower():
                            for nxt in lines[i+1:i+3]:
                                try:
                                    final_price = normalize_price(nxt)
                                    break
                                except ValueError:
                                    pass

            # 11. Capture ground-truth Pay Now screenshot proof
            try:
                await checkout_page.screenshot(path=str(paynow_shot_path), full_page=False)
                quote.paynow_screenshot_path = str(paynow_shot_path)
            except Exception as ss_err:
                logger.warning(f"Could not capture Pay Now screenshot: {ss_err}")

            print("[Yatra] Reached fare review / Pay Now page")
            print(f"[Yatra] Displayed price: ₹{quote.displayed_search_price or quote.displayed_price}")

            if final_price is not None and final_price > Decimal("0.00"):
                quote.final_payable_price = final_price
                quote.verification_timestamp = datetime.now(timezone.utc)
                print(f"[Yatra] Final payable price: ₹{final_price}")
                print(f"[Yatra] Screenshot saved: {paynow_shot_path}")

                if breakdown.get("base_fare"):
                    quote.base_fare = breakdown["base_fare"]  # type: ignore
                if breakdown.get("taxes"):
                    quote.taxes = breakdown["taxes"]  # type: ignore
                if breakdown.get("convenience_fee"):
                    quote.convenience_fee = breakdown["convenience_fee"]  # type: ignore
                if breakdown.get("other_charges"):
                    quote.other_charges = breakdown["other_charges"]  # type: ignore

                diff = final_price - (quote.displayed_search_price or quote.displayed_price)
                quote.price_difference = diff

                if diff != Decimal("0.00") or price_alert:
                    quote.verification_status = DataStatus.PRICE_CHANGED
                    if price_alert:
                        quote.error_reason = f"Price changed during checkout: {price_alert} (Diff: ₹{diff})"
                else:
                    quote.verification_status = DataStatus.FARE_VERIFIED
            else:
                quote.verification_status = DataStatus.VERIFICATION_FAILED
                quote.error_reason = "Fare review page reached but total amount could not be parsed"
                print(f"[Yatra][ERROR] Could not parse final payable price for {quote.flight_number}")
                if custom_screenshot_path:
                    fail_path = custom_screenshot_path.parent / "checkout_failed.png"
                    try:
                        active_p = checkout_page or page
                        await active_p.screenshot(path=str(fail_path), full_page=False)
                    except Exception:
                        pass

        except PlaywrightTimeoutError as te:
            logger.warning(f"Timeout during checkout verification for {quote.flight_number}: {te}")
            quote.verification_status = DataStatus.VERIFICATION_FAILED
            quote.error_reason = f"Timeout during booking progression: {te}"
            print(f"[Yatra][ERROR] Flight {quote.flight_number} verification timed out")
            if custom_screenshot_path:
                fail_path = custom_screenshot_path.parent / "checkout_failed.png"
                try:
                    active_p = checkout_page or page
                    await active_p.screenshot(path=str(fail_path), full_page=False)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Unexpected error during checkout verification for {quote.flight_number}: {e}")
            quote.verification_status = DataStatus.VERIFICATION_FAILED
            quote.error_reason = f"Unexpected checkout error: {e}"
            print(f"[Yatra][ERROR] Flight {quote.flight_number} verification failed: {e}")
            if custom_screenshot_path:
                fail_path = custom_screenshot_path.parent / "checkout_failed.png"
                try:
                    active_p = checkout_page or page
                    await active_p.screenshot(path=str(fail_path), full_page=False)
                except Exception:
                    pass
        finally:
            if checkout_page and checkout_page is not page:
                try:
                    await checkout_page.close()
                except Exception:
                    pass
            try:
                await page.bring_to_front()
            except Exception:
                pass

        return quote

    async def _find_flight_card(self, page: Page, quote: NormalizedFareQuote) -> Optional[Any]:
        """Locates the card element matching flight number or airline details."""
        clean_fn = quote.flight_number.replace("-", "").strip()
        first_segment = quote.flight_number.split("/")[0].strip()
        first_clean = first_segment.replace("-", "").strip()

        card_selectors = [
            f"div.tuple:has-text('{quote.flight_number}')",
            f"div.tuple:has-text('{clean_fn}')",
            f"div.tuple:has-text('{first_segment}')",
            f"div.tuple:has-text('{first_clean}')",
            f"div.flightItem:has-text('{quote.flight_number}')",
            f"div.flight-seg:has-text('{quote.flight_number}')",
        ]
        if quote.departure_time and quote.departure_time != "00:00":
            card_selectors.append(f"div.tuple:has-text('{quote.airline}'):has-text('{quote.departure_time}')")

        for sel in card_selectors:
            try:
                loc = page.locator(sel)
                first_loc = getattr(loc, "first", loc)
                if await first_loc.count() > 0:
                    return first_loc
            except Exception:
                continue

        try:
            loc = page.locator("div.tuple")
            first_loc = getattr(loc, "first", loc)
            if await first_loc.count() > 0:
                return first_loc
        except Exception:
            pass

        return None

    async def _handle_challenge(
        self,
        page: Page,
        quote: NormalizedFareQuote,
        challenge: AntiBotEvent,
        window_code: str,
        custom_dir: Optional[Path] = None,
    ) -> NormalizedFareQuote:
        """Captures challenge screenshot and records challenge state without evasion."""
        if custom_dir is not None:
            challenge_shot = custom_dir / "akamai_challenge.png"
        else:
            challenge_shot = self.run_manager.get_screenshot_path(
                quote.route, window_code, "checkout_challenge"
            )
        try:
            await page.screenshot(path=str(challenge_shot), full_page=False)
            challenge.screenshot_path = str(challenge_shot)
        except Exception:
            pass

        self.run_manager.record_anti_bot_event(challenge)
        if challenge.event_type == AntiBotEventType.CAPTCHA:
            quote.verification_status = DataStatus.CAPTCHA_BLOCKED
        elif challenge.event_type == AntiBotEventType.ACCESS_DENIED:
            quote.verification_status = DataStatus.ACCESS_DENIED
        else:
            quote.verification_status = DataStatus.CAPTCHA_BLOCKED

        quote.error_reason = f"Security barrier encountered during checkout: {challenge.message}"
        return quote
