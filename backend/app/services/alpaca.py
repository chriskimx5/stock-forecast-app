"""
Alpaca paper trading client.
Fill in ALPACA_API_KEY and ALPACA_SECRET_KEY in .env to activate.
All methods return None / empty gracefully when keys are missing.
"""
from __future__ import annotations

import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_HEADERS = {
    "APCA-API-KEY-ID": settings.alpaca_api_key,
    "APCA-API-SECRET-KEY": settings.alpaca_secret_key,
    "Content-Type": "application/json",
}


def _enabled() -> bool:
    return bool(settings.alpaca_api_key and settings.alpaca_secret_key)


def get_account() -> dict | None:
    if not _enabled():
        return None
    try:
        r = httpx.get(f"{settings.alpaca_base_url}/v2/account", headers=_HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Alpaca get_account failed: %s", e)
        return None


def get_positions() -> list[dict]:
    if not _enabled():
        return []
    try:
        r = httpx.get(f"{settings.alpaca_base_url}/v2/positions", headers=_HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Alpaca get_positions failed: %s", e)
        return []


def place_order(ticker: str, shares: float, side: str = "buy") -> dict | None:
    """side: 'buy' or 'sell'"""
    if not _enabled():
        logger.info("Alpaca not configured — skipping order %s %s %s", side, shares, ticker)
        return None
    try:
        payload = {
            "symbol": ticker,
            "qty": str(round(shares, 4)),
            "side": side,
            "type": "market",
            "time_in_force": "day",
        }
        r = httpx.post(f"{settings.alpaca_base_url}/v2/orders", headers=_HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Alpaca place_order failed: %s", e)
        return None


def close_position(ticker: str) -> dict | None:
    if not _enabled():
        return None
    try:
        r = httpx.delete(f"{settings.alpaca_base_url}/v2/positions/{ticker}", headers=_HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Alpaca close_position failed: %s", e)
        return None
