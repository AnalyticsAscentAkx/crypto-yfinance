import requests
import pandas as pd
from .cache import ttl_cache


@ttl_cache(ttl=3600)
def get_fear_greed(days: int = 30) -> pd.DataFrame:
    """Return the Crypto Fear & Greed Index history.

    Data comes from the alternative.me API — updated once per day.

    Parameters
    ----------
    days : how many days of history to return (default 30, max ~2000)

    Returns
    -------
    DataFrame with columns: timestamp, value, classification

    Classifications: ``Extreme Fear``, ``Fear``, ``Neutral``, ``Greed``, ``Extreme Greed``

    Examples
    --------
    >>> df = get_fear_greed(30)
    >>> print(df.tail())
    """
    url = f"https://api.alternative.me/fng/?limit={days}&format=json"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json().get("data", [])

    rows = []
    for entry in data:
        rows.append({
            "timestamp": pd.to_datetime(int(entry["timestamp"]), unit="s"),
            "value": int(entry["value"]),
            "classification": entry["value_classification"],
        })

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return df
