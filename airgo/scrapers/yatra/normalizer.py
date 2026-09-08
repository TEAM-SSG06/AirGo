"""
Reusable price and currency normalization utility.
Transforms raw airfare strings (e.g., '₹4,999', '₹ 4,999', '4,999', '4999.00')
into clean, validated Decimal / float numeric representations.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Union


# Matches standard numeric amounts with optional commas and decimal parts
_PRICE_REGEX = re.compile(r"(\d[\d,]*(?:\.\d+)?)")


def normalize_price(
    raw_price: Union[str, int, float, Decimal],
    allow_zero: bool = True,
    default: Optional[Decimal] = None
) -> Decimal:
    """
    Normalizes a raw price into a Decimal numeric value.

    Examples:
        normalize_price('₹4,999') -> Decimal('4999.00')
        normalize_price('₹ 4,999') -> Decimal('4999.00')
        normalize_price('4,999') -> Decimal('4999.00')
        normalize_price(4999) -> Decimal('4999.00')
        normalize_price('4999.50') -> Decimal('4999.50')
        normalize_price('Rs. 4,999/-') -> Decimal('4999.00')

    Args:
        raw_price: The raw price representation (string, int, float, Decimal).
        allow_zero: If False, raises ValueError when price <= 0.
        default: Optional fallback Decimal if input cannot be parsed.

    Returns:
        Decimal representation of the numeric price rounded to 2 decimal places.

    Raises:
        ValueError: If input is invalid and no default is provided.
    """
    if raw_price is None:
        if default is not None:
            return default
        raise ValueError("Price input cannot be None")

    if isinstance(raw_price, (int, float, Decimal)):
        try:
            val = Decimal(str(raw_price))
        except (InvalidOperation, TypeError):
            if default is not None:
                return default
            raise ValueError(f"Could not convert numeric value to Decimal: {raw_price}")
    elif isinstance(raw_price, str):
        cleaned = raw_price.strip().replace("\xa0", " ")
        if not cleaned:
            if default is not None:
                return default
            raise ValueError("Price string cannot be empty or whitespace")

        match = _PRICE_REGEX.search(cleaned)
        if not match:
            if default is not None:
                return default
            raise ValueError(f"No numeric digits found in price string: {raw_price}")

        cleaned_digits = match.group(1).replace(",", "")
        try:
            val = Decimal(cleaned_digits)
        except InvalidOperation:
            if default is not None:
                return default
            raise ValueError(f"Failed to parse cleaned price '{cleaned_digits}' from original '{raw_price}'")
    else:
        if default is not None:
            return default
        raise ValueError(f"Unsupported price type: {type(raw_price)}")

    if not allow_zero and val <= Decimal("0"):
        raise ValueError(f"Price must be greater than zero, got: {val}")

    if val < Decimal("0"):
        raise ValueError(f"Price cannot be negative, got: {val}")

    return val.quantize(Decimal("0.01"))


def normalize_price_float(
    raw_price: Union[str, int, float, Decimal],
    allow_zero: bool = True,
    default: Optional[float] = None
) -> float:
    """Helper returning clean float representation of price."""
    dec_default = Decimal(str(default)) if default is not None else None
    dec_val = normalize_price(raw_price, allow_zero=allow_zero, default=dec_default)
    return float(dec_val)
