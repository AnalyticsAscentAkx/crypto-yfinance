from .http import get_json
from .futures import BASE_URL, futures_pair, validate_period
from .validation import positive_int
import pandas as pd
from .cache import ttl_cache

@ttl_cache(ttl=300)
def get_open_interest(symbol: str, period: str = "1d", limit: int = 30) -> pd.DataFrame:
    """Return historical open interest for a perpetual futures contract on Binance.

    Open interest = total value of outstanding futures positions.
    Rising OI alongside rising price confirms a strong trend.
    Rising OI alongside falling price suggests a short-driven move.

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'``, ``'ETH_USD'``
    period : ``'5m'``, ``'15m'``, ``'30m'``, ``'1h'``, ``'2h'``, ``'4h'``,
             ``'6h'``, ``'12h'``, ``'1d'`` (default)
    limit  : number of records (default 30, max 500)

    Returns
    -------
    DataFrame with columns: timestamp, open_interest, open_interest_usd
    """
    pair = futures_pair(symbol)
    positive_int(limit, 'limit', 500)
    validate_period(period)
    data = get_json(
        f"{BASE_URL}/futures/data/openInterestHist",
        params={"symbol": pair, "period": period, "limit": limit},
        timeout=10,
    )
    if not isinstance(data, list):
        raise ValueError(f"Binance returned an unexpected response for {symbol}: {data}")

    if not data:
        raise ValueError(f"No open interest data found for '{symbol}'.")

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["open_interest"] = df["sumOpenInterest"].astype(float)
    df["open_interest_usd"] = df["sumOpenInterestValue"].astype(float)
    return df[["timestamp", "open_interest", "open_interest_usd"]].sort_values("timestamp").reset_index(drop=True)
