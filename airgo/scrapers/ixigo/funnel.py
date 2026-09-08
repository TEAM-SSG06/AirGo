"""Safe Ixigo booking-funnel traversal.

The funnel stops at the review/payment landing page. It never fills payment fields
or submits a booking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FunnelResult:
    status: str
    confirmed_price: float | None = None
    base_fare: float | None = None
    taxes_fees: float | None = None
    message: str | None = None


def _text_price(value: Any) -> float | None:
    if value is None:
        return None
    cleaned = str(value).replace(",", "").replace("₹", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


async def _visible_price(page: Any) -> float | None:
    """Read a price from explicit Ixigo price attributes, without inventing a value."""
    return await page.evaluate(
        """() => {
          const nodes = [...document.querySelectorAll('[data-total-price], [data-confirmed-price]')];
          for (const node of nodes) {
            const value = node.getAttribute('data-total-price') || node.getAttribute('data-confirmed-price');
            if (value) return value;
          }
          return null;
        }"""
    )


async def verify_fare(page: Any, candidate: dict[str, Any], timeout_ms: int = 30_000) -> FunnelResult:
    """Walk one selected fare to review, then stop before payment details.

    Ixigo's live DOM can change. Selectors are limited to explicit data attributes and
    accessible names; missing controls result in ``unavailable`` rather than a guess.
    """
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
        if await page.locator("[data-captcha], iframe[title*='captcha' i]").count():
            return FunnelResult("blocked", message="captcha_or_block_detected")

        flight_number = str(candidate.get("flight_number", "")).replace('"', '\\"')
        fare_class = str(candidate.get("fare_class", "")).replace('"', '\\"')
        exact_selector = (
            f'[data-select-fare][data-flight-number="{flight_number}"]'
            f'[data-fare-class="{fare_class}"]'
        )
        select_button = page.locator(exact_selector).first
        if await select_button.count() == 0:
            return FunnelResult("unavailable", message="fare_selection_control_not_found")
        await select_button.click(timeout=timeout_ms)

        continue_button = page.locator("[data-continue-to-traveller]").first
        if await continue_button.count() == 0:
            return FunnelResult("unavailable", message="traveller_step_control_not_found")
        await continue_button.click(timeout=timeout_ms)

        review_button = page.locator("[data-review-booking], [data-continue-to-review]").first
        if await review_button.count() == 0:
            return FunnelResult("unavailable", message="review_step_control_not_found")
        await review_button.click(timeout=timeout_ms)

        payment_landing = page.locator("[data-payment-landing], [data-pay-now]").first
        if await payment_landing.count() == 0:
            return FunnelResult("unavailable", message="payment_landing_not_reached")

        # Deliberately stop before interacting with any payment form.
        payment_field = page.locator("input[name*='cvv' i], input[name*='card' i], [data-payment-field]")
        if await payment_field.count():
            return FunnelResult("ok", confirmed_price=_text_price(await _visible_price(page)), message="stopped_before_payment_field")

        confirmed = _text_price(await _visible_price(page))
        return FunnelResult(
            "ok" if confirmed is not None else "unavailable",
            confirmed_price=confirmed,
            message="stopped_before_payment_submission",
        )
    except Exception as exc:  # Playwright exceptions vary by installed version.
        return FunnelResult("unavailable", message=f"funnel_error:{type(exc).__name__}:{exc}")
