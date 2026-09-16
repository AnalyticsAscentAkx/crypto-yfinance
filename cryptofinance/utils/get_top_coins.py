from .clients import CoinGeckoAPI
import pandas as pd
from .cache import ttl_cache


@ttl_cache(ttl=300)
def get_top_coins(n: int = 50, currency: str = "usd") -> pd.DataFrame:
    """Return the top N coins ranked by market cap.

    Parameters
    ----------
    n        : number of coins to return (default 50, max 250)
    currency : quote currency for prices (default ``'usd'``)

    Returns
    -------
    DataFrame with columns: rank, name, symbol, price, market_cap,
    volume_24h, price_change_pct_24h, ath, circulating_supply
    """
    cg = CoinGeckoAPI()
    per_page = min(n, 250)
    raw = cg.get_coins_markets(
        vs_currency=currency,
        order="market_cap_desc",
        per_page=per_page,
        page=1,
        sparkline=False,
        price_change_percentage="24h",
    )

    rows = []
    for i, c in enumerate(raw[:n], start=1):
        rows.append({
            "rank": i,
            "name": c.get("name"),
            "symbol": c.get("symbol", "").upper(),
            "price": c.get("current_price"),
            "market_cap": c.get("market_cap"),
            "volume_24h": c.get("total_volume"),
            "price_change_pct_24h": c.get("price_change_percentage_24h"),
            "ath": c.get("ath"),
            "circulating_supply": c.get("circulating_supply"),
            "coingecko_id": c.get("id"),
        })

    return pd.DataFrame(rows)
