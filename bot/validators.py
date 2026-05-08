"""
Input validation for trading bot CLI parameters.
All validation functions raise ValueError with descriptive messages on failure.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET", "STOP_LOSS_LIMIT"}

def validate_symbol(symbol: str) -> str:
    """Ensure symbol is a non-empty uppercase string (e.g. BTCUSDT)."""
    s = symbol.strip().upper()
    if not s:
        raise ValueError("Symbol must not be empty.")
    if not s.isalnum():
        raise ValueError(f"Symbol '{s}' must be alphanumeric (e.g. BTCUSDT).")
    return s


def validate_side(side: str) -> str:
    """Ensure side is BUY or SELL."""
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValueError(f"Side must be one of {sorted(VALID_SIDES)}, got '{side}'.")
    return s


def validate_order_type(order_type: str) -> str:
    """Ensure order type is one of the supported types."""
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type must be one of {sorted(VALID_ORDER_TYPES)}, got '{order_type}'."
        )
    return t


def validate_quantity(quantity: str | float) -> Decimal:
    """Ensure quantity is a positive decimal number."""
    try:
        q = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")
    if q <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {q}.")
    return q


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Validate price field.

    - LIMIT orders require a positive price.
    - MARKET orders must not provide a price.
    - STOP_MARKET orders require a stop price (validated separately via stop_price).
    """
    if order_type == "MARKET":
        if price is not None:
            raise ValueError("Price must not be provided for MARKET orders.")
        return None

    if order_type == "LIMIT":
        if price is None:
            raise ValueError(f"Price is required for {order_type} orders.")
        try:
            p = Decimal(str(price))
        except InvalidOperation:
            raise ValueError(f"Price '{price}' is not a valid number.")
        if p <= 0:
            raise ValueError(f"Price must be greater than zero, got {p}.")
        return p

    return None


def validate_stop_price(stop_price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """Validate stop price for STOP_MARKET orders."""
    if order_type != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValueError("--stop-price is required for STOP_MARKET orders.")
    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValueError(f"Stop price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than zero, got {sp}.")
    return sp


def validate_all(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
) -> dict:
    """
    Run all validations and return a clean params dict.

    Returns:
        dict with keys: symbol, side, order_type, quantity, price, stop_price
    """
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.strip().upper()),
        "stop_price": validate_stop_price(stop_price, order_type.strip().upper()),
    }
