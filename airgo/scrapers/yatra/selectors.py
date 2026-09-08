"""
Centralized CSS and XPath selectors for the Yatra flight search results page.
Organized into resilient selector fallbacks matching dynamic React DOM layouts.
"""

from typing import List


class YatraSelectors:
    """Central repository of DOM selectors for Yatra flight search and checkout interface."""

    # Containers for flight cards
    FLIGHT_CARDS: List[str] = [
        "div.tuple",
        "div.flightItem",
        "div.flight-seg",
        "div.flight-tuple",
        "div[class*='flightItem']",
        "div[class*='flight-item']",
        "div[class*='flight-card']",
        "div.flight-list > div.tuple",
    ]

    # Airline name selectors within a flight card
    AIRLINE_NAME: List[str] = [
        ".airline-name span.text",
        "span.text.ellipsis",
        ".airline-holder span.text",
        "div.fs-13.airline-name span.text",
        "span.airline-name",
        "div[class*='airline-name']",
        "span.i-b.text-blue",
        "div.fs-15",
        "img[alt]",
    ]

    # Flight code / number
    FLIGHT_NUMBER: List[str] = [
        ".fl-no span",
        "p.fl-no span",
        "p.fl-no",
        "span.fl-code",
        "span.flight-number",
        "p.font-lightgray",
        "span.normal",
        "span.fs-12.font-lightgray",
    ]

    # Departure and Arrival times
    DEPARTURE_TIME: List[str] = [
        "[autom='departureTimeLabel']",
        ".dtime .time",
        "div[class*='depart'] .fs-18",
        "div.depart-time",
        "span.depart-time",
        "div.fs-18:first-of-type",
    ]
    ARRIVAL_TIME: List[str] = [
        "[autom='arrivalTimeLabel']",
        ".atime p.time",
        "div[class*='arrival'] .fs-18",
        "div.arrival-time",
        "span.arrival-time",
        "div.fs-18:last-of-type",
    ]

    # Duration & Stops
    DURATION: List[str] = [
        "[autom='durationLabel']",
        "p.du",
        "p.duration",
        "p.fs-12",
        "span.duration",
        "span.fs-12",
        "div[class*='duration']",
    ]
    STOPS: List[str] = [
        ".dotted-borderbtm",
        "span.cursor-default",
        "span.stops",
        "span[class*='stops']",
        "div[class*='stops']",
    ]

    # City / Airport / IATA code labels
    ORIGIN_IATA: List[str] = [
        "p.city-code:first-of-type",
        "span.city-code:first-of-type",
        "p[class*='origin']",
    ]
    DESTINATION_IATA: List[str] = [
        "p.city-code:last-of-type",
        "span.city-code:last-of-type",
        "p[class*='destination']",
    ]

    # Primary displayed fare price
    DISPLAYED_PRICE: List[str] = [
        "[autom='priceLabel'] .fare-summary-tooltip",
        ".fare-summary-tooltip",
        "div.tipsy.fare-summary-tooltip",
        "div.tipsy.fs-18",
        "div[autom='priceLabel']",
        "span.tipsy",
        "p.fs-18.font-bold",
        "span[class*='fare']",
        "span[class*='price']",
        "div[class*='total-price']",
        "span.total-fare",
    ]

    # Button to expand multiple fares
    MORE_FARES_BUTTON: List[str] = [
        "button[autom='morefares']",
        "button.secondary-button",
        "button.button",
    ]

    # Multiple fare options / family bundles within a flight card
    FARE_OPTIONS_CONTAINER: List[str] = [
        "div.table-box",
        "div.branded-fare",
        "div[class*='fare-family']",
        "div[class*='fare-dropdown']",
        "div[class*='fare-options']",
        "div.fare-option",
        "div[class*='fare-item']",
        "div[class*='fare-card']",
    ]
    FARE_OPTION_NAME: List[str] = [
        "td.col.bold",
        "span.fare-name",
        "p.fare-type",
        "span.fare-title",
        "span.font-bold",
    ]
    FARE_OPTION_PRICE: List[str] = [
        "div.v-aligm-m.i-b",
        "div.tipsy",
        "span.fare-price",
        "span.price",
        "p.price",
        "span.tipsy",
        "span[class*='fare']",
    ]

    # Sold out or unavailable indicators
    SOLD_OUT: List[str] = [
        "span.sold-out",
        "div.sold-out",
        "span[class*='sold-out']",
        "div[class*='soldout']",
        "div[class*='unavailable']",
    ]

    # Anti-bot, WAF, and challenge markers
    CHALLENGE_SIGNATURES: List[str] = [
        "Access Denied",
        "You don't have permission to access",
        "Akamai Bot Manager",
        "Cloudflare",
        "cf-turnstile",
        "recaptcha",
        "hcaptcha",
        "Bot Protection",
        "Security Check",
        "Please verify you are a human",
        "Pardon Our Interruption",
    ]

    # --- Phase 3: Booking Flow & Pre-Payment / Pay Now Selectors ---

    # Flight card booking / selection buttons
    BOOK_BUTTON: List[str] = [
        "button[autom='booknow']",
        "div.booknow-btn button",
        "button.secondary-button",
        "button.booking-btn",
        "button[class*='book']",
        "button[class*='choose']",
        "input[value*='Book']",
    ]

    # Fare option selection buttons inside fare bundles
    SELECT_FARE_BUTTON: List[str] = [
        "button[autom='booknow']",
        "button.select-fare-btn",
        "button[class*='select-fare']",
        "div.fare-option button",
    ]

    # Modal dismissal on checkout page
    CHECKOUT_MODAL_CLOSE: List[str] = [
        "span.style_cross__Rwqim",
        "span[class*='cross']",
        "img[alt='cross']",
        "button.close",
        "span.close-popup",
    ]

    # Review / Itinerary progression buttons
    CONTINUE_BOOKING_BUTTON: List[str] = [
        "button.bg-\\[\\#D60F0F\\]",
        "button.style_btnRed__EltTU",
        "button[id*='continue']",
        "input[value*='Continue']",
    ]

    # Popups, add-ons (insurance, seats, meals) skip/dismiss buttons
    ADDON_SKIP_BUTTON: List[str] = [
        "button.bg-\\[\\#D60F0F\\]",
        "span.style_cross__Rwqim",
        "span[class*='cross']",
        "img[alt='cross']",
        "span.close-popup",
        "button.close",
        "button[class*='close']",
    ]

    # Pre-payment / Pay Now page container indicators
    PAYNOW_CONTAINER: List[str] = [
        "div.payment-options",
        "div[class*='payment-container']",
        "div[class*='payment-wrapper']",
        "div#payment-modes",
        "div[class*='pay-now']",
    ]

    # Pre-Payment / Pay Now total payable amount
    PAYNOW_TOTAL_AMOUNT: List[str] = [
        "span.total-payable",
        "div[class*='total-amount']",
        "span[class*='final-amount']",
        "div.pay-amount",
        "span.pay-amount",
        "span[id*='totalPayable']",
        "span[id*='payableAmount']",
        "div.grand-total",
        "span.grand-total",
        "div[class*='total-fare']",
        "p[class*='total-payable']",
        "span[class*='total-price']",
    ]

    # Pre-Payment breakdown components (where exposed)
    PAYNOW_BASE_FARE: List[str] = [
        "span.base-fare",
        "div.base-fare",
        "span[class*='base-fare']",
        "div[class*='baseFare']",
        "td.base-fare",
    ]
    PAYNOW_TAXES: List[str] = [
        "span.tax-amount",
        "div.tax-amount",
        "span[class*='taxes']",
        "span[class*='tax']",
        "div[class*='taxes']",
        "td.tax-amount",
    ]
    PAYNOW_CONVENIENCE_FEE: List[str] = [
        "span.convenience-fee",
        "div.convenience-fee",
        "span[class*='convenience']",
        "div[class*='convenienceFee']",
        "td.convenience-fee",
    ]
    PAYNOW_OTHER_CHARGES: List[str] = [
        "span.other-charges",
        "div.other-charges",
        "span[class*='surcharges']",
        "div[class*='udf']",
        "td.other-charges",
    ]

    # Price change and sold-out notifications during checkout
    PRICE_CHANGE_ALERT: List[str] = [
        "div[class*='price-change']",
        "div[class*='fare-update']",
        "div[class*='alert-warning']",
        "div.fare-change",
        "p[class*='price-change']",
    ]
