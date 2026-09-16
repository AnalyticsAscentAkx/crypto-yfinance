from .clients import CoinGeckoAPI
from .cache import ttl_cache


@ttl_cache(ttl=300)
def get_dominance() -> dict:
    """Return market dominance percentages for all major assets.

    Sourced from CoinGecko's global market data endpoint.

    Returns
    -------
    dict mapping ticker symbol → dominance percentage (float)

    Example
    -------
    >>> d = get_dominance()
    >>> print(d['BTC'])   # e.g. 52.4
    >>> print(d['ETH'])   # e.g. 17.1
    """
    cg = CoinGeckoAPI()
    global_data = cg.get_global()
    raw = global_data.get("market_cap_percentage", {})
    return {sym.upper(): round(pct, 4) for sym, pct in raw.items()}
