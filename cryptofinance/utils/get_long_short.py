from .http import get_json
from .futures import (BASE_URL, BYBIT_PERIODS, OKX_PERIODS, bybit_rows, check_limit,
                      first_available, futures_pair, okx_instrument, okx_rows,
                      provider_period, validate_period)
from .validation import positive_int
import pandas as pd
from .cache import ttl_cache

@ttl_cache(ttl=300)
def get_long_short_ratio(symbol: str, period: str = "1d", limit: int = 30) -> pd.DataFrame:
    """Return the global long/short account ratio for a perpetual futures contract.

    This is the ratio of accounts that hold net long positions vs. net short.
    It's a contrarian indicator — when the crowd is heavily one-sided,
    the market often moves against them.

    Data comes from Binance, falling back to Bybit (max 500 rows) and then OKX
    (max 100 rows). Each exchange measures its own users, so levels differ
    between providers. The provider used is in ``df.attrs['source']``.
    OKX daily rows are stamped 16:00 UTC (midnight in Hong Kong) rather than 00:00 UTC.

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'``, ``'ETH_USD'``
    period : ``'5m'``, ``'15m'``, ``'30m'``, ``'1h'``, ``'2h'``, ``'4h'``,
             ``'6h'``, ``'12h'``, ``'1d'`` (default)
    limit  : number of records (default 30, max 500)

    Returns
    -------
    DataFrame with columns: timestamp, long_short_ratio, long_pct, short_pct
    """
    positive_int(limit, 'limit', 500)
    validate_period(period)
    return first_available(symbol, "long/short", (
        ("binance", lambda: _binance(symbol, period, limit)),
        ("bybit", lambda: _bybit(symbol, period, limit)),
        ("okx", lambda: _okx(symbol, period, limit)),
    ))


def _frame(timestamps, long_share):
    long_share = pd.Series(long_share, dtype=float)
    return pd.DataFrame({
        "timestamp": pd.to_datetime(timestamps, unit="ms"),
        "long_short_ratio": long_share / (1 - long_share),
        "long_pct": long_share * 100,
        "short_pct": (1 - long_share) * 100,
    })


def _binance(symbol, period, limit):
    data = get_json(
        f"{BASE_URL}/futures/data/globalLongShortAccountRatio",
        params={"symbol": futures_pair(symbol), "period": period, "limit": limit},
        timeout=10,
    )
    if not isinstance(data, list) or not data:
        raise ValueError(f"Binance returned no long/short data: {data}")
    df = _frame([int(r["timestamp"]) for r in data], [float(r["longAccount"]) for r in data])
    # Keep Binance's own published ratio rather than the recomputed one.
    df["long_short_ratio"] = [float(r["longShortRatio"]) for r in data]
    return df


def _bybit(symbol, period, limit):
    check_limit(limit, 500, "Bybit")
    rows = bybit_rows("/v5/market/account-ratio", {
        "symbol": futures_pair(symbol), "limit": limit,
        "period": provider_period(period, BYBIT_PERIODS, "Bybit"),
    })
    return _frame([int(r["timestamp"]) for r in rows], [float(r["buyRatio"]) for r in rows])


def _okx(symbol, period, limit):
    check_limit(limit, 100, "OKX")
    # Rows are [ts, long/short ratio].
    rows = okx_rows("/api/v5/rubik/stat/contracts/long-short-account-ratio-contract", {
        "instId": okx_instrument(symbol), "limit": limit,
        "period": provider_period(period, OKX_PERIODS, "OKX"),
    })
    ratio = pd.Series([float(r[1]) for r in rows])
    return _frame([int(r[0]) for r in rows], ratio / (1 + ratio))
