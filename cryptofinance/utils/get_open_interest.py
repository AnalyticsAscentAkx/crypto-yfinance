from .http import get_json
from .futures import (BASE_URL, BYBIT_PERIODS, OKX_PERIODS, bybit_rows, check_limit,
                      first_available, futures_pair, okx_instrument, okx_rows,
                      provider_period, validate_period)
from .validation import positive_int
import pandas as pd
from .cache import ttl_cache

@ttl_cache(ttl=300)
def get_open_interest(symbol: str, period: str = "1d", limit: int = 30) -> pd.DataFrame:
    """Return historical open interest for a perpetual futures contract.

    Open interest = total value of outstanding futures positions.
    Rising OI alongside rising price confirms a strong trend.
    Rising OI alongside falling price suggests a short-driven move.

    Data comes from Binance, falling back to Bybit (no USD value, so
    ``open_interest_usd`` is NaN; max 200 rows) and then OKX (max 100 rows).
    Open interest is exchange-specific, so the level differs between providers.
    The provider used is in ``df.attrs['source']``. OKX daily rows are stamped
    16:00 UTC (midnight in Hong Kong) rather than 00:00 UTC.

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'``, ``'ETH_USD'``
    period : ``'5m'``, ``'15m'``, ``'30m'``, ``'1h'``, ``'2h'``, ``'4h'``,
             ``'6h'``, ``'12h'``, ``'1d'`` (default)
    limit  : number of records (default 30, max 500)

    Returns
    -------
    DataFrame with columns: timestamp, open_interest, open_interest_usd
    ``open_interest`` is in units of the base coin.
    """
    positive_int(limit, 'limit', 500)
    validate_period(period)
    return first_available(symbol, "open interest", (
        ("binance", lambda: _binance(symbol, period, limit)),
        ("bybit", lambda: _bybit(symbol, period, limit)),
        ("okx", lambda: _okx(symbol, period, limit)),
    ))


def _binance(symbol, period, limit):
    data = get_json(
        f"{BASE_URL}/futures/data/openInterestHist",
        params={"symbol": futures_pair(symbol), "period": period, "limit": limit},
        timeout=10,
    )
    if not isinstance(data, list) or not data:
        raise ValueError(f"Binance returned no open interest: {data}")
    return pd.DataFrame({
        "timestamp": pd.to_datetime([int(r["timestamp"]) for r in data], unit="ms"),
        "open_interest": [float(r["sumOpenInterest"]) for r in data],
        "open_interest_usd": [float(r["sumOpenInterestValue"]) for r in data],
    })


def _bybit(symbol, period, limit):
    check_limit(limit, 200, "Bybit")
    rows = bybit_rows("/v5/market/open-interest", {
        "symbol": futures_pair(symbol), "limit": limit,
        "intervalTime": provider_period(period, BYBIT_PERIODS, "Bybit"),
    })
    # openInterest counts both sides; singleOpenInterest matches Binance and OKX.
    return pd.DataFrame({
        "timestamp": pd.to_datetime([int(r["timestamp"]) for r in rows], unit="ms"),
        "open_interest": [float(r.get("singleOpenInterest") or r["openInterest"]) for r in rows],
        "open_interest_usd": float("nan"),
    })


def _okx(symbol, period, limit):
    check_limit(limit, 100, "OKX")
    # Rows are [ts, contracts, base-coin amount, USD value].
    rows = okx_rows("/api/v5/rubik/stat/contracts/open-interest-history", {
        "instId": okx_instrument(symbol), "limit": limit,
        "period": provider_period(period, OKX_PERIODS, "OKX"),
    })
    return pd.DataFrame({
        "timestamp": pd.to_datetime([int(r[0]) for r in rows], unit="ms"),
        "open_interest": [float(r[2]) for r in rows],
        "open_interest_usd": [float(r[3]) for r in rows],
    })
