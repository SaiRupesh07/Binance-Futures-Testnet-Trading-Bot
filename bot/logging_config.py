"""
Logging configuration for the trading bot.
Sets up both file and console handlers with structured formatting.
"""

import logging
import logging.handlers
import os
from pathlib import Path


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "trading_bot.log"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return the root logger with file + console handlers.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured logger instance.
    """
    LOG_DIR.mkdir(exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)  # capture everything; handlers filter

    if logger.handlers:
        # Avoid duplicate handlers if called multiple times
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── File handler (DEBUG+) ──────────────────────────────────────────────
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # ── Console handler (INFO+ by default) ────────────────────────────────
    ch = logging.StreamHandler()
    ch.setLevel(numeric_level)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'trading_bot' namespace."""
    return logging.getLogger(f"trading_bot.{name}")
