#!/usr/bin/env python3
"""
CLI entry point for the Binance Futures Testnet trading bot.

Usage examples:
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 80000
  python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 75000
  python cli.py account
  python cli.py ping
"""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import argparse
import os
import sys
from typing import Optional

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logging, get_logger
from bot.orders import dispatch_order
from bot.validators import validate_all

# ── ANSI colours (degrade gracefully on Windows without colorama) ──────────
try:
    import colorama
    colorama.init(autoreset=True)
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"
except ImportError:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = ""


def _env(key: str, required: bool = True) -> Optional[str]:
    val = os.environ.get(key)
    if required and not val:
        print(f"{RED}ERROR: environment variable {key!r} is not set.{RESET}")
        print(f"  Set it with:  export {key}=<your_value>")
        sys.exit(1)
    return val


def _print_separator(char: str = "─", width: int = 60) -> None:
    print(char * width)


def _print_order_summary(summary: dict) -> None:
    _print_separator()
    print(f"{BOLD}{CYAN}  ORDER REQUEST SUMMARY{RESET}")
    _print_separator()
    print(f"  Symbol     : {BOLD}{summary['symbol']}{RESET}")
    print(f"  Side       : {BOLD}{summary['side']}{RESET}")
    print(f"  Type       : {summary['type']}")
    print(f"  Quantity   : {summary['quantity']}")
    if summary.get("price") and summary["price"] != "N/A":
        print(f"  Price      : {summary['price']}")
    if summary.get("stop_price") and summary["stop_price"] != "N/A":
        print(f"  Stop Price : {summary['stop_price']}")
    _print_separator()


def _print_order_response(resp: dict) -> None:
    print(f"{BOLD}{CYAN}  ORDER RESPONSE DETAILS{RESET}")
    _print_separator()
    print(f"  orderId      : {resp.get('orderId', 'N/A')}")
    print(f"  clientOrderId: {resp.get('clientOrderId', 'N/A')}")
    print(f"  status       : {BOLD}{resp.get('status', 'N/A')}{RESET}")
    print(f"  executedQty  : {resp.get('executedQty', 'N/A')}")
    print(f"  avgPrice     : {resp.get('avgPrice', 'N/A')}")
    print(f"  price        : {resp.get('price', 'N/A')}")
    print(f"  type         : {resp.get('type', 'N/A')}")
    print(f"  side         : {resp.get('side', 'N/A')}")
    print(f"  timeInForce  : {resp.get('timeInForce', 'N/A')}")
    _print_separator()


# ── Sub-command handlers ───────────────────────────────────────────────────

def cmd_place(args: argparse.Namespace, client: BinanceClient, logger) -> int:
    """Handle the 'place' sub-command."""
    try:
        params = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
            stop_price=getattr(args, "stop_price", None),
        )
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        print(f"\n{RED}✗ Validation error: {exc}{RESET}\n")
        return 1

    _print_order_summary({
        "symbol":     params["symbol"],
        "side":       params["side"],
        "type":       params["order_type"],
        "quantity":   str(params["quantity"]),
        "price":      str(params["price"]) if params["price"] else "N/A",
        "stop_price": str(params["stop_price"]) if params["stop_price"] else "N/A",
    })

    result = dispatch_order(client, **params)

    if result["success"]:
        _print_order_response(result["response"])
        print(f"{GREEN}{BOLD}✔ Order placed successfully!{RESET}\n")
        return 0
    else:
        print(f"\n{RED}✗ Order failed: {result['error']}{RESET}\n")
        return 1


def cmd_account(args: argparse.Namespace, client: BinanceClient, logger) -> int:
    """Handle the 'account' sub-command."""
    logger.info("Fetching account information.")
    try:
        info = client.get_account()
        print(f"\n{BOLD}{CYAN}ACCOUNT INFORMATION{RESET}")
        _print_separator()
        balances = [
            b for b in info.get('balances', [])
            if float(b.get('free', 0)) > 0 or float(b.get('locked', 0)) > 0
        ]
        if balances:
            for b in balances:
                print(f"  {b['asset']:<10} free: {b['free']}  locked: {b['locked']}")
        else:
            print("  No non-zero balances found.")
        _print_separator()
        return 0
    except BinanceAPIError as exc:
        logger.error("Account fetch error: %s", exc)
        print(f"{RED}✗ {exc}{RESET}")
        return 1


def cmd_ping(args: argparse.Namespace, client: BinanceClient, logger) -> int:
    """Handle the 'ping' sub-command."""
    logger.info("Pinging Binance Futures Testnet.")
    try:
        ts = client.get_server_time()
        print(f"\n{GREEN}✔ Connected to Binance Futures Testnet{RESET}")
        print(f"  Server time: {ts.get('serverTime')} ms\n")
        return 0
    except Exception as exc:
        logger.error("Ping failed: %s", exc)
        print(f"{RED}✗ Cannot reach testnet: {exc}{RESET}")
        return 1


# ── Argument parser ────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py ping
  python cli.py account
  python cli.py place --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT  --quantity 0.001 --price 80000
  python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 75000
        """,
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log verbosity (default: INFO). File always gets DEBUG.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ── place ──
    place_p = sub.add_parser("place", help="Place a new futures order.")
    place_p.add_argument("--symbol",     required=True, help="Trading pair, e.g. BTCUSDT")
    place_p.add_argument("--side",       required=True, choices=["BUY", "SELL"], help="Order side")
    place_p.add_argument("--type",       required=True, choices=["MARKET", "LIMIT", "STOP_MARKET"],
                         help="Order type")
    place_p.add_argument("--quantity",   required=True, type=float, help="Order quantity")
    place_p.add_argument("--price",      type=float, default=None,
                         help="Limit price (required for LIMIT orders)")
    place_p.add_argument("--stop-price", dest="stop_price", type=float, default=None,
                         help="Stop price (required for STOP_MARKET orders)")

    # ── account ──
    sub.add_parser("account", help="Display account balances.")

    # ── ping ──
    sub.add_parser("ping", help="Check connectivity to the testnet.")

    return parser


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logger = setup_logging(args.log_level)
    log = get_logger("cli")
    log.info("Trading bot started | command=%s", args.command)

    api_key    = _env("BINANCE_TESTNET_API_KEY")
    api_secret = _env("BINANCE_TESTNET_API_SECRET")

    try:
        client = BinanceClient(api_key, api_secret)
    except ValueError as exc:
        print(f"{RED}✗ Client init error: {exc}{RESET}")
        sys.exit(1)

    command_map = {
        "place":   cmd_place,
        "account": cmd_account,
        "ping":    cmd_ping,
    }

    handler = command_map[args.command]
    exit_code = handler(args, client, log)
    log.info("Trading bot finished | exit_code=%s", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()