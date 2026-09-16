from .clients import CoinGeckoAPI


def search_symbol(query: str, quote: str = "USD", limit: int = 10) -> list:
    """Search CoinGecko for current and newly launched cryptocurrencies.

    Results include a ready-to-use ``pair`` value for :class:`Ticker`. Exact
    symbol/name/ID matches are ordered first, followed by market-cap rank.
    """
    clean = str(query).strip()
    clean_quote = str(quote).strip().upper()
    if not clean:
        raise ValueError("query must be non-empty")
    if not clean_quote.isalnum():
        raise ValueError("quote must contain only letters or numbers")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
        raise ValueError("limit must be an integer from 1 to 50")

    try:
        coins = CoinGeckoAPI().search(clean).get("coins", [])
    except Exception as exc:
        raise ValueError(f"Symbol search failed: {exc}") from exc

    lowered = clean.lower()

    def order(coin):
        exact = not (
            coin.get("id", "").lower() == lowered
            or coin.get("symbol", "").lower() == lowered
            or coin.get("name", "").lower() == lowered
        )
        rank = coin.get("market_cap_rank")
        return exact, rank if isinstance(rank, int) and rank > 0 else 10**9

    output = []
    for coin in sorted(coins, key=order)[:limit]:
        symbol = coin.get("symbol", "").upper()
        if not symbol:
            continue
        output.append({
            "id": coin.get("id"),
            "symbol": symbol,
            "name": coin.get("name"),
            "market_cap_rank": coin.get("market_cap_rank"),
            "pair": f"{symbol}_{clean_quote}",
        })
    return output
