"""Shared Binance USD-margined futures API configuration."""
from .validation import split_pair

BASE_URL = "https://fapi.binance.com"
PERIODS = {"5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"}


def futures_pair(symbol):
    base, quote = split_pair(symbol)
    if quote == "USD":
        quote = "USDT"
    return base + quote


def validate_period(period):
    if period not in PERIODS:
        raise ValueError(f"period must be one of {sorted(PERIODS)}")
