"""
Binance Futures Testnet REST client.

Handles authentication (HMAC-SHA256 signing), request execution,
response parsing, and low-level error propagation.
Uses only the standard library + requests — no python-binance dependency.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Optional
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

logger = get_logger("client")

BASE_URL = "https://testnet.binance.vision"
RECV_WINDOW = 5000  # ms


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error payload."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures REST API.

    Responsibilities:
    - Sign requests with HMAC-SHA256
    - Attach API-Key header
    - Log request / response pairs
    - Translate error payloads into BinanceAPIError
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL) -> None:
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret.encode()
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceClient initialised. base_url=%s", self._base_url)

    # ──────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, query_string: str) -> str:
        return hmac.new(self._api_secret, query_string.encode(), hashlib.sha256).hexdigest()

    def _build_signed_params(self, params: dict) -> dict:
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = RECV_WINDOW
        qs = urlencode(params)
        params["signature"] = self._sign(qs)
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        signed: bool = True,
    ) -> Any:
        url = f"{self._base_url}{endpoint}"
        params = params or {}

        if signed:
            params = self._build_signed_params(params)

        logger.debug(
            "REQUEST  method=%s url=%s params=%s",
            method.upper(),
            url,
            {k: v for k, v in params.items() if k != "signature"},
        )

        try:
            if method.upper() in ("GET", "DELETE"):
                resp = self._session.request(method, url, params=params, timeout=10)
            else:
                resp = self._session.request(method, url, data=params, timeout=10)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out: %s", exc)
            raise

        logger.debug(
            "RESPONSE status=%s body=%s",
            resp.status_code,
            resp.text[:500],
        )

        try:
            data = resp.json()
        except ValueError:
            resp.raise_for_status()
            raise

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            err = BinanceAPIError(data["code"], data.get("msg", "Unknown error"))
            logger.error("API error: %s", err)
            raise err

        resp.raise_for_status()
        return data

    # ──────────────────────────────────────────────────────────────────────
    # Public API methods
    # ──────────────────────────────────────────────────────────────────────

    def get_server_time(self) -> dict:
        """Fetch server time (unsigned). Useful for connectivity checks."""
        return self._request("GET", "/api/v3/time", signed=False)

    def get_exchange_info(self) -> dict:
        """Return exchange info including symbol filters."""
        return self._request("GET", "/api/v3/exchangeInfo", signed=False)

    def get_account(self) -> dict:
        """Return futures account information."""
        return self._request("GET", "/api/v3/account")

    def place_order(self, **kwargs) -> dict:
        """
        Place a futures order.

        Accepted kwargs mirror the Binance /api/v3/order POST parameters:
          symbol, side, type, quantity, price, timeInForce, stopPrice, etc.
        """
        params = {k: str(v) for k, v in kwargs.items() if v is not None}
        return self._request("POST", "/api/v3/order", params=params)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order by orderId."""
        return self._request(
            "DELETE",
            "/api/v3/order",
            params={"symbol": symbol, "orderId": order_id},
        )

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query a specific order."""
        return self._request(
            "GET",
            "/api/v3/order",
            params={"symbol": symbol, "orderId": order_id},
        )
