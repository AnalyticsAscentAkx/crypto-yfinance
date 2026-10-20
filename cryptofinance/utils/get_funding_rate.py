from .http import get_json
from .futures import (BASE_URL, bybit_rows, check_limit, first_available,
                      futures_pair, okx_instrument, okx_rows)
from .validation import positive_int
import pandas as pd
from .cache import ttl_cache

@ttl_cache(ttl=300)
def get_funding_rate(symbol: str, limit: int = 100) -> pd.DataFrame:
    """Return historical funding rates for a perpetual futures contract.

    Funding is paid between long and short traders every 8 hours on most major
    perps, but many contracts settle every 4 hours or every hour.
    A positive rate means longs pay shorts (market is bullish/overleveraged long).
    A negative rate means shorts pay longs (market is bearish/overleveraged short).

    Data comes from Binance, falling back to Bybit (max 199 rows) and then OKX
    (max 399 rows). The provider used is in ``df.attrs['source']``.

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'``, ``'ETH_USD'``
    limit  : number of records to return (default 100, max 1000)

    Returns
    -------
    DataFrame with columns: timestamp, funding_rate, funding_interval_hours,
    annualized_pct

    ``funding_interval_hours`` is measured from the spacing between settlements,
    so it follows contracts that change interval. ``annualized_pct`` uses it:
    ``funding_rate * (24 / funding_interval_hours) * 365 * 100``.
    """
    positive_int(limit, 'limit', 1000)
    # One extra settlement lets the oldest returned row have a measured interval.
    fetch = limit + 1
    df = first_available(symbol, "funding rate", (
        ("binance", lambda: _binance(symbol, min(fetch, 1000))),
        ("bybit", lambda: _bybit(symbol, fetch)),
        ("okx", lambda: _okx(symbol, fetch)),
    ))
    result = _annualize(df).tail(limit).reset_index(drop=True)
    result.attrs["source"] = df.attrs["source"]
    return result


def _binance(symbol, limit):
    data = get_json(
        f"{BASE_URL}/fapi/v1/fundingRate",
        params={"symbol": futures_pair(symbol), "limit": limit},
        timeout=10,
    )
    if not isinstance(data, list) or not data:
        raise ValueError(f"Binance returned no funding rates: {data}")
    return pd.DataFrame({
        "timestamp": pd.to_datetime([int(r["fundingTime"]) for r in data], unit="ms"),
        "funding_rate": [float(r["fundingRate"]) for r in data],
    })


def _bybit(symbol, limit):
    check_limit(limit, 200, "Bybit")
    rows = bybit_rows("/v5/market/funding/history",
                      {"symbol": futures_pair(symbol), "limit": limit})
    return pd.DataFrame({
        "timestamp": pd.to_datetime([int(r["fundingRateTimestamp"]) for r in rows], unit="ms"),
        "funding_rate": [float(r["fundingRate"]) for r in rows],
    })


def _okx(symbol, limit):
    check_limit(limit, 400, "OKX")
    rows = okx_rows("/api/v5/public/funding-rate-history",
                    {"instId": okx_instrument(symbol), "limit": limit})
    return pd.DataFrame({
        "timestamp": pd.to_datetime([int(r["fundingTime"]) for r in rows], unit="ms"),
        "funding_rate": [float(r.get("realizedRate") or r["fundingRate"]) for r in rows],
    })


def _annualize(df):
    df = df.sort_values("timestamp").reset_index(drop=True)
    # Settlement times can carry a few ms of jitter; intervals are whole hours.
    hours = (df["timestamp"].diff().dt.total_seconds() / 3600).round()
    df["funding_interval_hours"] = hours.bfill()
    df["annualized_pct"] = df["funding_rate"] * (24 / df["funding_interval_hours"]) * 365 * 100
    return df[["timestamp", "funding_rate", "funding_interval_hours", "annualized_pct"]]
