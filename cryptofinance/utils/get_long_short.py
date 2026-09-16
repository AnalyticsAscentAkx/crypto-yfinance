from .http import get_json
from .futures import BASE_URL, futures_pair, validate_period
from .validation import positive_int
import pandas as pd
from .cache import ttl_cache

@ttl_cache(ttl=300)
def get_long_short_ratio(symbol: str, period: str = "1d", limit: int = 30) -> pd.DataFrame:
    """Return the global long/short account ratio from Binance Futures.

    This is the ratio of accounts that hold net long positions vs. net short.
    It's a contrarian indicator — when the crowd is heavily one-sided,
    the market often moves against them.

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
    pair = futures_pair(symbol)
    positive_int(limit, 'limit', 500)
    validate_period(period)
    data = get_json(
        f"{BASE_URL}/futures/data/globalLongShortAccountRatio",
        params={"symbol": pair, "period": period, "limit": limit},
        timeout=10,
    )
    if not isinstance(data, list):
        raise ValueError(f"Binance returned an unexpected response for {symbol}: {data}")

    if not data:
        raise ValueError(f"No long/short data found for '{symbol}'.")

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["long_short_ratio"] = df["longShortRatio"].astype(float)
    df["long_pct"] = df["longAccount"].astype(float) * 100
    df["short_pct"] = df["shortAccount"].astype(float) * 100
    return df[["timestamp", "long_short_ratio", "long_pct", "short_pct"]].sort_values("timestamp").reset_index(drop=True)
