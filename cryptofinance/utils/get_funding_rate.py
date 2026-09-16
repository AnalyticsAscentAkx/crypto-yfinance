from .http import get_json
from .futures import BASE_URL, futures_pair, validate_period
from .validation import positive_int
import pandas as pd
from .cache import ttl_cache

@ttl_cache(ttl=300)
def get_funding_rate(symbol: str, limit: int = 100) -> pd.DataFrame:
    """Return historical funding rates for a perpetual futures contract.

    Funding rates are paid every 8 hours between long and short traders.
    A positive rate means longs pay shorts (market is bullish/overleveraged long).
    A negative rate means shorts pay longs (market is bearish/overleveraged short).

    Parameters
    ----------
    symbol : e.g. ``'BTC_USD'``, ``'ETH_USD'``
    limit  : number of records to return (default 100, max 1000)

    Returns
    -------
    DataFrame with columns: timestamp, funding_rate, annualized_pct

    ``annualized_pct`` assumes 3 funding periods per day × 365 days.
    """
    pair = futures_pair(symbol)
    positive_int(limit, 'limit', 1000)
    data = get_json(
        f"{BASE_URL}/fapi/v1/fundingRate",
        params={"symbol": pair, "limit": limit},
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
    df["annualized_pct"] = df["funding_rate"] * 3 * 365 * 100  # 8h intervals → annualised
    return df[["timestamp", "funding_rate", "annualized_pct"]].sort_values("timestamp").reset_index(drop=True)
