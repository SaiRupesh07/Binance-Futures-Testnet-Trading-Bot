"""
Order placement logic.

Bridges validated user input → BinanceClient API calls → structured result dicts.
Keeps CLI and client layers fully decoupled.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from .client import BinanceClient, BinanceAPIError
from .logging_config import get_logger

logger = get_logger("orders")


def _fmt(val) -> str:
    """Format Decimal or numeric value without trailing zeros."""
    if val is None:
        return "N/A"
    d = Decimal(str(val))
    return format(d.normalize(), "f")


def _build_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Optional[Decimal] = None,
    stop_price: Optional[Decimal] = None,
) -> dict:
    return {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": _fmt(quantity),
        "price": _fmt(price),
        "stop_price": _fmt(stop_price),
    }


def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
) -> dict:
    """
    Place a MARKET order on Binance Futures.

    Returns:
        dict with keys: summary, response, success, error
    """
    summary = _build_order_summary(symbol, side, "MARKET", quantity)
    logger.info(
        "Placing MARKET order | symbol=%s side=%s qty=%s",
        symbol, side, _fmt(quantity),
    )

    try:
        resp = client.place_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=_fmt(quantity),
        )
        logger.info("MARKET order placed successfully | orderId=%s status=%s", resp.get("orderId"), resp.get("status"))
        return {"summary": summary, "response": resp, "success": True, "error": None}

    except BinanceAPIError as exc:
        logger.error("Failed to place MARKET order: %s", exc)
        return {"summary": summary, "response": None, "success": False, "error": str(exc)}

    except Exception as exc:
        logger.exception("Unexpected error placing MARKET order: %s", exc)
        return {"summary": summary, "response": None, "success": False, "error": str(exc)}


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> dict:
    """
    Place a LIMIT order on Binance Futures.

    Returns:
        dict with keys: summary, response, success, error
    """
    summary = _build_order_summary(symbol, side, "LIMIT", quantity, price=price)
    logger.info(
        "Placing LIMIT order | symbol=%s side=%s qty=%s price=%s tif=%s",
        symbol, side, _fmt(quantity), _fmt(price), time_in_force,
    )

    try:
        resp = client.place_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            quantity=_fmt(quantity),
            price=_fmt(price),
            timeInForce=time_in_force,
        )
        logger.info("LIMIT order placed successfully | orderId=%s status=%s", resp.get("orderId"), resp.get("status"))
        return {"summary": summary, "response": resp, "success": True, "error": None}

    except BinanceAPIError as exc:
        logger.error("Failed to place LIMIT order: %s", exc)
        return {"summary": summary, "response": None, "success": False, "error": str(exc)}

    except Exception as exc:
        logger.exception("Unexpected error placing LIMIT order: %s", exc)
        return {"summary": summary, "response": None, "success": False, "error": str(exc)}


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_price: Decimal,
) -> dict:
    """
    Place a STOP_MARKET order on Binance Futures (bonus order type).

    Returns:
        dict with keys: summary, response, success, error
    """
    summary = _build_order_summary(symbol, side, "STOP_MARKET", quantity, stop_price=stop_price)
    logger.info(
        "Placing STOP_MARKET order | symbol=%s side=%s qty=%s stopPrice=%s",
        symbol, side, _fmt(quantity), _fmt(stop_price),
    )

    try:
        resp = client.place_order(
            symbol=symbol,
            side=side,
            type="STOP_LOSS_LIMIT",
            quantity=_fmt(quantity),
            stopPrice=_fmt(stop_price),
            price=_fmt(stop_price),
            timeInForce="GTC",
        )
        logger.info("STOP_MARKET order placed | orderId=%s status=%s", resp.get("orderId"), resp.get("status"))
        return {"summary": summary, "response": resp, "success": True, "error": None}

    except BinanceAPIError as exc:
        logger.error("Failed to place STOP_MARKET order: %s", exc)
        return {"summary": summary, "response": None, "success": False, "error": str(exc)}

    except Exception as exc:
        logger.exception("Unexpected error placing STOP_MARKET order: %s", exc)
        return {"summary": summary, "response": None, "success": False, "error": str(exc)}


def dispatch_order(
    client: BinanceClient,
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Optional[Decimal] = None,
    stop_price: Optional[Decimal] = None,
) -> dict:
    """
    Central dispatcher — route to the correct order function by type.

    Args:
        client:      Authenticated BinanceClient instance.
        symbol:      Trading pair (e.g. BTCUSDT).
        side:        BUY or SELL.
        order_type:  MARKET | LIMIT | STOP_MARKET.
        quantity:    Order quantity.
        price:       Required for LIMIT orders.
        stop_price:  Required for STOP_MARKET orders.

    Returns:
        Result dict from the specific order function.
    """
    if order_type == "MARKET":
        return place_market_order(client, symbol, side, quantity)

    if order_type == "LIMIT":
        return place_limit_order(client, symbol, side, quantity, price)

    if order_type == "STOP_MARKET":
        return place_stop_market_order(client, symbol, side, quantity, stop_price)

    raise ValueError(f"Unsupported order type: {order_type}")
