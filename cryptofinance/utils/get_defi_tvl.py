import requests
import pandas as pd
from .cache import ttl_cache
from .validation import positive_int

_LLAMA = "https://api.llama.fi"


@ttl_cache(ttl=600)
def get_defi_tvl(protocol: str) -> pd.DataFrame:
    """Return historical TVL for a DeFi protocol via DeFiLlama.

    Parameters
    ----------
    protocol : protocol slug, e.g. ``'uniswap'``, ``'aave'``, ``'curve'``,
               ``'lido'``, ``'makerdao'``, ``'compound'``, ``'pancakeswap'``

    Returns
    -------
    DataFrame with columns: timestamp, tvl_usd

    Examples
    --------
    >>> df = get_defi_tvl('uniswap')
    >>> df.tail()
    """
    resp = requests.get(f"{_LLAMA}/protocol/{protocol.lower()}", timeout=10)
    if resp.status_code == 404:
        raise ValueError(
            f"Protocol '{protocol}' not found on DeFiLlama. "
            "Try a slug like 'uniswap', 'aave', 'curve', 'lido', 'makerdao'."
        )
    resp.raise_for_status()
    raw = resp.json()

    tvl_data = raw.get("tvl", [])
    rows = [
        {"timestamp": pd.to_datetime(entry["date"], unit="s"), "tvl_usd": entry["totalLiquidityUSD"]}
        for entry in tvl_data
    ]
    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


@ttl_cache(ttl=600)
def get_top_defi(n: int = 20) -> pd.DataFrame:
    """Return the top N DeFi protocols by current TVL.

    Parameters
    ----------
    n : number of protocols (default 20)

    Returns
    -------
    DataFrame with columns: name, symbol, tvl_usd, chain, category, change_1h, change_1d, change_7d
    """
    positive_int(n, "n")
    resp = requests.get(f"{_LLAMA}/protocols", timeout=10)
    resp.raise_for_status()
    protocols = resp.json()

    rows = []
    for p in sorted(protocols, key=lambda x: x.get("tvl") or 0, reverse=True)[:n]:
        rows.append({
            "name": p.get("name"),
            "symbol": p.get("symbol"),
            "tvl_usd": p.get("tvl"),
            "chain": p.get("chain"),
            "category": p.get("category"),
            "change_1h": p.get("change_1h"),
            "change_1d": p.get("change_1d"),
            "change_7d": p.get("change_7d"),
        })
    return pd.DataFrame(rows)


@ttl_cache(ttl=600)
def get_tvl_by_chain() -> pd.DataFrame:
    """Return current TVL broken down by blockchain.

    Returns
    -------
    DataFrame with columns: chain, tvl_usd

    Useful for tracking which L1/L2 ecosystem is winning DeFi market share.
    """
    resp = requests.get(f"{_LLAMA}/v2/chains", timeout=10)
    resp.raise_for_status()
    chains = resp.json()

    rows = [{"chain": c.get("name"), "tvl_usd": c.get("tvl")} for c in chains]
    return pd.DataFrame(rows).sort_values("tvl_usd", ascending=False).reset_index(drop=True)
