"""Shared USDT-margined perpetual futures configuration and provider fallback.

Binance is tried first, then Bybit, then OKX. Each provider can be blocked by
region or missing a contract, so the first one that answers is used and its
name is recorded in ``DataFrame.attrs['source']``.
"""
import logging

from .http import get_json
from .validation import split_pair

logger = logging.getLogger("cryptofinance")

BASE_URL = "https://fapi.binance.com"
BYBIT_URL = "https://api.bybit.com"
OKX_URL = "https://www.okx.com"
PERIODS = {"5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"}
BYBIT_PERIODS = {"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1d"}
OKX_PERIODS = {"5m": "5m", "15m": "15m", "30m": "30m", "1h": "1H", "2h": "2H",
               "4h": "4H", "6h": "6H", "12h": "12H", "1d": "1D"}


def futures_pair(symbol):
    base, quote = split_pair(symbol)
    if quote == "USD":
        quote = "USDT"
    return base + quote


def okx_instrument(symbol):
    base, quote = split_pair(symbol)
    if quote == "USD":
        quote = "USDT"
    return f"{base}-{quote}-SWAP"


def validate_period(period):
    if period not in PERIODS:
        raise ValueError(f"period must be one of {sorted(PERIODS)}")


def provider_period(period, mapping, provider):
    if period not in mapping:
        raise ValueError(f"{provider} does not offer period {period!r}")
    return mapping[period]


def check_limit(limit, maximum, provider):
    if limit > maximum:
        raise ValueError(f"{provider} returns at most {maximum} rows per request")


def bybit_rows(path, params):
    data = get_json(f"{BYBIT_URL}{path}", params={"category": "linear", **params}, timeout=10)
    if data.get("retCode") != 0:
        raise ValueError(f"Bybit: {data.get('retMsg')}")
    rows = data.get("result", {}).get("list") or []
    if not rows:
        raise ValueError("Bybit returned no rows")
    return rows


def okx_rows(path, params):
    data = get_json(f"{OKX_URL}{path}", params=params, timeout=10)
    if data.get("code") != "0":
        raise ValueError(f"OKX: {data.get('msg')}")
    if not data.get("data"):
        raise ValueError("OKX returned no rows")
    return data["data"]


def first_available(symbol, what, providers):
    """Return the first provider's frame, sorted by time, tagged with its source."""
    errors = []
    for name, fetch in providers:
        try:
            df = fetch()
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            logger.debug("%s provider=%s symbol=%s failed: %s", what, name, symbol, exc)
            continue
        df = df.sort_values("timestamp").reset_index(drop=True)
        df.attrs["source"] = name
        return df
    raise ValueError(f"No {what} data found for '{symbol}'. Check that it has an active "
                     f"USDT perpetual on Binance, Bybit or OKX. {'; '.join(errors)}")
