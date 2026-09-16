from .clients import CoinGeckoAPI
from .cache import ttl_cache


@ttl_cache(ttl=300)
def get_trending() -> list:
    """Return the top 7 trending coins on CoinGecko right now.

    These are ranked by search volume over the last 24 hours.

    Returns
    -------
    list of dicts, each with: name, symbol, market_cap_rank, price_btc, score
    """
    cg = CoinGeckoAPI()
    raw = cg.get_search_trending()
    out = []
    for item in raw.get("coins", []):
        c = item.get("item", {})
        out.append({
            "name": c.get("name"),
            "symbol": c.get("symbol"),
            "market_cap_rank": c.get("market_cap_rank"),
            "price_btc": c.get("price_btc"),
            "score": c.get("score"),
            "thumb": c.get("thumb"),
            "coingecko_id": c.get("id"),
        })
    return out
