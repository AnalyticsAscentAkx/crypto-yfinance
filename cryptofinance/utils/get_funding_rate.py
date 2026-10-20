from .http import get_json
from .futures import BASE_URL, futures_pair, validate_period
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
    pair = futures_pair(symbol)
    positive_int(limit, 'limit', 1000)
    # One extra settlement lets the oldest returned row have a measured interval.
    data = get_json(
        f"{BASE_URL}/fapi/v1/fundingRate",
        params={"symbol": pair, "limit": min(limit + 1, 1000)},
        timeout=10,
    )
    if not isinstance(data, list):
        raise ValueError(f"Binance returned an unexpected response for {symbol}: {data}")

    if not data:
        raise ValueError(f"No funding rate data found for '{symbol}'. "
                         "Check that it has an active perpetual futures contract on Binance.")

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["fundingTime"], unit="ms")
    df["funding_rate"] = df["fundingRate"].astype(float)
    return _annualize(df).tail(limit).reset_index(drop=True)


def _annualize(df):
    df = df.sort_values("timestamp").reset_index(drop=True)
    # Settlement times can carry a few ms of jitter; intervals are whole hours.
    hours = (df["timestamp"].diff().dt.total_seconds() / 3600).round()
    df["funding_interval_hours"] = hours.bfill()
    df["annualized_pct"] = df["funding_rate"] * (24 / df["funding_interval_hours"]) * 365 * 100
    return df[["timestamp", "funding_rate", "funding_interval_hours", "annualized_pct"]]
